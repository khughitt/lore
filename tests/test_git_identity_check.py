"""git-identity-check: refuses a commit whose author or committer is not the identity the
checkout's profile declares.

Ported from ops tests/test_git_identity_check.py. Fixtures reuse the profile world (lore's
definitions, records, a fake tasks resolver, real git checkouts) and every git run is
hermetic: an environment built key by key, no system config, a fixture global config.
"""
import ast
import contextlib
import io
import os
from pathlib import Path
import shlex
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from conftest import ROOT, git, init_repo
from lore import _identity_check, cli

ME = 'Test <personal@example.invalid>'
WORK = 'Test <work@example.invalid>'
SWITCH = 'git -c hook.identity-check.enabled=false commit'
LAUNCHER = 'bin/git-identity-check'


@pytest.fixture
def ident(delivery):
    """The delivery world plus a work checkout, a work family directory and a fixture
    global git config holding the personal identity."""
    w = delivery
    w.gitconfig = Path(w.env['GIT_CONFIG_GLOBAL'])
    w.hook = ''
    base = w.records.parent
    w.base = base
    w.rad = base / 'rad'
    init_repo(w.rad, w.env)
    entry = dict(w.row['entry'], config=str(w.records / 'rad/tasks/.config.toml'), records=str(w.records / 'rad'),
                 checkout=str(w.rad), name='rad', purpose='A work fixture', profile='work')
    rad_row = {'input': str(w.rad), 'kind': 'path', 'status': 'resolved', 'prefix': 'rad', 'root': str(w.rad),
               'records': str(w.records / 'rad'), 'entry': entry}
    w.data[f'resolve {w.rad} --json'] = {'results': [rad_row], 'warnings': []}
    w.data['resolve --all --json']['results'].append(rad_row)
    w.family = base / 'cainex'
    w.family.mkdir()
    with w.private.open('a') as f:
        f.write(f'\n[[family]]\npath="{w.family}"\nprofiles=["work"]\n')
    w.save()
    write_global(w, 'Test', 'personal@example.invalid')
    return w


def write_global(w, name, email, extra=''):
    w.gitconfig.write_text(f'[user]\n\tname = {name}\n\temail = {email}\n{w.hook}{extra}')


def unregistered(w, path, **row):
    w.data[f'resolve {path} --json'] = {'results': [{'input': str(path), 'kind': 'path', 'status': 'unregistered', **row}],
                                        'warnings': []}
    w.save()


def plain_repo(w, path):
    """A repository with no commits; git init alone, since its path need not be UTF-8."""
    path.mkdir()
    run_git(w, path, 'init', '-q')
    return path


def scratch(w, name='scratch'):
    path = plain_repo(w, w.base / name)
    unregistered(w, path)
    return path


def run_git(w, cwd, *args, check=True, **extra):
    return subprocess.run(['git', *args], cwd=cwd, env=w.env | extra, capture_output=True, text=True, check=check)


def run_check(w, *argv, cwd, **extra):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = cli.git_identity_check(list(argv), w.env | extra, str(cwd))
    return code, err.getvalue()


# Verdicts


def test_the_profile_identity_passes(ident):
    assert run_check(ident, cwd=ident.checkout) == (0, '')


def test_a_wrong_global_identity_is_refused_for_both_roles(ident):
    w = ident
    write_global(w, 't', 't@t')
    code, err = run_check(w, cwd=w.checkout)
    assert code == 1
    assert "git-identity-check: author t <t@t> is not this checkout's identity," in err
    assert "git-identity-check: committer t <t@t> is not this checkout's identity," in err
    assert (f'  {ME} ({w.private} profile personal; selected by {w.records}/demo/tasks/.config.toml profile)'
            in err)
    assert 'A test or tool may have rewritten git config. Fix the value at that origin, then commit again.' in err


def test_a_wrong_author_alone_is_refused_alone(ident):
    code, err = run_check(ident, cwd=ident.checkout, GIT_AUTHOR_NAME='Other', GIT_AUTHOR_EMAIL='other@example.invalid')
    assert code == 1
    assert 'author Other <other@example.invalid>' in err
    assert 'committer' not in err
    assert '  Fix the value at that origin, then commit again.' in err
    assert 'git config' not in err


def test_the_author_allowance_passes_a_foreign_author_but_never_a_foreign_committer(ident):
    foreign = {'GIT_AUTHOR_NAME': 'Other', 'GIT_AUTHOR_EMAIL': 'other@example.invalid', 'OPS_IDENTITY_AUTHOR': 'allow'}
    assert run_check(ident, cwd=ident.checkout, **foreign) == (0, '')
    code, err = run_check(ident, cwd=ident.checkout, GIT_COMMITTER_NAME='Envy', **foreign)
    assert code == 1
    assert 'committer Envy <personal@example.invalid>' in err


def test_an_unknown_allowance_value_cannot_judge(ident):
    code, err = run_check(ident, cwd=ident.checkout, OPS_IDENTITY_AUTHOR='yes')
    assert code == 2
    assert "OPS_IDENTITY_AUTHOR must be allow or unset, not 'yes'" in err


def test_the_work_profile_expects_the_work_identity(ident):
    code, err = run_check(ident, cwd=ident.rad)
    assert code == 1
    assert f'  {WORK} ({ident.private} profile work; selected by {ident.records}/rad/tasks/.config.toml profile)' in err


@pytest.mark.parametrize('name', ['clone', 'caf\udce9'])  # b"caf\xe9": not UTF-8
def test_an_unregistered_family_clone_is_judged_with_the_family_identity(ident, name):
    clone = plain_repo(ident, ident.family / name)
    unregistered(ident, clone)
    code, err = run_check(ident, cwd=clone)
    assert code == 1
    assert f'  {WORK} ({ident.private} profile work; selected by profile path {ident.family})' in err


@pytest.mark.parametrize('name', ['scratch', 'caf\udce9'])
def test_a_default_profile_repository_is_not_judged(ident, name):
    path = scratch(ident, name)
    write_global(ident, 'Fixture', 'fixture@example.invalid')
    assert run_check(ident, cwd=path) == (0, '')


def test_the_records_store_is_not_judged_even_with_a_foreign_author(ident):
    w = ident
    unregistered(w, w.records, records_store=str(w.records))
    assert run_check(w, cwd=w.records, GIT_AUTHOR_NAME='Other', GIT_AUTHOR_EMAIL='other@example.invalid') == (0, '')


def test_a_linked_worktree_is_judged_by_its_main_checkout(ident):
    w = ident
    tree = w.base / 'wt'
    run_git(w, w.checkout, 'worktree', 'add', '-q', str(tree))
    write_global(w, 't', 't@t')
    code, err = run_check(w, cwd=tree)
    assert code == 1
    assert f'selected by {w.records}/demo/tasks/.config.toml profile)' in err


def test_an_unresolvable_profile_cannot_judge(ident):
    ident.row['entry']['profile'] = 'not-defined'
    ident.save()
    code, err = run_check(ident, cwd=ident.checkout)
    assert code == 2
    assert 'git-identity-check: cannot judge' in err
    assert SWITCH in err


def test_the_resolver_never_sees_a_repository_local_variable(ident):
    with patch.object(_identity_check, 'resolve', wraps=_identity_check.resolve) as resolve:
        assert run_check(ident, cwd=ident.checkout, GIT_DIR=str(ident.checkout / '.git'),
                         GIT_INDEX_FILE='.git/index') == (0, '')
    assert resolve.call_args.args[1].keys() & _identity_check.GIT_LOCAL_ENV == set()


def test_a_registry_without_lore_is_a_sandbox_and_not_judged(ident):
    w = ident
    w.data['resolve lore --json'] = {'results': [{'input': 'lore', 'kind': 'prefix', 'status': 'unregistered',
                                                  'prefix': 'lore'}], 'warnings': []}
    w.save()
    write_global(w, 't', 't@t')
    assert run_check(w, cwd=w.checkout) == (
        0, f"git-identity-check: not judged: the tasks registry (XDG_CONFIG_HOME={w.env['XDG_CONFIG_HOME']}) "
           'does not register lore (a sandboxed XDG_CONFIG_HOME?)\n')


def test_a_path_argument_ignores_an_inherited_git_dir(ident):
    # Unscrubbed, git var would read rad's local Fixture identity and refuse.
    run_git(ident, ident.rad, 'config', 'user.name', 'Fixture')
    assert run_check(ident, str(ident.checkout), cwd=ident.base, GIT_DIR=str(ident.rad / '.git')) == (0, '')


# Fail closed: whatever goes wrong, exit 2 and the off switch, never a traceback.


@pytest.mark.parametrize('stderr', ['projects.toml: TOML parse error at line 1, column 10',
                                    'io: Permission denied (os error 13)'])
def test_a_registry_tasks_cannot_read_cannot_judge_and_is_never_a_sandbox(ident, stderr):
    ident.data['resolve lore --json'] = {'_exit': 1, '_stderr': stderr}
    ident.save()
    code, err = run_check(ident, cwd=ident.checkout)
    assert code == 2
    assert stderr in err
    assert 'not judged' not in err
    assert SWITCH in err


def test_a_resolver_failure_cannot_judge(ident):
    with patch.object(_identity_check, 'resolve', side_effect=OSError('Permission denied')):
        code, err = run_check(ident, cwd=ident.checkout)
    assert code == 2
    assert 'Permission denied' in err
    assert SWITCH in err


def test_run_as_a_script_without_tomllib_it_cannot_judge(ident):
    script = str(ident.corpus / LAUNCHER)
    boot = ("import runpy, sys; sys.modules['tomllib'] = None; sys.argv = [sys.argv[1]]; "
            "runpy.run_path(sys.argv[0], run_name='__main__')")
    result = subprocess.run([sys.executable, '-c', boot, script], cwd=ident.checkout, env=ident.env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert 'Traceback' not in result.stderr
    assert 'tomllib' in result.stderr
    assert SWITCH in result.stderr


def test_the_launcher_parses_as_python_3_9():
    ast.parse((ROOT / LAUNCHER).read_text(), feature_version=(3, 9))


def test_an_inherited_git_dir_never_reaches_the_caller_repository(ident, tmp_path_factory):
    caller = tmp_path_factory.mktemp('caller') / 'caller'
    init_repo(caller, ident.env)
    git(caller, ident.env, 'config', 'core.filemode', 'false')
    before = (caller / '.git/config').read_bytes()
    with patch.dict(os.environ, {'GIT_DIR': str(caller / '.git'), 'GIT_WORK_TREE': str(caller),
                                 'GIT_INDEX_FILE': str(caller / '.git/index')}):
        assert run_check(ident, cwd=ident.checkout) == (0, '')
        write_global(ident, 't', 't@t')
        assert run_check(ident, cwd=ident.checkout)[0] == 1
    assert (caller / '.git/config').read_bytes() == before


# Origins


def test_a_global_user_identity_names_its_file_and_scope(ident):
    write_global(ident, 't', 't@t')
    _, err = run_check(ident, cwd=ident.checkout)
    assert f'  user.name=t   file:{ident.gitconfig} (global)' in err
    assert f'  user.email=t@t   file:{ident.gitconfig} (global)' in err


def test_a_local_identity_names_the_command_that_removes_it(ident):
    run_git(ident, ident.checkout, 'config', 'user.name', 'Fixture')
    _, err = run_check(ident, cwd=ident.checkout)
    assert '  user.name=Fixture   file:.git/config (local)' in err
    assert '    remove it: git config --local --unset user.name' in err
    assert 'user.email' not in err


def test_a_role_key_under_a_correct_user_identity_is_named_not_the_environment(ident):
    write_global(ident, 'Test', 'personal@example.invalid', '[committer]\n\temail = t@t\n')
    code, err = run_check(ident, cwd=ident.checkout)
    assert code == 1
    assert f'  committer.email=t@t   file:{ident.gitconfig} (global)' in err
    assert 'environment' not in err
    assert 'author ' not in err


def test_an_author_role_key_is_named(ident):
    write_global(ident, 'Test', 'personal@example.invalid', '[author]\n\tname = Bot\n')
    _, err = run_check(ident, cwd=ident.checkout)
    assert f'  author.name=Bot   file:{ident.gitconfig} (global)' in err


def test_an_environment_identity_is_named_as_such(ident):
    _, err = run_check(ident, cwd=ident.checkout, GIT_COMMITTER_NAME='Envy')
    assert "  committer name 'Envy' came from the environment (GIT_COMMITTER_NAME)" in err
    assert 'committer email' not in err


def test_an_environment_value_beats_a_correct_role_key(ident):
    write_global(ident, 'Test', 'personal@example.invalid', '[committer]\n\tname = Test\n')
    _, err = run_check(ident, cwd=ident.checkout, GIT_COMMITTER_NAME='Envy')
    assert 'came from the environment (GIT_COMMITTER_NAME)' in err
    assert 'committer.name=' not in err


def test_an_email_with_no_key_set_names_the_email_variable(ident):
    ident.gitconfig.write_text('[user]\n\tname = Test\n')
    code, err = run_check(ident, cwd=ident.checkout, EMAIL='other@example.invalid')
    assert code == 1
    assert "  committer email 'other@example.invalid' came from the environment (EMAIL)" in err


def test_a_value_with_no_key_or_variable_set_is_named_as_git_default(ident):
    ident.gitconfig.write_text('')
    cwd = str(ident.checkout)
    assert _identity_check.origin(cwd, ident.env, 'committer', 'name', 'Login') == (
        "  committer name 'Login' is git's default from the system user: neither committer.name nor user.name is set",
        False)
    assert _identity_check.origin(cwd, ident.env, 'author', 'email', 'me@host') == (
        "  author email 'me@host' is git's default from the system user and host name: "
        'neither author.email nor user.email is set', False)


def test_an_author_from_the_environment_mentions_the_author_option(ident):
    _, err = run_check(ident, cwd=ident.checkout, GIT_AUTHOR_EMAIL='other@example.invalid')
    assert ("  author email 'other@example.invalid' came from the environment (GIT_AUTHOR_EMAIL) or --author"
            in err)


# The guard as git runs it: a hook declared in the fixture's global config.


@pytest.fixture
def hooked(ident):
    w = ident
    launcher = shlex.quote(str(w.corpus / LAUNCHER))
    w.hook = ('[hook "identity-check"]\n\tevent = pre-commit\n\tevent = pre-merge-commit\n'
              f'\tcommand = {shlex.quote(sys.executable)} {launcher}\n')
    write_global(w, 'Test', 'personal@example.invalid')
    return w


def commit(w, cwd, *args, check=False, **extra):
    return run_git(w, cwd, 'commit', '-q', '--allow-empty', '-m', 'probe', *args, check=check, **extra)


def count(w, cwd):
    return int(run_git(w, cwd, 'rev-list', '--count', '--all').stdout)


def test_the_expected_identity_commits(hooked):
    before = count(hooked, hooked.checkout)
    assert commit(hooked, hooked.checkout).returncode == 0
    assert count(hooked, hooked.checkout) == before + 1


def test_a_rewritten_global_identity_refuses_the_next_commit(hooked):
    w = hooked
    commit(w, w.checkout, check=True)
    before = count(w, w.checkout)
    run_git(w, w.checkout, 'config', '--global', 'user.name', 't')
    run_git(w, w.checkout, 'config', '--global', 'user.email', 't@t')
    result = commit(w, w.checkout)
    assert result.returncode != 0
    assert "committer t <t@t> is not this checkout's identity" in result.stderr
    assert count(w, w.checkout) == before


def test_a_fixture_identity_written_through_an_inherited_git_dir_refuses_the_next_commit(hooked):
    w = hooked
    path = scratch(w)
    run_git(w, path, 'config', 'user.name', 'Fixture', GIT_DIR=str(w.checkout / '.git'))
    result = commit(w, w.checkout)
    assert result.returncode != 0
    assert 'user.name=Fixture' in result.stderr
    assert '(local)' in result.stderr


def test_a_git_dir_naming_a_claimed_repository_from_a_non_repository_is_refused(hooked):
    w = hooked
    before = count(w, w.checkout)
    elsewhere = w.base / 'elsewhere'
    elsewhere.mkdir()
    result = commit(w, elsewhere, GIT_DIR=str(w.checkout / '.git'), GIT_AUTHOR_NAME='Fixture',
                    GIT_COMMITTER_NAME='Fixture')
    assert result.returncode != 0
    assert "committer Fixture <personal@example.invalid> is not this checkout's identity" in result.stderr
    assert count(w, w.checkout) == before


def test_a_git_dir_naming_a_claimed_repository_from_another_repository_is_refused(hooked):
    w = hooked
    before = count(w, w.checkout)
    path = scratch(w)
    result = commit(w, path, GIT_DIR=str(w.checkout / '.git'), GIT_AUTHOR_NAME='Fixture', GIT_COMMITTER_NAME='Fixture')
    assert result.returncode != 0
    assert f'selected by {w.records}/demo/tasks/.config.toml profile)' in result.stderr
    assert count(w, w.checkout) == before


def test_a_linked_worktree_commit_is_judged_by_its_main_checkout(hooked):
    w = hooked
    before = count(w, w.checkout)
    tree = w.base / 'wt'
    run_git(w, w.checkout, 'worktree', 'add', '-q', str(tree))
    result = commit(w, tree, GIT_COMMITTER_NAME='Envy')
    assert result.returncode != 0
    assert f'selected by {w.records}/demo/tasks/.config.toml profile)' in result.stderr
    assert count(w, w.checkout) == before
    assert commit(w, tree).returncode == 0
    assert count(w, w.checkout) == before + 1


def test_a_sandboxed_registry_lets_any_commit_through_with_one_notice(hooked):
    w = hooked
    w.data['resolve lore --json'] = {'results': [{'input': 'lore', 'kind': 'prefix', 'status': 'unregistered',
                                                  'prefix': 'lore'}], 'warnings': []}
    w.save()
    write_global(w, 't', 't@t')
    before = count(w, w.checkout)
    result = commit(w, w.checkout)
    assert result.returncode == 0
    assert result.stderr.splitlines() == [
        f"git-identity-check: not judged: the tasks registry (XDG_CONFIG_HOME={w.env['XDG_CONFIG_HOME']}) "
        'does not register lore (a sandboxed XDG_CONFIG_HOME?)']
    assert count(w, w.checkout) == before + 1


def test_a_foreign_author_needs_the_allowance(hooked):
    other = 'Other <other@example.invalid>'
    assert commit(hooked, hooked.checkout, '--author', other).returncode != 0
    assert commit(hooked, hooked.checkout, '--author', other, OPS_IDENTITY_AUTHOR='allow').returncode == 0


def test_amending_a_foreign_commit_needs_the_author_allowance(hooked):
    w = hooked
    commit(w, w.checkout, '--author', 'Other <other@example.invalid>', check=True, OPS_IDENTITY_AUTHOR='allow')
    result = run_git(w, w.checkout, 'commit', '-q', '--amend', '--no-edit', check=False)
    assert result.returncode != 0
    assert 'author Other <other@example.invalid>' in result.stderr


def test_a_command_line_identity_is_traced_to_the_command_line(hooked):
    result = run_git(hooked, hooked.checkout, '-c', 'user.name=Cli', 'commit', '-q', '--allow-empty', '-m', 'probe',
                     check=False)
    assert result.returncode != 0
    assert 'user.name=Cli   command line: (command)' in result.stderr


def test_a_merge_commit_is_judged(hooked):
    w = hooked
    commit(w, w.checkout, check=True)
    run_git(w, w.checkout, 'checkout', '-q', '-b', 'side')
    commit(w, w.checkout, '-m', 'side', check=True)
    run_git(w, w.checkout, 'checkout', '-q', '-')
    commit(w, w.checkout, '-m', 'main', check=True)
    before = count(w, w.checkout)
    result = run_git(w, w.checkout, 'merge', '--no-ff', '--no-edit', 'side', check=False, GIT_COMMITTER_NAME='Envy')
    assert result.returncode != 0
    assert 'committer Envy' in result.stderr
    assert count(w, w.checkout) == before


@pytest.mark.parametrize('name', ['scratch', 'caf\udce9'])
def test_a_fixture_repository_commits_with_any_identity(hooked, name):
    path = scratch(hooked, name)
    write_global(hooked, 'Fixture', 'fixture@example.invalid')
    assert commit(hooked, path).returncode == 0


def test_the_documented_switch_commits_past_the_guard(hooked):
    write_global(hooked, 't', 't@t')
    result = run_git(hooked, hooked.checkout, '-c', 'hook.identity-check.enabled=false', 'commit', '-q',
                     '--allow-empty', '-m', 'probe', check=False)
    assert result.returncode == 0


# The entry as the global config declares it: the command found on PATH, else under $HOME.
# HOME names an empty sandbox while the registry stays reachable, as in a test that
# sandboxes HOME but inherits XDG_CONFIG_HOME, so these commits reach the launcher through
# PATH alone unless a case says otherwise.

ENTRY = ('command -v git-identity-check >/dev/null && exec git-identity-check'
         ' || exec \\"$HOME/.local/bin/git-identity-check\\"')


@pytest.fixture
def entry(ident):
    w = ident
    w.entry_bin = w.base / 'entrybin'
    w.entry_bin.mkdir()
    (w.entry_bin / 'git-identity-check').symlink_to(w.corpus / LAUNCHER)
    w.hook = f'[hook "identity-check"]\n\tevent = pre-commit\n\tevent = pre-merge-commit\n\tcommand = {ENTRY}\n'
    write_global(w, 'Test', 'personal@example.invalid')
    sandbox_home = w.base / 'sandbox-home'
    sandbox_home.mkdir()
    fake_tasks = w.env['PATH'].split(os.pathsep)[0]
    # The caller's PATH may hold an installed copy; the bare PATH reaches only git and the fake tasks.
    bare = os.pathsep.join([fake_tasks, '/usr/bin', '/bin'])
    w.env.update(PATH=f"{w.entry_bin}{os.pathsep}{w.env['PATH']}", HOME=str(sandbox_home))
    return SimpleNamespace(w=w, bare=bare, sandbox_home=sandbox_home)


def test_the_system_interpreter_runs_the_launcher_whatever_python3_is_first_on_path(entry):
    w = entry.w
    stub = w.base / 'stubpython'
    stub.mkdir()
    (stub / 'python3').write_text('#!/bin/sh\nexit 3\n')
    (stub / 'python3').chmod(0o755)
    path = os.pathsep.join([str(stub), w.env['PATH']])
    assert commit(w, w.checkout, PATH=path).returncode == 0
    result = commit(w, w.checkout, PATH=path, GIT_COMMITTER_NAME='Envy')
    assert result.returncode != 0
    assert 'committer Envy' in result.stderr


def test_a_launcher_missing_from_path_is_found_under_home(entry):
    w = entry.w
    home = w.base / 'home'
    (home / '.local/bin').mkdir(parents=True)
    (home / '.local/bin/git-identity-check').symlink_to(w.corpus / LAUNCHER)
    before = count(w, w.checkout)
    assert commit(w, w.checkout, PATH=entry.bare, HOME=str(home)).returncode == 0
    result = commit(w, w.checkout, PATH=entry.bare, HOME=str(home), GIT_COMMITTER_NAME='Envy')
    assert result.returncode != 0
    assert 'committer Envy' in result.stderr
    assert count(w, w.checkout) == before + 1


def test_a_launcher_missing_from_path_and_home_refuses_the_commit(entry):
    w = entry.w
    before = count(w, w.checkout)
    result = commit(w, w.checkout, PATH=entry.bare)
    assert result.returncode != 0
    assert str(entry.sandbox_home / '.local/bin/git-identity-check') in result.stderr
    assert count(w, w.checkout) == before


def test_a_refusal_from_the_copy_on_path_never_falls_through_to_home(entry):
    w = entry.w
    home = w.base / 'home'
    (home / '.local/bin').mkdir(parents=True)
    (home / '.local/bin/git-identity-check').write_text('#!/bin/sh\nexit 0\n')
    (home / '.local/bin/git-identity-check').chmod(0o755)
    before = count(w, w.checkout)
    result = commit(w, w.checkout, HOME=str(home), GIT_COMMITTER_NAME='Envy')
    assert result.returncode != 0
    assert 'committer Envy' in result.stderr
    assert count(w, w.checkout) == before
