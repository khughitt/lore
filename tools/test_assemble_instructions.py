"""Exercise the assembler's observable bytes, ownership and Git-view boundaries."""
import importlib.machinery
import importlib.util
import json
import hashlib
import re
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
CATALOG_IDS = IDS[:6] + ['notation'] + IDS[6:]
# Fixture repositories ignore the host's global and system Git config and its hooks.
HERMETIC_GIT = {'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}


def isolated_env(home, **extra):
    """A fixture subprocess's environment, built key by key: the host's PATH, a HOME the
    test owns and hermetic Git, never the inherited environment or a copy of it."""
    return {'PATH': os.environ['PATH'], 'HOME': str(home), **HERMETIC_GIT, **extra}


GIT_ENV: dict[str, str]  # bound per test by `home`; unbound outside a test


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    path = tmp_path / 'home'
    path.mkdir()
    monkeypatch.setitem(globals(), 'GIT_ENV', isolated_env(path))
    return path


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True,
                          env=GIT_ENV).stdout


def commit_all(repo):
    git(repo, 'init', '-q', '-b', 'main')
    git(repo, 'config', 'user.name', 'Assembly fixture')
    git(repo, 'config', 'user.email', 'assembly-fixture@example.invalid')
    git(repo, 'config', 'core.hooksPath', 'fixture-no-hooks')
    git(repo, 'config', 'commit.gpgsign', 'false')
    git(repo, 'add', '.')
    git(repo, 'commit', '-q', '-m', 'test: bootstrap sources without manifest')


def invoke(world, *args):
    return subprocess.run([sys.executable, str(world.root / 'bin/assemble-instructions'), *args],
                          cwd=world.root, env=world.env, capture_output=True)


def build(world, command='write', *args):
    return invoke(world, command, '--owner-root', f'ops={world.ops}', *args)


@pytest.fixture
def world(tmp_path, home):
    root, ops, store = tmp_path / 'lore', tmp_path / 'ops', tmp_path / 'records'
    shutil.copytree(ROOT / 'instructions', root / 'instructions')
    (root / 'instructions/AGENTS.manifest.json').unlink(missing_ok=True)
    # Reference worlds use immutable initial policy, not today's editable prose.
    baseline = (ROOT / 'tools/fixtures/instruction-assembly/baseline.md').read_bytes()
    boundary = baseline.index(b'<!-- ops:projects start')
    cuts = [m.start() for m in re.finditer(rb'^## ', baseline[:boundary], re.M)] + [boundary]
    historical = {name: baseline[a:b][:-1] for name, a, b in zip(IDS[:-1], cuts, cuts[1:])}
    # Fragments cataloged after version one leave the reference world.
    path = root / 'instructions/assembly.toml'
    head, *blocks = path.read_text().split('\n[[fragments]]\n')
    path.write_text('\n[[fragments]]\n'.join([head] + [
        block for block in blocks if tomllib.loads('[[fragments]]\n' + block)['fragments'][0]['id'] in IDS]))
    catalog = tomllib.loads(path.read_text())
    for fragment in catalog['fragments']:
        if fragment['owner'] == 'lore':
            (root / fragment['source']).write_bytes(historical[fragment['id']])
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
    # Evidence owned by lore:records lives in a records directory inside a records repository.
    (config / 'projects.toml').write_text('[projects]\nops = ' + json.dumps(str(ops)) +
                                          '\nlore = ' + json.dumps(str(tmp_path / 'wrong-lore')) +
                                          '\n[records]\nlore = ' + json.dumps(str(store / 'lore')) + '\n')
    directories = {'lore': root, 'ops': ops, 'lore:records': store / 'lore'}
    (store / 'lore').mkdir(parents=True)
    for fragment in catalog['fragments']:
        for evidence in fragment['evidence']:
            if evidence['path'] in ('none recorded', 'n/a'): continue
            file = directories[evidence['owner']] / evidence['path']
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('Disposable historical evidence.\n')
    (store / 'lore/.keep').touch()
    for repo in (root, ops, store):
        commit_all(repo)
    heads = {'lore': git(root, 'rev-parse', 'HEAD').decode().strip(),
             'ops': git(ops, 'rev-parse', 'HEAD').decode().strip(),
             'lore:records': git(store, 'rev-parse', 'HEAD').decode().strip()}
    path = root / 'instructions/assembly.toml'
    text = path.read_text()
    for fragment in catalog['fragments']:
        for evidence in fragment['evidence']:
            if evidence['path'] in ('none recorded', 'n/a'): continue
            text = text.replace('revision = ' + json.dumps(evidence['revision']),
                                'revision = ' + json.dumps(heads[evidence['owner']]))
    path.write_text(text)
    return SimpleNamespace(root=root, ops=ops, store=store, config=config,
                           env=isolated_env(home, XDG_CONFIG_HOME=str(config.parent)),
                           initial=initial)


def outputs(world):
    return tuple((world.root / path).read_bytes() for path in
                 ('instructions/AGENTS.md', 'instructions/AGENTS.manifest.json'))


def change_evidence(world, **changes):
    path = world.root / 'instructions/assembly.toml'
    text = path.read_text()
    prefix, marker, remainder = text.partition('[[fragments.evidence]]\n')
    body, next_marker, suffix = remainder.partition('[[fragments]]')
    for key, value in changes.items():
        body = re.sub(r'^' + key + r' = .*$', lambda _: key + ' = ' + json.dumps(value), body, flags=re.M)
    path.write_text(prefix + marker + body + next_marker + suffix)
    return tomllib.loads(body)


def lore_evidence(world):
    """Point the first evidence at a committed lore file, whatever owners the real catalog uses."""
    file = world.root / 'docs/evidence.md'
    file.parent.mkdir(exist_ok=True)
    file.write_text('Disposable historical evidence.\n')
    git(world.root, 'add', 'docs/evidence.md')
    git(world.root, 'commit', '-q', '-m', 'test: add lore-owned evidence')
    return change_evidence(world, owner='lore', path='docs/evidence.md',
                           revision=git(world.root, 'rev-parse', 'HEAD').decode().strip())


@pytest.mark.parametrize('command', ['render', 'render --manifest', 'write', 'check'])
@pytest.mark.parametrize('status', ['recorded', 'none recorded', 'n/a'])
@pytest.mark.parametrize('bad', ['missing-commit', 'blob', 'mutable', 'abbreviated', 'missing-path', 'tree'])
def test_invalid_concrete_evidence_is_rejected_before_output(world, command, status, bad):
    lore_evidence(world)
    assert build(world).returncode == 0
    before = outputs(world)
    evidence = change_evidence(world, status=status)
    if bad == 'missing-commit': evidence['revision'] = '0' * 40
    elif bad == 'blob':
        evidence['revision'] = git(world.root, 'rev-parse', 'HEAD:' + evidence['path']).decode().strip()
    elif bad == 'mutable': evidence['revision'] = 'HEAD'
    elif bad == 'abbreviated': evidence['revision'] = evidence['revision'][:12]
    elif bad == 'tree': evidence['path'] = 'docs'
    else:
        evidence['path'] = 'disk-only.md'
        (world.root / evidence['path']).write_text('Not in the historical commit.\n')
    change_evidence(world, **evidence)
    result = build(world, *command.split())
    assert result.returncode == 1, result.stdout
    assert b'evidence' in result.stderr
    for key in ('owner', 'revision', 'path'):
        assert evidence[key].encode() in result.stderr
    assert not result.stdout
    assert outputs(world) == before


@pytest.mark.parametrize('path,revision', [
    ('none recorded', 'HEAD'), ('n/a', 'HEAD'),
    ('docs/instruction-provenance.md', 'none recorded'),
    ('docs/instruction-provenance.md', 'n/a'), ('none recorded', 'n/a')])
def test_malformed_evidence_sentinel_pairs_are_rejected(world, path, revision):
    change_evidence(world, path=path, revision=revision)
    result = build(world)
    assert result.returncode == 1
    assert b'evidence' in result.stderr and b'sentinel' in result.stderr
    assert not (world.root / 'instructions/AGENTS.manifest.json').exists()


@pytest.mark.parametrize('sentinel', ['none recorded', 'n/a'])
@pytest.mark.parametrize('status', ['recorded', 'none recorded', 'n/a'])
def test_paired_evidence_sentinels_preserve_metadata_without_owner_lookup(world, sentinel, status):
    expected = change_evidence(world, owner='notes', path=sentinel, revision=sentinel, status=status)
    result = build(world)
    assert result.returncode == 0, result.stderr
    assert json.loads(outputs(world)[1])['fragments'][0]['evidence'][0] == expected


@pytest.mark.parametrize('owner', ['Bad', 'bad/name', 'lore:notes', ':records'])
def test_evidence_owner_requires_a_project_prefix(world, owner):
    change_evidence(world, owner=owner)
    result = build(world)
    assert result.returncode == 1
    assert b'evidence owner' in result.stderr
    assert b'Traceback' not in result.stderr


@pytest.mark.parametrize('case', ['registered', 'unregistered', 'worktree', 'alien'])
def test_evidence_only_external_owner_uses_registry_and_override_identity(world, case):
    lore_evidence(world)
    external = world.root.parent / 'notes'
    git(world.root.parent, 'clone', '-q', str(world.root), str(external))
    expected = change_evidence(world, owner='notes')
    if case != 'unregistered':
        registry = world.config / 'projects.toml'
        registry.write_text(registry.read_text().replace('[projects]\n', '[projects]\nnotes = ' + json.dumps(str(external)) + '\n', 1))
    args = ()
    if case in ('worktree', 'alien'):
        selected = world.root.parent / 'notes-override'
        if case == 'worktree': git(external, 'worktree', 'add', '-q', '--detach', str(selected), 'HEAD')
        else: git(world.root.parent, 'clone', '-q', str(external), str(selected))
        args = ('--owner-root', f'notes={selected}')
    result = build(world, 'write', *args)
    if case in ('unregistered', 'alien'):
        assert result.returncode == 1
        assert b'registered' in result.stderr and b'notes' in result.stderr
        assert not (world.root / 'instructions/AGENTS.manifest.json').exists()
    else:
        assert result.returncode == 0, result.stderr
        assert json.loads(outputs(world)[1])['fragments'][0]['evidence'][0] == expected
        assert build(world, 'check', *args).returncode == 0


@pytest.mark.parametrize('case', ['registered', 'unregistered', 'missing-path', 'alien'])
def test_records_evidence_owner_reads_the_registered_records_directory(world, case):
    store = world.store
    record = store / 'lore/tasks/lore-000000.md'
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text('Disposable task record.\n')
    git(store, 'add', '.')
    git(store, 'commit', '-q', '-m', 'test: add a task record')
    path = 'tasks/absent.md' if case == 'missing-path' else 'tasks/lore-000000.md'
    expected = change_evidence(world, owner='lore:records', path=path,
                               revision=git(store, 'rev-parse', 'HEAD').decode().strip())
    registry = world.config / 'projects.toml'
    records = '' if case == 'unregistered' else '[records]\nlore = ' + json.dumps(str(store / 'lore')) + '\n'
    registry.write_text(registry.read_text().partition('[records]\n')[0] + records)
    args = ()
    if case == 'alien':
        alien = world.root.parent / 'records-alien'
        git(world.root.parent, 'clone', '-q', str(store), str(alien))
        args = ('--owner-root', f'lore:records={alien / "lore"}')
    result = build(world, 'write', *args)
    if case == 'registered':
        assert result.returncode == 0, result.stderr
        assert json.loads(outputs(world)[1])['fragments'][0]['evidence'][0] == expected
        assert build(world, 'check').returncode == 0
    else:
        assert result.returncode == 1
        assert b'lore:records' in result.stderr and b'Traceback' not in result.stderr
        assert not (world.root / 'instructions/AGENTS.manifest.json').exists()


def inventory(root):
    catalog = tomllib.loads((root / 'instructions/assembly.toml').read_text())
    return ([f['id'] for f in catalog['fragments']],
            {f['classification'] for f in catalog['fragments']})


def test_catalog_inventory_preserves_v1_mandatory_ids():
    assert inventory(ROOT) == (CATALOG_IDS, {'mandatory'})


def test_historical_reference_fixtures_match_independent_git_blobs():
    for name, object_id, expected in [
        ('baseline.md', '5297be329c58bc758b20c48a504a87887be5470a', '66f5ae3d32e218ac3688969171179501ecdcc253e4d9a01f48c05ddb04350642'),
        ('initial.md', '08bd5862dcd0fa47000dac7f13e8617875f99586', '2729ca9ae116c50501a65764af73b4729498df283407f8b6a5a5e98e15cc2760')]:
        fixture = (ROOT / 'tools/fixtures/instruction-assembly' / name).read_bytes()
        assert fixture == git(ROOT, 'cat-file', 'blob', object_id)
        assert hashlib.sha256(fixture).hexdigest() == expected


def test_fixture_subprocesses_receive_no_inherited_environment(world, tmp_path, monkeypatch):
    monkeypatch.setenv('LORE_TEST_CANARY', 'fake-credential')
    assert set(world.env) == {'PATH', 'HOME', *HERMETIC_GIT, 'XDG_CONFIG_HOME'}
    assert world.env['HOME'] == str(tmp_path / 'home')
    shown = git(world.root, '-c', 'alias.show-env=!env', 'show-env').decode()
    assert 'LORE_TEST_CANARY' not in shown
    assert f'HOME={tmp_path / "home"}\n' in shown


def test_render_reproduces_initial_bytes_without_writing(world):
    result = build(world, 'render')
    assert result.returncode == 0, result.stderr
    assert result.stdout == world.initial
    assert not (world.root / 'instructions/AGENTS.manifest.json').exists()


def files(root):
    return {path: path.read_bytes() for path in sorted(root.rglob('*')) if path.is_file()}


def test_render_manifest_previews_the_pair_write_produces_without_writing(world):
    before = files(world.root.parent)
    plain, preview = build(world, 'render'), build(world, 'render', '--manifest')
    assert files(world.root.parent) == before
    assert plain.returncode == 0 and preview.returncode == 0, preview.stderr
    assert json.loads(preview.stdout)['artifact']['sha256'] == hashlib.sha256(plain.stdout).hexdigest()
    assert build(world).returncode == 0
    assert outputs(world) == (plain.stdout, preview.stdout)


def test_render_manifest_reads_the_owner_root_override(world):
    prepared = world.root.parent / 'prepared-ops'
    git(world.ops, 'worktree', 'add', '-q', '--detach', str(prepared), 'HEAD')
    projects = added_projects(world)
    (prepared / 'instructions/fragments/projects.md').write_bytes(projects)
    override = ('--owner-root', f'ops={prepared}')
    before = files(world.root.parent)
    plain, preview = invoke(world, 'render', *override), invoke(world, 'render', '--manifest', *override)
    assert files(world.root.parent) == before
    assert plain.returncode == 0 and preview.returncode == 0, preview.stderr
    assert plain.stderr == preview.stderr == b''
    assert plain.stdout.endswith(projects)
    assert invoke(world, 'write', *override).returncode == 0
    assert outputs(world) == (plain.stdout, preview.stdout)


@pytest.mark.parametrize('args', [(), ('--manifest',)])
def test_render_with_a_missing_source_prints_nothing(world, args):
    (world.root / 'instructions/fragments/core.md').unlink()
    result = build(world, 'render', *args)
    assert result.returncode == 1
    assert b'instructions/fragments/core.md' in result.stderr
    assert not result.stdout


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


def test_blob_ids_match_git_without_a_subprocess(world, monkeypatch):
    module = load_assembler(world)
    catalog = tomllib.loads((world.root / 'instructions/assembly.toml').read_text())
    inputs = [((world.root if f['owner'] == 'lore' else world.ops) / f['source']).read_bytes()
              for f in catalog['fragments']]
    current = tomllib.loads((ROOT / 'instructions/assembly.toml').read_text())
    inputs += [(ROOT / f['source']).read_bytes() for f in current['fragments'] if f['owner'] == 'lore']
    inputs.append((ROOT / 'bin/assemble-instructions').read_bytes())
    expected = [subprocess.run(['git', '-C', str(world.root), 'hash-object', '--stdin'], input=data,
                               capture_output=True, check=True).stdout.decode().strip() for data in inputs]
    def refuse(*args, **kwargs):
        raise AssertionError('blob must not start a subprocess')
    monkeypatch.setattr(module.subprocess, 'run', refuse)
    assert [module.blob(data) for data in inputs] == expected


def test_foreign_git_calls_ask_for_local_env_names_once(world, monkeypatch):
    module = load_assembler(world)
    calls = []
    run = module.subprocess.run
    def counting(argv, *args, **kwargs):
        calls.append(argv)
        return run(argv, *args, **kwargs)
    monkeypatch.setattr(module.subprocess, 'run', counting)
    heads = {module.git_bytes(world.ops, 'rev-parse', 'HEAD') for _ in range(3)}
    assert len(heads) == 1
    assert sum('--local-env-vars' in argv for argv in calls) == 1


def evidence_catalog(*pointers):
    return {'fragments': [{'evidence': [{'owner': owner, 'revision': revision, 'path': path}
                                        for owner, revision, path in pointers]}]}


def commit_files(world, files):
    for name, data in files.items():
        (world.root / name).write_bytes(data)
    git(world.root, 'add', '--', *files)
    git(world.root, 'commit', '-q', '-m', 'test: historical evidence files')
    return git(world.root, 'rev-parse', 'HEAD').decode().strip()


def invalid(module, catalog, owners):
    with pytest.raises(ValueError) as error:
        module.validate_evidence(catalog, owners)
    return str(error.value)


def test_newline_paths_keep_their_answers_paired(world):
    module = load_assembler(world)
    head = commit_files(world, {'notes\nwith newline.md': b'kept\n', 'binary.dat': b'a\0b\0\0c\n',
                                'plain.md': b'plain\n'})
    owners = {'lore': world.root}
    module.validate_evidence(evidence_catalog(('lore', head, 'notes\nwith newline.md'),
                                              ('lore', head, 'binary.dat'), ('lore', head, 'plain.md')), owners)
    assert invalid(module, evidence_catalog(('lore', head, 'notes\nwith newline.md'), ('lore', head, 'binary.dat'),
                                            ('lore', head, 'docs')),
                   owners) == f'invalid evidence lore {head}:docs: historical path must identify a file blob'


def test_batch_call_failure_is_a_git_failure(world, monkeypatch):
    module = load_assembler(world)
    head = commit_files(world, {'plain.md': b'plain\n'})
    def old_git(argv, *args, **kwargs):
        return subprocess.CompletedProcess(argv, 129, b'', b"error: unknown switch `Z'")
    monkeypatch.setattr(module.subprocess, 'run', old_git)
    assert invalid(module, evidence_catalog(('lore', head, 'plain.md')),
                   {'lore': world.root}) == f"invalid evidence lore {head}:plain.md: git failed: error: unknown switch `Z'"


def test_missing_paths_are_not_file_blobs(world):
    module = load_assembler(world)
    head = commit_files(world, {'plain.md': b'plain\n'})
    assert invalid(module, evidence_catalog(('lore', head, 'notes\nmissing.md'), ('lore', head, 'plain.md')),
                   {'lore': world.root}) == f'invalid evidence lore {head}:notes\nmissing.md: historical path must identify a file blob'


def test_first_failing_pointer_in_catalog_order_is_reported(world):
    module = load_assembler(world)
    head = commit_files(world, {'plain.md': b'plain\n'})
    ops_head = git(world.ops, 'rev-parse', 'HEAD').decode().strip()
    owners = {'lore': world.root, 'ops': world.ops}
    assert invalid(module, evidence_catalog(('lore', head, 'plain.md'), ('ops', ops_head, 'missing.md'),
                                            ('lore', 'HEAD', 'plain.md')),
                   owners) == f'invalid evidence ops {ops_head}:missing.md: historical path must identify a file blob'
    assert invalid(module, evidence_catalog(('lore', 'HEAD', 'plain.md'), ('ops', ops_head, 'missing.md')),
                   owners) == 'invalid evidence lore HEAD:plain.md: revision must be a full immutable commit id'


def test_earlier_invalid_pointer_outranks_a_later_repository_failure(world):
    module = load_assembler(world)
    head = commit_files(world, {'plain.md': b'plain\n'})
    owners = {'lore': world.root, 'ops': world.root.parent / 'no-such-ops'}
    unavailable = ('ops', '0' * 40, 'docs/notes.md')
    assert invalid(module, evidence_catalog(('lore', head, 'missing.md'), unavailable),
                   owners) == f'invalid evidence lore {head}:missing.md: historical path must identify a file blob'
    assert invalid(module, evidence_catalog(unavailable, ('lore', head, 'missing.md')),
                   owners).startswith(f'invalid evidence ops {"0" * 40}:docs/notes.md: git failed: ')


def test_unreadable_historical_blob_is_rejected(world):
    module = load_assembler(world)
    head = commit_files(world, {'damaged.md': b'content that will not survive truncation\n', 'plain.md': b'plain\n'})
    object_id = git(world.root, 'rev-parse', f'{head}:damaged.md').decode().strip()
    loose = world.root / '.git/objects' / object_id[:2] / object_id[2:]
    loose.chmod(0o644)
    loose.write_bytes(loose.read_bytes()[:12])
    message = invalid(module, evidence_catalog(('lore', head, 'plain.md'), ('lore', head, 'damaged.md'),
                                               ('lore', head, 'plain.md')), {'lore': world.root})
    assert message.startswith(f'invalid evidence lore {head}:damaged.md: historical blob is unreadable: ')


def test_evidence_validation_spawns_one_git_per_owner(world, monkeypatch):
    module = load_assembler(world)
    catalog = module.catalog_from((world.root / 'instructions/assembly.toml').read_bytes())
    owners = {'lore': world.root, 'ops': world.ops, 'lore:records': world.store / 'lore'}
    concrete = {e['owner'] for f in catalog['fragments'] for e in f['evidence']
                if e['path'] not in ('none recorded', 'n/a')}
    calls = []
    run = module.subprocess.run
    def counting(argv, *args, **kwargs):
        calls.append(argv)
        return run(argv, *args, **kwargs)
    monkeypatch.setattr(module.subprocess, 'run', counting)
    module.validate_evidence(catalog, owners)
    lookups = [argv for argv in calls if '--local-env-vars' in argv]
    assert len(calls) - len(lookups) <= len(concrete)
    assert len(lookups) <= 1


def commit_pair(world):
    assert build(world).returncode == 0
    git(world.root, 'add', '.')
    git(world.root, 'commit', '-q', '-m', 'test: commit assembled pair')


@pytest.mark.parametrize('path', ['instructions/assembly.toml', 'instructions/fragments/core.md',
                                  'instructions/AGENTS.md', 'instructions/AGENTS.manifest.json'])
def test_invalid_staged_input_cannot_be_hidden_by_restoring_disk(world, path):
    commit_pair(world)
    file = world.root / path
    before = file.read_bytes()
    file.write_bytes(b'invalid staged bytes\n')
    git(world.root, 'add', path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(before)
    assert build(world, 'check').returncode == 1


def test_consistent_index_ignores_unstaged_policy_but_working_tree_check_rejects_it(world):
    commit_pair(world)
    source = world.root / 'instructions/fragments/core.md'
    source.write_bytes(source.read_bytes() + b'- Approved policy update.\n')
    assert build(world).returncode == 0
    git(world.root, 'add', '.')
    source.write_bytes(source.read_bytes() + b'- Unstaged policy.\n')
    assert build(world, 'check').returncode == 0
    assert build(world, 'check', '--working-tree').returncode == 1


def test_staged_invalid_evidence_cannot_be_hidden_by_a_valid_disk_catalog(world):
    commit_pair(world)
    catalog = world.root / 'instructions/assembly.toml'
    valid = catalog.read_bytes()
    change_evidence(world, revision='0' * 40)
    git(world.root, 'add', 'instructions/assembly.toml')
    catalog.write_bytes(valid)
    result = build(world, 'check')
    assert result.returncode == 1
    assert b'evidence' in result.stderr and b'0' * 40 in result.stderr
    assert build(world, 'check', '--working-tree').returncode == 0


def test_staged_valid_evidence_ignores_an_invalid_disk_catalog(world):
    commit_pair(world)
    change_evidence(world, location='Another inspected section')
    assert build(world).returncode == 0
    git(world.root, 'add', '.')
    change_evidence(world, revision='0' * 40)
    assert build(world, 'check').returncode == 0
    result = build(world, 'check', '--working-tree')
    assert result.returncode == 1 and b'evidence' in result.stderr


def test_worktree_commit_hook_uses_each_evidence_owners_repository(world):
    commit_pair(world)
    worktree = world.root.parent / 'lore-worktree'
    git(world.root, 'worktree', 'add', '-q', '-b', 'hook-evidence', str(worktree), 'HEAD')
    hooks = worktree / 'fixture-no-hooks'
    hooks.mkdir()
    hook = hooks / 'pre-commit'
    hook.write_text('#!/bin/sh\nexec ' + sys.executable + ' bin/assemble-instructions check\n')
    hook.chmod(0o755)
    (worktree / 'other.md').write_text('Unrelated staged content.\n')
    git(worktree, 'add', 'other.md')
    result = subprocess.run(['git', '-C', str(worktree), 'commit', '-q', '-m', 'test: hook evidence'],
                            env=world.env, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_hook_environment_preserves_the_selected_local_index(world):
    commit_pair(world)
    catalog = world.root / 'instructions/assembly.toml'
    valid = catalog.read_bytes()
    alternate = world.root.parent / 'hook-index'
    shutil.copy(world.root / '.git/index', alternate)
    world.env.update(GIT_DIR=str(world.root / '.git'), GIT_WORK_TREE=str(world.root), GIT_INDEX_FILE=str(alternate))
    change_evidence(world, revision='0' * 40)
    subprocess.run(['git', '-C', str(world.root), 'add', 'instructions/assembly.toml'],
                   env=world.env, check=True, capture_output=True)
    catalog.write_bytes(valid)
    result = build(world, 'check')
    assert result.returncode == 1
    assert b'0' * 40 in result.stderr


REQUIRED_PATHS = ['instructions/assembly.toml', 'instructions/AGENTS.md',
                  'instructions/AGENTS.manifest.json', 'bin/assemble-instructions'] + [
                      f'instructions/fragments/{name}.md' for name in IDS[:-1]]

@pytest.mark.parametrize('action', ['delete', 'rename'])
@pytest.mark.parametrize('path', REQUIRED_PATHS)
def test_required_staged_delete_or_rename_never_falls_back_to_disk(world, action, path):
    commit_pair(world)
    file = world.root / path
    before = file.read_bytes()
    if action == 'delete': git(world.root, 'rm', '-q', path)
    else: git(world.root, 'mv', path, path + '.moved')
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(before)
    assert build(world, 'check').returncode == 1


def test_staged_assembler_must_equal_executing_code(world):
    commit_pair(world)
    script = world.root / 'bin/assemble-instructions'
    script.write_bytes(script.read_bytes() + b'\n# stage intended code\n')
    assert build(world).returncode == 0
    git(world.root, 'add', '.')
    script.write_bytes(script.read_bytes() + b'\n# different executing code\n')
    result = build(world, 'check')
    assert result.returncode == 1
    assert b'assembler' in result.stderr and b'index' in result.stderr


def test_unrelated_staging_keeps_working_tree_check(world):
    commit_pair(world)
    (world.root / 'other.md').write_text('unrelated\n')
    git(world.root, 'add', 'other.md')
    (world.root / 'instructions/AGENTS.md').write_text('unstaged drift\n')
    assert build(world, 'check').returncode == 1


def test_renderer_drift_and_failure_are_reported_and_skip_is_narrow(world):
    commit_pair(world)
    renderer = world.ops / 'bin/ops-projects'
    renderer.write_text('import sys\nsys.stdout.write("drift\\n")\n')
    assert build(world, 'check').returncode == 1
    assert build(world, 'check', '--skip-projects-render').returncode == 0
    (world.root / 'instructions/AGENTS.md').write_text('stale artifact\n')
    assert build(world, 'check', '--skip-projects-render').returncode == 1
    renderer.write_text('import sys\nsys.stderr.write("bad renderer\\n")\nsys.exit(1)\n')
    result = build(world, 'check')
    assert result.returncode == 1 and b'render failed' in result.stderr and b'bad renderer' in result.stderr


END_MARKER = b'<!-- ops:projects end -->\n'


def added_projects(world, count=1):
    """Projects bytes with `count` new entries, as a host registration would render them."""
    current = (world.ops / 'instructions/fragments/projects.md').read_bytes()
    entries = b''.join(b'- `zz%02d` -- fixture %02d -- A newly registered project\n' % (n, n) for n in range(count))
    return current.replace(END_MARKER, entries + END_MARKER)


def set_renderer(world, data):
    (world.ops / 'bin/ops-projects').write_text(f'import sys\nsys.stdout.buffer.write({data!r})\n')


def refresh_ops(world, data):
    (world.ops / 'instructions/fragments/projects.md').write_bytes(data)
    set_renderer(world, data)


def snapshot(world):
    return outputs(world) + ((world.ops / 'instructions/fragments/projects.md').read_bytes(),)


def check_without_writes(world, *args):
    before = snapshot(world)
    result = build(world, 'check', *args)
    assert snapshot(world) == before
    assert result.returncode == 1
    assert b'Traceback' not in result.stderr
    return result.stderr.decode()


def test_renderer_drift_names_the_registry_owner_and_both_repairs(world):
    commit_pair(world)
    set_renderer(world, added_projects(world))
    err = check_without_writes(world)
    assert 'Projects input differs from this host' in err
    assert 'owner ops' in err
    assert 'just projects in ops, then just assemble in lore' in err
    assert '+ - `zz00` -- fixture 00' in err


def test_refreshed_projects_input_with_stale_artifact_is_projects_only(world):
    commit_pair(world)
    refresh_ops(world, added_projects(world))
    err = check_without_writes(world)
    assert 'artifact Projects block stale' in err
    assert 'just assemble in lore' in err
    assert 'just projects' not in err and 'instructions/fragments/' not in err
    assert '+ - `zz00` -- fixture 00' in err


def test_projects_evidence_is_bounded(world):
    commit_pair(world)
    refresh_ops(world, added_projects(world, 40))
    err = check_without_writes(world)
    changed = [line for line in err.splitlines() if line.lstrip().startswith(('+ ', '- '))]
    assert 0 < len(changed) < 40
    assert 'more changed lines' in err


@pytest.mark.parametrize('drift', ['local', 'mixed'])
def test_local_or_mixed_artifact_drift_keeps_the_fragment_hint(world, drift):
    commit_pair(world)
    core = world.root / 'instructions/fragments/core.md'
    core.write_bytes(core.read_bytes() + b'- Unassembled policy.\n')
    if drift == 'mixed': refresh_ops(world, added_projects(world))
    err = check_without_writes(world)
    assert 'artifact stale; edit instructions/fragments/' in err
    assert 'Projects block' not in err


@pytest.mark.parametrize('damage', ['missing', 'duplicated'])
def test_unrecognised_markers_keep_the_general_failure(world, damage):
    commit_pair(world)
    refresh_ops(world, added_projects(world))
    artifact = world.root / 'instructions/AGENTS.md'
    data = artifact.read_bytes()
    artifact.write_bytes(data.replace(END_MARKER, b'') if damage == 'missing' else data + END_MARKER)
    err = check_without_writes(world)
    assert 'artifact stale; edit instructions/fragments/' in err
    assert 'Projects block' not in err


def test_projects_only_classification_reads_the_staged_artifact(world):
    commit_pair(world)
    core = world.root / 'instructions/fragments/core.md'
    core.write_bytes(core.read_bytes() + b'- Approved policy update.\n')
    assert build(world).returncode == 0
    git(world.root, 'add', '.')
    refresh_ops(world, added_projects(world))
    assert build(world).returncode == 0
    err = check_without_writes(world)
    assert 'artifact Projects block stale' in err
    assert build(world, 'check', '--working-tree').returncode == 0


def test_unrelated_staging_classifies_the_working_tree_artifact(world):
    commit_pair(world)
    (world.root / 'other.md').write_text('unrelated\n')
    git(world.root, 'add', 'other.md')
    refresh_ops(world, added_projects(world))
    err = check_without_writes(world)
    assert 'artifact Projects block stale' in err
    assert build(world).returncode == 0
    assert build(world, 'check').returncode == 0


def test_pinned_proofs_survive_current_policy_renderer_and_internal_api_change(world):
    commit_pair(world)
    lore_rev = git(world.root, 'rev-parse', 'HEAD').decode().strip()
    ops_rev = git(world.ops, 'rev-parse', 'HEAD').decode().strip()
    args = ('--revision', lore_rev, '--owner-root', f'ops={world.ops}')
    baseline = invoke(world, 'verify-baseline', *args)
    assert baseline.returncode == 0, baseline.stderr
    initial = invoke(world, 'verify-initial', *args, '--projects-revision', ops_rev)
    assert initial.returncode == 0, initial.stderr
    core = world.root / 'instructions/fragments/core.md'
    core.write_bytes(core.read_bytes() + b'- Later approved policy.\n')
    assert build(world).returncode == 0
    assert build(world, 'check').returncode == 0
    script = world.root / 'bin/assemble-instructions'
    changed = script.read_text().replace('def assemble(catalog_bytes, sources, assembler_bytes, required_ids, *, mode=',
                                         'def renamed_current_assemble(catalog_bytes, sources, assembler_bytes, required_ids, *, mode=')
    changed = changed.replace('        catalog = catalog_from(catalog_bytes)\n',
                              '        raise ValueError("current production validation must not run")\n')
    script.write_text(changed)
    change_evidence(world, revision='0' * 40)
    (world.root / 'tools/instruction-assembly-proof-driver.py').write_text('raise RuntimeError("current driver must not run")\n')
    (world.ops / 'bin/ops-projects').write_text('raise RuntimeError("live renderer must not run")\n')
    assert invoke(world, 'verify-baseline', *args).returncode == 0
    assert invoke(world, 'verify-initial', *args, '--projects-revision', ops_rev).returncode == 0


def test_pinned_proof_rejects_changed_snapshot_and_missing_revision(world):
    commit_pair(world)
    core = world.root / 'instructions/fragments/core.md'
    core.write_bytes(core.read_bytes() + b'- Incorrect initial snapshot.\n')
    git(world.root, 'add', '.')
    git(world.root, 'commit', '-q', '-m', 'test: changed snapshot')
    changed = git(world.root, 'rev-parse', 'HEAD').decode().strip()
    result = invoke(world, 'verify-baseline', '--revision', changed, '--owner-root', f'ops={world.ops}')
    assert result.returncode == 1 and b'baseline' in result.stderr
    result = invoke(world, 'verify-baseline', '--revision', 'missing-revision', '--owner-root', f'ops={world.ops}')
    assert result.returncode == 1 and b'git' in result.stderr.lower()


@pytest.mark.parametrize('change', ['missing', 'unregistered', 'bad-path', 'bad-records'])
def test_registry_errors_are_clear_validation_failures(world, change):
    registry = world.config / 'projects.toml'
    if change == 'missing': registry.unlink()
    elif change == 'unregistered': registry.write_text('[projects]\n')
    elif change == 'bad-records': registry.write_text('records = 1\n' + registry.read_text().partition('[records]\n')[0])
    else: registry.write_text('[projects]\nops = 123\n')
    result = build(world)
    assert result.returncode == 1
    assert b'Traceback' not in result.stderr
    assert not (world.root / 'instructions/AGENTS.manifest.json').exists()


@pytest.mark.parametrize('change', ['missing', 'old-marker', 'duplicate-marker'])
def test_projects_input_structure_and_renderer_failures_are_guarded(world, change):
    commit_pair(world)
    projects = world.ops / 'instructions/fragments/projects.md'
    if change == 'missing': (world.ops / 'bin/ops-projects').unlink()
    elif change == 'old-marker': projects.write_bytes(projects.read_bytes().replace(b'edit identity.toml in the project, or identity-mirror.toml in ops', b'edit identity-mirror.toml in ops'))
    else: projects.write_bytes(projects.read_bytes() + b'<!-- ops:projects end -->\n')
    result = build(world, 'check')
    assert result.returncode == 1
    assert b'Projects' in result.stderr or b'render failed' in result.stderr


def test_deployed_recipes_ignore_stale_preparation_environment(world):
    shutil.copy(ROOT / 'justfile', world.root / 'justfile')
    shutil.copy(ROOT / 'bin/skill-sizes.py', world.root / 'bin/skill-sizes.py')
    (world.root / 'hooks').mkdir(exist_ok=True)
    shutil.copy(ROOT / 'hooks/claude-profile', world.root / 'hooks/claude-profile')  # check_cmd compiles it
    for name in ('ops-check', 'ops-docs'):
        (world.root / 'tools' / name).write_text('import sys\n')
    (world.root / 'tools/tt').write_text('import subprocess, sys\nsys.exit(subprocess.run(sys.argv[sys.argv.index("--") + 1:]).returncode)\n')
    task_stub = world.root / 'bin/tasks'
    task_stub.write_text('#!/bin/sh\nexit 0\n')
    task_stub.chmod(0o755)
    commit_pair(world)
    stale = world.root.parent / 'old-ops-worktree'
    git(world.ops, 'worktree', 'add', '-q', '--detach', str(stale), 'HEAD')
    (stale / 'instructions/fragments/projects.md').write_text('stale source\n')
    env = {**world.env, 'PATH': str(world.root / 'bin') + os.pathsep + world.env['PATH']}
    for value in (None, str(stale), 'stale path with spaces'):
        selected = dict(env)
        if value is not None: selected['LORE_ASSEMBLY_OPS_ROOT'] = value
        result = subprocess.run(['just', 'check'], cwd=world.root, env=selected, capture_output=True)
        assert result.returncode == 0, result.stderr
        assert b'owner-root override' not in result.stderr


def test_version_one_inventory_does_not_freeze_current_policy_text(world):
    checkout = world.root
    source = checkout / 'instructions/fragments/core.md'
    source.write_bytes(source.read_bytes() + b'- Later reviewed policy.\n')
    assert inventory(checkout) == (IDS, {'mandatory'})


def test_later_policy_bytes_are_rendered_without_changing_historical_fixtures(world):
    source = world.root / 'instructions/fragments/core.md'
    original = source.read_bytes()
    updated = original + b'- Later reviewed policy.\n'
    source.write_bytes(updated)
    expected = world.initial.replace(original + b'\n', updated + b'\n', 1)
    result = build(world, 'render')
    assert result.returncode == 0 and result.stdout == expected
    assert build(world).returncode == 0
    assert outputs(world)[0] == expected
    assert (world.root / 'tools/fixtures/instruction-assembly/initial.md').read_bytes() == world.initial

# Rule provenance: byte boundaries, honest unknowns and immutable subject bindings.
RULE_A = 'rule:' + 'a' * 32
RULE_B = 'rule:' + 'b' * 32
CLAUSE_A = 'clause:' + 'c' * 32


def marked(rule_id, content):
    return f'<!-- {rule_id} begin -->\n'.encode() + content + f'<!-- {rule_id} end -->\n'.encode()


@pytest.mark.parametrize('content', [b'- Keep intent.\n', 'A café.\n'.encode(), b'| A | B |\n|---|---|\n| x | y |\n'])
def test_rule_scan_byte_identity_and_offsets(world, content):
    module = load_assembler(world)
    source = b'## Heading\n\n' + marked(RULE_A, content) + marked(RULE_B, b'Paragraph.\n')
    scan = module.scan_rules(source)
    assert scan['rendered'] == b'## Heading\n\n' + content + b'Paragraph.\n'
    assert scan['rules'][0] == {'id': RULE_A, 'text': content.decode(), 'sha256': hashlib.sha256(content).hexdigest(),
                                'offset': 12, 'length': len(content)}
    reverse = module.scan_rules(marked(RULE_B, b'Paragraph.\n') + marked(RULE_A, content))
    assert reverse['rules'][1]['sha256'] == scan['rules'][0]['sha256']
    assert scan['uncovered'] == []


@pytest.mark.parametrize('source', [
    marked(RULE_A, b'x\n') + marked(RULE_A, b'y\n'),
    marked(RULE_A, marked(RULE_B, b'x\n')),
    marked(RULE_A, b'x\n').replace((RULE_A + ' end').encode(), (RULE_B + ' end').encode()),
    b'<!-- rule:broken begin -->\nx\n',
    b'```md\n' + marked(RULE_A, b'x\n') + b'```\n',
    marked(RULE_A, b'x\n')[:-1], marked(RULE_A, b'x\n') + b'\n',
    b'\xff\n', marked(RULE_A, b'x\n\n'),
])
def test_rule_marker_errors(world, source):
    with pytest.raises((ValueError, UnicodeError)):
        load_assembler(world).scan_rules(source)


def test_exclusion_block_boundaries(world):
    module = load_assembler(world)
    scan = module.scan_rules(b'## Heading\n\nIntro.\n\n```md\n\n# code\n```\n' + marked(RULE_A, b'- Rule.\n'))
    assert scan['uncovered'] == [dict(text='Intro.\n', start_line=3, end_line=3),
                                  dict(text='```md\n\n# code\n```\n', start_line=5, end_line=8)]
    record = module.new_rule_record(RULE_A, 'Rule', b'- Rule.\n')
    with pytest.raises(ValueError, match='add-rule.*exclusion'):
        module.validate_rule_set({RULE_A: record}, {'core': scan}, {})
    exclusions = {'core': [dict(text=b['text'], reason='example/connective prose') for b in scan['uncovered']]}
    module.validate_rule_set({RULE_A: record}, {'core': scan}, exclusions)
    exclusions['core'].append(dict(text='unused\n', reason='invalid'))
    with pytest.raises(ValueError, match='exclusion'):
        module.validate_rule_set({RULE_A: record}, {'core': scan}, exclusions)


def test_record_schema_and_bindings(world):
    module = load_assembler(world)
    record = module.new_rule_record(RULE_A, 'Keep intent', b'- Keep intent.\n')
    module.validate_rule(record)
    assert record['impact']['tier'] == 'unknown'
    assert record['events'] == record['assessments'] == []
    scan = module.scan_rules(marked(RULE_A, b'- Keep intent.\n'))
    module.validate_rule_set({RULE_A: record}, {'core': scan}, {})
    for change in ('extra', 'hash', 'missing', 'retired', 'dangling'):
        bad = json.loads(json.dumps(record))
        if change == 'extra': bad['extra'] = 1
        if change == 'hash': bad['revisions'][0]['sha256'] = '0' * 64
        if change == 'retired': bad['state'] = 'retired'
        if change == 'dangling': bad['relations'] = [{'kind': 'split_from', 'targets': [RULE_B]}]
        with pytest.raises(ValueError):
            module.validate_rule_set({} if change == 'missing' else {RULE_A: bad}, {'core': scan}, {})


def test_record_schema_clause_quote_and_retired_history(world):
    module = load_assembler(world)
    r = module.new_rule_record(RULE_A, 'Intent', b'- Keep intent.\n')
    rev = r['revisions'][0]
    clause = dict(id=CLAUSE_A, text='Keep intent.', offset=2, sha256=hashlib.sha256(b'Keep intent.').hexdigest(),
                  parent_sha256=rev['sha256'], overlaps=[])
    rev['clauses'].append(clause)
    module.validate_rule(r)
    clause['offset'] = 3
    with pytest.raises(ValueError, match='clause'):
        module.validate_rule(r)
    clause['offset'] = 2
    r['state'] = 'retired'
    module.validate_rule_set({RULE_A: r}, {}, {})


def test_record_schema_fixtures(world):
    module = load_assembler(world)
    fixtures = ROOT / 'tools/fixtures/rule-provenance'
    for name in ('simple', 'compound', 'historical-excerpt', 'reaffirmed'):
        module.validate_rule(json.loads((fixtures / (name + '.json')).read_text()))
    bad = json.loads((fixtures / 'invalid.json').read_text())
    with pytest.raises(ValueError): module.validate_rule(bad)
    for name, schema in module.rule_schemas().items():
        assert json.loads((ROOT / f'instructions/schemas/{name}.json').read_text()) == schema


def test_rule_reader_uses_selected_index(world):
    module = load_assembler(world)
    r = module.new_rule_record(RULE_A, 'Intent', b'- Keep intent.\n')
    path = world.root / 'instructions/rules' / (RULE_A[5:] + '.json')
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(r))
    git(world.root, 'add', 'instructions/rules')
    path.write_text('invalid')
    assert module.read_rule_set(world.root, index=True)[RULE_A] == r
    with pytest.raises(ValueError): module.read_rule_set(world.root)


def test_record_schema_historical_and_duplicate_events(world):
    module = load_assembler(world)
    path = ROOT / 'tools/fixtures/rule-provenance/historical-excerpt.json'
    record = json.loads(path.read_bytes())
    module.validate_rule(record)
    record['events'].append(record['events'][0])
    with pytest.raises(ValueError, match='duplicate events'):
        module.validate_rule(record)
    record['events'].pop()
    record['assessments'] = [{'id': 'a1', 'kind': 'applicability', 'subject': record['events'][0]['subject']}]
    with pytest.raises(ValueError):
        module.validate_rule(record)
