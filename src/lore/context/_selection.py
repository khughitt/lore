"""Decide, per rule, include or omit from entries and a context: tests, closure, then lead-ins."""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from ._applicability import required_by, state
from ._facts import duty, fact
from ._vocabulary import FACTS


@dataclass(frozen=True)
class Decision:
    rule: str
    include: bool
    reason: str      # no-entry | stale | proposed | unknown-fact | entry-holds | no-tests
                     # | required-by | test-false | no-companion
    detail: dict = field(compare=True)
    length: int = 0


def decide(rules, entries, context, *, shadow):
    """One Decision per rule, in artifact order (spec section 6)."""
    incoming = required_by(entries)
    first = {}
    for rule in rules:
        entry = entries.get(rule.id)
        if entry is None:
            first[rule.id] = (True, 'no-entry', {})
            continue
        review = state(entry, rule.sha256, incoming.get(rule.id, ()))
        if review == 'stale':
            first[rule.id] = (True, 'stale', {})
        elif review == 'proposed' and not shadow:
            first[rule.id] = (True, 'proposed', {})
        elif entry.accompanies:
            first[rule.id] = (True, 'lead-in', {})          # provisional: pruned after closure
        elif not entry.alternatives:
            first[rule.id] = (True, 'no-tests', {})
        else:
            first[rule.id] = _evaluate(entry, context)
    # P: every included rule, lead-ins among them. C: P closed under requires from every entry.
    included = {rule for rule, (keep, _, _) in first.items() if keep}
    by = {}
    queue = sorted(included)
    while queue:
        source = queue.pop(0)
        entry = entries.get(source)
        for target in (entry.requires if entry else ()):
            if target not in first:
                continue
            if target not in included:
                included.add(target)
                queue.append(target)
            if not first[target][0]:
                by.setdefault(target, set()).add(source)
    # Pruning: a lead-in none of whose companions is in C and that nothing else in C requires.
    decisions = []
    for rule in rules:
        keep, reason, detail = first[rule.id]
        if rule.id in by:
            keep, reason, detail = True, 'required-by', {**detail, 'by': sorted(by[rule.id])}
        elif reason == 'lead-in':
            entry = entries[rule.id]
            companions = [c for c in entry.accompanies if c in included]
            requirers = [r for r in incoming.get(rule.id, ()) if r in included and r != rule.id]
            if companions or requirers:
                keep, reason = True, 'entry-holds'
                detail = {'companions': companions, 'by': requirers}
            else:
                keep, reason, detail = False, 'no-companion', {'companions': list(entry.accompanies)}
        decisions.append(Decision(rule.id, keep, reason, detail, rule.length))
    return tuple(decisions)


def _evaluate(entry, context):
    names = sorted({t.fact for alt in entry.alternatives for t in alt.when})
    duties = sorted({d for alt in entry.alternatives for d in alt.governs})
    facts = {name: fact(context, name).value for name in names}
    duty_values = {name: duty(context, name) for name in duties}
    unknown = [n for n in names if facts[n] is None] + [d for d in duties if duty_values[d] is None]
    detail = {'facts': {n: _plain(v) for n, v in facts.items()}, 'duties': duty_values}
    if unknown:
        return True, 'unknown-fact', {**detail, 'unknown': unknown}
    for alt in entry.alternatives:
        if all(_holds(t, facts[t.fact]) for t in alt.when) and \
                (not alt.governs or any(duty_values[d] for d in alt.governs)):
            return True, 'entry-holds', detail
    return False, 'test-false', detail


def _holds(test, value):
    if FACTS[test.fact][0] == 'list':
        members = set(value)
        hit = bool(members & set(test.value))
        return hit if test.op == 'in' else not hit
    if test.op == 'eq':
        return value == test.value and type(value) is type(test.value)
    hit = value in test.value
    return hit if test.op == 'in' else not hit


def _plain(value):
    return list(value) if isinstance(value, tuple) else value
