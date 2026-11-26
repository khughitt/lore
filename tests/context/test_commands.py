"""The `lore context` commands, run by explicit path in an isolated repository copy."""
import hashlib
import json
import subprocess
import sys

from lore.context import check
from lore.context._corpus import APPLICABILITY, ARTIFACT, MANIFEST

from .conftest import AH, A, B, BH, GIT_ENV, ROOT, commit_all, git

EMPTY = {'schema': 1, 'name': 'empty'}
POLICY = f'[rule.{BH}]\n' + '''when = [{{ fact = "actor.shell", in = ["zsh"] }}]
note = "zsh only"
rule_sha256 = "{sha}"
'''


def run_python(code):
    env = {'PATH': GIT_ENV['PATH'], 'HOME': GIT_ENV['HOME'], 'PYTHONPATH': str(ROOT / 'src'),
           'PYTHONDONTWRITEBYTECODE': '1'}
    return subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True, check=True).stdout


def lore(repo, *args):
    env = dict(GIT_ENV)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return subprocess.run([sys.executable, str(repo / 'bin/lore'), 'context', *args], env=env, cwd=repo,
                          capture_output=True)


def write_context(repo, data, name='ctx.json'):
    path = repo.parent / name
    path.write_text(json.dumps(data))
    return str(path)


def rule_sha(repo, rule):
    manifest = json.loads((repo / MANIFEST).read_text())
    return next(r['sha256'] for f in manifest['fragments'] for r in f['rules'] if r['id'] == rule)


def with_policy(repo, text=None, commit=True):
    (repo / APPLICABILITY).write_text(text if text is not None else POLICY.format(sha=rule_sha(repo, B)))
    if commit:
        commit_all(repo, 'policy')


BASH = {'schema': 1, 'name': 'bash', 'facts': {'actor.shell': {'value': 'bash', 'source': 'test'}}}


def test_importing_cli_does_not_import_the_context_package():
    out = run_python('import sys, lore.cli; print("lore.context" in sys.modules)')
    assert out.strip() == 'False'


def test_select_with_empty_context_prints_the_artifact(repo):
    result = lore(repo, 'select', '--context', write_context(repo, EMPTY))
    assert result.returncode == 0, result.stderr
    assert result.stdout == (repo / ARTIFACT).read_bytes()


def test_live_select_ignores_a_policy_whose_entries_are_all_proposed(repo):
    with_policy(repo)
    ctx = write_context(repo, BASH)
    live = lore(repo, 'select', '--context', ctx)
    shadow = lore(repo, 'select', '--context', ctx, '--shadow')
    assert live.stdout == (repo / ARTIFACT).read_bytes()
    assert shadow.stdout == b'## A\n\n- a\n\n## B\n\n- c\n'


def test_select_json_record_identifies_inputs_selector_and_mode(repo):
    with_policy(repo)
    ctx = write_context(repo, BASH)
    record = json.loads(lore(repo, 'select', '--context', ctx, '--shadow', '--json').stdout)
    plain = lore(repo, 'select', '--context', ctx, '--shadow').stdout
    sha = lambda p: hashlib.sha256((repo / p).read_bytes()).hexdigest()
    assert record['corpus'] == {'artifact_sha256': sha(ARTIFACT), 'manifest_sha256': sha(MANIFEST),
                                'applicability_sha256': sha(APPLICABILITY)}
    assert record['mode'] == 'shadow' and record['output']['sha256'] == hashlib.sha256(plain).hexdigest()
    assert record['selector']['commit'] == git(repo, 'rev-parse', 'HEAD').decode().strip()
    assert record['replayable'] is True
    record_file = repo.parent / 'record.json'
    both = lore(repo, 'select', '--context', ctx, '--shadow', '--record', str(record_file))
    assert both.stdout == plain and json.loads(record_file.read_text())['output'] == record['output']


def test_record_is_replayable_only_from_a_clean_tree(repo):
    (repo / 'src/lore/context/_errors.py').write_text(
        (repo / 'src/lore/context/_errors.py').read_text() + '# dirty\n')
    record = json.loads(lore(repo, 'select', '--context', write_context(repo, EMPTY), '--json').stdout)
    assert record['selector']['clean'] is False and record['replayable'] is False


def test_explain_names_the_unknown_fact_that_kept_a_rule(repo):
    with_policy(repo)
    out = lore(repo, 'explain', '--context', write_context(repo, EMPTY), '--shadow').stdout.decode()
    line = next(line for line in out.splitlines() if B in line)
    assert line.startswith('include') and 'unknown-fact' in line and 'actor.shell' in line
    assert out.splitlines()[-1].startswith('selected ')


def test_check_passes_on_the_real_checkout():
    problems, warnings = check(ROOT)
    assert problems == []


def test_check_reads_index_when_an_input_is_staged(repo):
    with_policy(repo, POLICY.format(sha=rule_sha(repo, B)).replace('when = [{ fact = "actor.shell", in = ["zsh"] }]',
                                                                   'governs = ["fly"]'), commit=False)
    git(repo, 'add', APPLICABILITY)
    with_policy(repo, commit=False)
    assert check(repo, 'working')[0] == []
    problems, _ = check(repo)
    assert problems and 'fly' in problems[0]
    assert lore(repo, 'check').returncode == 1


def test_check_reports_stale_entry_as_warning_not_problem(repo):
    with_policy(repo, POLICY.format(sha='0' * 64))
    problems, warnings = check(repo)
    assert problems == [] and warnings and warnings[0].startswith(B)
    result = lore(repo, 'check')
    assert result.returncode == 0 and b'stale' in result.stderr


def test_approve_writes_digest_that_makes_entry_reviewed(repo):
    with_policy(repo)
    result = lore(repo, 'approve', B)
    assert result.returncode == 0, result.stderr
    assert result.stdout.decode().startswith(B)
    text = (repo / APPLICABILITY).read_text()
    assert text.splitlines()[1].startswith('reviewed = "')
    live = lore(repo, 'select', '--context', write_context(repo, BASH))
    assert b'- b\n' not in live.stdout


def test_approve_refuses_and_writes_nothing_when_check_has_a_problem(repo):
    bad = POLICY.format(sha=rule_sha(repo, B)) + f'\n[rule.{AH}]\ngoverns = ["fly"]\nrule_sha256 = "x"\n'
    with_policy(repo, bad)
    result = lore(repo, 'approve', B)
    assert result.returncode == 1 and b'nothing written' in result.stderr
    assert (repo / APPLICABILITY).read_text() == bad


def test_select_refuses_unknown_fact_in_context_file(repo):
    result = lore(repo, 'select', '--context',
                  write_context(repo, {'schema': 1, 'name': 'x', 'facts': {'actor.mood': {'value': 1, 'source': 's'}}}))
    assert result.returncode == 1 and result.stderr.startswith(b'lore context:') and b'actor.mood' in result.stderr


def test_select_refuses_artifact_that_does_not_match_the_manifest(repo):
    (repo / ARTIFACT).write_bytes((repo / ARTIFACT).read_bytes() + b'x\n')
    result = lore(repo, 'select', '--context', write_context(repo, EMPTY))
    assert result.returncode == 1 and b'does not match the manifest' in result.stderr
    assert lore(repo, 'check').returncode == 1
