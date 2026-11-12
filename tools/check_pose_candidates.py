"""Run optional body-keypoint candidates on saved development originals only."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image
from app.pose import PoseCandidates


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    rows = [json.loads(line) for line in (ROOT/'data/labels/skirt-baseline-v1.jsonl').read_text().splitlines()]
    # First six training examples; no final-test images or fitted thresholds.
    rows = [r for r in rows if r['split'] == 'development_train'][:6]
    model = PoseCandidates(ROOT/'artifacts/models/movenet-lightning-f16-v4')
    results = []
    for row in rows:
        path = ROOT / row['original_path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Original changed')
        with Image.open(path) as im:
            image = im.convert('RGB')
        start = time.monotonic()
        result = model.detect(image, row['sample_id'])
        results.append({'sample_id': row['sample_id'], 'image_sha256': row['sha256'],
                        'elapsed_seconds': time.monotonic() - start, 'output': result})
    report = {'date_asia_manila': '2026-10-17', 'status': 'passed', 'model_sha256': model.sha256,
              'runtime': model.runtime, 'tool_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'adapter_sha256': hashlib.sha256((ROOT/'app/pose.py').read_bytes()).hexdigest(),
              'model_contract_sha256': hashlib.sha256((ROOT/'artifacts/models/movenet-lightning-f16-v4/contract.json').read_bytes()).hexdigest(),
              'results': results, 'camera_used': False, 'pi_verified': False,
              'limitations': ['Six training-source images; invocation/contract check only',
                             'No landmark ground truth or accuracy measurement',
                             'Unverified visibility, wearer association, waist or floor contact',
                             'CPU timings include preprocessing; not target-Pi latency']}
    with a.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'status': 'passed', 'saved_images': len(results), 'geometry_eligible': False}))


if __name__ == '__main__':
    main()
