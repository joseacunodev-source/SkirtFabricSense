"""Create a platform-specific hashed requirements file from pip installation reports."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--report', type=Path, action='append', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
packages = {}
for path in args.report:
    for item in json.loads(path.read_text(encoding='utf-8'))['install']:
        metadata = item['metadata']
        name = metadata['name'].lower().replace('_', '-')
        value = (metadata['version'], item['download_info']['archive_info']['hashes']['sha256'])
        if name in packages and packages[name] != value:
            raise ValueError('Conflicting report versions: ' + name)
        packages[name] = value
with args.output.open('x', encoding='utf-8') as stream:
    stream.write('# Resolved WSL Ubuntu x86_64 / CPython 3.12 artifacts; not a Raspberry Pi lock.\n')
    stream.write('# Install using python -m pip install --require-hashes -r this-file\n')
    for name, (version, digest) in sorted(packages.items()):
        stream.write(f'{name}=={version} --hash=sha256:{digest}\n')
print(f'Wrote {len(packages)} pinned package artifacts to {args.output}')
