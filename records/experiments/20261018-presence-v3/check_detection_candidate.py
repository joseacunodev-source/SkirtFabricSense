"""Paired frozen development comparison of mask and presence combinations."""
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


def metrics(results, name):
    positive = [r for r in results if r['presence_target'] == 1]
    negative = [r for r in results if r['presence_target'] == 0]
    accepted = [r for r in positive if r['paths'][name]['accepted']]
    correct = sum(r['paths'][name]['pleating_prediction'] == r['expected_pleating'] for r in accepted)
    rejected = sum(not r['paths'][name]['accepted'] for r in negative)
    return {'positive_count':len(positive), 'positive_accepted':len(accepted),
            'positive_coverage':len(accepted)/len(positive), 'correct_pleating':correct,
            'accepted_pleating_accuracy':correct/len(accepted) if accepted else None,
            'negative_count':len(negative), 'negative_rejected':rejected,
            'negative_rejection':rejected/len(negative)}


def compare(candidate, baseline):
    return {'accepted_skirts_preserved':candidate['positive_accepted'] >= baseline['positive_accepted'],
            'correct_pleating_preserved':candidate['correct_pleating'] >= baseline['correct_pleating'],
            'negative_rejection_improved':candidate['negative_rejected'] > baseline['negative_rejected']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--presence', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    run = json.loads((a.archive/'run.json').read_text())
    inputs = a.archive/'inputs.json'
    if run['status'] != 'completed' or sha(inputs) != run['frozen_inputs_sha256']:
        raise ValueError('Incomplete run or changed frozen inputs')
    for source in run['executed_sources']:
        if sha(a.archive/source['path']) != source['sha256']:
            raise ValueError('Executed source changed')
    rows = json.loads(inputs.read_text())
    validate(rows)
    rows = [r for r in rows if r['split'] == 'development_validation']
    masks = {name:SkirtLocalizer(ROOT/f'artifacts/models/skirt-localizer-{name}') for name in ('v1', 'v2')}
    gate = PresenceGate(a.presence)
    if gate.sha256 != run['export']['sha256']:
        raise ValueError('Presence model differs from archived run')
    pleating = SkirtPredictor(ROOT/'artifacts/releases/skirt-finetune-v1-desktop-research-v7')
    results = []
    for row in rows:
        path = ROOT/row['original_path']
        if sha(path) != row['sha256']:
            raise ValueError('Original changed')
        with Image.open(path) as im:
            image = im.convert('RGB')
        presence = gate.check(image)
        item = {'sample_id':row['sample_id'], 'presence_target':row['presence_target'],
                'expected_pleating':row['label'] if row['presence_target'] else None,
                'presence':presence, 'paths':{}}
        for name, localizer in masks.items():
            region = localizer.locate(image)
            accepted = region['status'] == 'provisional'
            prediction = pleating.predict(image, tuple(region['roi']), True)['style']['label'] if accepted else None
            item['paths'][name] = {'accepted':accepted, 'pleating_prediction':prediction, 'localization':region}
            item['paths'][name+'_plus_presence'] = {
                'accepted':accepted and presence['accepted'],
                'pleating_prediction':prediction if accepted and presence['accepted'] else None}
        results.append(item)
    summary = {name:metrics(results,name) for name in ('v1','v2','v1_plus_presence','v2_plus_presence')}
    criteria = compare(summary['v2_plus_presence'], summary['v1'])
    report = {'recorded_utc':datetime.now(timezone.utc).isoformat(), 'status':'completed',
              'source_sha256':sha(Path(__file__)), 'inputs_sha256':sha(inputs), 'split_hash':run['split_hash'],
              'models':{'masks':{k:m.sha256 for k,m in masks.items()}, 'presence':gate.sha256},
              'fixed_presence_threshold':.5, 'fixed_mask_threshold':.5,
              'primary_candidate':'v2_plus_presence', 'baseline':'v1', 'metrics':summary,
              'development_criteria':criteria, 'development_criteria_passed':all(criteria.values()),
              'deployment_approved':False, 'results':results,
              'limitations':['Agent-reviewed source-domain development only; no final test',
                             'Presence checkpoint selected on these validation groups',
                             'Joint data and optimization changes; no causal attribution to one change',
                             'Development comparison does not approve camera, public demonstration or Pi deployment']}
    with a.output.open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2)
        f.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'results'},indent=2))


if __name__ == '__main__':
    main()
