"""Run git against a named repository without inheriting a hook's repository selection."""
import functools
import os
import pathlib
import subprocess

# The checkout this package executes from: src/lore/context/_git.py -> parents[3].
EXECUTING_ROOT = pathlib.Path(__file__).resolve().parents[3]


def run(root, *args):
    """`git -C <root> <args>` with bytes output; never raises on a non-zero exit.

    A commit hook exports GIT_DIR and GIT_INDEX_FILE, which win over `-C`. They are kept
    for the executing checkout, so a pre-commit check reads the index being committed,
    and dropped for every other repository, so a fixture or a foreign checkout reads its own.
    """
    env = os.environ
    if pathlib.Path(root).resolve() != EXECUTING_ROOT:
        names = _local_env_names()
        env = {key: value for key, value in env.items() if key not in names}
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, env=env)


@functools.cache
def _local_env_names():
    # The names depend on the git binary, not the repository, so one answer serves the run.
    result = subprocess.run(['git', 'rev-parse', '--local-env-vars'], capture_output=True,
                            cwd=EXECUTING_ROOT)
    return frozenset(result.stdout.decode().split())
