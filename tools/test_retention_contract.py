"""Shared wire examples catch invalid v1 records accepted as historical subsets."""
import importlib.machinery
import importlib.util
import json
import re
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / 'tools/fixtures/retention-contract/cases.json').read_text())


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate key: {key}')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f'non-JSON constant: {value}')


@pytest.fixture(scope='module', params=['fullmatch', 'search'])
def validate(request):
    loader = importlib.machinery.SourceFileLoader('retention_assembly', str(ROOT / 'bin/assemble-instructions'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    previous, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    if request.param == "search":
        # JSON Schema patterns search; the assembler supplies fullmatch by default.
        module.re = SimpleNamespace(fullmatch=re.search)
    return module.validate_schema


@pytest.mark.parametrize('case', CASES, ids=lambda case: case['name'])
def test_retention_v1_structure(case, validate):
    path = ROOT / f"skills/references/retention-v1-{case['kind']}.schema.json"
    assert path.is_file(), f'missing v1 schema: {path.name}'
    schema = json.loads(path.read_text())
    try:
        value = json.loads(case['raw'], object_pairs_hook=strict_object,
                           parse_constant=reject_constant)
        validate(value, schema, case['name'])
        valid = True
    except ValueError:
        valid = False
    assert valid == case['structural_valid']


@pytest.mark.parametrize('kind,selector,good,bad', [
    ('record', 'digest', 'a' * 64, ['x' + 'a' * 64, 'a' * 64 + 'x', 'a' * 64 + '\n']),
    ('record', 'owner', 'task:lore-a8b553', ['!task:lore-a8b553', 'task:lore-a8b553!', 'task:lore-a8b553\n']),
    ('record', 'location', '/tmp/item', ['relative/tmp/item', '/tmp/item\n', '/tmp/item\x00']),
    ('record', 'trigger', 'after review', ['none', 'after review\n', 'after\x00review']),
    ('record', 'worktree-path', '.worktrees/item', ['bad.worktrees/item', '.worktrees/item\n']),
    ('manifest', 'member-path', 'dir/file', ['../dir/file', '/dir/file', 'dir/file/', 'dir/file\n']),
])
def test_exported_patterns_bound_the_whole_value(kind, selector, good, bad):
    schema = json.loads((ROOT / f'skills/references/retention-v1-{kind}.schema.json').read_text())
    if selector == 'worktree-path':
        pattern = schema['anyOf'][0]['properties']['path']['pattern']
    elif selector == 'member-path':
        pattern = schema['properties']['entries']['items']['anyOf'][0]['properties']['path']['pattern']
    else:
        pattern = schema['$defs'][selector]['pattern']
    assert re.search(pattern, good)
    # A bare dollar anchor can match before a final newline; reject that suffix too.
    for value in bad:
        assert re.search(pattern, value) is None, repr(value)
