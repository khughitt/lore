"""Parse and validate a selection context: facts with sources or reasons, held and withheld duties."""
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from ._errors import ContextError
from ._vocabulary import DUTIES, FACTS, value_problem


@dataclass(frozen=True)
class Fact:
    value: object | None      # None means unknown
    source: str | None
    reason: str | None


@dataclass(frozen=True)
class Context:
    name: str
    facts: Mapping[str, Fact]
    held: frozenset[str]
    withheld: Mapping[str, str]    # duty -> the launcher's words and where they are


NOT_SUPPLIED = Fact(None, None, 'not supplied')


def load_context(data):
    """A Context from its JSON document; every departure from the schema is a ContextError."""
    if not isinstance(data, dict):
        raise ContextError('a selection context is a JSON object')
    _keys(data, {'schema', 'name', 'assembled', 'facts', 'duties'}, 'context')
    if data.get('schema') != 1:
        raise ContextError(f'context schema {data.get("schema")!r} is not 1')
    name = data.get('name')
    if not isinstance(name, str) or not name:
        raise ContextError('context name must be a nonempty string')
    facts = {}
    raw_facts = data.get('facts', {})
    if not isinstance(raw_facts, dict):
        raise ContextError('context facts must be an object')
    for fact_name, raw in raw_facts.items():
        if fact_name not in FACTS:
            raise ContextError(f'unknown fact {fact_name!r}')
        facts[fact_name] = _fact(fact_name, raw)
    held, withheld = _duties(data.get('duties', {}))
    return Context(name, MappingProxyType(facts), held, MappingProxyType(withheld))


def fact(context, name):
    return context.facts.get(name, NOT_SUPPLIED)


def duty(context, name):
    """True held, False withheld, None unknown."""
    if name in context.held:
        return True
    if name in context.withheld:
        return False
    return None


def _fact(name, raw):
    if not isinstance(raw, dict) or 'value' not in raw:
        raise ContextError(f'fact {name} must be an object with a value')
    _keys(raw, {'value', 'source', 'reason'}, f'fact {name}')
    value = raw['value']
    if value is None:
        reason = raw.get('reason')
        if not isinstance(reason, str) or not reason:
            raise ContextError(f'fact {name} is unknown without a reason')
        if 'source' in raw:
            raise ContextError(f'fact {name} is unknown and also names a source')
        return Fact(None, None, reason)
    source = raw.get('source')
    if not isinstance(source, str) or not source:
        raise ContextError(f'fact {name} has a value without a source')
    if 'reason' in raw:
        raise ContextError(f'fact {name} has a value and also a reason')
    problem = value_problem(name, value)
    if problem:
        raise ContextError(problem)
    return Fact(tuple(value) if isinstance(value, list) else value, source, None)


def _duties(raw):
    if not isinstance(raw, dict):
        raise ContextError('context duties must be an object')
    _keys(raw, {'held', 'withheld'}, 'duties')
    held_list = raw.get('held', [])
    if not isinstance(held_list, list):
        raise ContextError('duties.held must be a list')
    for name in held_list:
        _duty_name(name)
    withheld = {}
    withheld_list = raw.get('withheld', [])
    if not isinstance(withheld_list, list):
        raise ContextError('duties.withheld must be a list')
    for item in withheld_list:
        if not isinstance(item, dict):
            raise ContextError('each withheld duty is an object with duty and source')
        _keys(item, {'duty', 'source'}, 'withheld duty')
        name = _duty_name(item.get('duty'))
        source = item.get('source')
        if not isinstance(source, str) or not source:
            raise ContextError(f'withheld duty {name} has no source quoting the launcher')
        withheld[name] = source
    both = set(held_list) & set(withheld)
    if both:
        raise ContextError(f'duty {", ".join(sorted(both))} is both held and withheld')
    return frozenset(held_list), withheld


def _duty_name(name):
    if name not in DUTIES:
        raise ContextError(f'unknown duty {name!r}')
    return name


def _keys(obj, allowed, where):
    extra = set(obj) - allowed
    if extra:
        raise ContextError(f'{where} has unknown key {", ".join(sorted(map(str, extra)))}')
