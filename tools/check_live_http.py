"""Check the live HTTP adapter with three saved development frames, not a camera."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8766')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    def request(path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        with urlopen(Request(args.url+path, data=data, headers={'Content-Type':'application/json'}), timeout=10) as response:
            return json.load(response)
    reference = ROOT / 'records/validation/2026-10-10-automatic-pilot.json'
    expected = json.loads(reference.read_text())['results'][:3]
    rows = {r['sample_id']:r for r in map(json.loads, (ROOT / 'data/labels/skirt-baseline-v1.jsonl').read_text().splitlines())}
    checks = []
    for case in expected:
        row = rows[case['sample_id']]
        raw = (ROOT / row['original_path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Changed source image')
        payload = {'image_base64':base64.b64encode(raw).decode(), 'fabric_enabled':False, 'presentation':'worn'}
        job = request('/api/live', payload)
        deadline = time.monotonic()+10
        while True:
            result = request('/api/jobs?id='+job['id'])
            if result['state'] != 'pending':
                break
            if time.monotonic() > deadline:
                raise TimeoutError('Live HTTP job did not complete')
            time.sleep(.05)
        if result['state'] != 'complete' or result['result'] != case['prediction']:
            raise AssertionError('Live HTTP output differs from archived automatic output')
        checks.append({'sample_id':row['sample_id'], 'exact_match':True})
    report = {'status':'passed', 'checks':checks,
              'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
              'limits':'Three saved development images; HTTP integration only, not new accuracy or camera/Pi performance evidence'}
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report))

if __name__ == '__main__':
    main()
