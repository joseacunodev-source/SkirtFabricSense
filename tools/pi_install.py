"""Plan or install a verified offline research kit on its explicitly selected Pi 4 profile."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import struct
import subprocess
import sys
import uuid


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def observe():
    board = Path('/sys/firmware/devicetree/base/model')
    release = Path('/etc/os-release')
    fields = {}
    if release.is_file():
        for line in release.read_text().splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                fields[key] = value.strip('"')
    return {'system': platform.system(), 'machine': platform.machine(),
            'pointer_bits': struct.calcsize('P') * 8,
            'python': list(sys.version_info[:2]), 'libc': list(platform.libc_ver()),
            'board': board.read_text().rstrip('\x00\n') if board.is_file() else '',
            'os_codename': fields.get('VERSION_CODENAME'),
            'effective_uid': os.geteuid() if hasattr(os, 'geteuid') else None}


def blockers(observation, profile):
    target = profile['target']
    problems = []
    if observation['system'] != 'Linux': problems.append('Linux is required')
    if observation['machine'].lower() not in ('aarch64', 'arm64') or observation['pointer_bits'] != 64:
        problems.append('64-bit ARM userspace is required')
    if not observation['board'].startswith('Raspberry Pi 4 '):
        problems.append('Raspberry Pi 4 Model B identity is required for this profile')
    if '.'.join(map(str, observation['python'])) != target['python']:
        problems.append('System CPython '+target['python']+' is required; do not replace OS Python')
    if observation['os_codename'] != target.get('os_codename', 'trixie'):
        problems.append('This candidate is restricted to the recorded Trixie OS profile')
    if observation['effective_uid'] == 0:
        problems.append('Run as the normal desktop user, not root/sudo')
    try:
        libc_name, libc_version = observation['libc']
        actual = tuple(int(part) for part in libc_version.split('.')[:2])
        required = tuple(int(part) for part in target.get('min_glibc', '2.28').split('.'))
        if libc_name != 'glibc' or actual < required: raise ValueError
    except (TypeError, ValueError, KeyError):
        problems.append('glibc '+target.get('min_glibc', '2.28')+' or newer is required')
    return problems


def verify_kit(path):
    module = importlib.import_module('tools.pi_kit' if __package__ else 'pi_kit')
    return module.verify_kit(path)


def no_links(path):
    if any(ord(char) < 32 or ord(char) == 127 for char in str(path)):
        raise ValueError('Control characters are not supported in installation paths')
    for item in (path, *path.parents):
        if item.is_symlink() or (item.exists() and getattr(item.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('Symlinks/junctions are not allowed: '+str(item))


def locations(kit, destination, records):
    original = [Path(p).absolute() for p in (kit, destination, records)]
    for path in original: no_links(path)
    kit, destination, records = [p.resolve() for p in original]
    if destination.exists(): raise ValueError('Choose a new destination; existing releases are preserved')
    if not destination.is_relative_to(Path.home().resolve()):
        raise ValueError('Use a destination under the current desktop user home')
    if destination.is_relative_to(kit) or kit.is_relative_to(destination):
        raise ValueError('Destination and input kit must be separate')
    if records.is_relative_to(kit) or records.is_relative_to(destination):
        raise ValueError('Keep installation records outside the immutable kit and release')
    return kit, destination, records


def plan(kit, destination, records, observation=None, fabric_research=False):
    kit, destination, records = locations(kit, destination, records)
    verified = verify_kit(kit)
    profile = json.loads((kit/'config/profile.json').read_text())
    observation = observe() if observation is None else observation
    problems = blockers(observation, profile)
    return {'status': 'blocked' if problems else 'planned_not_installed',
            'pi_verified': False, 'full_live_acceptance': False,
            'kit': str(kit), 'destination': str(destination), 'records': str(records),
            'observation': observation, 'profile': profile, 'kit_verification': verified,
            'blockers': problems, 'fabric_research': fabric_research,
            'operations': ['Copy verified kit into new release', 'Create isolated venv',
                           'Install local hash-pinned wheels without network or source builds',
                           'Check dependencies and record installed versions/environment',
                           'Invoke all four models and compare with desktop synthetic reference',
                           'Generate inactive user service and desktop kiosk files'],
            'not_automated': ['OS image flashing, APT packages or system upgrades',
                              'Enabling services, desktop autologin or camera permissions',
                              'Camera/display/calibration/live performance acceptance']}


def unit_argument(value):
    if any(ord(char) < 32 or ord(char) == 127 for char in str(value)):
        raise ValueError('Control characters are not supported in startup arguments')
    return '"'+str(value).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%')+'"'


def desktop_argument(value):
    no_links(Path(value))
    # Desktop Entry value unescaping occurs before Exec argument unescaping.
    escaped = str(value).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    return '"'+escaped.replace('\\', '\\\\').replace('%', '%%')+'"'


def startup_files(destination, record_dir, fabric_research=False):
    """Generate inactive files; never alter systemd or desktop session settings."""
    destination, record_dir = Path(destination), Path(record_dir)
    no_links(destination); no_links(record_dir)
    python = destination/'venv/bin/python'
    station = destination/'kit/station'
    command = [python, '-B', station/'station_package.py', 'launch', station, '--port', '8766']
    if fabric_research: command.append('--fabric-research')
    unit = ('[Unit]\nDescription=SkirtFabricSense research backend\n\n'
            '[Service]\nType=simple\nWorkingDirectory='+unit_argument(station)+'\n'
            'ExecStart='+' '.join(unit_argument(str(arg).replace('$', '$$')) for arg in command)+'\n'
            'Environment=PYTHONDONTWRITEBYTECODE=1\nRestart=on-failure\nRestartSec=5\n'
            'TimeoutStopSec=15\nNoNewPrivileges=true\nUMask=0077\n\n'
            '[Install]\nWantedBy=default.target\n')
    (record_dir/'skirtfabric.service').write_text(unit, encoding='utf-8')
    kiosk = ('#!/bin/sh\nset -eu\n'
             'if [ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then\n'
             '  echo "Start kiosk from the logged-in graphical desktop." >&2; exit 1\nfi\n'
             'if command -v chromium >/dev/null 2>&1; then browser=chromium\n'
             'elif command -v chromium-browser >/dev/null 2>&1; then browser=chromium-browser\n'
             'else echo "Chromium is not installed." >&2; exit 1\nfi\n'
             + shlex.quote(str(python))+" - <<'SKIRT_READY'\n"
             'import json,time,urllib.request\n'
             'deadline=time.monotonic()+60\n'
             'while time.monotonic()<deadline:\n'
             '    try:\n'
             '        with urllib.request.urlopen("http://127.0.0.1:8766/api/status",timeout=2) as response:\n'
             '            if json.loads(response.read(4096)).get("status")=="ready": break\n'
             '    except (OSError,ValueError): pass\n'
             '    time.sleep(1)\n'
             'else: raise SystemExit("Backend not ready; inspect the user service log.")\n'
             'SKIRT_READY\n'
             'exec "$browser" --kiosk --no-first-run '
             '--user-data-dir="${XDG_DATA_HOME:-$HOME/.local/share}/skirtfabric-browser" '
             'http://127.0.0.1:8766/\n')
    script = record_dir/'start-skirtfabric-kiosk.sh'
    script.write_text(kiosk, encoding='utf-8'); script.chmod(0o700)
    desktop = ('[Desktop Entry]\nType=Application\nName=SkirtFabricSense research station\n'
               'Exec='+desktop_argument(script)+'\nTerminal=false\n')
    (record_dir/'skirtfabric.desktop').write_text(desktop, encoding='utf-8')
    return ['skirtfabric.service', 'start-skirtfabric-kiosk.sh', 'skirtfabric.desktop']


def install(kit, destination, records, fabric_research=False):
    proposed = plan(kit, destination, records, fabric_research=fabric_research)
    if proposed['blockers']: raise ValueError('; '.join(proposed['blockers']))
    kit, destination, records = map(Path, (proposed['kit'], proposed['destination'], proposed['records']))
    records.mkdir(parents=True, exist_ok=True)
    run = records/('install-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8])
    run.mkdir(); write_json(run/'plan.json', proposed)
    ledger = records/'installations.jsonl'
    stages = []

    def stage(name, command, check=True):
        try:
            result = subprocess.run([str(x) for x in command], capture_output=True, text=True, timeout=600,
                                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        except (OSError, subprocess.SubprocessError) as exc:
            result = subprocess.CompletedProcess(command, -1, '', str(exc))
        (run/(name+'.log')).write_text(result.stdout+'\n'+result.stderr, encoding='utf-8')
        event = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'environment_role': 'edge-pi4',
                 'action': name, 'command': list(map(str, command)), 'exit_code': result.returncode,
                 'status': 'succeeded' if result.returncode == 0 else 'failed',
                 'requested_runtime': proposed['profile']['runtime'],
                 'verification_log': str(run/(name+'.log')),
                 'version_evidence': str(run/'installed-versions.json'),
                 'environment_snapshot': str(run/'environment.json')}
        with ledger.open('a', encoding='utf-8') as stream: stream.write(json.dumps(event)+'\n')
        stages.append(event)
        if check and result.returncode: raise RuntimeError(name+' failed; see '+event['verification_log'])
        return result

    status, error = 'failed', None
    try:
        destination.mkdir(parents=True, exist_ok=False)
        shutil.copytree(kit, destination/'kit', symlinks=False)
        verify_kit(destination/'kit')
        stage('create-venv', [sys.executable, '-m', 'venv', destination/'venv'])
        python = destination/'venv/bin/python'
        stage('install-wheels', [python, '-m', 'pip', 'install', '--no-index', '--only-binary=:all:',
                                '--find-links', destination/'kit/wheels', '--require-hashes', '-r',
                                destination/'kit/requirements/runtime-candidate.lock.txt'])
        stage('dependency-check', [python, '-m', 'pip', 'check'])
        versions = stage('installed-versions', [python, '-c',
            'import importlib.metadata,json; print(json.dumps({d.metadata["Name"]:d.version for d in importlib.metadata.distributions()}))'])
        installed = json.loads(versions.stdout)
        write_json(run/'installed-versions.json', installed)
        if not isinstance(installed, dict): raise ValueError('Installed version inventory is not an object')
        normalized = lambda name: re.sub(r'[-_.]+', '-', name).lower()
        actual = {normalized(name): version for name, version in installed.items()}
        expected = proposed['kit_verification']['wheel_packages']
        if not expected or any(actual.get(normalized(item['name'])) != item['version'] for item in expected):
            raise ValueError('Observed installed package versions differ from verified wheel inventory')
        stage('environment-snapshot', [python, '-B', destination/'kit/tools/collect_environment.py',
                                      '--role', 'edge-pi4', '--output', run/'environment.json'])
        stage('model-probe', [python, '-B', destination/'kit/tools/pi_probe.py', '--station',
                             destination/'kit/station', '--reference', destination/'kit/reference/model-probe.json',
                             '--output', run/'model-probe.json', '--iterations', '3'])
        probe = json.loads((run/'model-probe.json').read_text())
        if (not isinstance(probe, dict)
                or not isinstance(probe.get('parity'), dict)
                or not isinstance(probe.get('worker'), dict)
                or not isinstance(probe['worker'].get('models'), dict)
                or probe.get('status') != 'passed' or probe.get('pi_verified') is not False
                or probe.get('full_live_acceptance') is not False
                or probe.get('parity', {}).get('status') != 'passed'
                or probe.get('station_inventory_sha256') != proposed['kit_verification']['station_inventory_sha256']
                or set(probe.get('worker', {}).get('models', {})) != {'pleating','localizer','presence','fabric'}):
            raise ValueError('Model probe did not return the required research-only passing state')
        startup_files(destination, run, fabric_research)
        status = 'installed_model_checks_passed_physical_acceptance_open'
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        error = str(exc)
        # Best-effort snapshot after partial changes; never modify or remove failed release files.
        python = destination/'venv/bin/python'
        if python.is_file() and not (run/'environment.json').exists():
            try:
                stage('partial-environment-snapshot', [python, '-B', kit/'tools/collect_environment.py',
                      '--role', 'edge-pi4-partial', '--output', run/'environment.json'], check=False)
            except (OSError, subprocess.SubprocessError): pass
    report = {'status': status, 'pi_verified': False, 'full_live_acceptance': False,
              'destination': str(destination), 'records_directory': str(run), 'error': error,
              'stages': stages, 'service_enabled': False, 'camera_permission_granted': False,
              'limits': 'Synthetic model/parity installation gate only; independent labels, geometry, '
                        'camera/display, full frame age, sustained performance and reboot acceptance remain open.'}
    write_json(run/'installation-result.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'install'])
    parser.add_argument('--kit', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--records', type=Path, required=True)
    parser.add_argument('--fabric-research', action='store_true')
    args = parser.parse_args()
    try:
        result = (plan if args.action == 'plan' else install)(args.kit, args.destination, args.records,
                                                            fabric_research=args.fabric_research)
        print(json.dumps(result, indent=2, allow_nan=False))
        return int(result['status'] in ('blocked', 'failed'))
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc), 'pi_verified': False})); return 1


if __name__ == '__main__': raise SystemExit(main())
