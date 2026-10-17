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
    (config / 'projects.toml').write_text('[projects]\nops = ' + json.dumps(str(ops)) +
                                          '\nlore = ' + json.dumps(str(tmp_path / 'wrong-lore')) + '\n')
    for fragment in catalog['fragments']:
        for evidence in fragment['evidence']:
            if evidence['path'] in ('none recorded', 'n/a'): continue
            repo = root if evidence['owner'] == 'lore' else ops
            file = repo / evidence['path']
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('Disposable historical evidence.\n')
    for repo in (root, ops):
        git(repo, 'init', '-q', '-b', 'main')
        git(repo, 'config', 'user.name', 'Assembly fixture')
        git(repo, 'config', 'user.email', 'assembly-fixture@example.invalid')
        git(repo, 'config', 'core.hooksPath', 'fixture-no-hooks')
        git(repo, 'config', 'commit.gpgsign', 'false')
        git(repo, 'add', '.')
        git(repo, 'commit', '-q', '-m', 'test: bootstrap sources without manifest')
    path = root / 'instructions/assembly.toml'
    text = path.read_text()
    for fragment in catalog['fragments']:
        for evidence in fragment['evidence']:
            if evidence['path'] in ('none recorded', 'n/a'): continue
            repo = root if evidence['owner'] == 'lore' else ops
            revision = git(repo, 'rev-parse', 'HEAD').decode().strip()
            text = text.replace('revision = ' + json.dumps(evidence['revision']),
                                'revision = ' + json.dumps(revision))
    path.write_text(text)
    return SimpleNamespace(root=root, ops=ops, config=config,
                           env={**os.environ, 'XDG_CONFIG_HOME': str(config.parent)}, initial=initial)


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


@pytest.mark.parametrize('command', ['render', 'write', 'check'])
@pytest.mark.parametrize('status', ['recorded', 'none recorded', 'n/a'])
@pytest.mark.parametrize('bad', ['missing-commit', 'blob', 'mutable', 'abbreviated', 'missing-path', 'tree'])
def test_invalid_concrete_evidence_is_rejected_before_output(world, command, status, bad):
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
    result = build(world, command)
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


@pytest.mark.parametrize('owner', ['Bad', 'bad/name'])
def test_evidence_owner_requires_a_project_prefix(world, owner):
    change_evidence(world, owner=owner)
    result = build(world)
    assert result.returncode == 1
    assert b'evidence owner' in result.stderr
    assert b'Traceback' not in result.stderr


@pytest.mark.parametrize('case', ['registered', 'unregistered', 'worktree', 'alien'])
def test_evidence_only_external_owner_uses_registry_and_override_identity(world, case):
    external = world.root.parent / 'notes'
    git(world.root.parent, 'clone', '-q', str(world.root), str(external))
    expected = change_evidence(world, owner='notes')
    if case != 'unregistered':
        registry = world.config / 'projects.toml'
        registry.write_text(registry.read_text() + 'notes = ' + json.dumps(str(external)) + '\n')
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
    owners = {'lore': world.root, 'ops': world.ops}
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


@pytest.mark.parametrize('change', ['missing', 'unregistered', 'bad-path'])
def test_registry_errors_are_clear_validation_failures(world, change):
    registry = world.config / 'projects.toml'
    if change == 'missing': registry.unlink()
    elif change == 'unregistered': registry.write_text('[projects]\n')
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
    env = {**world.env, 'PATH': str(world.root / 'bin') + os.pathsep + os.environ['PATH']}
    env.pop('LORE_ASSEMBLY_OPS_ROOT', None)
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
