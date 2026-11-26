"""Synthetic corpora shaped like the delivered artifact and manifest, and isolated git fixtures."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess

import pytest

from lore.context._corpus import APPLICABILITY, ARTIFACT, MANIFEST, from_bytes

ROOT = pathlib.Path(__file__).resolve().parents[2]
AH, BH, CH = 'a' * 32, 'b' * 32, 'c' * 32
A, B, C = 'rule:' + AH, 'rule:' + BH, 'rule:' + CH


def build(parts):
    """Artifact bytes and a version 2 manifest dict from ('rule', hex, text), ('text', text)
    and ('generated', text) parts; one fragment record per contiguous run."""
    artifact = b''
    fragments = []
    for part in parts:
        kind, text = part[0], part[-1].encode()
        assert text.endswith(b'\n'), part
        offset = len(artifact)
        artifact += text
        if kind == 'generated':
            fragments.append({'id': f'generated-{len(fragments)}', 'offset': offset, 'length': len(text),
                              'generated': 'tasks-resolve', 'rules': []})
            continue
        if not fragments or 'generated' in fragments[-1]:
            fragments.append({'id': f'fragment-{len(fragments)}', 'offset': offset, 'length': 0, 'rules': []})
        fragment = fragments[-1]
        fragment['length'] = len(artifact) - fragment['offset']
        if kind == 'rule':
            fragment['rules'].append({'id': 'rule:' + part[1], 'offset': offset, 'length': len(text),
                                      'sha256': hashlib.sha256(text).hexdigest()})
    manifest = {'version': 2, 'artifact': {'path': ARTIFACT, 'sha256': hashlib.sha256(artifact).hexdigest()},
                'fragments': fragments}
    return artifact, manifest


def _encode(manifest):
    return manifest if isinstance(manifest, bytes) else json.dumps(manifest, indent=2).encode()


def write_tree(tmp_path, artifact, manifest, applicability=None):
    root = pathlib.Path(tmp_path)
    (root / 'instructions').mkdir(parents=True, exist_ok=True)
    (root / ARTIFACT).write_bytes(artifact)
    (root / MANIFEST).write_bytes(_encode(manifest))
    if applicability is not None:
        (root / APPLICABILITY).write_bytes(applicability.encode() if isinstance(applicability, str) else applicability)
    return root


def corpus_of(artifact, manifest, applicability=None):
    if isinstance(applicability, str):
        applicability = applicability.encode()
    return from_bytes(artifact, _encode(manifest), applicability)


def _git_env(home):
    env = {}
    env['PATH'] = os.environ['PATH']
    env['HOME'] = str(home)
    env['GIT_CONFIG_GLOBAL'] = '/dev/null'
    env['GIT_CONFIG_NOSYSTEM'] = '1'
    env['GIT_AUTHOR_NAME'] = 'Fixture'
    env['GIT_AUTHOR_EMAIL'] = 'fixture@example.invalid'
    env['GIT_COMMITTER_NAME'] = 'Fixture'
    env['GIT_COMMITTER_EMAIL'] = 'fixture@example.invalid'
    return env


GIT_ENV = _git_env(pathlib.Path(os.environ.get('TMPDIR', '/tmp')) / 'lore-context-test-home')


def git(root, *args, env=None):
    return subprocess.run(['git', '-C', str(root), *args], env=env or GIT_ENV, check=True,
                          capture_output=True).stdout


def init(root):
    """`git init` in root, asserting git selects the new repository before any write."""
    root = pathlib.Path(root)
    root.mkdir(parents=True, exist_ok=True)
    git(root, 'init', '-q', '-b', 'main')
    assert pathlib.Path(git(root, 'rev-parse', '--show-toplevel').decode().strip()) == root.resolve()
    assert pathlib.Path(git(root, 'rev-parse', '--absolute-git-dir').decode().strip()).is_relative_to(root.resolve())
    return root


def commit_all(root, message='fixture'):
    git(root, 'add', '-A')
    git(root, 'commit', '-qm', message)


def git_repo(tmp_path, artifact, manifest, applicability=None):
    root = init(tmp_path)
    write_tree(root, artifact, manifest, applicability)
    commit_all(root)
    return root


@pytest.fixture
def repo(tmp_path):
    """A committed synthetic corpus plus a copy of src/lore and bin/lore, so commands run by
    explicit path and the selector identity sees a clean tree until a test dirties it."""
    artifact, manifest = build([('text', '## A\n\n'), ('rule', AH, '- a\n'), ('text', '\n## B\n\n'),
                                ('rule', BH, '- b\n'), ('text', '\n'), ('rule', CH, '- c\n')])
    root = init(tmp_path / 'repo')
    write_tree(root, artifact, manifest)
    shutil.copytree(ROOT / 'src/lore', root / 'src/lore', ignore=shutil.ignore_patterns('__pycache__'))
    (root / 'bin').mkdir()
    shutil.copy2(ROOT / 'bin/lore', root / 'bin/lore')
    (root / '.gitignore').write_text('__pycache__/\n')
    commit_all(root)
    return root
