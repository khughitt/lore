"""Tasks CLI response boundary; config-only queries with no repair or locks."""
import json
import subprocess
from ._configuration import ProfileError


def query(args, env):
    try:
        result = subprocess.run(['tasks', *args], env=env, capture_output=True, text=True, timeout=5)
        if result.returncode:
            raise ProfileError(f"tasks {' '.join(args)}: {result.stderr.strip() or result.returncode}")
        data = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise ProfileError(f'tasks query failed: {error}') from error
    if not isinstance(data, dict) or data.get('warnings') or not isinstance(data.get('results'), list):
        raise ProfileError('tasks query returned invalid metadata or warnings')
    if not data['results'] and '--all' not in args:
        raise ProfileError('tasks query returned no result')
    if '--all' not in args and len(data['results']) != 1:
        raise ProfileError('tasks query returned ambiguous results')
    for row in data['results']:
        if not isinstance(row, dict) or row.get('status') not in {'resolved','unregistered'} or row.get('entry_error'):
            raise ProfileError('tasks query returned unresolved or unreadable metadata')
        if 'records_store' in row and not isinstance(row['records_store'], str):
            raise ProfileError('tasks query returned invalid records_store')
        if 'entry' in row and not isinstance(row['entry'],dict):
            raise ProfileError('tasks query returned invalid entry')
    return data
