"""Reproduce a frozen worn-subset join of archived development predictions."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    manifest = ROOT/'data/manifests/worn-pleating-development-v1.jsonl'
    comparison = ROOT/'records/validation/2026-10-15-localizer-threeway.json'
    metadata = json.loads((ROOT/'data/manifests/worn-pleating-development-v1.json').read_text())
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if sha(manifest) != metadata['manifest']['sha256']:
        raise ValueError('Frozen subset changed')
    rows = [json.loads(line) for line in manifest.read_text(encoding='utf-8').splitlines()]
    val = [r for r in rows if r['split'] == 'development_validation']
    ids = {r['sample_id'] for r in val}
    if len(ids) != len(val) or any(r['presentation'] != 'worn' for r in rows):
        raise ValueError('Invalid subset membership')
    all_results = json.loads(comparison.read_text())['results']
    selected = [r for r in all_results if r['sample_id'] in ids]
    if len(selected) != len(ids) or {r['sample_id'] for r in selected} != ids:
        raise ValueError('Incomplete prediction join')
    metrics = {}
    for name in ('v1', 'v2', 'v3'):
        accepted = [r for r in selected if r[name]['accepted']]
        correct = sum(r[name]['prediction'] == r['expected'] for r in accepted)
        metrics[name] = {'worn_validation_images':len(selected), 'accepted':len(accepted),
                         'correct_pleating':correct, 'coverage':len(accepted)/len(selected),
                         'accuracy_accepted':correct/len(accepted) if accepted else None}
    report = {'date_asia_manila':'2026-10-17', 'method':'Exact archived development subset join; no new inference',
              'tool_sha256':sha(Path(__file__)), 'metrics':metrics,
              'sources':[{'path':path.relative_to(ROOT).as_posix(), 'sha256':sha(path)}
                         for path in (manifest, comparison)],
              'limitations':['Models selected on broader mixed-presentation development data',
                             'Single-agent presentation and pleating labels; not independent test truth',
                             'No worn-specific negative accuracy, camera or Pi measurements',
                             'No model promotion inferred']}
    with a.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(metrics))


if __name__ == '__main__':
    main()
