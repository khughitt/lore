"""Exercise the shipped interim commands; a second handwritten route would drift."""
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SDD = ROOT / 'vendor/superpowers/skills/subagent-driven-development/scripts'
INLINE = ROOT / 'vendor/superpowers/skills/executing-plans/scripts'


@pytest.fixture
def world(tmp_path):
    home = tmp_path / 'home'; home.mkdir()
    repo = tmp_path / 'code'; repo.mkdir()
    env = dict(PATH=os.environ['PATH'], HOME=str(home), GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_NOSYSTEM='1', GIT_AUTHOR_NAME='Fixture',
               GIT_AUTHOR_EMAIL='fixture@example.invalid', GIT_COMMITTER_NAME='Fixture',
               GIT_COMMITTER_EMAIL='fixture@example.invalid')
    def run(*args):
        return subprocess.run([str(a) for a in args], cwd=repo, env=env, capture_output=True, text=True)
    def git(*args):
        result = run('git', *args)
        assert result.returncode == 0, result.stderr
        return result.stdout.strip()
    git('init', '-q', '-b', 'main')
    assert Path(git('rev-parse', '--show-toplevel')) == repo
    assert Path(git('rev-parse', '--absolute-git-dir')).is_relative_to(repo)
    (repo / 'code.txt').write_text('base\n')
    git('add', '.'); git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'test: base')
    plans = tmp_path / 'plans with spaces'; plans.mkdir()
    plan = plans / 'plan.md'; plan.write_text('# Plan\n\n### Task 1: One\n\nDo it.\n')
    workspace = tmp_path / 'external workspace'; workspace.mkdir()
    return SimpleNamespace(repo=repo, env=env, run=run, git=git, plan=plan,
                           workspace=workspace, base=git('rev-parse', 'HEAD'))


def invoke(w, name, *args):
    script = ROOT / 'bin' / name
    assert script.is_file(), f'missing shipped helper: {name}'
    return w.run('bash', script, *args)


def start(w):
    return invoke(w, 'plan-task-start', w.workspace, w.plan, 1)


def init(w):
    return invoke(w, 'plan-workspace-init', w.workspace, w.plan)


def done(w, code, base=None):
    return invoke(w, 'plan-task-done', w.workspace, w.plan, 1, base or w.base,
                  '--', sys.executable, '-c', code)


def test_pinned_route_still_uses_worktree(world):
    w = world
    r = w.run('bash', INLINE / 'task-start', w.plan, 1)
    assert r.returncode == 0, r.stderr
    old = w.repo / '.superpowers/sdd/plan'
    assert (old / 'task-1-brief.md').is_file()
    r = w.run('bash', INLINE / 'task-done', w.plan, 1, w.base, '--', 'true')
    assert r.returncode == 0, r.stderr
    assert 'Task 1: complete' in (old / 'progress.md').read_text()
    (w.repo / 'code.txt').write_text('change\n')
    w.git('add', '.'); w.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'test: change')
    r = w.run('bash', SDD / 'review-package', w.plan, w.base, 'HEAD')
    assert r.returncode == 0, r.stderr
    assert list(old.glob('review-*.diff'))


def test_start_resume_preserves_base_and_reviewed_briefs(world):
    w = world
    first = start(w); assert first.returncode == 0, first.stderr
    assert f'base: {w.base}' in first.stdout
    brief = Path(next(line[7:] for line in first.stdout.splitlines() if line.startswith('brief: ')))
    assert brief.parent == w.workspace
    saved = brief.read_bytes()
    (w.repo / 'code.txt').write_text('changed\n')
    w.git('add', '.'); w.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'test: later')
    w.plan.write_text(w.plan.read_text() + 'Revised detail.\n')
    resumed = start(w); assert resumed.returncode == 0, resumed.stderr
    assert f'base: {w.base}' in resumed.stdout
    assert brief.read_bytes() == saved
    assert len(list(w.workspace.glob('task-1-brief-*.md'))) == 2
    assert not (w.repo / '.superpowers').exists()


def test_completion_preserves_failed_attempts_and_records_once(world):
    w = world; assert start(w).returncode == 0
    for _ in range(2):
        failed = done(w, 'print("full failure output"); raise SystemExit(7)')
        assert failed.returncode == 7
        assert 'Task 1: complete' not in (w.workspace / 'progress.md').read_text()
    logs = {p: p.read_bytes() for p in w.workspace.glob('task-1-tests-*.log')}
    assert len(logs) == 2 and all(b'full failure output' in data for data in logs.values())
    passed = done(w, 'print("check passed")'); assert passed.returncode == 0, passed.stderr
    assert (w.workspace / 'progress.md').read_text().count('Task 1: complete') == 1
    assert len(list(w.workspace.glob('task-1-tests-*.log'))) == 3
    assert all(p.read_bytes() == data for p, data in logs.items())
    repeated = done(w, 'print("fresh retry")')
    assert repeated.returncode == 0 and 'already complete' in repeated.stdout
    assert len(list(w.workspace.glob('task-1-tests-*.log'))) == 4
    assert (w.workspace / 'progress.md').read_text().count('Task 1: complete') == 1
    review = w.workspace / 'review.diff'
    (w.repo / 'code.txt').write_text('implemented\n')
    w.git('add', '.'); w.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'test: implementation')
    r = w.run('bash', SDD / 'review-package', w.plan, w.base, 'HEAD', review)
    assert r.returncode == 0 and review.stat().st_size > 0
    assert not (w.repo / '.superpowers').exists()


def test_setup_binds_identity_before_writing_then_start_keeps_setup_records(world):
    w = world
    bound = init(w); assert bound.returncode == 0, bound.stderr
    assert bound.stdout.strip() == str(w.workspace)
    assert (w.workspace / 'plan-path').read_text() == f'{w.plan}\n'
    ledger = w.workspace / 'progress.md'
    assert ledger.read_text() == f'# SDD ledger — plan: {w.plan}\n'
    with ledger.open('a') as f:
        f.write('Setup: baseline 12 passed\nPre-flight: no shared interfaces\n')
    (w.workspace / 'baseline-tests.log').write_text('12 passed\n')
    again = init(w); assert again.returncode == 0, again.stderr
    started = start(w); assert started.returncode == 0, started.stderr
    lines = ledger.read_text().splitlines()
    assert lines[:3] == [f'# SDD ledger — plan: {w.plan}', 'Setup: baseline 12 passed',
                         'Pre-flight: no shared interfaces']
    assert lines[3] == f'Task 1: BASE {w.base}'
    assert (w.workspace / 'baseline-tests.log').read_text() == '12 passed\n'


def test_start_refusal_of_unmarked_workspace_names_setup_entry_point(world):
    w = world
    (w.workspace / 'baseline-tests.log').write_text('12 passed\n')
    result = start(w)
    assert result.returncode == 2
    assert 'plan-workspace-init' in result.stderr


@pytest.mark.parametrize('entry', [start, init])
@pytest.mark.parametrize('failure', ['collision', 'unmarked', 'missing', 'inside', 'ledger'])
def test_refuses_other_plan_or_unusable_workspace(world, failure, entry):
    w = world
    if failure in ('collision', 'ledger'):
        assert start(w).returncode == 0
    if failure == 'collision':
        other = w.plan.parent / 'other'; other.mkdir()
        w.plan = other / w.plan.name; w.plan.write_text('### Task 1: Other\n')
    elif failure == 'unmarked':
        (w.workspace / 'old-report.md').write_text('preserve')
    elif failure == 'missing':
        w.workspace = w.workspace / 'not-created'
    elif failure == 'inside':
        w.workspace = w.repo
    else:
        (w.workspace / 'progress.md').write_text('# another ledger\n')
    before = {p: p.read_bytes() for p in w.workspace.glob('*') if p.is_file()}
    result = entry(w)
    assert result.returncode != 0
    if failure == 'collision':
        assert result.returncode == 2
        assert str(w.plan.parent.parent / w.plan.name) in result.stderr
        assert str(w.plan) in result.stderr
        assert str(w.workspace / 'plan-path') in result.stderr
        assert 'pass the recorded plan path' in result.stderr
        assert 'distinct plans' in result.stderr
    assert all(p.read_bytes() == data for p, data in before.items())
    assert not (w.repo / '.superpowers').exists()


def test_completion_refuses_unstarted_workspace_distinct_from_plan_mismatch(world):
    w = world
    result = done(w, 'print("must not run")')
    assert result.returncode == 2
    assert 'not started' in result.stderr
    assert str(w.workspace / 'plan-path') in result.stderr
    assert 'another plan' not in result.stderr
    assert 'must not run' not in result.stdout and 'must not run' not in result.stderr
    assert list(w.workspace.iterdir()) == []


def test_completion_explains_post_integration_plan_path_mismatch_and_recovers(world):
    w = world
    rel_plan = Path('docs/plans/in-tree-plan.md')
    (w.repo / rel_plan.parent).mkdir(parents=True)
    (w.repo / rel_plan).write_text('# Plan\n\n### Task 1: One\n\nDo it.\n')
    w.git('add', '.')
    w.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'test: add in-tree plan')
    base = w.git('rev-parse', 'HEAD')

    wt = w.repo.parent / 'worktree-task-1'
    w.git('worktree', 'add', '-q', '-b', 'feat/task-1', str(wt))
    started = subprocess.run(
        ['bash', str(ROOT / 'bin/plan-task-start'), str(w.workspace), str(rel_plan), '1'],
        cwd=wt, env=w.env, capture_output=True, text=True,
    )
    assert started.returncode == 0, started.stderr
    recorded = str((wt / rel_plan).resolve())
    supplied = str((w.repo / rel_plan).resolve())
    assert (w.workspace / 'plan-path').read_text().strip() == recorded

    (wt / 'code.txt').write_text('implemented in worktree\n')
    subprocess.run(['git', 'add', '.'], cwd=wt, env=w.env, check=True)
    subprocess.run(
        ['git', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'feat: worktree change'],
        cwd=wt, env=w.env, check=True,
    )
    w.git('merge', '--ff-only', 'feat/task-1')

    before = {p: p.read_bytes() for p in w.workspace.iterdir()}
    mismatch = invoke(
        w, 'plan-task-done', w.workspace, rel_plan, 1, base,
        '--', sys.executable, '-c', 'print("must not run")',
    )
    assert mismatch.returncode == 2
    assert 'another plan' in mismatch.stderr
    assert 'not started' not in mismatch.stderr
    assert recorded in mismatch.stderr
    assert supplied in mismatch.stderr
    assert str(w.workspace / 'plan-path') in mismatch.stderr
    assert 'pass the recorded plan path' in mismatch.stderr
    assert 'distinct plans' in mismatch.stderr
    assert 'must not run' not in mismatch.stdout and 'must not run' not in mismatch.stderr
    assert {p: p.read_bytes() for p in w.workspace.iterdir()} == before

    recorded_arg = (w.workspace / 'plan-path').read_text().strip()
    assert Path(recorded_arg).read_bytes() == (w.repo / rel_plan).read_bytes()
    recovered = invoke(
        w, 'plan-task-done', w.workspace, recorded_arg, 1, base,
        '--', sys.executable, '-c', 'print("post-integration check passed")',
    )
    assert recovered.returncode == 0, recovered.stderr
    assert 'Task 1: complete' in (w.workspace / 'progress.md').read_text()
    assert (w.workspace / 'plan-path').read_text().strip() == recorded
    assert not (w.repo / '.superpowers').exists() and not (wt / '.superpowers').exists()


def test_completion_rejects_wrong_base_before_running_command(world):
    w = world; assert start(w).returncode == 0
    result = done(w, 'print("must not run")', base='0' * 40)
    assert result.returncode != 0
    assert not list(w.workspace.glob('task-1-tests-*.log'))


def test_completion_at_old_head_does_not_skip_a_corrective_check(world):
    w = world; assert start(w).returncode == 0
    assert done(w, 'print("initial success")').returncode == 0
    (w.repo / 'code.txt').write_text('corrective change\n')
    w.git('add', '.'); w.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'fix: corrective change')
    checked = done(w, 'print("corrective failure"); raise SystemExit(7)')
    assert checked.returncode == 7
    assert len(list(w.workspace.glob('task-1-tests-*.log'))) == 2
    assert (w.workspace / 'progress.md').read_text().splitlines()[-1].startswith('Task 1: attempt (status 7,')
