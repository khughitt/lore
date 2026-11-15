"""Credential-isolated profile fixtures; only the tasks CLI boundary is faked."""
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

PUBLIC = '''
[profile.personal]
fragment="personal"
home="personal"
design_docs="records"
pr_draft="by-permission"
[profile.external]
fragment="external"
home="personal"
design_docs="exclude"
pr_draft="required"
[profile.work]
fragment="work"
home="work"
design_docs="exclude"
pr_draft="by-permission"
private=true
[profile.science]
fragment="science"
[default]
profiles=["external"]
[home.personal]
claude="~/.claude"
codex="~/.codex"
agy="~/.gemini/antigravity-cli"
[home.work]
claude="~/.claude-work"
codex="~/.codex-work"
agy="~/.gemini/antigravity-cli"
'''
PRIVATE = '''
[profile.personal]
gh_account="personal-test"
git_identity="Test <personal@example.invalid>"
[profile.external]
gh_account="personal-test"
git_identity="Test <personal@example.invalid>"
[profile.work]
gh_account="work-test"
git_identity="Test <work@example.invalid>"
'''


def git(path, env, *args):
    return subprocess.run(['git', '-C', str(path), *args], env=env, check=True,
                          capture_output=True, text=True).stdout.strip()


def init_repo(path, env):
    path.mkdir(parents=True, exist_ok=True)
    git(path, env, 'init', '-q')
    assert Path(git(path, env, 'rev-parse', '--show-toplevel')) == path
    assert Path(git(path, env, 'rev-parse', '--absolute-git-dir')).is_relative_to(path)
    git(path, env, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '--allow-empty', '-qm', 'fixture')


@pytest.fixture
def profile_world(tmp_path, monkeypatch):
    env = {'PATH': os.environ['PATH'], 'HOME': str(tmp_path),
           'XDG_CONFIG_HOME': str(tmp_path / 'config'),
           'XDG_STATE_HOME': str(tmp_path / 'state'),
           'GIT_CONFIG_GLOBAL': str(tmp_path / 'gitconfig'), 'GIT_CONFIG_NOSYSTEM': '1',
           'GIT_CEILING_DIRECTORIES': str(tmp_path.parent), 'PYTHONDONTWRITEBYTECODE': '1'}
    corpus = tmp_path / 'lore'; records = tmp_path / 'records'; checkout = tmp_path / 'project'
    for path in (corpus, records, checkout):
        init_repo(path, env)
    (corpus / 'profiles').mkdir()
    (corpus / 'profiles/profiles.toml').write_text(PUBLIC)
    for name in ('personal', 'external', 'work', 'science'):
        (corpus / f'profiles/{name}.md').write_text(f'# Profile: {name}\n')
    (records / 'lore').mkdir()
    private = records / 'lore/profiles.toml'; private.write_text(PRIVATE)
    commands = tmp_path / 'commands.jsonl'; replies = tmp_path / 'replies.json'
    bin_dir = tmp_path / 'bin'; bin_dir.mkdir()
    fake = bin_dir / 'tasks'
    fake.write_text(f'#!{sys.executable}\n' + '''import json,os,sys
key=" ".join(sys.argv[1:])
with open(os.environ["CALL_LOG"],"a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")
replies=json.load(open(os.environ["REPLIES"]))
if key not in replies: print("unexpected query: "+key,file=sys.stderr);sys.exit(4)
print(json.dumps(replies[key]))
''')
    fake.chmod(0o755)
    env.update(PATH=str(bin_dir) + os.pathsep + env['PATH'], CALL_LOG=str(commands), REPLIES=str(replies))
    entry = {'config': str(records / 'demo/tasks/.config.toml'), 'records': str(records / 'demo'),
             'checkout': str(checkout), 'kind': 'detached', 'name': 'demo', 'aliases': [],
             'purpose': 'A fixture', 'profile': 'personal'}
    row = {'input': str(checkout), 'kind': 'path', 'status': 'resolved', 'prefix': 'demo',
           'root': str(checkout), 'records': str(records / 'demo'), 'entry': entry}
    lore = {'input': 'lore', 'kind': 'prefix', 'status': 'resolved', 'prefix': 'lore',
            'root': str(corpus), 'records': str(records / 'lore'),
            'entry': {'config': str(records/'lore/tasks/.config.toml'), 'records': str(records / 'lore'),
                      'checkout': str(corpus), 'kind':'detached', 'profile': 'personal'}}
    data = {'resolve lore --json': {'results': [lore], 'warnings': []},
            f'resolve {checkout} --json': {'results': [row], 'warnings': []},
            'resolve --all --json': {'results': [row, lore], 'warnings': []}}
    def save(): replies.write_text(json.dumps(data))
    save()
    from lore import _profiles
    monkeypatch.setattr(_profiles, 'CORPUS', corpus)
    return SimpleNamespace(env=env, corpus=corpus, records=records, checkout=checkout,
                           private=private, data=data, row=row, save=save, calls=commands)


def live_tasks_unavailable(env):
    if 'LORE_TEST_LIVE_TASKS' not in env:
        return False
    if env['LORE_TEST_LIVE_TASKS'] != 'unavailable':
        raise ValueError('LORE_TEST_LIVE_TASKS must be absent or exactly unavailable')
    return True


def require_tasks(env):
    import shutil
    executable = shutil.which('tasks', path=env['PATH'])
    if not executable:
        raise RuntimeError('installed tasks missing; test-live cannot skip')
    return executable
