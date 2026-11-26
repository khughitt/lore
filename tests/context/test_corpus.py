"""The corpus reader: verified artifact, manifest and applicability from disk or the index."""
import hashlib
import json

import pytest

from lore.context import ContextError
from lore.context._corpus import APPLICABILITY, ARTIFACT, MANIFEST, load

from .conftest import A, AH, BH, ROOT, build, git, git_repo, write_tree


def test_load_reads_real_artifact_and_all_rule_ranges_hash():
    corpus = load(ROOT, 'working')
    manifest = json.loads((ROOT / MANIFEST).read_bytes())
    expected = [r['id'] for f in manifest['fragments'] for r in f.get('rules', [])]
    assert expected and [r.id for r in corpus.rules] == expected
    for rule in corpus.rules:
        assert hashlib.sha256(corpus.artifact[rule.offset:rule.offset + rule.length]).hexdigest() == rule.sha256
    assert len(corpus.generated) == sum('generated' in f for f in manifest['fragments']) >= 1
    assert corpus.applicability is None or isinstance(corpus.applicability, bytes)


def test_load_refuses_artifact_that_does_not_match_manifest(tmp_path):
    artifact, manifest = build([('rule', AH, '- one\n')])
    root = write_tree(tmp_path, artifact + b'x\n', manifest)
    with pytest.raises(ContextError, match='does not match the manifest'):
        load(root, 'working')


def test_load_refuses_rule_range_inside_a_line(tmp_path):
    artifact, manifest = build([('text', '## H\n'), ('rule', AH, '- one\n')])
    rule = manifest['fragments'][0]['rules'][0]
    rule['offset'] += 1
    rule['length'] -= 1
    rule['sha256'] = hashlib.sha256(artifact[rule['offset']:rule['offset'] + rule['length']]).hexdigest()
    with pytest.raises(ContextError, match='line boundary'):
        load(write_tree(tmp_path, artifact, manifest), 'working')


def test_load_refuses_rule_whose_bytes_do_not_hash(tmp_path):
    artifact, manifest = build([('rule', AH, '- one\n')])
    manifest['fragments'][0]['rules'][0]['sha256'] = '0' * 64
    with pytest.raises(ContextError, match=A):
        load(write_tree(tmp_path, artifact, manifest), 'working')


def test_load_refuses_manifest_version_other_than_2(tmp_path):
    artifact, manifest = build([('rule', AH, '- one\n')])
    manifest['version'] = 3
    with pytest.raises(ContextError, match='version'):
        load(write_tree(tmp_path, artifact, manifest), 'working')


def test_index_view_treats_unindexed_applicability_as_absent(tmp_path):
    artifact, manifest = build([('rule', AH, '- one\n')])
    root = git_repo(tmp_path, artifact, manifest)
    (root / APPLICABILITY).write_text('not even toml [')
    assert load(root, 'index').applicability is None
    assert load(root, 'working').applicability == b'not even toml ['


def test_index_view_refuses_artifact_missing_from_the_index(tmp_path):
    artifact, manifest = build([('rule', AH, '- one\n')])
    root = git_repo(tmp_path, artifact, manifest)
    git(root, 'rm', '-q', '--cached', ARTIFACT)
    with pytest.raises(ContextError, match=ARTIFACT):
        load(root, 'index')


def test_auto_view_reads_the_index_when_an_input_is_staged(tmp_path):
    artifact, manifest = build([('rule', AH, '- one\n')])
    root = git_repo(tmp_path, artifact, manifest)
    (root / APPLICABILITY).write_text('# staged\n')
    git(root, 'add', APPLICABILITY)
    (root / APPLICABILITY).write_text('# working copy\n')
    assert load(root).applicability == b'# staged\n'
    git(root, 'commit', '-qm', 'policy')
    assert load(root).applicability == b'# working copy\n'


def test_git_calls_on_another_repository_ignore_a_hook_environment(tmp_path, monkeypatch):
    artifact, manifest = build([('rule', AH, '- one\n')])
    root = git_repo(tmp_path / 'target', artifact, manifest)
    other = git_repo(tmp_path / 'other', *build([('rule', BH, '- two\n')]))
    monkeypatch.setenv('GIT_DIR', str(other / '.git'))
    monkeypatch.setenv('GIT_INDEX_FILE', str(other / '.git' / 'index'))
    assert load(root, 'index').rules[0].id == A


@pytest.mark.parametrize('mutate', [
    lambda m: [m],
    lambda m: {**m, 'artifact': 'x'},
    lambda m: {**m, 'fragments': {}},
    lambda m: {**m, 'fragments': ['x']},
    lambda m: {**m, 'fragments': [{**m['fragments'][0], 'rules': [{'id': A}]}]},
    lambda m: {**m, 'fragments': [{**m['fragments'][0], 'rules': 'x'}]},
    lambda m: {**m, 'fragments': [{**m['fragments'][0],
                                   'rules': [{**m['fragments'][0]['rules'][0], 'offset': -1}]}]},
    lambda m: {**m, 'fragments': [{**m['fragments'][0],
                                   'rules': [{**m['fragments'][0]['rules'][0], 'offset': True}]}]},
    lambda m: {**m, 'fragments': [{**m['fragments'][0], 'generated': 'x', 'offset': '0'}]},
])
def test_load_refuses_malformed_manifest_shapes_with_a_context_error(tmp_path, mutate):
    artifact, manifest = build([('rule', AH, '- one\n')])
    with pytest.raises(ContextError, match='manifest'):
        load(write_tree(tmp_path, artifact, mutate(manifest)), 'working')
