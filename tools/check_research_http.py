"""Verify opt-in fabric/pose HTTP integration with saved images, no camera."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--port', type=int, default=18767)
    a = p.parse_args()
    bundle, output = a.bundle.resolve(), a.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    subprocess.run([sys.executable, str(ROOT/'tools/verify_release.py'), str(bundle), '--require-app'], check=True)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', a.port))
    address = f'http://127.0.0.1:{a.port}'
    def request(path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        with urlopen(Request(address+path, data=data, headers={'Content-Type':'application/json'}), timeout=10) as r:
            return json.load(r)
    def analyze(raw, enabled, presentation='worn'):
        job = request('/api/live', {'image_base64':base64.b64encode(raw).decode(),
                                   'fabric_enabled':enabled, 'presentation':presentation})
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            result = request('/api/jobs?id='+job['id'])
            if result['state'] == 'complete':
                return result['result']
            if result['state'] != 'pending':
                raise RuntimeError('Unexpected job state')
            time.sleep(.05)
        raise TimeoutError('Saved-frame inference did not complete')
    cases_path = ROOT/'records/validation/2026-10-17-fabric-automatic.json'
    cases = [r for r in json.loads(cases_path.read_text())['predictions'] if r['automatic'] is not None][:2]
    checks = []
    with output.with_suffix('.server.log').open('x') as log:
        child = subprocess.Popen([sys.executable, '-B', '-m', 'app.server', '--bundle', str(bundle),
            '--root', str(ROOT), '--port', str(a.port), '--no-review',
            '--experimental-localizer', str(ROOT/'artifacts/models/skirt-localizer-v1'),
            '--experimental-pose', str(ROOT/'artifacts/models/movenet-lightning-f16-v4'),
            '--experimental-fabric', str(ROOT/'artifacts/models/fabric-smoke-v1')],
            cwd=bundle, env=dict(os.environ, CUDA_VISIBLE_DEVICES='-1', PYTHONDONTWRITEBYTECODE='1'),
            stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 60
            while True:
                if child.poll() is not None:
                    raise RuntimeError('Research server exited')
                try:
                    request('/api/status')
                    break
                except OSError:
                    pass
                if time.monotonic() > deadline:
                    raise TimeoutError('Research server startup timeout')
                time.sleep(.2)
            for case in cases:
                raw = (ROOT/case['original_path']).read_bytes()
                if hashlib.sha256(raw).hexdigest() != case['image_sha256']:
                    raise ValueError('Original hash mismatch')
                off, on = analyze(raw, False), analyze(raw, True)
                assert off['fabric']['status'] == 'disabled'
                assert on['fabric']['status'] == 'research_only'
                assert on['fabric']['label'] == case['automatic']['label']
                assert on['fabric']['live_approved'] is False
                assert off['style'] == on['style']
                pose = on['metadata']['wearer_pose']
                assert pose['status'] == 'provisional_landmark_candidates'
                assert pose['frame_id'] == on['fabric']['source_frame_id']
                assert pose['geometry_eligible'] is False
                assert not any(point['observed'] for point in pose['landmarks'])
                assert on['length']['status'] == 'unavailable'
                checks.append({'sample_id':case['sample_id'], 'toggle_and_same_frame_passed':True,
                               'fabric_label':on['fabric']['label'], 'length_unavailable':True})
            secondary = analyze(raw, True, 'held')
            assert 'wearer_pose' not in secondary['metadata']
        finally:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
    subprocess.run([sys.executable, str(ROOT/'tools/verify_release.py'), str(bundle), '--require-app'], check=True)
    report = {'date_asia_manila':'2026-10-17', 'status':'passed', 'checks':checks,
              'secondary_mode_skips_wearer_pose':True, 'server_stopped':child.poll() is not None,
              'camera_used':False, 'pi_verified':False,
              'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'reference_sha256':hashlib.sha256(cases_path.read_bytes()).hexdigest(),
              'limitations':['Saved-image HTTP integration only; not new recognition accuracy or camera evidence',
                             'Research models remain unapproved; pose does not enable calibrated length']}
    with output.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
