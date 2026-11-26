"""Parse lore's command groups and git-identity-check, and dispatch to their subsystems."""
import argparse
import json
import pathlib
import sys
from . import _hooks, _identity_check
from ._configuration import ProfileError
from ._profiles import resolve, check, audit, defined
from ._rendering import explain_text, session_text


def main(argv, env, cwd):
    parser = argparse.ArgumentParser(prog='lore')
    groups = parser.add_subparsers(dest='group', required=True)
    profile = groups.add_parser('profile')
    commands = profile.add_subparsers(dest='command', required=True)
    commands.add_parser('check')
    commands.add_parser('list', help='every profile lore defines').add_argument('--json', action='store_true')
    for name in ('resolve', 'explain', 'session', 'audit'):
        sub = commands.add_parser(name)
        sub.add_argument('path', nargs='?', default='.')
        if name == 'resolve': sub.add_argument('--json', action='store_true')
    hook = groups.add_parser('hook', help='relay notice subscribers; one envelope on stdin')
    hooks = hook.add_subparsers(dest='command', required=True)
    for name in ('profile-notice', 'stale-notice'): hooks.add_parser(name)
    _context_parser(groups)
    args = parser.parse_args(argv)
    if args.group == 'hook':
        return _hook(args.command, env)
    if args.group == 'context':
        # Imported here: the hook and profile groups run in every session and must not load,
        # or be broken by, the selection package.
        from .context import _commands
        return _commands.run(args)
    if args.command == 'list':
        return _list(args.json, env)
    try:
        if args.command == 'check':
            problems = check(env)
            for problem in problems: print(f'lore profile: {problem}', file=sys.stderr)
            return 1 if problems else 0
        path = pathlib.Path(cwd) / args.path
        if args.command == 'audit':
            for line in audit(path, env): print(line)
            return 0
        result = resolve(path, env)
        if args.command == 'session': output = session_text(result)
        elif args.command == 'resolve' and args.json:
            output = json.dumps({k:v for k,v in result.items() if not k.startswith('_')},indent=2)+'\n'
        else: output = explain_text(result)
    except (ProfileError, OSError, ValueError) as error:
        print(f'lore profile: {error}', file=sys.stderr)
        return 1
    sys.stdout.write(output)
    return 0


def _context_parser(groups):
    context = groups.add_parser('context', help='select the delivered rules that apply to a context')
    commands = context.add_subparsers(dest='command', required=True)
    select = commands.add_parser('select', help='the selected text, or its record with --json')
    select.add_argument('--context', required=True, metavar='FILE')
    select.add_argument('--shadow', action='store_true', help='also apply proposed entries')
    select.add_argument('--json', action='store_true', help='print the selection record instead')
    select.add_argument('--record', metavar='FILE', help='also write the selection record')
    explain = commands.add_parser('explain', help='one line per rule: decision, reason, facts used')
    explain.add_argument('--context', required=True, metavar='FILE')
    explain.add_argument('--shadow', action='store_true')
    commands.add_parser('check', help='validate the applicability file and the empty-context invariant')
    approve = commands.add_parser('approve', help='write reviewed digests for user-approved entries')
    approve.add_argument('rules', nargs='+', metavar='RULE_ID')
    band = commands.add_parser('shadow-band', help="what band's pi worker would receive, per recorded attempt")
    band.add_argument('--attempts', required=True, metavar='DIR')
    band.add_argument('--fixture', required=True, metavar='FILE')
    band.add_argument('--json', action='store_true')


def _list(as_json, env):
    """The defined profile names; a configuration lore cannot load exits 2."""
    try:
        names = defined(env)
    except (ProfileError, OSError, ValueError) as error:
        print(f'lore profile: {error}', file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps({'profiles': names}) + '\n' if as_json else ''.join(f'{n}\n' for n in names))
    return 0


def git_identity_check(argv, env, cwd):
    """The git-identity-check command: 0 pass or not judged, 1 mismatch, 2 cannot judge."""
    parser = argparse.ArgumentParser(prog='git-identity-check', description=_identity_check.__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('path', nargs='?')
    args = parser.parse_args(argv)
    return _identity_check.run(args.path, env, cwd)


def _hook(name, env):
    """Reply on stdout; the profile notice never fails, the stale notice fails visibly
    to relay (nonzero, one bounded stderr line, no context)."""
    raw = sys.stdin.buffer.read(_hooks.INPUT_LIMIT + 1)
    if name == 'profile-notice':
        sys.stdout.write(_hooks.profile_notice(raw, env))
        return 0
    try:
        reply = _hooks.stale_notice(raw, env)
    except (_hooks.EnvelopeError, _hooks.NoticeFailed) as error:
        print(f'lore hook {name}: {error}', file=sys.stderr)
        return 1
    sys.stdout.write(reply)
    return 0
