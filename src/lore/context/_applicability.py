"""Applicability entries: parse, validate, digest, report review state and write `reviewed`."""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import re
import tomllib

from ._errors import ContextError
from ._vocabulary import DUTIES, FACTS, MOMENTS, OPERATORS

RULE_KEY = re.compile(r'[0-9a-f]{32}')
RULE_ID = re.compile(r'rule:[0-9a-f]{32}')
ENTRY_KEYS = {'when', 'governs', 'any', 'accompanies', 'requires', 'by', 'note', 'rule_sha256', 'reviewed'}


@dataclass(frozen=True)
class Test:
    __test__ = False          # not a pytest test class
    fact: str
    op: str
    value: object             # scalar for eq, tuple of scalars for in/not_in


@dataclass(frozen=True)
class Alternative:
    when: tuple[Test, ...]
    governs: tuple[str, ...]


@dataclass(frozen=True)
class Entry:
    rule: str
    alternatives: tuple[Alternative, ...]
    accompanies: tuple[str, ...]
    requires: tuple[str, ...]
    by: str | None
    note: str | None
    rule_sha256: str | None
    reviewed: str | None
    mixed: bool = False       # top-level when/governs together with any; a check failure


def parse(data):
    """Entries by rule id; None (no file) is no entries. Structural errors name the table key."""
    if data is None:
        return {}
    try:
        document = tomllib.loads(data.decode('utf-8') if isinstance(data, bytes) else data)
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise ContextError(f'applicability.toml does not parse: {error}') from None
    unknown_top = set(document) - {'rule'}
    if unknown_top:
        raise ContextError(f'applicability.toml has unknown top-level key {", ".join(sorted(unknown_top))}')
    tables = document.get('rule', {})
    if not isinstance(tables, dict):
        raise ContextError('applicability.toml: rule must be a table of [rule.<32 hex>] tables')
    entries = {}
    for key, table in tables.items():
        where = f'[rule.{key}]'
        if not RULE_KEY.fullmatch(key) or not isinstance(table, dict):
            raise ContextError(f'{where}: a table key is 32 lowercase hex digits naming a rule')
        rule = 'rule:' + key
        extra = set(table) - ENTRY_KEYS
        if extra:
            raise ContextError(f'{where}: unknown key {", ".join(sorted(extra))}')
        top = None
        if 'when' in table or 'governs' in table:
            top = _alternative(table, where)
        alternatives = []
        if 'any' in table:
            if not isinstance(table['any'], list) or not table['any']:
                raise ContextError(f'{where}: any must be a nonempty list of tables')
            alternatives = [_alternative(item, f'{where} any[{i}]') for i, item in enumerate(table['any'])]
        if top is not None:
            alternatives.insert(0, top)
        entries[rule] = Entry(
            rule=rule, alternatives=tuple(alternatives),
            accompanies=_ids(table, 'accompanies', where), requires=_ids(table, 'requires', where),
            by=_text(table, 'by', where), note=_text(table, 'note', where),
            rule_sha256=_text(table, 'rule_sha256', where), reviewed=_text(table, 'reviewed', where),
            mixed=top is not None and 'any' in table)
    return entries


def required_by(entries):
    """rule -> sorted rules whose entries require it."""
    result = {}
    for entry in entries.values():
        for target in entry.requires:
            result.setdefault(target, set()).add(entry.rule)
    return {rule: tuple(sorted(sources)) for rule, sources in result.items()}


def digest(entry, required_by):
    obj = {
        'rule': entry.rule,
        'alternatives': [{'when': [{'fact': t.fact, 'op': t.op, 'value': list(t.value) if isinstance(t.value, tuple)
                                    else t.value} for t in alt.when],
                          'governs': sorted(alt.governs)} for alt in entry.alternatives],
        'accompanies': sorted(entry.accompanies),
        'requires': sorted(entry.requires),
        'by': entry.by,
        'note': entry.note,
        'rule_sha256': entry.rule_sha256,
        'required_by': sorted(required_by),
    }
    canonical = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return hashlib.sha256(canonical).hexdigest()


def state(entry, rule_sha256, required_by):
    if entry.rule_sha256 != rule_sha256:
        return 'stale'
    return 'reviewed' if entry.reviewed == digest(entry, required_by) else 'proposed'


def problems(entries, rules):
    """Check failures, one line each starting with the rule id; rules: live id -> manifest sha256."""
    out = []
    for rule, entry in entries.items():
        def bad(text):
            out.append(f'{rule}: {text}')
        if rule not in rules:
            bad('is not a live rule in the manifest')
        if entry.rule_sha256 is None:
            bad('has no rule_sha256')
        if entry.mixed:
            bad('mixes top-level when/governs with any')
        if entry.by is not None and entry.by not in MOMENTS:
            bad(f'by names unknown moment {entry.by!r}')
        if entry.accompanies and entry.alternatives:
            bad('has accompanies together with tests')
        for alt in entry.alternatives:
            for name in alt.governs:
                if name not in DUTIES:
                    bad(f'governs unknown duty {name!r}')
            for test in alt.when:
                problem = _test_problem(test)
                if problem:
                    bad(problem)
        for field in ('requires', 'accompanies'):
            for target in getattr(entry, field):
                if target not in rules:
                    bad(f'{field} names {target}, which is not a live rule')
        for target in entry.accompanies:
            if target in entries and entries[target].accompanies:
                bad(f'accompanies {target}, which is itself a lead-in')
    cycle = _cycle(entries)
    if cycle:
        out.append(f'{cycle[0]}: requires cycle {" -> ".join(cycle)}')
    return out


def stale(entries, rules):
    """Warnings: entries written against rule text that has since changed."""
    return [f'{rule}: stale: rule text changed since the entry was written; it omits nothing until refreshed'
            for rule, entry in entries.items() if rule in rules and entry.rule_sha256 is not None
            and entry.rule_sha256 != rules[rule]]


def with_reviewed(text, entries, rules, rule_ids):
    """The file text with `reviewed` digests written for rule_ids, directly after each table header."""
    found = problems(entries, rules)
    if found:
        raise ContextError('applicability.toml has problems; fix them before approving:\n' + '\n'.join(found))
    incoming = required_by(entries)
    lines = text.splitlines(keepends=True)
    for rule in rule_ids:
        entry = entries.get(rule)
        if entry is None:
            raise ContextError(f'{rule} has no entry to approve')
        if state(entry, rules[rule], incoming.get(rule, ())) == 'stale':
            raise ContextError(f'{rule} entry is stale; refresh rule_sha256 and its tests before approving')
        value = digest(entry, incoming.get(rule, ()))
        header = re.compile(r'^\s*\[\s*rule\.' + rule.removeprefix('rule:') + r'\s*\]\s*(#.*)?$')
        start = next((i for i, line in enumerate(lines) if header.match(line.rstrip('\n'))), None)
        if start is None:
            raise ContextError(f'{rule} table header not found in the file text')
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('[')), len(lines))
        body = [line for line in lines[start + 1:end] if not re.match(r'^reviewed\s*=', line)]
        lines = lines[:start + 1] + [f'reviewed = "{value}"\n'] + body + lines[end:]
    new = ''.join(lines)
    reparsed = parse(new.encode())
    for rule, entry in entries.items():
        if rule in rule_ids:
            if state(reparsed[rule], rules[rule], incoming.get(rule, ())) != 'reviewed':
                raise ContextError(f'{rule} is not reviewed after writing its digest; file left unchanged')
        elif reparsed.get(rule) != entry:
            raise ContextError(f'writing digests changed the entry for {rule}; file left unchanged')
    if set(reparsed) != set(entries):
        raise ContextError('writing digests changed the set of entries; file left unchanged')
    return new


def _alternative(table, where):
    if not isinstance(table, dict) or not ({'when', 'governs'} & set(table)):
        raise ContextError(f'{where}: an alternative has when, governs or both')
    when = table.get('when', [])
    if not isinstance(when, list):
        raise ContextError(f'{where}: when must be a list of tests')
    governs = table.get('governs', [])
    if not isinstance(governs, list) or not all(isinstance(d, str) for d in governs):
        raise ContextError(f'{where}: governs must be a list of duty names')
    if 'any' in where:
        extra = set(table) - {'when', 'governs'}
        if extra:
            raise ContextError(f'{where}: unknown key {", ".join(sorted(extra))}')
    return Alternative(tuple(_test(t, where) for t in when), tuple(governs))


def _test(raw, where):
    if not isinstance(raw, dict) or not isinstance(raw.get('fact'), str):
        raise ContextError(f'{where}: a test is {{ fact = "...", <operator> = ... }}')
    ops = set(raw) - {'fact'}
    if len(ops) != 1:
        raise ContextError(f'{where}: test on {raw["fact"]} needs exactly one operator')
    op = ops.pop()
    value = raw[op]
    if isinstance(value, list):
        value = tuple(value)
    return Test(raw['fact'], op, value)


def _test_problem(test):
    if test.fact not in FACTS:
        return f'tests unknown fact {test.fact!r}'
    if test.op not in OPERATORS:
        return f'uses unknown operator {test.op!r} on {test.fact}'
    kind, allowed = FACTS[test.fact]
    if test.op == 'eq':
        if kind == 'list':
            return f'uses eq on list fact {test.fact}'
        values = (test.value,)
        if isinstance(test.value, tuple):
            return f'eq on {test.fact} takes a single value'
    else:
        if not isinstance(test.value, tuple):
            return f'{test.op} on {test.fact} takes a list'
        values = test.value
    for value in values:
        if kind == 'bool':
            if not isinstance(value, bool):
                return f'{test.fact} takes true or false, not {value!r}'
        elif not isinstance(value, str) or not value or (allowed is not None and value not in allowed):
            return f'{test.fact} has no value {value!r}'
    return None


def _ids(table, field, where):
    value = table.get(field, [])
    if not isinstance(value, list) or not all(isinstance(v, str) and RULE_ID.fullmatch(v) for v in value):
        raise ContextError(f'{where}: {field} must be a list of rule:<32 hex> ids')
    return tuple(value)


def _text(table, field, where):
    value = table.get(field)
    if value is not None and not isinstance(value, str):
        raise ContextError(f'{where}: {field} must be a string')
    return value


def _cycle(entries):
    """The first requires cycle found, as a path that returns to its start, or None."""
    graph = {rule: entry.requires for rule, entry in entries.items()}
    done, path = set(), []

    def visit(rule):
        if rule in path:
            return path[path.index(rule):] + [rule]
        if rule in done:
            return None
        path.append(rule)
        for target in graph.get(rule, ()):
            found = visit(target)
            if found:
                return found
        path.pop()
        done.add(rule)
        return None

    for rule in sorted(graph):
        found = visit(rule)
        if found:
            return found
    return None
