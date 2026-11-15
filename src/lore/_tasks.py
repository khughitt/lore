"""Tasks CLI response boundary; config-only queries with no repair or locks."""
import json
from pathlib import Path
import re
import subprocess
from ._configuration import ProfileError

PREFIX = re.compile(r'[a-z][a-z0-9_-]*')


def _path(value):
    return isinstance(value, str) and bool(value) and Path(value).is_absolute()


def _validate_row(row):
    if not isinstance(row, dict) or row.get('status') not in ('resolved', 'unregistered'):
        raise ProfileError('tasks query returned unresolved or invalid metadata')
    if row.get('entry_error'):
        raise ProfileError(f"{row.get('prefix', 'tasks entry')}: {row['entry_error']}")
    if 'records_store' in row and not _path(row['records_store']):
        raise ProfileError('tasks query returned invalid records_store')
    if row['status'] == 'resolved':
        if not isinstance(row.get('prefix'), str) or not row['prefix'] or not _path(row.get('root')):
            raise ProfileError('resolved tasks row lacks prefix or absolute root')
        if 'entry' not in row:
            raise ProfileError('resolved tasks row lacks required entry')
    if 'entry' in row:
        entry = row['entry']
        if not isinstance(entry, dict) or entry.get('kind') not in ('in-tree', 'detached', 'linked'):
            raise ProfileError('tasks entry lacks valid layout kind')
        for key in ('config', 'records', 'checkout'):
            if not _path(entry.get(key)):
                raise ProfileError(f'tasks entry lacks absolute {key} path')
        if 'profile' in entry and not isinstance(entry['profile'], str):
            raise ProfileError('tasks entry has invalid profile assignment')


def _unrelated(warning, row, args):
    """Catalogue entry warnings name a prefix; unknown/global diagnostics stay fatal."""
    first, separator, rest = warning.partition(':')
    if not separator:
        return False
    if first == 'entry_conflict':
        prefix = rest.partition(':')[0].strip()
    elif rest.lstrip().startswith(('/', 'multiple records entries:')):
        prefix = first
    else:
        return False
    required = {row.get('prefix'), args[1] if len(args) > 1 else None}
    return PREFIX.fullmatch(prefix) is not None and prefix not in required


def query(args, env):
    try:
        result = subprocess.run(['tasks', *args], env=env, capture_output=True, text=True, timeout=5)
        if result.returncode:
            raise ProfileError(f"tasks {' '.join(args)}: {result.stderr.strip() or result.returncode}")
        data = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise ProfileError(f'tasks query failed: {error}') from error
    if not isinstance(data, dict) or not isinstance(data.get('results'), list):
        raise ProfileError('tasks query returned invalid results')
    warnings = data.get('warnings')
    if not isinstance(warnings, list) or any(not isinstance(w, str) for w in warnings):
        raise ProfileError('tasks query returned invalid warnings')
    if not data['results'] and '--all' not in args:
        raise ProfileError('tasks query returned no result')
    if '--all' not in args and len(data['results']) != 1:
        raise ProfileError('tasks query returned ambiguous results')
    for row in data['results']:
        _validate_row(row)
    # Full-catalogue consumers (check and private listings) cannot omit broken entries.
    relevant = warnings if '--all' in args else [w for w in warnings if not _unrelated(w, data['results'][0], args)]
    if relevant:
        raise ProfileError('tasks catalogue: ' + '; '.join(relevant))
    return data
