"""The selection record and the selector's identity: what was selected, from what, by which code."""
import hashlib
import pathlib

from . import _git

PACKAGE = 'src/lore/context'
WATCHED = (PACKAGE, 'instructions/AGENTS.md', 'instructions/AGENTS.manifest.json', 'instructions/applicability.toml')


def selector_identity(root):
    """Digest of the selector's source files, the checkout's commit, and whether the selector and
    its inputs are unchanged from that commit."""
    root = pathlib.Path(root)
    digest = hashlib.sha256()
    for path in sorted((root / PACKAGE).glob('*.py')):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode() + b'\0' + hashlib.sha256(path.read_bytes()).hexdigest().encode() + b'\n')
    head = _git.run(root, 'rev-parse', '--verify', '-q', 'HEAD')
    commit = head.stdout.decode().strip() if head.returncode == 0 else None
    status = _git.run(root, 'status', '--porcelain', '--', *WATCHED)
    clean = status.returncode == 0 and not status.stdout.strip()
    return {'sha256': digest.hexdigest(), 'commit': commit, 'clean': clean}


def build_record(mode, context_data, corpus, decisions, output, identity):
    return {
        'schema': 1,
        'mode': mode,
        'context': context_data,
        'corpus': {
            'artifact_sha256': _sha(corpus.artifact),
            'manifest_sha256': _sha(corpus.manifest),
            'applicability_sha256': None if corpus.applicability is None else _sha(corpus.applicability),
        },
        'selector': identity,
        'replayable': bool(identity['clean'] and identity['commit']),
        'rules': [{'id': d.rule, 'decision': 'include' if d.include else 'omit', 'reason': d.reason,
                   'detail': d.detail, 'bytes': d.length} for d in decisions],
        'output': {'sha256': _sha(output), 'bytes': len(output), 'artifact_bytes': len(corpus.artifact)},
        'delivery': None,
    }


def _sha(data):
    return hashlib.sha256(data).hexdigest()
