"""Relay notice subscribers in fresh processes: `lore hook profile-notice` and
`lore hook stale-notice` read one relay schema-2 SubscriberEnvelope and reply with
exactly `{}` or `{"context": ...}`. The profile notice's context is the native hook's
stdout, byte for byte."""
import json
import subprocess
import sys

import pytest

# Decoded SessionStart events as relay projects them: relay test/fixtures/hook-events/
# {claude-code,codex,agy}.SessionStart.expected.json at relay 5537ead, with cwd and
# transcriptPath substituted per test.
EVENTS = {
    'claude-code': {'facts': {'model': {'status': 'valid', 'value': 'claude-opus-5-5'}},
                    'private': {'scratchpadDir': {'status': 'valid', 'value': '/scratch/sess'}}},
    'codex': {'facts': {'model': {'status': 'valid', 'value': 'gpt-6'}}, 'private': {}},
    'agy': {'facts': {}, 'private': {}},
}


def envelope(cwd, harness='claude-code', transcript=None, subscriber='lore-profile'):
    event = EVENTS[harness]
    private = dict(event['private'])
    if transcript is not None:
        private['transcriptPath'] = {'status': 'valid', 'value': str(transcript)}
    return json.dumps({'schema': 2, 'type': 'event', 'subscriber': subscriber,
        'event': {'schema': 2, 'kind': 'session-start', 'harness': harness, 'nativeEvent': 'SessionStart',
                  'cwd': str(cwd), 'identity': {'status': 'valid', 'value': {'agentId': f'{harness}:s', 'sessionId': 's'}},
                  'facts': event['facts'], 'tool': None, 'private': private},
        'registry': {'status': 'not-requested'}})


def run(w, command, stdin, root=None, extra=None, cwd=None):
    env = w.env | {'CLAUDE_ENV_FILE': str(w.records.parent / 'export.sh')} | (extra or {})
    return subprocess.run([sys.executable, str((root or w.corpus) / 'bin/lore'), 'hook', command],
        input=stdin.encode() if isinstance(stdin, str) else stdin, cwd=cwd or w.records.parent,
        env=env, capture_output=True, timeout=30)


def native(w, payload, extra=None):
    env = w.env | {'CLAUDE_ENV_FILE': str(w.records.parent / 'export.sh')} | (extra or {})
    return subprocess.run([sys.executable, str(w.corpus / 'hooks/claude-profile')], input=payload,
        cwd=w.checkout, env=env, capture_output=True, text=True, timeout=10)


def context(result):
    assert result.returncode == 0, result.stderr
    reply = json.loads(result.stdout)
    assert set(reply) == {'context'}, reply
    return reply['context']


def export(w):
    path = w.records.parent / 'export.sh'
    text = path.read_text() if path.exists() else None
    path.unlink(missing_ok=True)
    return text


@pytest.mark.parametrize('harness,transcript', [
    ('claude-code', '.claude-work/projects/p/s.jsonl'),
    ('codex', '.codex/sessions/rollout.jsonl'),
    ('agy', None),
])
def test_profile_context_is_the_native_hook_text(delivery, harness, transcript):
    w = delivery
    path = w.records.parent / transcript if transcript else None
    payload = {'cwd': str(w.checkout)} | ({'transcript_path': str(path)} if path else {})
    expected = native(w, json.dumps(payload))
    expected_export = export(w)
    assert expected.returncode == 0 and expected.stdout.startswith('profile: personal')
    # The subscriber's process cwd is unrelated; only event.cwd selects the checkout.
    assert context(run(w, 'profile-notice', envelope(w.checkout, harness, path))) == expected.stdout
    assert export(w) == expected_export == 'export AGENT_PROFILE=personal\n'
    if harness == 'claude-code':
        assert '; home: work;' in expected.stdout


def test_profile_failure_is_the_native_unresolved_line(delivery):
    w = delivery
    w.private.write_text('not [toml')
    expected = native(w, json.dumps({'cwd': str(w.checkout)}))
    assert expected.stdout.startswith('profile: unresolved')
    text = context(run(w, 'profile-notice', envelope(w.checkout)))
    assert text == expected.stdout and len(text.splitlines()) == 1
    assert export(w) is None


@pytest.mark.parametrize('stdin', [
    b'', b'not json', b'null', b'[]', b'\xff{}',
    b'{"cwd": "/repo", "hook_event_name": "SessionStart", "session_id": "s"}',
    b'{"schema": 1, "type": "event"}',
    b'{"schema": 2, "schema": 2, "type": "event"}',
], ids=['empty', 'invalid', 'null', 'array', 'not-utf8', 'native-payload', 'schema-1', 'duplicate-key'])
def test_profile_rejects_non_envelope_input_visibly(delivery, stdin):
    w = delivery
    text = context(run(w, 'profile-notice', stdin))
    assert text.startswith('profile: unresolved — relay envelope') and len(text.splitlines()) == 1
    assert 'bin/lore profile session' in text
    assert export(w) is None


@pytest.mark.parametrize('change', ['kind', 'relative-cwd', 'transcript-fact'])
def test_profile_rejects_malformed_events(delivery, change):
    w = delivery
    data = json.loads(envelope(w.checkout))
    if change == 'kind': data['event']['kind'] = 'prompt'
    elif change == 'relative-cwd': data['event']['cwd'] = 'project'
    else: data['event']['private']['transcriptPath'] = {'status': 'valid', 'value': 7}
    text = context(run(w, 'profile-notice', json.dumps(data)))
    assert text.startswith('profile: unresolved — relay envelope')


def test_profile_ignores_missing_or_invalid_transcript_facts(delivery):
    w = delivery
    data = json.loads(envelope(w.checkout))
    data['event']['private']['transcriptPath'] = {'status': 'invalid'}
    expected = native(w, json.dumps({'cwd': str(w.checkout)}))
    assert context(run(w, 'profile-notice', json.dumps(data))) == expected.stdout


def test_profile_over_relay_context_limit_is_unresolved(delivery):
    w = delivery
    (w.corpus / 'profiles/personal.md').write_text('# Profile: personal\n' + 'x' * 10_000 + '\n')
    text = context(run(w, 'profile-notice', envelope(w.checkout)))
    assert text.startswith('profile: unresolved — ') and 'over relay' in text
    assert len(text.splitlines()) == 1 and export(w) is None


def test_profile_import_failure_is_one_line(delivery):
    w = delivery
    (w.corpus / 'src/lore/__init__.py').write_text("raise RuntimeError('first\\nsecond')\n")
    text = context(run(w, 'profile-notice', envelope(w.checkout)))
    assert text.startswith('profile: unresolved — first second;') and len(text.splitlines()) == 1
    assert 'bin/lore profile session' in text
    # Other commands keep ordinary failure.
    assert run(w, 'stale-notice', envelope(w.checkout)).returncode != 0


ASSEMBLER = '''#!/usr/bin/env python3
import os, pathlib, sys
pathlib.Path(os.environ["ASSEMBLER_LOG"]).write_text(" ".join(sys.argv[1:]) + "\\n" + os.getcwd())
sys.stderr.write(os.environ.get("ASSEMBLER_STDERR", ""))
sys.stdout.write("provenance: noise\\n")
sys.exit(int(os.environ.get("ASSEMBLER_EXIT", "0")))
'''


@pytest.fixture
def stale(delivery):
    w = delivery
    script = w.corpus / 'bin/assemble-instructions'
    script.write_text(ASSEMBLER); script.chmod(0o755)
    w.log = w.records.parent / 'assembler.log'
    w.env['ASSEMBLER_LOG'] = str(w.log)
    return w


def test_stale_current_is_empty_and_checks_the_executing_tree(stale):
    w = stale
    r = run(w, 'stale-notice', envelope(w.checkout, subscriber='lore-stale'))
    assert r.returncode == 0 and r.stdout == b'{}'
    argv, cwd = w.log.read_text().splitlines()
    assert argv == 'check --working-tree' and cwd == str(w.corpus)


@pytest.mark.parametrize('stderr,line', [
    ('artifact stale; run just assemble\nmanifest stale; run just assemble\n',
     'artifact stale; run just assemble manifest stale; run just assemble\n'),
    ('', 'assemble-instructions: validation failed\n'),
])
def test_stale_drift_is_one_context_line(stale, stderr, line):
    w = stale
    r = run(w, 'stale-notice', envelope(w.checkout), extra={'ASSEMBLER_EXIT': '1', 'ASSEMBLER_STDERR': stderr})
    assert context(r) == line


@pytest.mark.parametrize('stdin', [b'not json', b'{"schema": 1}'])
def test_stale_rejects_non_envelope_input(stale, stdin):
    r = run(stale, 'stale-notice', stdin)
    assert r.returncode != 0 and r.stdout == b''
    assert b'relay envelope' in r.stderr and not stale.log.exists()


def test_stale_execution_failure_is_a_failed_notice(stale):
    w = stale
    r = run(w, 'stale-notice', envelope(w.checkout), extra={'ASSEMBLER_EXIT': '2', 'ASSEMBLER_STDERR': 'secret\n'})
    assert r.returncode != 0 and r.stdout == b''
    assert b'exited 2' in r.stderr and b'secret' not in r.stderr
