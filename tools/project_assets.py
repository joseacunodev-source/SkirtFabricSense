"""Inventory and privately transfer Git-excluded project assets without environments.

The manifest is suitable for Git. Archives contain local datasets/model artifacts
and must be transferred only where their actual terms and authorization permit.
No downloads, model execution, installation or Git publication occur here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT/'config/project-assets-v2.json'
FAMILIES = ('data/external', 'data/raw', 'data/processed', 'data/cache',
            'data/candidates', 'artifacts', 'output/geometry-review', 'docs/references', 'records')
RECORD_SUFFIXES = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.bin',
                   '.npz', '.npy', '.tflite', '.keras', '.h5', '.pt', '.pth', '.onnx'}
BLOCKED_PARTS = {'.git', 'node_modules', '__pycache__', '.ipynb_checkpoints', 'tmp',
                 '.venv', '.venv-tools', 'venv', 'env'}
SECRET_SUFFIXES = {'.pem', '.key', '.pfx', '.p12'}
ARCHIVE_SUFFIXES = {'.zip', '.7z', '.rar', '.tar', '.gz', '.bz2', '.xz'}
# Required by data/external/seed/acquisition_manifest.json. Other archives stay
# excluded so a transfer bundle cannot recursively inventory earlier bundles.
SOURCE_ARCHIVE_ALLOWLIST = {'data/external/dtd/dtd-r1.0.1-labels.tar.gz'}
CHUNK = 1024*1024


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    require(isinstance(value, str) and value and '\\' not in value and ':' not in value
            and not any(ord(c) < 32 for c in value),
            'Asset paths must be canonical relative forward-slash paths')
    path = PurePosixPath(value)
    require(not path.is_absolute() and '..' not in path.parts and str(path) == value,
            'Unsafe asset path')
    require(all(not p.endswith((' ', '.')) and not re.fullmatch(
        r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', p, flags=re.I) for p in path.parts),
        'Asset path is not portable to Windows')
    return path


def is_link(path):
    return path.is_symlink() or (path.exists() and bool(
        getattr(path.lstat(), 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)))


def safe_path(root, relative):
    path = root.joinpath(*canonical(relative).parts)
    for item in (path, *path.parents):
        if item == root.parent:
            break
        require(not is_link(item), 'Symlinks/junctions cannot be transferred: '+relative)
    require(path.resolve().is_relative_to(root.resolve()), 'Asset escapes project root')
    return path


def permitted(relative):
    path = canonical(relative)
    parts = path.parts
    if any(p.lower() in BLOCKED_PARTS or p.lower().startswith('.venv') for p in parts):
        return False
    name = path.name.lower()
    if (name.startswith(('.env', 'credentials', 'id_rsa', 'id_ed25519'))
            or path.suffix.lower() in SECRET_SUFFIXES):
        return False
    if path.suffix.lower() in ARCHIVE_SUFFIXES and relative not in SOURCE_ARCHIVE_ALLOWLIST:
        return False
    if any(relative.startswith(family+'/') for family in FAMILIES[:-1]):
        return True
    if relative.startswith('records/acquisitions/'):
        return True
    return relative.startswith('records/') and path.suffix.lower() in RECORD_SUFFIXES


def digest_file(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(CHUNK), b''):
            h.update(block)
    return h.hexdigest()


def manifest_rows(manifest):
    require(isinstance(manifest, dict) and type(manifest.get('schema_version')) is int
            and manifest['schema_version'] == 1
            and manifest.get('data_kind') == 'git_excluded_project_assets', 'Unsupported asset manifest')
    rows = manifest.get('files')
    require(isinstance(rows, list), 'Asset files must be a list')
    seen = set()
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'}, 'Invalid asset row')
        relative = row['path']; canonical(relative)
        require(permitted(relative), 'Disallowed transfer family: '+relative)
        # Windows cannot safely distinguish paths differing only by case.
        require(relative.casefold() not in seen, 'Duplicate/case-colliding asset path')
        seen.add(relative.casefold())
        require(type(row['bytes']) is int and row['bytes'] >= 0, 'Invalid asset byte count')
        require(isinstance(row['sha256'], str) and re.fullmatch('[a-f0-9]{64}', row['sha256']),
                'Invalid asset SHA256')
    require(manifest.get('file_count') == len(rows)
            and manifest.get('total_bytes') == sum(r['bytes'] for r in rows), 'Manifest totals disagree')
    return rows


def load_manifest(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    manifest_rows(data)
    return data


def inventory(root):
    root = Path(root).resolve()
    candidates = []
    skipped = []
    for family in FAMILIES:
        folder = root/family
        if not folder.exists():
            continue
        if is_link(folder):
            skipped.append(family); continue
        for current, dirs, files in os.walk(folder, followlinks=False):
            current = Path(current)
            keep = []
            for name in dirs:
                path = current/name
                if is_link(path):
                    skipped.append(path.relative_to(root).as_posix())
                elif name not in BLOCKED_PARTS and not name.startswith('.venv'):
                    keep.append(name)
            dirs[:] = keep
            for name in files:
                path = current/name
                relative = path.relative_to(root).as_posix()
                if is_link(path):
                    skipped.append(relative)
                elif permitted(relative):
                    candidates.append(relative)
    if candidates:
        result = subprocess.run(['git', '-C', str(root), 'check-ignore', '--no-index', '-z', '--stdin'],
                                input='\0'.join(candidates).encode()+b'\0', capture_output=True)
        require(result.returncode in (0, 1), 'git check-ignore failed; initialize/read the intended repository first')
        ignored = {s.decode('utf-8') for s in result.stdout.split(b'\0') if s}
    else:
        ignored = set()
    files = []
    for relative in sorted(ignored):
        path = safe_path(root, relative)
        require(path.is_file(), 'Asset disappeared while inventorying')
        files.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': digest_file(path)})
    return {'schema_version': 1, 'data_kind': 'git_excluded_project_assets',
            'file_count': len(files), 'total_bytes': sum(r['bytes'] for r in files), 'files': files,
            'excluded_link_paths': sorted(skipped),
            'scope': 'Git-ignored asset families only; no environment, credential, temporary or external WSL-run backup.',
            'distribution': 'Private authorized transfer only; source terms still apply. No GitHub upload is performed.'}


def verify(root, manifest):
    root = Path(root).resolve()
    missing, mismatched = [], []
    rows = manifest_rows(manifest)
    for row in rows:
        path = safe_path(root, row['path'])
        if not path.is_file():
            missing.append(row['path'])
        elif path.stat().st_size != row['bytes'] or digest_file(path) != row['sha256']:
            mismatched.append(row['path'])
    return {'status': 'passed' if not missing and not mismatched else 'failed',
            'files_expected': len(rows), 'bytes_expected': sum(r['bytes'] for r in rows),
            'missing': missing, 'mismatched': mismatched}


def pack(root, manifest, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    rows = manifest_rows(manifest)
    require(output.as_posix().casefold() not in {(root/r['path']).as_posix().casefold() for r in rows},
            'Archive output cannot replace an asset')
    require(verify(root, manifest)['status'] == 'passed', 'Source assets must pass verification before packing')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive file creation prevents overwriting an existing archive.
    handle = output.open('xb')
    try:
        with handle, zipfile.ZipFile(handle, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
            for row in rows:
                path = safe_path(root, row['path']); h = hashlib.sha256(); count = 0
                with path.open('rb') as source, archive.open(row['path'], 'w', force_zip64=True) as target:
                    for block in iter(lambda: source.read(CHUNK), b''):
                        count += len(block)
                        require(count <= row['bytes'], 'Source asset grew during packing')
                        h.update(block); target.write(block)
                require(count == row['bytes'] and h.hexdigest() == row['sha256'], 'Source changed during packing')
    except BaseException:
        handle.close()
        output.unlink(missing_ok=True)
        raise
    return {'status': 'packed', 'files': len(rows), 'archive_bytes': output.stat().st_size,
            'archive_sha256': digest_file(output)}


def restore(archive_path, manifest, destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    rows = manifest_rows(manifest)
    expected = {r['path']: r for r in rows}
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        names = []
        for item in infos:
            canonical(item.filename)
            mode = item.external_attr >> 16
            require(not item.is_dir() and stat.S_IFMT(mode) in (0, stat.S_IFREG), 'Archive links/non-files rejected')
            require(not item.flag_bits & 1, 'Encrypted archive members unsupported')
            require(item.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED), 'Unsupported ZIP compression')
            names.append(item.filename)
        require(len(names) == len(set(n.casefold() for n in names)) and set(names) == set(expected),
                'Archive must contain exactly the manifest paths without duplicates or extras')
        for item in infos:
            require(item.file_size == expected[item.filename]['bytes'], 'Archive size differs from manifest')
            target = safe_path(destination, item.filename)
            if target.exists():
                require(target.is_file() and target.stat().st_size == item.file_size
                        and digest_file(target) == expected[item.filename]['sha256'],
                        'Existing destination differs; preserve and resolve it before restore: '+item.filename)
        # Validate all bytes into an owned temporary directory before writing any destination file.
        with tempfile.TemporaryDirectory(prefix='skirt-assets-') as temp:
            staging = Path(temp)
            for item in infos:
                row = expected[item.filename]; staged = staging/item.filename
                staged.parent.mkdir(parents=True, exist_ok=True)
                h = hashlib.sha256(); count = 0
                with archive.open(item) as source, staged.open('xb') as target:
                    for block in iter(lambda: source.read(CHUNK), b''):
                        count += len(block)
                        require(count <= row['bytes'], 'Expanded archive exceeds manifest bound')
                        h.update(block); target.write(block)
                require(count == row['bytes'] and h.hexdigest() == row['sha256'], 'Archive asset SHA256 differs')
            copied = 0
            for row in rows:
                target = safe_path(destination, row['path'])
                if target.exists():
                    # Recheck rather than trusting the earlier preflight.
                    require(target.is_file() and digest_file(target) == row['sha256'], 'Destination changed during restore')
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                safe_path(destination, row['path'])
                with (staging/row['path']).open('rb') as source, target.open('xb') as outgoing:
                    shutil.copyfileobj(source, outgoing, length=CHUNK)
                copied += 1
    return {'status': 'restored', 'files_copied': copied, 'files_already_matched': len(rows)-copied,
            'verification': verify(destination, manifest)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    inv = commands.add_parser('inventory'); inv.add_argument('--output', type=Path, default=DEFAULT_MANIFEST)
    inv.add_argument('--root', type=Path, default=ROOT)
    for name in ('verify', 'pack', 'restore'):
        p = commands.add_parser(name); p.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
        if name == 'restore':
            p.add_argument('archive', type=Path); p.add_argument('--destination', type=Path, default=ROOT)
        else:
            p.add_argument('--root', type=Path, default=ROOT)
        if name == 'pack': p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'inventory':
            result = inventory(args.root); args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('x', encoding='utf-8') as stream:
                json.dump(result, stream, indent=2); stream.write('\n')
            print(json.dumps({k:v for k,v in result.items() if k != 'files'}))
        else:
            data = load_manifest(args.manifest)
            if args.command == 'verify': result = verify(args.root, data)
            elif args.command == 'pack': result = pack(args.root, data, args.output)
            else: result = restore(args.archive, data, args.destination)
            print(json.dumps(result, indent=2))
            return int(result['status'] == 'failed')
        return 0
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, RuntimeError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)})); return 1


if __name__ == '__main__': raise SystemExit(main())
