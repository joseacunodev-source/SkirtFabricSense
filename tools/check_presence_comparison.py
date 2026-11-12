"""Paired fixed-threshold desktop evaluation; never tunes on validation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image
from app.inference import SkirtPredictor
from app.localization import SkirtLocalizer
from app.presence import PresenceGate
from tools.training.train_presence import validate

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--archive', type=Path, default=ROOT/'records/experiments/20261011-presence-v1')
    parser.add_argument('--candidate', type=Path, default=ROOT/'artifacts/models/skirt-presence-v1')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    archive = args.archive
    report = json.loads((archive / 'run.json').read_text())
    inputs = archive / 'inputs.json'
    if sha(inputs) != report['frozen_inputs_sha256']:
        raise ValueError('Frozen training inputs changed')
    if sha(archive / 'training_source.py') != report['source_sha256']:
        raise ValueError('Executed training source changed')
    rows = json.loads(inputs.read_text())
    validate(rows)
    rows = [r for r in rows if r['split'] == 'development_validation']
    localizer = SkirtLocalizer(ROOT / 'artifacts/models/skirt-localizer-v1')
    presence = PresenceGate(args.candidate)
    pleating = SkirtPredictor(ROOT / 'artifacts/releases/skirt-finetune-v1-desktop-async-v2')
    results = []
    for row in rows:
        path = ROOT / row['original_path']
        if sha(path) != row['sha256']:
            raise ValueError('Changed original: ' + row['sample_id'])
        with Image.open(path) as original:
            image = original.convert('RGB')
        region = localizer.locate(image)
        gate = presence.check(image)
        accepted = region['status'] == 'provisional'
        predicted = pleating.predict(image, tuple(region['roi']), True)['style']['label'] if accepted else None
        results.append({'sample_id': row['sample_id'], 'target': row['presence_target'],
                        'expected_pleating': row['label'] if row['presence_target'] else None,
                        'localizer': region, 'presence': gate, 'baseline_accepted': accepted,
                        'candidate_accepted': accepted and gate['accepted'], 'pleating_prediction': predicted})
    positive = [r for r in results if r['target'] == 1]
    negative = [r for r in results if r['target'] == 0]
    metrics = {}
    for name, key in [('baseline_localizer', 'baseline_accepted'), ('candidate_presence_plus_localizer', 'candidate_accepted')]:
        accepted = [r for r in positive if r[key]]
        correct = sum(r['pleating_prediction'] == r['expected_pleating'] for r in accepted)
        false_accepts = sum(r[key] for r in negative)
        metrics[name] = {'positive_count': len(positive), 'positive_accepted': len(accepted),
                         'positive_coverage': len(accepted) / len(positive), 'correct_pleating': correct,
                         'accepted_pleating_accuracy': correct / len(accepted) if accepted else None,
                         'correct_pleating_over_all_positive': correct / len(positive),
                         'negative_count': len(negative), 'negative_false_accepts': false_accepts,
                         'negative_rejected': len(negative) - false_accepts,
                         'negative_rejection': (len(negative) - false_accepts) / len(negative)}
    output = {'date_utc': datetime.now(timezone.utc).isoformat(), 'source_sha256': sha(__file__),
              'frozen_inputs_sha256': sha(inputs), 'split_hash': report['split_hash'],
              'models': {'localizer': localizer.sha256, 'presence': presence.sha256,
                         'pleating': sha(ROOT / 'artifacts/models/skirt-finetune-v1/model.tflite')},
              'presence_threshold': .5, 'metrics': metrics, 'results': results,
              'promotion': 'not promoted automatically; assess paired coverage and rejection with documented limits',
              'limitations': ['Paired development evaluation, not independent final testing',
                              f'Negative validation has {len(negative)} agent-reviewed originals; no human confirmation',
                              'Presence checkpoint selected on this validation pool; no threshold tuning here',
                              'Unchanged mask geometry; no camera, fabric, hemline or Raspberry Pi verification']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(output, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k: v for k, v in output.items() if k != 'results'}, indent=2))

if __name__ == '__main__':
    main()
