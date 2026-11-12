"""Launch a private desktop bundle process and compare saved-frame HTTP results."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--port', type=int, default=18766)
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    if args.output.exists():
        raise FileExistsError(args.output)
    subprocess.run([sys.executable, str(ROOT/'tools/verify_release.py'), str(bundle), '--require-app'], check=True)
    address = f'http://127.0.0.1:{args.port}'
    # Never accidentally test an already-running user's server.
    import socket
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', args.port))
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='-1', PYTHONDONTWRITEBYTECODE='1')
    log = args.output.with_suffix('.server.log')
    with log.open('x') as stream:
        child = subprocess.Popen([sys.executable, '-B', '-m', 'app.server', '--bundle', str(bundle),
            '--root', str(ROOT), '--port', str(args.port), '--no-review', '--experimental-localizer',
            str(ROOT/'artifacts/models/skirt-localizer-v1')], cwd=bundle, env=env, stdout=stream, stderr=stream)
        try:
            deadline = time.monotonic() + 60
            while True:
                if child.poll() is not None:
                    raise RuntimeError('Bundle server exited; inspect saved log')
                try:
                    with urlopen(address, timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    pass
                if time.monotonic() >= deadline:
                    raise TimeoutError('Bundle startup timeout')
                time.sleep(.2)
            subprocess.run([sys.executable, str(ROOT/'tools/check_live_http.py'), '--url', address,
                            '--output', str(args.output.resolve())], check=True)
        finally:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
    subprocess.run([sys.executable, str(ROOT/'tools/verify_release.py'), str(bundle), '--require-app'], check=True)
    print(json.dumps({'status':'passed', 'camera_used':False, 'server_stopped':child.poll() is not None}))


if __name__ == '__main__':
    main()
