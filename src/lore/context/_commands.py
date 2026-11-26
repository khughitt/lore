"""The `lore context` subcommands over the checkout bin/lore runs from; each returns an exit code."""
import json
import pathlib
import sys

from . import _applicability, check, select_text
from ._band_shadow import render, report
from ._corpus import APPLICABILITY, load
from ._errors import ContextError
from ._git import EXECUTING_ROOT


def run(args, cwd, root=EXECUTING_ROOT):
    """Relative path arguments resolve against cwd, the caller's directory."""
    for name in ('context', 'record', 'attempts', 'fixture'):
        value = getattr(args, name, None)
        if value is not None:
            setattr(args, name, pathlib.Path(cwd) / value)
    try:
        if args.command == 'select':
            return _select(root, args)
        if args.command == 'explain':
            return _explain(root, args)
        if args.command == 'check':
            return _check(root)
        if args.command == 'approve':
            return _approve(root, args.rules)
        if args.command == 'shadow-band':
            return _shadow_band(root, args)
    except ContextError as error:
        print(f'lore context: {error}', file=sys.stderr)
        return 1
    raise AssertionError(args.command)


def _context(path):
    try:
        return json.loads(pathlib.Path(path).read_text())
    except OSError as error:
        raise ContextError(f'cannot read context {path}: {error.strerror}') from None
    except ValueError as error:
        raise ContextError(f'context {path} is not JSON: {error}') from None


def _select(root, args):
    text, record = select_text(root, _context(args.context), shadow=args.shadow)
    if args.record:
        try:
            pathlib.Path(args.record).write_text(json.dumps(record, indent=2) + '\n')
        except OSError as error:
            raise ContextError(f'cannot write record {args.record}: {error.strerror}') from None
    if args.json:
        sys.stdout.write(json.dumps(record, indent=2) + '\n')
    else:
        sys.stdout.buffer.write(text)
    return 0


def _explain(root, args):
    _, record = select_text(root, _context(args.context), shadow=args.shadow)
    for rule in record['rules']:
        detail = json.dumps(rule['detail'], sort_keys=True, separators=(',', ':'))
        print(f'{rule["decision"]:<7}  {rule["reason"]:<12}  {rule["id"]}  {rule["bytes"]:>5}  {detail}')
    output = record['output']
    print(f'selected {output["bytes"]} of {output["artifact_bytes"]} bytes ({record["mode"]})')
    return 0


def _check(root):
    problems, warnings = check(root)
    for line in problems:
        print(f'lore context: {line}', file=sys.stderr)
    for line in warnings:
        print(f'lore context: warning: {line}', file=sys.stderr)
    return 1 if problems else 0


def _approve(root, rule_ids):
    problems, _ = check(root, 'working')
    if problems:
        raise ContextError('check reports problems; nothing written:\n' + '\n'.join(problems))
    corpus = load(root, 'working')
    if corpus.applicability is None:
        raise ContextError(f'{APPLICABILITY} does not exist')
    text = corpus.applicability.decode('utf-8')
    entries = _applicability.parse(corpus.applicability)
    new = _applicability.with_reviewed(text, entries, {r.id: r.sha256 for r in corpus.rules}, list(rule_ids))
    (pathlib.Path(root) / APPLICABILITY).write_text(new)
    reparsed = _applicability.parse(new.encode())
    for rule in rule_ids:
        print(f'{rule}  {reparsed[rule].reviewed}')
    return 0


def _shadow_band(root, args):
    data = report(args.attempts, args.fixture, root)
    sys.stdout.write(json.dumps(data, indent=2) + '\n' if args.json else render(data))
    return 0
