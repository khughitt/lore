"""Read and verify the delivered artifact, its manifest and the applicability file."""
from dataclasses import dataclass
import hashlib
import json
import pathlib

from . import _git
from ._errors import ContextError

ARTIFACT = 'instructions/AGENTS.md'
MANIFEST = 'instructions/AGENTS.manifest.json'
APPLICABILITY = 'instructions/applicability.toml'
INPUTS = (ARTIFACT, MANIFEST, APPLICABILITY)


@dataclass(frozen=True)
class Rule:
    id: str
    sha256: str
    offset: int
    length: int
    fragment: str


@dataclass(frozen=True)
class Corpus:
    artifact: bytes
    manifest: bytes
    applicability: bytes | None
    rules: tuple[Rule, ...]
    generated: tuple[tuple[int, int], ...]


def load(root, view='auto'):
    """The three inputs from the working tree ('working') or the index ('index'), verified.

    'auto' reads the index when any input is staged, so a pre-commit check judges what the
    commit publishes, and the working tree otherwise.
    """
    root = pathlib.Path(root)
    if view == 'auto':
        view = 'index' if _staged(root) else 'working'
    if view == 'working':
        artifact, manifest = _disk(root, ARTIFACT), _disk(root, MANIFEST)
        path = root / APPLICABILITY
        applicability = path.read_bytes() if path.is_file() else None
    elif view == 'index':
        artifact, manifest = _indexed(root, ARTIFACT), _indexed(root, MANIFEST)
        applicability = _indexed(root, APPLICABILITY, required=False)
    else:
        raise ContextError(f'unknown view {view!r}')
    return _verify(artifact, manifest, applicability)


def from_bytes(artifact, manifest, applicability=None):
    """The same verification over bytes already in hand."""
    return _verify(artifact, manifest, applicability)


def _verify(artifact, manifest_bytes, applicability):
    try:
        manifest = json.loads(manifest_bytes)
    except ValueError as error:
        raise ContextError(f'{MANIFEST} is not JSON: {error}') from None
    if manifest.get('version') != 2:
        raise ContextError(f'{MANIFEST} has version {manifest.get("version")!r}; only version 2 is read')
    if hashlib.sha256(artifact).hexdigest() != manifest.get('artifact', {}).get('sha256'):
        raise ContextError(f'{ARTIFACT} does not match the manifest; run just assemble')
    rules, generated = [], []
    for fragment in manifest.get('fragments', []):
        if 'generated' in fragment:
            generated.append((fragment['offset'], fragment['length']))
        for record in fragment.get('rules', []):
            rule = Rule(record['id'], record['sha256'], record['offset'], record['length'], fragment['id'])
            end = rule.offset + rule.length
            if (rule.offset and artifact[rule.offset - 1:rule.offset] != b'\n') or rule.length <= 0 \
                    or end > len(artifact) or artifact[end - 1:end] != b'\n':
                raise ContextError(f'{rule.id} range {rule.offset}+{rule.length} is not on a line boundary')
            if hashlib.sha256(artifact[rule.offset:end]).hexdigest() != rule.sha256:
                raise ContextError(f'{rule.id} bytes do not hash to the manifest sha256; run just assemble')
            rules.append(rule)
    rules.sort(key=lambda r: r.offset)
    return Corpus(artifact, manifest_bytes, applicability, tuple(rules), tuple(generated))


def _disk(root, path):
    try:
        return (root / path).read_bytes()
    except OSError as error:
        raise ContextError(f'cannot read {path}: {error.strerror}') from None


def _staged(root):
    result = _git.run(root, 'diff', '--cached', '--name-only', '-z', '--', *INPUTS)
    if result.returncode:
        return False        # not a git work tree: read the working tree
    return any(result.stdout.split(b'\0'))


def _indexed(root, path, required=True):
    if _git.run(root, 'ls-files', '--error-unmatch', '--', path).returncode:
        if required:
            raise ContextError(f'{path} is not in the index')
        return None
    result = _git.run(root, 'show', f':{path}')
    if result.returncode:
        raise ContextError(f'cannot read {path} from the index: {result.stderr.decode(errors="replace").strip()}')
    return result.stdout
