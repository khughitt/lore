"""Selection: unknown includes, tests, governs, closure, review state and lead-ins."""
from unittest.mock import ANY

from lore.context._applicability import Alternative, Entry, Test, digest, required_by
from lore.context._corpus import Rule
from lore.context._facts import load_context
from lore.context._selection import Decision, decide

from .conftest import A, B, C

L = 'rule:' + 'd' * 32
RA, RB, RC, RL = (Rule(r, 'h' + r[-1], i * 10, 10, 'f') for i, r in enumerate((A, B, C, L)))


def entry(rule, when=(), governs=(), any=(), accompanies=(), requires=(), reviewed=True, sha=None):
    alternatives = tuple(any) or ((Alternative(tuple(when), tuple(governs)),) if when or governs else ())
    return Entry(rule, alternatives, tuple(accompanies), tuple(requires), None, None,
                 sha or 'h' + rule[-1], 'pending' if reviewed else None)


def finish(*entries):
    """Fill valid `reviewed` digests for entries marked reviewed, against the final requires graph."""
    incoming = required_by({e.rule: e for e in entries})
    out = {}
    for e in entries:
        if e.reviewed == 'pending':
            e = Entry(**{**e.__dict__, 'reviewed': None})
            e = Entry(**{**e.__dict__, 'reviewed': digest(e, incoming.get(e.rule, ()))})
        out[e.rule] = e
    return out


def context(facts=None, held=(), withheld=()):
    return load_context({'schema': 1, 'name': 't',
                         'facts': {k: {'value': v, 'source': 's'} for k, v in (facts or {}).items()},
                         'duties': {'held': list(held), 'withheld': [{'duty': d, 'source': 'q'} for d in withheld]}})


def by_rule(decisions):
    return {d.rule: d for d in decisions}


SHELL_ZSH = Test('actor.shell', 'in', ('zsh',))


def test_empty_context_includes_everything():
    entries = finish(entry(A, when=[SHELL_ZSH]), entry(B, governs=['commit']), entry(C))
    decisions = decide([RA, RB, RC], entries, context(), shadow=False)
    assert all(d.include for d in decisions)
    assert [d.reason for d in decisions] == ['unknown-fact', 'unknown-fact', 'no-tests']


def test_unknown_test_beside_false_test_keeps_the_rule():
    e = entry(A, when=[SHELL_ZSH, Test('actor.harness', 'in', ('codex',))])
    ctx = context(facts={'actor.harness': 'pi'})
    assert decide([RA], finish(e), ctx, shadow=False)[0] == Decision(A, True, 'unknown-fact', ANY, ANY)


def test_known_false_test_omits():
    d = decide([RA], finish(entry(A, when=[SHELL_ZSH])), context({'actor.shell': 'bash'}), shadow=False)[0]
    assert (d.include, d.reason, d.detail['facts']) == (False, 'test-false', {'actor.shell': 'bash'})


def test_governs_holds_when_any_duty_held():
    e = finish(entry(A, governs=['commit', 'integrate']))
    d = decide([RA], e, context(held=['commit'], withheld=['integrate']), shadow=False)[0]
    assert (d.include, d.reason) == (True, 'entry-holds')


def test_governs_with_one_withheld_and_one_unlisted_duty_keeps_the_rule():
    e = finish(entry(A, governs=['commit', 'integrate']))
    d = decide([RA], e, context(withheld=['integrate']), shadow=False)[0]
    assert (d.include, d.reason, d.detail['unknown']) == (True, 'unknown-fact', ['commit'])


def test_withheld_duty_omits():
    d = decide([RA], finish(entry(A, governs=['ask-user'])), context(withheld=['ask-user']), shadow=False)[0]
    assert (d.include, d.reason) == (False, 'test-false')


def test_any_alternative_holds_for_reviewer_role_or_review_runner():
    e = finish(entry(A, any=[Alternative((Test('actor.role', 'in', ('reviewer',)),), ()),
                             Alternative((), ('run-reviews',))]))
    reviewer = context({'actor.role': 'reviewer'}, withheld=['run-reviews'])
    runner = context({'actor.role': 'root'}, held=['run-reviews'])
    worker = context({'actor.role': 'worker'}, withheld=['run-reviews'])
    assert [decide([RA], e, c, shadow=False)[0].include for c in (reviewer, runner, worker)] == [True, True, False]


def test_in_on_list_fact_matches_any_element():
    e = finish(entry(A, when=[Test('target.profile', 'in', ('work',))]))
    assert decide([RA], e, context({'target.profile': ['personal', 'work']}), shadow=False)[0].include
    assert not decide([RA], e, context({'target.profile': ['personal']}), shadow=False)[0].include
    n = finish(entry(A, when=[Test('target.profile', 'not_in', ('work',))]))
    assert not decide([RA], n, context({'target.profile': ['personal', 'work']}), shadow=False)[0].include


def test_closure_restores_rule_its_own_entry_omitted():
    entries = finish(entry(A, requires=[B]), entry(B, when=[SHELL_ZSH]))
    d = by_rule(decide([RA, RB], entries, context({'actor.shell': 'bash'}), shadow=False))
    assert (d[B].include, d[B].reason, d[B].detail['by']) == (True, 'required-by', [A])


def test_proposed_entry_requires_is_honoured_in_live_mode():
    entries = finish(entry(A, requires=[B], reviewed=False), entry(B, when=[SHELL_ZSH]))
    d = by_rule(decide([RA, RB], entries, context({'actor.shell': 'bash'}), shadow=False))
    assert (d[A].reason, d[B].include, d[B].reason) == ('proposed', True, 'required-by')


def test_deleting_approved_requirement_keeps_required_rule_in_live_mode():
    entries = finish(entry(A, governs=['commit'], requires=[B]), entry(B, when=[SHELL_ZSH]))
    edited = dict(entries)
    edited[A] = Entry(**{**entries[A].__dict__, 'requires': ()})        # reviewed digests untouched
    d = by_rule(decide([RA, RB], edited, context({'actor.shell': 'bash'}, held=['commit']), shadow=False))
    assert (d[A].reason, d[B].include, d[B].reason) == ('proposed', True, 'proposed')


def test_stale_entry_omits_nothing_even_in_shadow():
    e = finish(entry(A, when=[SHELL_ZSH], sha='old'))
    for shadow in (False, True):
        d = decide([RA], e, context({'actor.shell': 'bash'}), shadow=shadow)[0]
        assert (d.include, d.reason) == (True, 'stale')


def test_proposed_entry_omits_only_in_shadow():
    e = finish(entry(A, when=[SHELL_ZSH], reviewed=False))
    ctx = context({'actor.shell': 'bash'})
    assert decide([RA], e, ctx, shadow=False)[0].reason == 'proposed'
    assert decide([RA], e, ctx, shadow=True)[0] == Decision(A, False, 'test-false', ANY, 10)


def lead_in_world(*extra):
    return finish(entry(A, when=[SHELL_ZSH]), entry(B, when=[Test('actor.role', 'in', ('reviewer',))]),
                  entry(L, accompanies=[A, B]), *extra)


def test_lead_in_dropped_when_all_companions_omitted():
    d = by_rule(decide([RL, RA, RB], lead_in_world(), context({'actor.shell': 'bash', 'actor.role': 'worker'}),
                       shadow=False))
    assert (d[L].include, d[L].reason) == (False, 'no-companion')


def test_lead_in_kept_when_a_companion_is_kept_by_an_unknown_fact():
    d = by_rule(decide([RL, RA, RB], lead_in_world(), context({'actor.role': 'worker'}), shadow=False))
    assert (d[A].reason, d[L].include, d[L].reason) == ('unknown-fact', True, 'entry-holds')


def test_lead_in_kept_when_required_by_an_included_rule():
    world = finish(entry(A, when=[SHELL_ZSH]), entry(B, when=[Test('actor.role', 'in', ('reviewer',))]),
                   entry(L, accompanies=[A, B]), entry(C, requires=[L]))
    d = by_rule(decide([RL, RA, RB, RC], world, context({'actor.shell': 'bash', 'actor.role': 'worker'}),
                       shadow=False))
    assert d[L].include and d[L].detail['by'] == [C]


def test_kept_lead_in_brings_its_own_requirement():
    world = finish(entry(A, when=[SHELL_ZSH]), entry(B, when=[Test('actor.role', 'in', ('reviewer',))]),
                   entry(L, accompanies=[A], requires=[B]))
    d = by_rule(decide([RL, RA, RB], world, context({'actor.shell': 'zsh', 'actor.role': 'worker'}), shadow=False))
    assert d[A].include and d[L].include
    assert (d[B].include, d[B].reason, d[B].detail['by']) == (True, 'required-by', [L])


def test_rule_required_only_by_a_pruned_lead_in_stays():
    world = finish(entry(A, when=[SHELL_ZSH]), entry(B, when=[Test('actor.role', 'in', ('reviewer',))]),
                   entry(L, accompanies=[A], requires=[B]))
    d = by_rule(decide([RL, RA, RB], world, context({'actor.shell': 'bash', 'actor.role': 'worker'}), shadow=False))
    assert (d[A].include, d[L].include, d[L].reason) == (False, False, 'no-companion')
    assert (d[B].include, d[B].reason) == (True, 'required-by')
