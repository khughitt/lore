"""Parse the profile command group and dispatch to resolution/rendering."""
import argparse
import json
import pathlib
import sys
from ._configuration import ProfileError
from ._profiles import resolve, check, audit
from ._rendering import explain_text, session_text


def main(argv, env, cwd):
    parser = argparse.ArgumentParser(prog='lore')
    groups = parser.add_subparsers(dest='group', required=True)
    profile = groups.add_parser('profile')
    commands = profile.add_subparsers(dest='command', required=True)
    commands.add_parser('check')
    for name in ('resolve', 'explain', 'session', 'audit'):
        sub = commands.add_parser(name)
        sub.add_argument('path', nargs='?', default='.')
        if name == 'resolve': sub.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
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
