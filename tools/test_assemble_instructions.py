"""Exercise the assembler's observable bytes, ownership and Git-view boundaries."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
IDS = ['core', 'refactoring', 'git', 'profiles', 'design-docs', 'communication',
       'decisions', 'processes', 'tests', 'shell', 'outcome-notes', 'trials', 'feedback', 'projects']


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True).stdout


def invoke(world, *args):
    return subprocess.run([sys.executable, str(world.root / 'bin/assemble-instructions'), *args],
                          cwd=world.root, env=world.env, capture_output=True)


def build(world, command='write', *args):
    return invoke(world, command, '--owner-root', f'ops={world.ops}', *args)


@pytest.fixture
def world(tmp_path):
    root, ops = tmp_path / 'lore', tmp_path / 'ops'
    shutil.copytree(ROOT / 'instructions', root / 'instructions')
    (root / 'instructions/AGENTS.manifest.json').unlink(missing_ok=True)
    shutil.copytree(ROOT / 'tools/fixtures/instruction-assembly', root / 'tools/fixtures/instruction-assembly')
    (root / 'bin').mkdir()
    if (ROOT / 'bin/assemble-instructions').exists():
        shutil.copy(ROOT / 'bin/assemble-instructions', root / 'bin/assemble-instructions')
    driver = ROOT / 'tools/instruction-assembly-proof-driver.py'
    if driver.exists():
        shutil.copy(driver, root / 'tools/instruction-assembly-proof-driver.py')
    initial = (root / 'tools/fixtures/instruction-assembly/initial.md').read_bytes()
    projects = initial[initial.index(b'<!-- ops:projects start'):]
    (ops / 'instructions/fragments').mkdir(parents=True)
    (ops / 'instructions/fragments/projects.md').write_bytes(projects)
    (ops / 'bin').mkdir()
    (ops / 'bin/ops-projects').write_text('import sys\nassert sys.argv[1:] == ["render"]\n'
                                         f'sys.stdout.buffer.write({projects!r})\n')
    config = tmp_path / 'config/tasks'
    config.mkdir(parents=True)
    (config / 'projects.toml').write_text('[projects]\nops = ' + json.dumps(str(ops)) +
                                          '\nlore = ' + json.dumps(str(tmp_path / 'wrong-lore')) + '\n')
    for repo in (root, ops):
        git(repo, 'init', '-q', '-b', 'main')
        git(repo, 'config', 'user.name', 'Assembly fixture')
        git(repo, 'config', 'user.email', 'assembly-fixture@example.invalid')
        git(repo, 'config', 'core.hooksPath', 'fixture-no-hooks')
        git(repo, 'config', 'commit.gpgsign', 'false')
        git(repo, 'add', '.')
        git(repo, 'commit', '-q', '-m', 'test: bootstrap sources without manifest')
    return SimpleNamespace(root=root, ops=ops, config=config,
                           env={**os.environ, 'XDG_CONFIG_HOME': str(config.parent)}, initial=initial)


def outputs(world):
    return tuple((world.root / path).read_bytes() for path in
                 ('instructions/AGENTS.md', 'instructions/AGENTS.manifest.json'))


def test_catalog_inventory_covers_every_baseline_section():
    catalog = tomllib.loads((ROOT / 'instructions/assembly.toml').read_text())
    assert [f['id'] for f in catalog['fragments']] == IDS
    assert {f['classification'] for f in catalog['fragments']} == {'mandatory'}
    baseline = (ROOT / 'tools/fixtures/instruction-assembly/baseline.md').read_bytes()
    pieces = [(ROOT / f['source']).read_bytes() for f in catalog['fragments'][:-1]]
    pieces.append((ROOT / 'tools/fixtures/instruction-assembly/baseline-projects.md').read_bytes())
    assert b'\n'.join(pieces) == baseline


def test_render_reproduces_initial_bytes_without_writing(world):
    result = build(world, 'render')
    assert result.returncode == 0, result.stderr
    assert result.stdout == world.initial
    assert not (world.root / 'instructions/AGENTS.manifest.json').exists()


def test_write_reproducible_manifest_spans_and_no_rewrite(world):
    assert build(world).returncode == 0
    before = outputs(world)
    manifest = json.loads(before[1])
    assert before[0] == world.initial
    assert len(before[0]) == sum(f['length'] for f in manifest['fragments']) + 13
    for f in manifest['fragments']:
        owner = world.root if f['owner'] == 'lore' else world.ops
        assert before[0][f['offset']:f['offset'] + f['length']] == (owner / f['source']).read_bytes()
    stamps = [(world.root / p).stat().st_mtime_ns for p in
              ('instructions/AGENTS.md', 'instructions/AGENTS.manifest.json')]
    git(world.root, 'add', '.')
    git(world.root, 'commit', '-q', '-m', 'test: commit generated pair')
    assert build(world).returncode == 0
    assert outputs(world) == before
    assert stamps == [(world.root / p).stat().st_mtime_ns for p in
                      ('instructions/AGENTS.md', 'instructions/AGENTS.manifest.json')]
    assert build(world, 'check').returncode == 0


@pytest.mark.parametrize('change', ['duplicate', 'version', 'unknown', 'empty-evidence', 'traversal', 'eof', 'missing'])
def test_bad_inputs_do_not_modify_outputs(world, change):
    assert build(world).returncode == 0
    before = outputs(world)
    path = world.root / 'instructions/assembly.toml'
    text = path.read_text()
    if change == 'duplicate': text = text.replace('id = "refactoring"', 'id = "core"', 1)
    elif change == 'version': text = text.replace('version = 1', 'version = 2', 1)
    elif change == 'unknown': text = text.replace('version = 1', 'version = 1\nmisspelled = "value"', 1)
    elif change == 'empty-evidence': text = text.replace('status = "none recorded"', 'status = ""', 1)
    elif change == 'traversal': text = text.replace('instructions/fragments/core.md', '../outside.md', 1)
    elif change == 'eof':
        source = world.root / 'instructions/fragments/core.md'
        source.write_bytes(source.read_bytes() + b'\n')
    else: (world.root / 'instructions/fragments/core.md').unlink()
    path.write_text(text)
    result = build(world)
    assert result.returncode == 1
    assert outputs(world) == before


@pytest.mark.parametrize('change', ['remove', 'downgrade'])
@pytest.mark.parametrize('command', ['render', 'write', 'check'])
def test_committed_mandatory_minimum_survives_proposed_catalog_and_manifest(world, change, command):
    assert build(world).returncode == 0
    git(world.root, 'add', '.')
    git(world.root, 'commit', '-q', '-m', 'test: record mandatory minimum')
    catalog = world.root / 'instructions/assembly.toml'
    text = catalog.read_text()
    if change == 'remove':
        begin = text.index('[[fragments]]')
        end = text.index('[[fragments]]', begin + 1)
        text = text[:begin] + text[end:]
    else: text = text.replace('classification = "mandatory"', 'classification = "adaptable"', 1)
    catalog.write_text(text)
    manifest = world.root / 'instructions/AGENTS.manifest.json'
    proposed = json.loads(manifest.read_text())
    proposed['fragments'] = [f for f in proposed['fragments'] if f['id'] != 'core']
    manifest.write_text(json.dumps(proposed))
    before = outputs(world)
    result = build(world, command)
    assert result.returncode == 1
    assert b'mandatory' in result.stderr
    assert outputs(world) == before


@pytest.mark.parametrize('path', ['instructions/AGENTS.md', 'instructions/AGENTS.manifest.json'])
def test_output_symlink_is_refused_before_either_file_changes(world, path):
    assert build(world).returncode == 0
    output = world.root / path
    saved = output.read_bytes()
    external = world.root.parent / 'outside-output'
    external.write_bytes(saved)
    output.unlink()
    output.symlink_to(external)
    result = build(world)
    assert result.returncode == 1 and b'symlink' in result.stderr
    assert external.read_bytes() == saved


def test_source_symlink_cannot_escape_owner(world):
    path = world.root / 'instructions/fragments/core.md'
    external = world.root.parent / 'outside-core'
    external.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(external)
    result = build(world)
    assert result.returncode == 1 and b'owner' in result.stderr
    assert not (world.root / 'instructions/AGENTS.manifest.json').exists()


@pytest.mark.parametrize('kind', ['unborn', 'not-git'])
def test_failed_git_is_not_bootstrap(world, kind):
    shutil.rmtree(world.root / '.git')
    if kind == 'unborn': git(world.root, 'init', '-q')
    result = build(world, 'render')
    assert result.returncode == 1 and b'git' in result.stderr.lower()


@pytest.mark.parametrize('command', ['write', 'check'])
def test_override_requires_registered_ops_repository(world, command):
    alien = world.root.parent / 'alien'
    git(world.root.parent, 'clone', '-q', str(world.ops), str(alien))
    result = invoke(world, command, '--owner-root', f'ops={alien}')
    assert result.returncode == 1 and b'registered ops' in result.stderr


def test_ops_worktree_override_is_announced_and_valid(world):
    worktree = world.root.parent / 'ops-worktree'
    git(world.ops, 'worktree', 'add', '-q', '--detach', str(worktree), 'HEAD')
    result = invoke(world, 'write', '--owner-root', f'ops={worktree}')
    assert result.returncode == 0, result.stderr
    result = invoke(world, 'check', '--owner-root', f'ops={worktree}')
    assert result.returncode == 0
    assert result.stderr.count(b'owner-root override') == 1
    assert str(worktree).encode() in result.stderr


def test_explicit_evidence_sentinels_are_preserved(world):
    assert build(world).returncode == 0
    evidence = [e for f in json.loads(outputs(world)[1])['fragments'] for e in f['evidence']]
    assert {'none recorded', 'n/a'} <= {e['status'] for e in evidence}


@pytest.mark.parametrize('bad', [{'version': 1, 'fragments': []}, {'version': True, 'fragments': []}])
def test_malformed_committed_manifest_is_not_an_empty_minimum(world, bad):
    (world.root / 'instructions/AGENTS.manifest.json').write_text(json.dumps(bad))
    git(world.root, 'add', '.')
    git(world.root, 'commit', '-q', '-m', 'test: corrupt committed manifest')
    result = build(world, 'render')
    assert result.returncode == 1 and b'committed manifest' in result.stderr


def load_assembler(world):
    loader = importlib.machinery.SourceFileLoader('tested_assembly', str(world.root / 'bin/assemble-instructions'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_interrupted_pair_is_detected_and_repaired(world, monkeypatch):
    assert build(world).returncode == 0
    module = load_assembler(world)
    core = world.root / 'instructions/fragments/core.md'
    core.write_bytes(core.read_bytes() + b'- Additional approved policy.\n')
    catalog_bytes = (world.root / 'instructions/assembly.toml').read_bytes()
    catalog = tomllib.loads(catalog_bytes.decode())
    sources = {f['id']: ((world.root if f['owner'] == 'lore' else world.ops) / f['source']).read_bytes()
               for f in catalog['fragments']}
    artifact, manifest = module.assemble(catalog_bytes, sources,
                                        (world.root / 'bin/assemble-instructions').read_bytes(), set())
    replace = module.os.replace
    count = 0
    def stop_after_artifact(src, dst):
        nonlocal count
        count += 1
        if count == 2: raise OSError('interrupted pair')
        replace(src, dst)
    with monkeypatch.context() as patch:
        patch.setattr(module.os, 'replace', stop_after_artifact)
        with pytest.raises(OSError, match='interrupted pair'):
            module.write_pair(world.root, artifact, manifest)
    assert build(world, 'check').returncode == 1
    assert not list((world.root / 'instructions').glob('.AGENTS*'))
    assert build(world).returncode == 0
    assert build(world, 'check').returncode == 0
