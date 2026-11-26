"""The band shadow report: attempt records, historical target facts and the per-rule tallies."""
import hashlib
import json
import pathlib

from lore.context._band_shadow import Attempt, read_attempts, render, report, target_facts
from lore.context._corpus import APPLICABILITY, MANIFEST

from .conftest import AH, BH, CH, B, C, commit_all, git, init

AGENTS_WITH_GUIDE = '<!-- ops:family start -->\nCode follows `tools/code-organization.md`.\n<!-- ops:family end -->\n'
AGENTS_LAYOUT_ONLY = '# guide\n\n## Layout\n\nCode follows `tools/code-organization.md`.\n'


def project(tmp_path, name, files_per_commit):
    """A git repository with one commit per dict of files; returns (root, [commit ids])."""
    root = init(tmp_path / name)
    commits = []
    for files in files_per_commit:
        for path, text in files.items():
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_text(text)
        (root / '.keep').write_text(str(len(commits)))
        commit_all(root, f'c{len(commits)}')
        commits.append(git(root, 'rev-parse', 'HEAD').decode().strip())
    return root, commits


def attempt_dir(directory, attempt_id, project_name, root, branch_point, launched=True, transcript=True):
    path = directory / attempt_id
    (path / 'sessions/worker').mkdir(parents=True)
    events = [{'type': 'created', 'project': project_name, 'root': str(root)},
              {'type': 'workspace', 'branchPoint': branch_point}]
    if launched:
        session = path / 'sessions/worker/s.jsonl'
        if transcript:
            session.write_text('{}\n')
        events.append({'type': 'runtime-started',
                       'sessionFile': f'/elsewhere/state/crew/attempts/{attempt_id}/sessions/worker/s.jsonl'})
    (path / 'events.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in events))


def test_read_attempts_separates_launched_from_refused(tmp_path):
    attempts = tmp_path / 'attempts'
    attempt_dir(attempts, 'A2', 'p', tmp_path, 'abc')
    attempt_dir(attempts, 'A1', 'p', tmp_path, None, launched=False)
    attempt_dir(attempts, 'A3', 'p', tmp_path, 'abc', transcript=False)
    got = read_attempts(attempts)
    assert [a.id for a in got] == ['A1', 'A2', 'A3']
    assert [a.launched for a in got] == [False, True, True]
    assert got[1].transcript == 'A2/sessions/worker/s.jsonl' and got[2].transcript is None
    assert got[0].branch_point is None and got[0].transcript is None


def test_target_facts_come_from_the_branch_point_not_the_working_tree(tmp_path):
    root, commits = project(tmp_path, 'p', [{'AGENTS.md': '# none\n'}])
    (root / 'AGENTS.md').write_text(AGENTS_WITH_GUIDE)
    facts = target_facts(Attempt('x', 'p', str(root), commits[0], True, None))
    assert facts['target.code_guide'] == {'value': False, 'source': f'p AGENTS.md at {commits[0]}'}


def test_code_guide_phrase_outside_the_identity_and_family_regions_is_not_adoption(tmp_path):
    root, commits = project(tmp_path, 'p', [{'AGENTS.md': AGENTS_LAYOUT_ONLY}, {'AGENTS.md': AGENTS_WITH_GUIDE}])
    first = target_facts(Attempt('x', 'p', str(root), commits[0], True, None))
    second = target_facts(Attempt('x', 'p', str(root), commits[1], True, None))
    assert first['target.code_guide']['value'] is False and second['target.code_guide']['value'] is True


def test_family_is_read_from_the_root_file_when_tools_has_none(tmp_path):
    root, commits = project(tmp_path, 'p', [{'family.toml': 'name = "guild"\n', 'justfile': 'test-fast:\n\ttrue\n',
                                             '.tt.toml': 'automatic_broad = false\n'}])
    facts = target_facts(Attempt('x', 'p', str(root), commits[0], True, None))
    assert facts['target.family'] == {'value': 'guild', 'source': f'p family.toml at {commits[0]}'}
    assert facts['target.test_front_door']['value'] is True and facts['target.test_policy']['value'] == 'off'


def test_family_is_unknown_when_no_family_file_exists_at_the_branch_point(tmp_path):
    root, commits = project(tmp_path, 'p', [{'README.md': 'x\n'}])
    facts = target_facts(Attempt('x', 'p', str(root), commits[0], True, None))
    assert facts['target.family']['value'] is None and 'staged' in facts['target.family']['reason']
    assert facts['target.test_policy']['value'] is None and facts['target.test_front_door']['value'] is False
    assert facts['target.stage'] == {'value': None, 'reason': 'not recoverable for a historical attempt'}


def test_unreadable_branch_point_makes_target_facts_unknown(tmp_path):
    root, _ = project(tmp_path, 'p', [{'AGENTS.md': AGENTS_WITH_GUIDE}])
    facts = target_facts(Attempt('x', 'p', str(root), '0' * 40, True, None))
    for name in ('target.code_guide', 'target.test_front_door', 'target.family', 'target.test_policy'):
        assert facts[name]['value'] is None and '0' * 40 in facts[name]['reason']
    gone = target_facts(Attempt('x', 'p', str(tmp_path / 'missing'), 'abc', True, None))
    assert gone['target.code_guide']['value'] is None and gone['target.project']['value'] == 'p'


def world(repo, tmp_path):
    """The repo corpus with titled rules and target-dependent entries, two projects and three attempts."""
    rules = repo / 'instructions/rules'
    rules.mkdir()
    for hexid, title in ((AH, 'Rule A'), (BH, 'Rule B'), (CH, 'Rule C')):
        (rules / f'{hexid}.json').write_text(json.dumps({'title': title}))
    manifest = json.loads((repo / MANIFEST).read_text())
    sha = {r['id']: r['sha256'] for f in manifest['fragments'] for r in f['rules']}
    (repo / APPLICABILITY).write_text(
        f'[rule.{BH}]\nwhen = [{{ fact = "target.code_guide", eq = true }}]\nrule_sha256 = "{sha[B]}"\n\n'
        f'[rule.{CH}]\ngoverns = ["ask-user"]\nrule_sha256 = "{sha[C]}"\n')
    commit_all(repo, 'policy')
    plain, plain_commits = project(tmp_path, 'plain', [{'AGENTS.md': '# none\n'}])
    attempts = tmp_path / 'attempts'
    attempt_dir(attempts, 'A1', 'plain', plain, plain_commits[0])
    attempt_dir(attempts, 'A2', 'gone', tmp_path / 'missing', 'f' * 40)
    attempt_dir(attempts, 'A3', 'plain', plain, None, launched=False)
    fixture = tmp_path / 'fixture.json'
    fixture.write_text(json.dumps({'schema': 1, 'name': 'w', 'duties': {
        'withheld': [{'duty': 'ask-user', 'source': 'brief: "never ask"'}]}}))
    return attempts, fixture


def test_report_identity_names_selector_corpus_policy_and_fixture(repo, tmp_path):
    attempts, fixture = world(repo, tmp_path)
    data = report(attempts, fixture, repo)
    sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
    identity = data['identity']
    assert identity['corpus'] == {'artifact_sha256': sha(repo / 'instructions/AGENTS.md'),
                                  'manifest_sha256': sha(repo / MANIFEST),
                                  'applicability_sha256': sha(repo / APPLICABILITY)}
    assert identity['fixture_sha256'] == sha(fixture) and identity['mode'] == 'shadow'
    assert identity['selector']['clean'] and identity['replayable']
    assert all(len(row['output_sha256']) == 64 for row in data['attempts'])
    (repo / 'src/lore/context/_errors.py').write_text('# dirty\n')
    dirty = report(attempts, fixture, repo)['identity']
    assert dirty['selector']['clean'] is False and dirty['replayable'] is False


def test_report_keeps_separate_rows_when_a_rule_is_omitted_for_one_project_and_kept_for_another(repo, tmp_path):
    attempts, fixture = world(repo, tmp_path)
    data = report(attempts, fixture, repo)
    omitted_b = [r for r in data['omitted_rules'] if r['id'] == B]
    kept_b = [r for r in data['kept_by_unknown'] if r['id'] == B]
    assert omitted_b == [{'id': B, 'title': 'Rule B', 'bytes': 4, 'reason': 'test-false', 'attempts': 1,
                          'projects': ['plain']}]
    assert kept_b == [{'id': B, 'title': 'Rule B', 'bytes': 4, 'unknown': ['target.code_guide'], 'attempts': 1,
                       'projects': ['gone']}]


def test_report_counts_only_launched_attempts_and_names_kept_by_unknown(repo, tmp_path):
    attempts, fixture = world(repo, tmp_path)
    data = report(attempts, fixture, repo)
    assert [a['id'] for a in data['attempts']] == ['A1', 'A2'] and data['not_launched'] == ['A3']
    omitted_c = next(r for r in data['omitted_rules'] if r['id'] == C)
    assert (omitted_c['attempts'], omitted_c['projects']) == (2, ['gone', 'plain'])
    a1 = data['attempts'][0]
    assert a1['omitted'] == [B, C] and a1['transcript'] == 'A1/sessions/worker/s.jsonl'
    assert 'target.stage' in a1['unknown_facts'] and 'target.code_guide' not in a1['unknown_facts']
    text = render(data)
    assert text.startswith('# Band worker shadow report\n') and '| plain | 1 |' in text and 'Rule B' in text
