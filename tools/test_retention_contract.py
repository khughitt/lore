"""Shared wire examples catch invalid v1 records accepted as historical subsets."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys

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


@pytest.fixture(scope='module')
def validate():
    loader = importlib.machinery.SourceFileLoader('retention_assembly', str(ROOT / 'bin/assemble-instructions'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    previous, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
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
