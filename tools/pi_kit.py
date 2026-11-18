"""Build and verify a bounded offline Pi 4 research kit; never install or claim Pi acceptance."""
from __future__ import annotations

import argparse
from email.parser import BytesParser
import itertools
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import zipfile

if __package__:
    from .station_package import verify_station
    from .verify_release import digest, entries, json_object, no_links, relative_path
else:
    from station_package import verify_station
    from verify_release import digest, entries, json_object, no_links, relative_path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ('pi_kit.py', 'pi_install.py', 'pi_probe.py', 'collect_environment.py',
         'station_package.py', 'verify_release.py')
FIXED = {'kit.json', 'INSTALL_PI4.md', 'config/profile.json',
         'reference/model-probe.json', 'requirements/runtime-candidate.lock.txt'}
ROLES = {'pleating', 'localizer', 'presence', 'fabric'}
SHA = re.compile(r'[0-9a-f]{64}')
LOCK_LINE = re.compile(r'([A-Za-z0-9][A-Za-z0-9_.-]*)==([^\s;]+)\s+--hash=sha256:([0-9a-f]{64})')


def require(value, reason):
    if not value:
        raise ValueError(reason)


def normalized(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def checked_path(value):
    relative_path(value)
    require(not any(ord(c) < 32 for c in value), 'Control character in kit path')
    for part in PurePosixPath(value).parts:
        require(not re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part, re.I),
                'Nonportable reserved kit path')
    return value


def tree(root):
    root = Path(root).absolute()
    no_links(root)
    require(root.is_dir(), 'Kit/input must be a directory')
    files, directories, folded = {}, set(), set()
    for current, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            path = Path(current) / name
            no_links(path)
            relative = checked_path(path.relative_to(root).as_posix())
            require(relative.casefold() not in folded, 'Case-colliding kit paths')
            folded.add(relative.casefold())
            if path.is_dir():
                directories.add(relative)
            else:
                require(stat.S_ISREG(path.lstat().st_mode), 'Nonregular kit/input file')
                files[relative] = path
    return files, directories


def read_lock(path):
    no_links(Path(path).absolute())
    result = {}
    for raw in Path(path).read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        match = LOCK_LINE.fullmatch(line)
        require(match is not None, 'Lock needs one exact version and SHA256 per line')
        name, version, sha = match.groups()
        key = normalized(name)
        require(key not in result, 'Duplicate package in candidate lock')
        result[key] = {'name': name, 'version': version, 'sha256': sha}
    require(result, 'Candidate lock is empty')
    return result


def validate_profile(profile):
    require(type(profile.get('schema_version')) is int and profile['schema_version'] == 1
            and profile.get('pi_verified') is False and profile.get('candidate_only') is True,
            'Profile must be an explicitly unverified candidate')
    target = profile.get('target', {})
    require(isinstance(target, dict) and target.get('board') == 'Raspberry Pi 4'
            and target.get('system') == 'Linux' and target.get('machine') == 'aarch64'
            and target.get('python') == '3.13' and target.get('abi') == 'cp313'
            and target.get('os_codename') == 'trixie', 'Unsupported Pi 4 target profile')
    require(target.get('min_glibc') == '2.28', 'Unsupported or missing candidate glibc minimum')
    runtime = profile.get('runtime', {})
    require(isinstance(runtime, dict) and runtime.get('distribution') == 'ai-edge-litert'
            and isinstance(runtime.get('version'), str) and runtime['version']
            and runtime.get('module') == 'ai_edge_litert.interpreter', 'Unsupported candidate runtime')
    return target, runtime


def platform_matches(value, target):
    minimum = tuple(map(int, target['min_glibc'].split('.')))
    for tag in value.split('.'):
        match = re.fullmatch(r'manylinux_(\d+)_(\d+)_aarch64', tag)
        if match:
            needed = tuple(map(int, match.groups()))
        elif tag == 'manylinux2014_aarch64':
            needed = (2, 17)
        else:
            return False
        if needed > minimum:
            return False
    return True


def wheel_info(path, target):
    path = Path(path)
    no_links(path.absolute())
    require(path.is_file() and path.suffix == '.whl', 'Wheelhouse contains a non-wheel')
    filename_parts = path.stem.split('-')
    require(len(filename_parts) in (5, 6), 'Invalid wheel filename')
    if len(filename_parts) == 6:
        require(re.fullmatch(r'[0-9][A-Za-z0-9_]*', filename_parts[2]), 'Invalid wheel build tag')
    with zipfile.ZipFile(path) as wheel:
        names, folded = [], set()
        for member in wheel.infolist():
            require(member.orig_filename == member.filename,
                    'Wheel member filename normalization rejected')
            name = member.filename.rstrip('/')
            checked_path(name)
            require(name.casefold() not in folded, 'Duplicate/case-colliding wheel member')
            folded.add(name.casefold())
            mode = stat.S_IFMT(member.external_attr >> 16)
            require(mode in (0, stat.S_IFREG, stat.S_IFDIR), 'Wheel contains a link or special member')
            require(not member.flag_bits & 1, 'Encrypted wheel member')
            names.append(member.filename)
        metadata_names = [name for name in names if re.fullmatch(r'[^/]+\.dist-info/METADATA', name)]
        require(len(metadata_names) == 1, 'Wheel must have exactly one top-level METADATA')
        metadata_name = metadata_names[0]
        wheel_name = metadata_name.rsplit('/', 1)[0] + '/WHEEL'
        require(wheel_name in names, 'Missing wheel tag metadata')
        require(wheel.getinfo(metadata_name).file_size <= 4_000_000
                and wheel.getinfo(wheel_name).file_size <= 100_000, 'Wheel metadata exceeds bound')
        metadata = BytesParser().parsebytes(wheel.read(metadata_name))
        tag_metadata = BytesParser().parsebytes(wheel.read(wheel_name))
    name, version = metadata.get('Name'), metadata.get('Version')
    require(len(metadata.get_all('Name', [])) == 1 and len(metadata.get_all('Version', [])) == 1
            and isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', name)
            and isinstance(version, str) and version and not re.search(r'\s', version),
            'Invalid wheel package identity')
    tags = tag_metadata.get_all('Tag', [])
    require(len(tags) == len(set(tags)), 'Duplicate wheel tag metadata')
    require(normalized(filename_parts[0]) == normalized(name) and filename_parts[1] == version,
            'Wheel filename and metadata identities differ')
    filename_tags = {'-'.join(combination) for combination in itertools.product(
        *(field.split('.') for field in filename_parts[-3:]))}
    require(set(tags) == filename_tags, 'Wheel filename and metadata tags differ')
    supported = False
    for tag in tags:
        fields = tag.split('-')
        require(len(fields) == 3, 'Invalid wheel tag')
        python_tag, abi, platform = fields
        universal = bool(set(python_tag.split('.')) & {'py3', 'py313'}) and abi == 'none' and platform == 'any'
        native = (python_tag == target['abi'] and abi == target['abi']
                  and platform_matches(platform, target))
        # Stable-ABI wheels may target an older CPython release.
        stable = (re.fullmatch(r'cp3\d+', python_tag) is not None and abi == 'abi3'
                  and int(python_tag[2:]) <= 313
                  and platform_matches(platform, target))
        supported = supported or universal or native or stable
    require(tags and supported, 'Wheel tags do not match the declared ARM64 CPython profile')
    return {'name': name, 'version': version, 'path': 'wheels/' + path.name,
            'sha256': digest(path), 'bytes': path.stat().st_size, 'tags': sorted(tags)}


def validate_wheels(wheelhouse, lock, profile):
    target, runtime = validate_profile(profile)
    files, directories = tree(wheelhouse)
    require(not directories and files, 'Wheelhouse must contain only top-level wheels')
    wheels = {}
    for relative, path in sorted(files.items()):
        require('/' not in relative, 'Wheelhouse must be flat')
        record = wheel_info(path, target)
        key = normalized(record['name'])
        require(key not in wheels, 'Duplicate wheel distribution')
        require(key in lock and lock[key]['version'] == record['version']
                and lock[key]['sha256'] == record['sha256'], 'Wheel identity/hash differs from candidate lock')
        wheels[key] = record
    require(set(wheels) == set(lock), 'Candidate lock and wheelhouse memberships differ')
    require({'numpy', 'pillow', normalized(runtime['distribution'])} <= set(wheels),
            'Missing required runtime, NumPy or Pillow wheel')
    require(wheels[normalized(runtime['distribution'])]['version'] == runtime['version'],
            'Runtime wheel differs from target profile')
    return [wheels[name] for name in sorted(wheels)]


def validate_reference(reference, station):
    require(type(reference.get('schema_version')) is int and reference['schema_version'] == 1
            and reference.get('kind') == 'pi_model_probe' and reference.get('status') == 'passed'
            and reference.get('pi_verified') is False and reference.get('full_live_acceptance') is False,
            'Reference must be a passing synthetic probe, without Pi/live acceptance claims')
    require(reference.get('station_inventory_sha256') == digest(Path(station) / 'station-inventory.json'),
            'Reference station inventory identity differs')
    worker = reference.get('worker', {})
    models = worker.get('models', {}) if isinstance(worker, dict) else {}
    require(isinstance(worker, dict) and worker.get('status') == 'passed'
            and isinstance(models, dict) and set(models) == ROLES,
            'Reference requires all four passing model roles')
    fixture = worker.get('fixture', {})
    require(isinstance(fixture, dict) and fixture.get('id') == 'rgb_mod256_v1'
            and type(fixture.get('seed')) is int and fixture['seed'] == 42,
            'Unsupported reference fixture')
    station = Path(station)
    expected = {'pleating': digest(station / 'application/model.tflite')}
    config = json_object(station / 'station.json')
    expected.update({role: config['models'][role]['sha256'] for role in ROLES - {'pleating'}})
    for role, record in models.items():
        require(isinstance(record, dict) and record.get('model_sha256') == expected[role],
                'Reference model identity differs: ' + role)
        for direction in ('input', 'output'):
            tensor = record.get(direction, {})
            require(isinstance(tensor, dict) and tensor.get('dtype') == 'float32'
                    and isinstance(tensor.get('shape'), list) and tensor['shape']
                    and all(type(v) is int and 0 < v <= 1_000_000 for v in tensor['shape'])
                    and isinstance(tensor.get('sha256'), str) and SHA.fullmatch(tensor['sha256']),
                    'Invalid reference tensor contract: ' + role)
        values = record['output'].get('values')
        require(isinstance(values, list) and values and len(values) <= 1_000_000
                and math.prod(record['output']['shape']) == len(values)
                and all(type(v) in (float, int) and math.isfinite(v) for v in values),
                'Invalid reference output values: ' + role)
    return reference


def verify_kit(kit):
    kit = Path(kit).absolute()
    actual, directories = tree(kit)
    require('inventory.json' in actual and 'kit.json' in actual, 'Missing kit manifests')
    inventory, config = json_object(kit / 'inventory.json'), json_object(kit / 'kit.json')
    for record in (inventory, config):
        require(type(record.get('schema_version')) is int and record['schema_version'] == 1
                and record.get('kind') == 'pi4_research_preparation' and record.get('pi_verified') is False,
                'Unsupported preparation kit metadata')
    require(config.get('status') == 'research_only' and config.get('candidate_only') is True
            and config.get('dependencies_included') is True,
            'Kit must preserve research/candidate status')
    payload = entries(inventory.get('files'), sizes=True)
    require(set(actual) == set(payload) | {'inventory.json'}, 'Kit inventory membership mismatch')
    expected_dirs = {p.as_posix() for name in payload for p in PurePosixPath(name).parents if str(p) != '.'}
    require(directories == expected_dirs, 'Unlisted kit directory')
    for name, record in payload.items():
        checked_path(name)
        require(actual[name].stat().st_size == record['bytes'] and digest(actual[name]) == record['sha256'],
                'Kit file changed: ' + name)
    allowlisted = FIXED | {'tools/' + name for name in TOOLS}
    allowlisted.update(name for name in actual if name.startswith('station/'))
    allowlisted.update(name for name in actual if re.fullmatch(r'wheels/[^/]+\.whl', name))
    require(set(payload) == allowlisted, 'Unsupported or missing kit payload family')
    require(config.get('profile') == 'config/profile.json'
            and config.get('requirements') == 'requirements/runtime-candidate.lock.txt'
            and config.get('reference') == 'reference/model-probe.json', 'Unsupported kit configuration paths')
    station = verify_station(kit / 'station')
    station_sha = digest(kit / 'station/station-inventory.json')
    require(config.get('station_inventory_sha256') == station_sha, 'Configured station identity differs')
    profile = json_object(kit / 'config/profile.json')
    validate_reference(json_object(kit / 'reference/model-probe.json'), kit / 'station')
    wheels = validate_wheels(kit / 'wheels', read_lock(kit / 'requirements/runtime-candidate.lock.txt'), profile)
    require(config.get('wheel_packages') == wheels, 'Configured wheel metadata differs')
    return {'status': 'passed', 'kind': 'pi4_research_preparation', 'payload_files': len(payload),
            'payload_bytes': sum(row['bytes'] for row in payload.values()),
            'station_inventory_sha256': station_sha, 'station': station,
            'target': profile['target'], 'wheel_packages': wheels,
            'pi_verified': False, 'runtime_verified': False, 'full_live_acceptance': False,
            'limits': 'Hashes, wheel metadata and synthetic reference only; no ARM64 install or device execution verified.'}


def build(station, wheelhouse, lock, reference, profile, guide, output, root=ROOT):
    root, output = Path(root).absolute(), Path(output).absolute()
    inputs = [Path(value).absolute() for value in (station, wheelhouse, lock, reference, profile, guide)]
    station, wheelhouse, lock, reference, profile, guide = inputs
    require(not output.exists(), 'Refusing to overwrite preparation kit')
    for path in (root, *inputs):
        no_links(path)
    for parent in output.parents:
        if parent.exists():
            no_links(parent)
    immutable = inputs + [root / 'tools']
    require(all(not output.resolve().is_relative_to(path.resolve() if path.is_dir() else path.parent.resolve())
                for path in immutable), 'Output must not be inside immutable input directories')
    verify_station(station)
    source_files, _ = tree(station)
    candidate = json_object(profile)
    wheels = validate_wheels(wheelhouse, read_lock(lock), candidate)
    validate_reference(json_object(reference), station)
    sources = {'station/' + name: path for name, path in source_files.items()}
    sources.update({'tools/' + name: root / 'tools' / name for name in TOOLS})
    sources.update({'INSTALL_PI4.md': guide, 'config/profile.json': profile,
                    'reference/model-probe.json': reference, 'requirements/runtime-candidate.lock.txt': lock})
    sources.update({row['path']: wheelhouse / Path(row['path']).name for row in wheels})
    for path in sources.values():
        no_links(path)
        require(path.is_file(), 'Required kit source is missing')
    # Validate all inputs before creating any output. Failed copies remain explicit partial output.
    output.mkdir(parents=True, exist_ok=False)
    for relative, path in sorted(sources.items()):
        target = output / checked_path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        with path.open('rb') as incoming, target.open('xb') as outgoing:
            shutil.copyfileobj(incoming, outgoing)
        require(digest(path) == digest(target), 'Input changed while copying kit')
    config = {'schema_version': 1, 'kind': 'pi4_research_preparation', 'status': 'research_only',
              'candidate_only': True, 'pi_verified': False, 'dependencies_included': True,
              'profile': 'config/profile.json', 'requirements': 'requirements/runtime-candidate.lock.txt',
              'reference': 'reference/model-probe.json', 'station_inventory_sha256': digest(station / 'station-inventory.json'),
              'wheel_packages': wheels,
              'limits': ['ARM64 wheels are candidates until installed and invoked on the target Pi 4',
                         'No accepted fabric, calibrated length, camera or Pi performance claims']}
    with (output / 'kit.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(config, stream, indent=2); stream.write('\n')
    payload, _ = tree(output)
    inventory = {'schema_version': 1, 'kind': 'pi4_research_preparation', 'pi_verified': False,
                 'files': [{'path': name, 'bytes': path.stat().st_size, 'sha256': digest(path)}
                           for name, path in sorted(payload.items())]}
    with (output / 'inventory.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(inventory, stream, indent=2); stream.write('\n')
    return verify_kit(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    make = commands.add_parser('build')
    for name in ('station', 'wheelhouse', 'lock', 'reference', 'profile', 'guide', 'output'):
        make.add_argument('--' + name, type=Path, required=True)
    make.add_argument('--root', type=Path, default=ROOT)
    check = commands.add_parser('verify'); check.add_argument('kit', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'build':
            result = build(args.station, args.wheelhouse, args.lock, args.reference,
                           args.profile, args.guide, args.output, args.root)
        else:
            result = verify_kit(args.kit)
        print(json.dumps(result, indent=2)); return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc), 'pi_verified': False})); return 1


if __name__ == '__main__':
    raise SystemExit(main())
