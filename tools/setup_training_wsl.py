"""One-time recorded Ubuntu training setup; run as WSL root, packages in user venv."""
import datetime
import atexit
import json
import os
from pathlib import Path
import pwd
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ENV = '/home/skirttrain/skirt-fabric-sense/.venv-training'
RECORDS = ROOT / 'records/package-installs'
STAMP = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')


def capture_exit_inventory():
    """Keep partial environment evidence even when installation exits early."""
    interpreter = ENV + '/bin/python' if Path(ENV + '/bin/python').exists() else sys.executable
    folder = ROOT / 'records/environments'
    snapshot = folder / (STAMP + '-exit-inventory.json')
    subprocess.run([interpreter, str(ROOT/'tools/collect_environment.py'), '--role',
                    'training-wsl-setup-exit', '--output', str(snapshot)], check=False)
    with (folder / (STAMP + '-exit-freeze.txt')).open('x') as stream:
        subprocess.run([interpreter, '-m', 'pip', 'freeze', '--all'], stdout=stream,
                       stderr=subprocess.STDOUT, check=False)
    with (folder / (STAMP + '-exit-dpkg.txt')).open('x') as stream:
        subprocess.run(['dpkg-query', '-W'], stdout=stream, check=False)


def run(name, command, role='training-wsl'):
    path = RECORDS / f'{STAMP}-{name}.txt'
    with path.open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    entry = dict(recorded_at=datetime.datetime.now().astimezone().isoformat(),
                 environment_role=role, action=name, command=command,
                 status='succeeded' if result.returncode == 0 else 'failed',
                 exit_code=result.returncode, evidence=str(path.relative_to(ROOT)),
                 verification='Command exit status; package versions in pip reports and final inventory')
    with (ROOT / 'records/installations.jsonl').open('a') as stream:
        stream.write(json.dumps(entry) + '\n')
    print(name, result.returncode, str(path), flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == '__main__':
    if os.geteuid() != 0:
        raise SystemExit('Run as WSL root; package commands execute as skirttrain')
    atexit.register(capture_exit_inventory)
    run('apt-update', ['apt-get', 'update'])
    run('apt-install', ['apt-get', 'install', '-y', 'python3-venv', 'python3-pip'])
    try:
        pwd.getpwnam('skirttrain')
    except KeyError:
        run('create-training-user', ['useradd', '--create-home', '--shell', '/bin/bash', 'skirttrain'])
    prefix = ['runuser', '-u', 'skirttrain', '--']
    run('create-training-directory', prefix + ['mkdir', '-p', '/home/skirttrain/skirt-fabric-sense'])
    if Path(ENV).exists():
        raise SystemExit('Training environment exists; inspect before resuming installations')
    run('create-training-venv', prefix + ['python3', '-m', 'venv', ENV])
    run('pip-upgrade', prefix + [ENV+'/bin/python', '-m', 'pip', 'install', '--upgrade', 'pip',
                                '--report', str(RECORDS / (STAMP+'-pip.json'))])
    run('tensorflow-install', prefix + [ENV+'/bin/python', '-m', 'pip', 'install',
        'tensorflow[and-cuda]==2.20.0', 'Pillow==12.3.0', '--report', str(RECORDS / (STAMP+'-tensorflow.json'))])
    run('pip-check', prefix + [ENV+'/bin/python', '-m', 'pip', 'check'])
    run('environment-snapshot', prefix + [ENV+'/bin/python', str(ROOT/'tools/collect_environment.py'),
        '--role', 'training-wsl', '--output', str(ROOT/'records/environments'/ (STAMP+'-training-wsl.json'))])
    with (ROOT/'requirements/training-wsl-py312-freeze.txt').open('x') as stream:
        subprocess.run([ENV+'/bin/python', '-m', 'pip', 'freeze', '--all'], stdout=stream, check=True)
    with (ROOT/'records/environments'/ (STAMP+'-ubuntu-packages.txt')).open('x') as stream:
        subprocess.run(['dpkg-query', '-W'], stdout=stream, check=True)
