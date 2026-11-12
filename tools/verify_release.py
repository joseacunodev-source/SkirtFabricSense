"""Read-only structural/hash acceptance for local development bundles (stdlib only)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

APP_REQUIRED = {'app/inference.py', 'app/review.py', 'app/server.py',
                'app/static/index.html', 'app/static/review.html'}
PREPROCESSING = ('Source annotated bbox plus 5% each side; RGB Pillow bilinear '
                 'letterbox224; padding128; model Rescaling(1/127.5,offset=-1) exactly once')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def no_links(path):
    for item in (path, *path.parents):
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError(f'Link/reparse point rejected: {item}')


def relative_path(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError('Unsafe payload path')
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ('', '.', '..') for p in value.split('/')):
        raise ValueError('Unsafe payload path: ' + value)
    if any(p.endswith((' ', '.')) for p in path.parts):
        raise ValueError('Nonportable payload path: ' + value)
    return value


def json_object(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs)
    if not isinstance(value, dict):
        raise ValueError('Metadata must be an object')
    return value


def entries(value, sizes=False):
    if not isinstance(value, list) or not value:
        raise ValueError('Missing file inventory')
    output, folded = {}, set()
    for item in value:
        if not isinstance(item, dict):
            raise ValueError('Invalid file entry')
        path = relative_path(item.get('path'))
        if path.casefold() in folded or path in ('manifest.json', 'inventory.json'):
            raise ValueError('Duplicate or reserved payload path: ' + path)
        folded.add(path.casefold())
        if not isinstance(item.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', item['sha256']):
            raise ValueError('Invalid SHA256: ' + path)
        if sizes and (type(item.get('bytes')) is not int or item['bytes'] < 0):
            raise ValueError('Invalid byte count: ' + path)
        output[path] = item
    return output


def verify(bundle: Path, require_app=False):
    root = Path(os.path.abspath(bundle))
    no_links(root)
    if not root.is_dir():
        raise ValueError('Bundle must be a directory')
    actual, directories = set(), set()
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(current) / name
            no_links(path)
            relative = relative_path(path.relative_to(root).as_posix())
            if path.is_dir():
                directories.add(relative)
            elif stat.S_ISREG(path.lstat().st_mode):
                actual.add(relative)
            else:
                raise ValueError('Nonregular payload: ' + relative)
    manifest = json_object(root / 'manifest.json')
    inventory = json_object(root / 'inventory.json')
    for metadata in (manifest, inventory):
        if (type(metadata.get('schema_version')) is not int or metadata['schema_version'] != 1
                or metadata.get('bundle_id') != 'skirt-finetune-v1'
                or metadata.get('status') != 'development_only' or metadata.get('pi_verified') is not False):
            raise ValueError('Unsupported development bundle metadata')
    if inventory.get('dependencies_included') is not False:
        raise ValueError('Unexpected dependency payload declaration')
    if manifest.get('model') != 'model.tflite' or manifest.get('contract') != 'contract.json':
        raise ValueError('Unexpected model/contract paths')
    model_files = entries(manifest.get('files'))
    payload = entries(inventory.get('files'), sizes=True)
    if set(model_files) != {'model.tflite', 'contract.json'}:
        raise ValueError('Manifest must describe exactly model and contract')
    if actual != set(payload) | {'manifest.json', 'inventory.json'}:
        raise ValueError('Payload inventory mismatch: ' + str(sorted(actual ^ (set(payload) | {'manifest.json', 'inventory.json'}))))
    expected_dirs = {str(parent) for name in payload for parent in PurePosixPath(name).parents if str(parent) != '.'}
    if directories != expected_dirs:
        raise ValueError('Unexpected or missing payload directories')
    for name, item in payload.items():
        path = root / name
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError('Payload size/hash mismatch: ' + name)
    for name, item in model_files.items():
        if name not in payload or item['sha256'] != payload[name]['sha256']:
            raise ValueError('Manifest/inventory disagreement: ' + name)
    has_app = any(name.startswith('app/') for name in payload)
    if require_app or has_app:
        if not APP_REQUIRED <= payload.keys():
            raise ValueError('Missing required application files')
        if ('app/pipeline.py' in payload) != ('app/live_state.py' in payload):
            raise ValueError('Incomplete async application pair')
    contract = json_object(root / 'contract.json')
    if (contract.get('input') != {'shape': [1, 224, 224, 3], 'dtype': 'float32', 'color': 'RGB', 'range': [0, 255]}
            or contract.get('output') != {'shape': [1, 2], 'dtype': 'float32', 'labels': ['non_pleated', 'pleated'], 'semantics': 'uncalibrated softmax scores'}
            or contract.get('preprocessing') != PREPROCESSING
            or contract.get('normalization') != 'Inside model only'
            or contract.get('pi_verified') is not False):
        raise ValueError('Unsupported pleating model contract')
    return {'status': 'passed', 'bundle_id': manifest['bundle_id'], 'payload_files': len(payload),
            'application_included': has_app, 'manifest_sha256': digest(root / 'manifest.json'),
            'inventory_sha256': digest(root / 'inventory.json'), 'pi_verified': False,
            'runtime_verified': False, 'publisher_authenticated': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--require-app', action='store_true')
    args = parser.parse_args()
    try:
        result = verify(args.bundle, args.require_app)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, json.dumps({'status': 'failed', 'reason': str(exc)}) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
