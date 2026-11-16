"""Relay notice subscribers: the profile session notice and the stale-instructions notice.

Each reads one relay schema-2 SubscriberEnvelope (relay docs/adapters.md, Hook events)
and writes exactly `{}` or `{"context": TEXT}` (Notice protocol). Native encoding is
relay's; these commands never see a harness payload.
"""
import json
import pathlib
import subprocess
import sys

from ._configuration import ProfileError
from ._profiles import resolve
from ._rendering import ROOT, command, session_text

INPUT_LIMIT = 4 * 1024 * 1024
CONTEXT_LIMIT = 10_000  # relay's ceiling, in UTF-16 code units (JavaScript string length)
CHECK_TIMEOUT = 10


class EnvelopeError(ValueError):
    pass


def _object(pairs):
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise EnvelopeError('duplicate key')
    return dict(pairs)


def read_envelope(raw):
    """The SessionStart event of one envelope, or EnvelopeError naming what is wrong."""
    try:
        if len(raw) > INPUT_LIMIT:
            raise EnvelopeError('over 4 MiB')
        try:
            data = json.loads(raw.decode('utf-8'), object_pairs_hook=_object)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise EnvelopeError(f'not strict UTF-8 JSON ({error.__class__.__name__})') from None
        if not isinstance(data, dict) or data.get('schema') != 2 or data.get('type') != 'event':
            raise EnvelopeError('not a schema-2 event envelope')
        event = data.get('event')
        if not isinstance(event, dict) or event.get('schema') != 2:
            raise EnvelopeError('event is not a schema-2 HookEvent')
        if event.get('kind') != 'session-start':
            raise EnvelopeError(f"event kind {event.get('kind')!r}, expected 'session-start'")
        cwd = event.get('cwd')
        if not isinstance(cwd, str) or not pathlib.PurePath(cwd).is_absolute():
            raise EnvelopeError('event cwd is not an absolute path')
        if not isinstance(event.get('private'), dict):
            raise EnvelopeError('event private is not an object')
        return event
    except EnvelopeError as error:
        raise EnvelopeError(f'relay envelope rejected: {error}') from None


def _transcript(event):
    """The valid transcriptPath fact, else None; a missing or invalid fact names no home."""
    fact = event['private'].get('transcriptPath')
    if fact is None or (isinstance(fact, dict) and fact.get('status') in ('missing', 'invalid')):
        return None
    if not (isinstance(fact, dict) and fact.get('status') == 'valid' and isinstance(fact.get('value'), str)):
        raise EnvelopeError('relay envelope rejected: malformed transcriptPath fact')
    return fact['value']


def _units(text):
    return len(text.encode('utf-16-le')) // 2


def _reply(text):
    return json.dumps({'context': text}) if text else '{}'


def unresolved(error):
    """The one line every profile failure becomes, as hooks/claude-profile prints it."""
    reason = ' '.join(str(error).splitlines())
    return f'profile: unresolved — {reason}; repair the lore checkout, then run {command("session")}\n'


def profile_notice(raw, env):
    """The native hook's text as context: export only after the text fits, and every
    failure, invalid input included, is one visible line rather than an omission."""
    try:
        event = read_envelope(raw)
        transcript = _transcript(event)
        result = resolve(event['cwd'], env, {'transcript_path': transcript} if transcript else None)
        text = session_text(result)
        if _units(text) > CONTEXT_LIMIT:
            raise ProfileError(f'session text is {_units(text)} UTF-16 units, over relay\'s {CONTEXT_LIMIT} context limit')
        if env.get('CLAUDE_ENV_FILE'):
            with open(env['CLAUDE_ENV_FILE'], 'a') as handle:
                handle.write(f"export AGENT_PROFILE={','.join(p['name'] for p in result['profiles'])}\n")
    except Exception as error:
        text = unresolved(error)
    return _reply(text)


class NoticeFailed(RuntimeError):
    """An execution failure: no context, a nonzero exit relay reports as NOTICE_FAILED."""


def stale_notice(raw, env):
    """One line when this checkout's delivered instructions or Projects block are stale.
    Only validation/drift (exit 1) becomes context; its stderr is the check's own report."""
    read_envelope(raw)
    script = ROOT / 'bin/assemble-instructions'
    try:
        checked = subprocess.run([sys.executable, str(script), 'check', '--working-tree'], cwd=ROOT,
                                 env=dict(env), capture_output=True, text=True, timeout=CHECK_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise NoticeFailed(f'assemble-instructions check timed out after {CHECK_TIMEOUT} s') from None
    except OSError as error:
        raise NoticeFailed(f'assemble-instructions check could not run: {error.strerror}') from None
    if checked.returncode == 0:
        return _reply(None)
    if checked.returncode != 1:
        raise NoticeFailed(f'assemble-instructions check exited {checked.returncode}')
    report = checked.stderr.strip() or 'assemble-instructions: validation failed'
    text = ' '.join(report.splitlines()) + '\n'
    if _units(text) > CONTEXT_LIMIT:
        raise NoticeFailed(f'stale report is {_units(text)} UTF-16 units, over relay\'s {CONTEXT_LIMIT} context limit')
    return _reply(text)
