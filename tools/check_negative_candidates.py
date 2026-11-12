"""Measure candidate acceptance on annotation-selected development negatives.

This does not certify absent skirts or estimate final camera false acceptance.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image
from app.localization import SkirtLocalizer

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    path = ROOT / 'data/manifests/negative-candidates-v1.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    localizer = SkirtLocalizer(ROOT / 'artifacts/models/skirt-localizer-v1')
    predictions = []
    for row in rows:
        source = ROOT / row['original_path']
        if hashlib.sha256(source.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Candidate image changed')
        with Image.open(source) as im: result = localizer.locate(im.convert('RGB'))
        predictions.append({'sample_id':row['sample_id'], 'localization':result})
    accepted = sum(r['localization']['status'] == 'provisional' for r in predictions)
    report = {'date_utc':datetime.now(timezone.utc).isoformat(), 'candidate_images':len(rows),
              'provisional_roi_count':accepted, 'candidate_acceptance_rate':accepted/len(rows),
              'reasons':dict(Counter(r['localization']['reason'] for r in predictions)),
              'localizer_sha256':localizer.sha256, 'runtime':localizer.runtime,
              'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'decoder_sha256':hashlib.sha256((ROOT/'app/localization.py').read_bytes()).hexdigest(),
              'threshold_changed':False, 'training_performed':False,
              'predictions':predictions,
              'limits':['Source train2020 images with no annotated skirt; not certified absence',
                        'Development diagnostic, not locked test or camera-domain accuracy',
                        'No thresholds fitted; no model promoted']}
    with args.output.open('x', encoding='utf-8') as stream: json.dump(report, stream, indent=2)
    print(json.dumps({k:v for k,v in report.items() if k != 'predictions'}))

if __name__ == '__main__': main()
