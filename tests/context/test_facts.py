"""The selection context: vocabulary, facts with sources or reasons, and duties."""
import json

import pytest

from lore.context import ContextError
from lore.context._facts import Fact, duty, fact, load_context
from lore.context._vocabulary import DUTIES, FACTS

from .conftest import ROOT


def ctx(**facts):
    return {'schema': 1, 'name': 'x', 'facts': facts}


def test_empty_context_has_every_fact_and_duty_unknown():
    c = load_context({'schema': 1, 'name': 'empty'})
    assert fact(c, 'actor.shell').value is None and duty(c, 'ask-user') is None


def test_context_rejects_fact_outside_vocabulary():
    with pytest.raises(ContextError, match='actor.mood'):
        load_context(ctx(**{'actor.mood': {'value': 'fine', 'source': 's'}}))


def test_known_false_is_a_known_value_not_unknown():
    c = load_context(ctx(**{'actor.interactive': {'value': False, 'source': 'launcher'}}))
    assert fact(c, 'actor.interactive') == Fact(False, 'launcher', None)
    assert fact(c, 'actor.interactive').value is not None


def test_context_rejects_value_outside_fact_values():
    with pytest.raises(ContextError, match='fish'):
        load_context(ctx(**{'actor.shell': {'value': 'fish', 'source': 's'}}))


def test_context_rejects_known_value_without_source():
    with pytest.raises(ContextError, match='without a source'):
        load_context(ctx(**{'actor.shell': {'value': 'zsh'}}))


def test_context_rejects_unknown_without_reason():
    with pytest.raises(ContextError, match='without a reason'):
        load_context(ctx(**{'actor.shell': {'value': None}}))


def test_context_rejects_wrong_type():
    with pytest.raises(ContextError, match='true or false'):
        load_context(ctx(**{'actor.interactive': {'value': 'yes', 'source': 's'}}))
    with pytest.raises(ContextError, match='list'):
        load_context(ctx(**{'target.profile': {'value': 'personal', 'source': 's'}}))


def test_context_rejects_duty_in_both_lists():
    with pytest.raises(ContextError, match='both held and withheld'):
        load_context({'schema': 1, 'name': 'x', 'duties': {
            'held': ['commit'], 'withheld': [{'duty': 'commit', 'source': 'brief: "never commit"'}]}})


def test_context_rejects_withheld_duty_without_source():
    with pytest.raises(ContextError, match='no source'):
        load_context({'schema': 1, 'name': 'x', 'duties': {'withheld': [{'duty': 'commit'}]}})


def test_list_fact_and_duties_load():
    c = load_context({'schema': 1, 'name': 'x', 'facts': {'target.profile': {'value': ['personal'], 'source': 's'}},
                      'duties': {'held': ['commit'], 'withheld': [{'duty': 'spend', 'source': 'q'}]}})
    assert fact(c, 'target.profile').value == ('personal',)
    assert (duty(c, 'commit'), duty(c, 'spend'), duty(c, 'desktop')) == (True, False, None)


def test_schema_file_enumerates_the_vocabulary():
    schema = json.loads((ROOT / 'instructions/selection-context.json').read_text())
    assert set(schema['properties']['facts']['properties']) == set(FACTS)
    assert set(schema['$defs']['duty']['enum']) == DUTIES


def test_context_rejects_boolean_schema():
    with pytest.raises(ContextError, match='schema True is not 1'):
        load_context({'schema': True, 'name': 'x'})


@pytest.mark.parametrize('assembled', ['now', {'by': ''}, {'by': 'x', 'when': 'y'}, {'at': 3}])
def test_context_rejects_malformed_assembled(assembled):
    with pytest.raises(ContextError, match='assembled'):
        load_context({'schema': 1, 'name': 'x', 'assembled': assembled})


def test_context_accepts_assembled_by_and_at():
    load_context({'schema': 1, 'name': 'x', 'assembled': {'by': 'band', 'at': '2026-11-26T00:00:00Z'}})


def test_context_rejects_duplicate_held_or_withheld_duty():
    with pytest.raises(ContextError, match='commit is listed twice'):
        load_context({'schema': 1, 'name': 'x', 'duties': {'held': ['commit', 'commit']}})
    with pytest.raises(ContextError, match='commit is listed twice'):
        load_context({'schema': 1, 'name': 'x', 'duties': {'withheld': [
            {'duty': 'commit', 'source': 'a'}, {'duty': 'commit', 'source': 'b'}]}})
