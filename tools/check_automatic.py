"""Evaluate the experimental automatic crop on frozen development originals."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image
from app.inference import SkirtPredictor
from app.localization import AutomaticPredictor, SkirtLocalizer

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    manifest = ROOT / 'data/labels/skirt-baseline-v1.jsonl'
    rows = [json.loads(line) for line in manifest.read_text().splitlines()]
    rows = [r for r in rows if r['split'] == 'development_validation']
    localizer = SkirtLocalizer(ROOT / 'artifacts/models/skirt-localizer-v1')
    predictor = AutomaticPredictor(SkirtPredictor(ROOT / 'artifacts/releases/skirt-finetune-v1-desktop-async-v2'), localizer)
    results = []
    for row in rows:
        path = ROOT / row['original_path']
        if digest(path) != row['sha256']:
            raise ValueError('Source hash changed: ' + row['sample_id'])
        with Image.open(path) as image:
            result = predictor.predict(image.convert('RGB'), {'fabric_enabled': False, 'presentation': 'worn'})
        region = result['metadata']['localization']
        overlap = None
        if region['roi']:
            x, y, w, h = row['source_labels']['bbox']
            a, b, c, d = region['roi']
            intersection = max(0, min(c, x+w)-max(a, x))*max(0, min(d, y+h)-max(b, y))
            overlap = intersection / ((c-a)*(d-b)+w*h-intersection)
        results.append({'sample_id': row['sample_id'], 'expected': row['label'],
                        'bbox_iou': overlap, 'prediction': result})
    accepted = [r for r in results if r['prediction']['style']['label'] is not None]
    correct = sum(r['expected'] == r['prediction']['style']['label'] for r in accepted)
    diagnostics = []
    for value in (0, 128, 255):
        result = predictor.predict(Image.new('RGB', (640, 480), (value,)*3),
                                   {'fabric_enabled': False, 'presentation': 'hanging'})
        diagnostics.append({'synthetic_uniform_rgb': value, 'prediction': result})
    output = {'date_utc': datetime.now(timezone.utc).isoformat(),
              'source_sha256': digest(Path(__file__)), 'manifest_sha256': digest(manifest),
              'localizer_sha256': localizer.sha256, 'validation_images': len(rows),
              'accepted': len(accepted), 'correct_accepted': correct,
              'coverage': len(accepted)/len(rows),
              'accepted_accuracy': correct/len(accepted) if accepted else None,
              'correct_over_all_eligible': correct/len(rows),
              'mean_bbox_iou_accepted': sum(r['bbox_iou'] for r in accepted)/len(accepted) if accepted else None,
              'reasons': dict(Counter(r['prediction']['metadata']['localization']['reason'] for r in results)),
              'results': results, 'synthetic_diagnostics': diagnostics,
              'limitations': ['Development evaluation; labels await independent human review',
                             'No real negative scenes evaluated; uniform images are diagnostics only',
                             'No camera, geometry, fabric or Raspberry Pi verification',
                             'Decoder thresholds uncalibrated; no final test data accessed']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(output, stream, indent=2, allow_nan=False)
    print(json.dumps({k:v for k,v in output.items() if k not in ('results','synthetic_diagnostics')}))

if __name__ == '__main__':
    main()
