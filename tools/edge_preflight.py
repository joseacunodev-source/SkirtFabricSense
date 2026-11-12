"""Read-only Pi installation preflight; never installs or declares deployment verified."""
import argparse
from datetime import datetime, timedelta, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.verify_release import verify


def assess(observation):
    blockers = []
    if observation['system'] != 'Linux':
        blockers.append('Linux target OS required')
    if observation['machine'].lower() not in ('aarch64', 'arm64') or observation['pointer_bits'] != 64:
        blockers.append('64-bit ARM target environment required')
    if not observation['board_model'].startswith('Raspberry Pi'):
        blockers.append('Raspberry Pi board identity not observed')
    for package in ('numpy', 'Pillow'):
        if not observation['packages'].get(package):
            blockers.append('Missing application distribution: '+package)
    runtimes = [name for name in ('ai-edge-litert', 'tflite-runtime', 'tensorflow')
                if observation['packages'].get(name)]
    if not runtimes:
        blockers.append('No candidate inference runtime distribution installed')
    return {'platform_and_distribution_checks_passed': not blockers, 'blockers': blockers,
            'runtime_distributions': runtimes, 'pi_verified': False,
            'remaining_checks': ['Import the chosen runtime API and invoke all required model operators',
                                 'Compare permitted reference inputs with desktop outputs',
                                 'Verify camera, calibration, display and browser behavior',
                                 'Benchmark offline operation, load, temperature, reboot and recovery'],
            'limitations': 'Distribution presence does not establish ABI, import or operator compatibility.'}


def collect():
    packages = {}
    for name in ('numpy', 'Pillow', 'ai-edge-litert', 'tflite-runtime', 'tensorflow'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    board = Path('/sys/firmware/devicetree/base/model')
    return {'system': platform.system(), 'machine': platform.machine(),
            'pointer_bits': struct.calcsize('P') * 8, 'python': platform.python_version(),
            'python_executable': sys.executable, 'libc': list(platform.libc_ver()),
            'board_model': board.read_text(errors='replace').rstrip('\x00\n') if board.is_file() else '',
            'packages': packages}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    observation = collect()
    report = {'recorded_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'observations': observation, **assess(observation)}
    try:
        report['bundle'] = verify(a.bundle, require_app=True)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        report['blockers'].append('Bundle verification failed: '+str(exc))
        report['platform_and_distribution_checks_passed'] = False
    report['status'] = 'preflight_checks_passed_more_verification_required' if not report['blockers'] else 'preflight_requirements_unmet'
    with a.output.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps(report, indent=2))
    return 0 if not report['blockers'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
