"""Applicability entries: grammar, review digests, review state and the checks."""
import pytest

from lore.context import ContextError
from lore.context._applicability import (
    Alternative, Test, parse, problems, required_by, stale, state, with_reviewed)

from .conftest import A, AH, B, BH, C, CH

RULES = {A: 'ha', B: 'hb'}

TOML_A_ZSH = f'''[rule.{AH}]
when = [{{ fact = "actor.shell", in = ["zsh"] }}]
rule_sha256 = "ha"
'''

TOML_A_REQUIRES_B = f'''[rule.{AH}]
governs = ["commit"]
requires = ["{B}"]
rule_sha256 = "ha"

[rule.{BH}]
when = [{{ fact = "actor.interactive", eq = true }}]
rule_sha256 = "hb"
'''


def reviewed_text(text, ids):
    return with_reviewed(text, parse(text.encode()), RULES, ids)


TOML_A_REQUIRES_B_BOTH_REVIEWED = reviewed_text(TOML_A_REQUIRES_B, [A, B])


def test_editing_only_a_predicate_returns_reviewed_entry_to_proposed():
    text = with_reviewed(TOML_A_ZSH, parse(TOML_A_ZSH.encode()), RULES, [A])
    assert state(parse(text.encode())[A], 'ha', ()) == 'reviewed'
    edited = text.replace('"zsh"', '"zsh", "bash"')
    assert state(parse(edited.encode())[A], 'ha', ()) == 'proposed'


def test_removing_a_requirement_returns_the_required_rule_to_proposed():
    entries = parse(TOML_A_REQUIRES_B_BOTH_REVIEWED.encode())
    assert state(entries[B], 'hb', required_by(entries)[B]) == 'reviewed'
    without = parse(TOML_A_REQUIRES_B_BOTH_REVIEWED.replace(f'requires = ["{B}"]\n', '').encode())
    assert state(without[B], 'hb', required_by(without).get(B, ())) == 'proposed'


def test_adding_a_requirement_returns_the_required_rule_to_proposed():
    text = reviewed_text(TOML_A_ZSH + f'\n[rule.{BH}]\ngoverns = ["commit"]\nrule_sha256 = "hb"\n', [B])
    entries = parse(text.encode())
    assert state(entries[B], 'hb', required_by(entries).get(B, ())) == 'reviewed'
    added = parse(text.replace('in = ["zsh"] }]\n', f'in = ["zsh"] }}]\nrequires = ["{B}"]\n').encode())
    assert state(added[B], 'hb', required_by(added).get(B, ())) == 'proposed'


def test_changed_rule_text_makes_entry_stale():
    entries = parse(TOML_A_ZSH.encode())
    assert state(entries[A], 'other', ()) == 'stale'
    assert stale(entries, {A: 'other'}) and stale(entries, {A: 'other'})[0].startswith(A)
    assert problems(entries, {A: 'other'}) == []


def check(text, rules=None):
    return problems(parse(text.encode()), rules or {A: 'ha', B: 'hb', C: 'hc'})


def test_problems_reject_lead_in_with_tests():
    found = check(f'[rule.{AH}]\naccompanies = ["{B}"]\ngoverns = ["commit"]\nrule_sha256 = "ha"\n')
    assert any('accompanies together with tests' in p for p in found)


def test_problems_reject_lead_in_listing_a_lead_in():
    found = check(f'[rule.{AH}]\naccompanies = ["{B}"]\nrule_sha256 = "ha"\n'
                  f'[rule.{BH}]\naccompanies = ["{C}"]\nrule_sha256 = "hb"\n')
    assert any(p.startswith(A) and 'itself a lead-in' in p for p in found)


def test_problems_reject_mixing_top_level_tests_with_any():
    found = check(f'[rule.{AH}]\ngoverns = ["commit"]\nany = [{{ governs = ["spend"] }}]\nrule_sha256 = "ha"\n')
    assert any('mixes' in p for p in found)


def test_problems_reject_eq_on_list_fact():
    found = check(f'[rule.{AH}]\nwhen = [{{ fact = "target.profile", eq = "personal" }}]\nrule_sha256 = "ha"\n')
    assert any('eq on list fact' in p for p in found)


def test_problems_reject_unknown_duty_fact_and_moment():
    found = check(f'[rule.{AH}]\ngoverns = ["fly"]\nwhen = [{{ fact = "actor.mood", eq = "x" }}]\n'
                  f'by = "lunch"\nrule_sha256 = "ha"\n')
    assert any("'fly'" in p for p in found) and any("'actor.mood'" in p for p in found)
    assert any("'lunch'" in p for p in found)


def test_problems_reject_value_outside_fact_values_and_in_without_list():
    found = check(f'[rule.{AH}]\nwhen = [{{ fact = "actor.shell", in = ["fish"] }}, '
                  f'{{ fact = "actor.role", in = "worker" }}]\nrule_sha256 = "ha"\n')
    assert any("'fish'" in p for p in found) and any('takes a list' in p for p in found)


def test_problems_reject_requires_cycle_and_dead_rule():
    found = check(f'[rule.{AH}]\nrequires = ["{B}"]\nrule_sha256 = "ha"\n'
                  f'[rule.{BH}]\nrequires = ["{A}"]\nrule_sha256 = "hb"\n'
                  f'[rule.{CH}]\nrequires = ["rule:{"d" * 32}"]\nrule_sha256 = "hc"\n')
    assert any('requires cycle' in p for p in found)
    assert any(p.startswith(C) and 'not a live rule' in p for p in found)
    assert any('not a live rule in the manifest' in p for p in check(f'[rule.{"e" * 32}]\nrule_sha256 = "x"\n'))


def test_problems_reject_missing_rule_sha256():
    assert any('no rule_sha256' in p for p in check(f'[rule.{AH}]\ngoverns = ["commit"]\n'))


def test_parse_reads_any_alternatives():
    entry = parse(f'''[rule.{AH}]
any = [
  {{ when = [{{ fact = "actor.role", in = ["reviewer"] }}] }},
  {{ governs = ["run-reviews"] }},
]
rule_sha256 = "ha"
'''.encode())[A]
    assert entry.alternatives == (Alternative((Test('actor.role', 'in', ('reviewer',)),), ()),
                                  Alternative((), ('run-reviews',)))


def test_parse_names_the_table_key_on_a_structural_error():
    with pytest.raises(ContextError, match=f'rule.{AH}'):
        parse(f'[rule.{AH}]\nwhen = [{{ fact = "actor.shell" }}]\n'.encode())


def test_with_reviewed_refuses_stale_entry():
    with pytest.raises(ContextError, match='stale'):
        with_reviewed(TOML_A_ZSH, parse(TOML_A_ZSH.encode()), {A: 'other'}, [A])


def test_with_reviewed_refuses_a_file_with_problems():
    text = TOML_A_ZSH + f'\n[rule.{BH}]\ngoverns = ["fly"]\nrule_sha256 = "hb"\n'
    with pytest.raises(ContextError, match='problems'):
        with_reviewed(text, parse(text.encode()), RULES, [A])


def test_with_reviewed_keeps_comments_and_multi_line_arrays_and_leaves_other_entries_equal():
    old = f'''[rule.{AH}]  # a rule
any = [
  {{ when = [{{ fact = "actor.role", in = ["reviewer"] }}] }},
  {{ governs = ["run-reviews"] }},
]
rule_sha256 = "ha"

# section
[rule.{BH}]
governs = ["commit"]
rule_sha256 = "hb"
'''
    new = with_reviewed(old, parse(old.encode()), RULES, [A])
    lines = new.splitlines()
    assert lines[0] == f'[rule.{AH}]  # a rule' and lines[1].startswith('reviewed = "')
    assert lines[lines.index(f'[rule.{BH}]') - 1] == '# section'
    assert parse(new.encode())[B] == parse(old.encode())[B]
    assert state(parse(new.encode())[A], 'ha', ()) == 'reviewed'


def test_with_reviewed_replaces_an_earlier_digest():
    once = with_reviewed(TOML_A_ZSH, parse(TOML_A_ZSH.encode()), RULES, [A])
    edited = once.replace('"zsh"', '"zsh", "bash"')
    twice = with_reviewed(edited, parse(edited.encode()), RULES, [A])
    assert twice.count('reviewed =') == 1
    assert state(parse(twice.encode())[A], 'ha', ()) == 'reviewed'


def test_with_reviewed_refuses_a_rule_without_an_entry():
    with pytest.raises(ContextError, match='no entry'):
        with_reviewed(TOML_A_ZSH, parse(TOML_A_ZSH.encode()), RULES, [B])


def test_problems_reject_empty_name_on_an_unconstrained_scalar_fact():
    found = check(f'[rule.{AH}]\nwhen = [{{ fact = "actor.model", eq = "" }}, '
                  f'{{ fact = "target.project", in = ["lore", ""] }}]\nrule_sha256 = "ha"\n')
    assert any('actor.model' in p and "''" in p for p in found)
    assert any('target.project' in p and "''" in p for p in found)
