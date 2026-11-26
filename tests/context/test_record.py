"""The selection record and the selector identity."""
import hashlib

from lore.context import select_text
from lore.context._record import selector_identity

from .conftest import ROOT, commit_all

EMPTY = {'schema': 1, 'name': 'empty'}


def test_record_has_exactly_the_schema_1_keys(repo):
    text, record = select_text(repo, EMPTY)
    assert set(record) == {'schema', 'mode', 'context', 'corpus', 'selector', 'replayable', 'rules', 'output',
                           'delivery'}
    assert (record['schema'], record['mode'], record['context'], record['delivery']) == (1, 'live', EMPTY, None)
    assert record['output'] == {'sha256': hashlib.sha256(text).hexdigest(), 'bytes': len(text),
                                'artifact_bytes': len(text)}
    assert [set(r) for r in record['rules']] == [{'id', 'decision', 'reason', 'detail', 'bytes'}] * 3


def test_selector_identity_digest_follows_the_package_source(repo):
    before = selector_identity(repo)
    assert before['clean'] and len(before['commit']) == 40
    (repo / 'src/lore/context/_errors.py').write_text('# changed\n', encoding='utf-8')
    after = selector_identity(repo)
    assert after['sha256'] != before['sha256'] and not after['clean']
    commit_all(repo, 'change')
    assert selector_identity(repo)['clean']


def test_selector_identity_without_git_has_no_commit(tmp_path):
    (tmp_path / 'src/lore/context').mkdir(parents=True)
    (tmp_path / 'src/lore/context/x.py').write_text('')
    identity = selector_identity(tmp_path)
    assert identity['commit'] is None and identity['clean'] is False


def test_real_selector_identity_digests_the_real_package():
    identity = selector_identity(ROOT)
    assert len(identity['sha256']) == 64
