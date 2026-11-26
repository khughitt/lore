"""Shadow report: what band's pi worker would receive for each recorded attempt, from its branch point."""
from dataclasses import dataclass
import copy
import hashlib
import json
import pathlib
import re
import tomllib

from . import _git, select_text
from ._errors import ContextError

UNRECOVERABLE = 'not recoverable for a historical attempt'
GUIDE_LINES = ('Code follows `docs/code-organization.md`', 'Code follows `tools/code-organization.md`')
REGION = re.compile(r'<!-- ops:(identity|family) (start|end)')


@dataclass(frozen=True)
class Attempt:
    id: str
    project: str
    root: str
    branch_point: str | None
    launched: bool
    transcript: str | None      # relative to the attempts directory; None when missing


def read_attempts(directory):
    """One Attempt per subdirectory holding events.jsonl, sorted by id."""
    directory = pathlib.Path(directory)
    attempts = []
    for events in sorted(directory.glob('*/events.jsonl')):
        created = branch_point = started = None
        try:
            lines = events.read_text().splitlines()
        except OSError as error:
            raise ContextError(f'cannot read {events}: {error.strerror}') from None
        for number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except ValueError as error:
                raise ContextError(f'{events} line {number} is not JSON: {error}') from None
            if not isinstance(event, dict):
                raise ContextError(f'{events} line {number} is not a JSON object')
            kind = event.get('type')
            if kind == 'created' and created is None:
                created = event
            elif kind == 'workspace' and branch_point is None:
                branch_point = event.get('branchPoint')
            elif kind == 'runtime-started' and started is None:
                started = event
        if created is None:
            raise ContextError(f'{events} has no created event')
        for key in ('project', 'root'):
            if not isinstance(created.get(key), str) or not created[key]:
                raise ContextError(f'{events} created event has no {key}')
        attempts.append(Attempt(events.parent.name, created['project'], created['root'], branch_point,
                                started is not None, _transcript(directory, started)))
    return tuple(attempts)


def _transcript(directory, started):
    """The session file re-rooted under the attempts directory (the state directory was renamed)."""
    if not started or not started.get('sessionFile'):
        return None
    parts = pathlib.PurePath(started['sessionFile']).parts
    if 'attempts' not in parts:
        return None
    relative = pathlib.PurePath(*parts[len(parts) - parts[::-1].index('attempts'):])
    return relative.as_posix() if (directory / relative).is_file() else None


def target_facts(attempt, git=_git.run):
    """The context's target.* and host.* facts, read at the attempt's branch point."""
    facts = {'target.project': {'value': attempt.project, 'source': 'band attempt record: created.project'}}
    for name in ('target.stage', 'target.profile', 'host.host_budget'):
        facts[name] = {'value': None, 'reason': UNRECOVERABLE}
    checkout = ('target.code_guide', 'target.test_front_door', 'target.family', 'target.test_policy')
    if attempt.branch_point is None:
        return {**facts, **{n: {'value': None, 'reason': 'no branch point recorded'} for n in checkout}}
    commit = attempt.branch_point
    probe = git(attempt.root, 'cat-file', '-e', f'{commit}^{{commit}}')
    if probe.returncode:
        error = ' '.join(probe.stderr.decode(errors='replace').split()) or f'git exit {probe.returncode}'
        return {**facts, **{n: {'value': None, 'reason': f'cannot read {commit}: {error}'} for n in checkout}}

    def show(path):
        result = git(attempt.root, 'show', f'{commit}:{path}')
        return result.stdout.decode(errors='replace') if result.returncode == 0 else None

    def known(value, path):
        return {'value': value, 'source': f'{attempt.project} {path} at {commit}'}

    agents = show('AGENTS.md')
    facts['target.code_guide'] = known(agents is not None and _cites_guide(agents), 'AGENTS.md')
    justfile = show('justfile')
    facts['target.test_front_door'] = known(
        justfile is not None and any(line.startswith('test-fast') for line in justfile.splitlines()), 'justfile')
    facts['target.family'] = _family(show, known)
    facts['target.test_policy'] = _test_policy(show, known)
    return facts


def _cites_guide(agents):
    region = None
    for line in agents.splitlines():
        marker = REGION.search(line)
        if marker:
            region = marker.group(1) if marker.group(2) == 'start' else None
            continue
        if region and any(phrase in line for phrase in GUIDE_LINES):
            return True
        if line.startswith('Authority:') and 'docs/code-organization.md' in line:
            return True
    return False


def _family(show, known):
    for path in ('tools/family.toml', 'family.toml'):
        text = show(path)
        if text is None:
            continue
        match = re.search(r'^name\s*=\s*"([^"]+)"', text, re.M)
        if match and match.group(1) in ('guild', 'verifiably'):
            return known(match.group(1), path)
        return {'value': None, 'reason': f'{path} at the branch point names no family in the vocabulary'}
    return {'value': None, 'reason': 'no family file at the branch point; members took their copy in a staged '
                                     'rollout, so its absence does not show non-membership'}


def _test_policy(show, known):
    text = show('.tt.toml')
    if text is None:
        return {'value': None, 'reason': 'depends on the stage at the time, not recorded at the branch point'}
    try:
        value = tomllib.loads(text).get('automatic_broad')
    except tomllib.TOMLDecodeError as error:
        return {'value': None, 'reason': f'.tt.toml at the branch point does not parse: {error}'}
    if not isinstance(value, bool):
        return {'value': None, 'reason': '.tt.toml at the branch point sets no automatic_broad'}
    return known('broad' if value else 'off', '.tt.toml')


def report(directory, fixture_path, root, git=_git.run):
    """The shadow report over every attempt in directory, for the fixture context, from root's corpus."""
    root = pathlib.Path(root)
    try:
        fixture_bytes = pathlib.Path(fixture_path).read_bytes()
    except OSError as error:
        raise ContextError(f'cannot read fixture {fixture_path}: {error.strerror}') from None
    try:
        fixture = json.loads(fixture_bytes)
    except ValueError as error:
        raise ContextError(f'fixture {fixture_path} is not JSON: {error}') from None
    attempts = read_attempts(directory)
    rows, records = [], []
    omitted, kept = {}, {}
    for attempt in attempts:
        if not attempt.launched:
            continue
        context = copy.deepcopy(fixture)
        context.setdefault('facts', {}).update(target_facts(attempt, git))
        text, record = select_text(root, context, shadow=True)
        records.append(record)
        unknown = sorted(name for name, f in context['facts'].items() if f.get('value') is None)
        rows.append({'id': attempt.id, 'project': attempt.project, 'branch_point': attempt.branch_point,
                     'launched': True, 'transcript': attempt.transcript, 'selected_bytes': len(text),
                     'output_sha256': record['output']['sha256'],
                     'omitted': [r['id'] for r in record['rules'] if r['decision'] == 'omit'],
                     'unknown_facts': unknown})
        for rule in record['rules']:
            if rule['decision'] == 'omit':
                _tally(omitted, (rule['id'], rule['reason']), rule, attempt)
            elif rule['reason'] == 'unknown-fact':
                _tally(kept, (rule['id'], tuple(sorted(rule['detail']['unknown']))), rule, attempt)
    if not records:
        raise ContextError(f'no launched attempt under {directory}')
    selectors = {json.dumps(r['selector'], sort_keys=True) for r in records}
    corpora = {json.dumps(r['corpus'], sort_keys=True) for r in records}
    if len(selectors) != 1 or len(corpora) != 1:
        raise ContextError('selector or corpus changed between attempts; rerun from a clean commit')
    titles = _titles(root)
    return {
        'identity': {'mode': 'shadow', 'selector': records[0]['selector'], 'corpus': records[0]['corpus'],
                     'fixture_sha256': hashlib.sha256(fixture_bytes).hexdigest(),
                     'replayable': records[0]['replayable']},
        'artifact_bytes': records[0]['output']['artifact_bytes'],
        'attempts': rows,
        'not_launched': [a.id for a in attempts if not a.launched],
        'omitted_rules': [{'id': rule, 'title': titles.get(rule), 'bytes': v['bytes'], 'reason': reason,
                           'attempts': v['attempts'], 'projects': sorted(v['projects'])}
                          for (rule, reason), v in sorted(omitted.items(), key=_order)],
        'kept_by_unknown': [{'id': rule, 'title': titles.get(rule), 'bytes': v['bytes'], 'unknown': list(names),
                             'attempts': v['attempts'], 'projects': sorted(v['projects'])}
                            for (rule, names), v in sorted(kept.items(), key=_order)],
    }


def _tally(table, key, rule, attempt):
    row = table.setdefault(key, {'bytes': rule['bytes'], 'attempts': 0, 'projects': set()})
    row['attempts'] += 1
    row['projects'].add(attempt.project)


def _order(item):
    (rule, extra), value = item
    return (-value['bytes'], rule, extra)


def _titles(root):
    titles = {}
    for path in (root / 'instructions/rules').glob('*.json'):
        try:
            titles['rule:' + path.stem] = json.loads(path.read_text()).get('title')
        except (OSError, ValueError):
            continue
    return titles


def render(data):
    """A Markdown rendering of the report: identity, per-project summary, omitted rules, kept by unknown."""
    identity = data['identity']
    lines = ['# Band worker shadow report', '', '## Identity', '',
             f'- mode: {identity["mode"]}',
             f'- selector: sha256 {identity["selector"]["sha256"]}, commit {identity["selector"]["commit"]}, '
             f'clean {str(identity["selector"]["clean"]).lower()}',
             f'- artifact sha256: {identity["corpus"]["artifact_sha256"]}',
             f'- manifest sha256: {identity["corpus"]["manifest_sha256"]}',
             f'- applicability sha256: {identity["corpus"]["applicability_sha256"]}',
             f'- fixture sha256: {identity["fixture_sha256"]}',
             f'- replayable: {str(identity["replayable"]).lower()}', '',
             '## Per project', '', '| Project | Attempts | Selected bytes (min to max) | Artifact bytes |',
             '| --- | --- | --- | --- |']
    projects = {}
    for row in data['attempts']:
        projects.setdefault(row['project'], []).append(row['selected_bytes'])
    for project, sizes in sorted(projects.items()):
        lines.append(f'| {project} | {len(sizes)} | {min(sizes)} to {max(sizes)} | {data["artifact_bytes"]} |')
    lines += ['', f'Not launched: {", ".join(data["not_launched"]) or "none"}.', '', '## Omitted rules', '',
              '| Rule | Title | Bytes | Reason | Attempts | Projects |', '| --- | --- | --- | --- | --- | --- |']
    for row in data['omitted_rules']:
        lines.append(f'| {row["id"]} | {row["title"]} | {row["bytes"]} | {row["reason"]} | {row["attempts"]} | '
                     f'{", ".join(row["projects"])} |')
    lines += ['', '## Kept because a fact is unknown', '', '| Rule | Title | Bytes | Unknown | Attempts | Projects |',
              '| --- | --- | --- | --- | --- | --- |']
    for row in data['kept_by_unknown']:
        lines.append(f'| {row["id"]} | {row["title"]} | {row["bytes"]} | {", ".join(row["unknown"])} | '
                     f'{row["attempts"]} | {", ".join(row["projects"])} |')
    return '\n'.join(lines) + '\n'
