"""Run the assembler from the same recorded revision as this proof driver."""
import base64
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys

pinned = Path(sys.argv[1])
payload = json.load(sys.stdin)
loader = importlib.machinery.SourceFileLoader('pinned_assembly', str(pinned))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)
sources = {name: base64.b64decode(data, validate=True) for name, data in payload['sources'].items()}
artifact, manifest = module.assemble(base64.b64decode(payload['catalog'], validate=True), sources,
                                     pinned.read_bytes(), set(payload['required_ids']), mode=payload['mode'])
manifest['reference'] = payload['reference']
if payload['mode'] == 'baseline':
    projects = next(f for f in manifest['fragments'] if f['id'] == 'projects')
    projects['snapshot'] = payload['reference']['projects_snapshot']
(pinned.parent / 'proof-manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
sys.stdout.buffer.write(artifact)
