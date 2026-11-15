#!/usr/bin/env python3
"""Local transition acceptance: compare installed catalogue with old ops and this tree."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from lore import ProfileError, resolve
from lore._configuration import load, expand
from lore._tasks import query


def _semantic(result):
    def warning(text):
        if text.startswith('.git/info/exclude hides ') and '; run ' in text:
            return text.partition('; run ')[0] + '; run <profile audit>'
        return text
    fields = ('checkout', 'path', 'worktree', 'project', 'records', 'layout', 'notes', 'private_projects')
    value = {key: result.get(key) for key in fields}
    value['profiles'] = [p['name'] for p in result['profiles']]
    value['home'] = result['home']['name']
    value['keys'] = {k: item['value'] for k, item in result['keys'].items()}
    value['warnings'] = [warning(w) for w in result['warnings']]
    value['fragments'] = [(Path(p).name, Path(p).read_text()) for p in result['fragments']]
    value['notes_text'] = Path(result['notes']).read_text() if result.get('notes') else None
    return value


def compare_resolution(old, new):
    if new.get('kind') != 'checkout':
        return ['classification differs for ordinary checkout']
    left, right = _semantic(old), _semantic(new)
    return [f'resolution differs: {key}' for key in left if left[key] != right[key]]


def compare_definitions(old, new, env):
    def normalized(config):
        result = copy.deepcopy({k:v for k,v in config.items() if k not in {'_sources','_paths'}})
        for rule in result.get('family', []):
            rule['path'] = str(expand(rule['path'], env).resolve())
        return result
    left, right = normalized(old), normalized(new)
    return [] if left == right else ['effective profile definitions differ']


def compare_all(rows, old_resolve, new_resolve):
    report = {'present': [], 'matched': [], 'unavailable': [], 'differences': {}}
    for row in rows:
        if row['status'] == 'unregistered':
            continue
        prefix = row['prefix']
        path = Path(row['root'])
        if not path.is_dir():
            report['unavailable'].append(prefix)
            continue
        report['present'].append(prefix)
        try:
            differences = compare_resolution(old_resolve(path), new_resolve(path))
        except Exception as error:
            differences = [f'resolution failed: {error}']
        if differences: report['differences'][prefix] = differences
        else: report['matched'].append(prefix)
    return report


def _old_resolve(ops, path, env):
    run = subprocess.run([sys.executable, str(ops / 'bin/ops-profile'), 'resolve', str(path), '--json'],
                         env=env, capture_output=True, text=True, timeout=15)
    if run.returncode:
        raise RuntimeError(run.stderr.strip() or f'old resolver exit {run.returncode}')
    return json.loads(run.stdout)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ops-root', required=True, type=Path)
    args = parser.parse_args(argv)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    try:
        ops = args.ops_root.resolve()
        registered = query(['resolve', 'ops', '--json'], env)['results'][0]
        if Path(registered['root']).resolve() != ops:
            raise RuntimeError('--ops-root must name the registered ops checkout')
        lore = query(['resolve', 'lore', '--json'], env)['results'][0]
        records = Path(lore['entry']['records'])
        private = records / 'profiles.toml'
        definitions = load(ROOT/'profiles/profiles.toml', private, env)
        old_config = tomllib.loads((ops/'profiles.toml').read_text())
        rows = query(['resolve', '--all', '--json'], env)['results']
        report = compare_all(rows, lambda p: _old_resolve(ops,p,env), lambda p: resolve(p,env))
        report['definition_differences'] = compare_definitions(old_config, definitions, env)
        store = records.parent
        current, previous = resolve(store,env), _old_resolve(ops,store,env)
        good_store = (current['kind']=='records-store' and current['project'] is None
                      and current['keys']['design_docs']['value']=='not-applicable'
                      and all(current['keys'][k]['value']==previous['keys'][k]['value']
                              for k in ('gh_account','git_identity')))
        report['store_verified'] = good_store
        report['passed'] = bool(report['present']) and not report['differences'] and not report['definition_differences'] and good_store
        print(json.dumps(report, indent=2))
        return 0 if report['passed'] else 1
    except (ProfileError, OSError, ValueError, RuntimeError, KeyError) as error:
        print(f'profile parity: {error}',file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
