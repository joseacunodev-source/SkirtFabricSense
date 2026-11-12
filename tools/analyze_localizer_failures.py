"""Summarize archived development failures without rerunning or tuning models."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def summarize(comparison, negatives):
    index = {}
    for row in negatives:
        if row['sample_id'] in index:
            raise ValueError('Duplicate negative identity')
        index[row['sample_id']] = row
    seen = set()
    buckets = {}
    persistent = []
    reasons = {name: Counter() for name in ('v1', 'v2', 'v3')}
    for row in comparison['results']:
        sid = row['sample_id']
        if sid in seen:
            raise ValueError('Duplicate evaluation identity')
        seen.add(sid)
        for name in reasons:
            if type(row[name]['accepted']) is not bool:
                raise ValueError('Invalid acceptance flag')
            if not row[name]['accepted']:
                reasons[name][row[name]['region']['reason']] += 1
        if row['positive']:
            continue
        source = index[sid]
        if source['split'] != 'development_validation' or source['label'] != 'no_skirt':
            raise ValueError('Negative is not an admitted development validation sample')
        bucket = source['sampling_bucket']
        counts = buckets.setdefault(bucket, {'count': 0, 'v1_false_accepts': 0,
                                             'v2_false_accepts': 0, 'v3_false_accepts': 0})
        counts['count'] += 1
        for name in reasons:
            counts[name + '_false_accepts'] += row[name]['accepted']
        if all(row[name]['accepted'] for name in reasons):
            persistent.append({'sample_id': sid, 'sampling_bucket': bucket,
                               'original_path': source['original_path'],
                               'sha256': source['sha256'], 'group_id': source['group_id']})
    return {'negative_buckets': buckets, 'all_models_false_accept': persistent,
            'rejection_reasons_all_99_inputs': {k: dict(v) for k, v in reasons.items()},
            'limitations': ['Archived development outputs only; not new model evaluation',
                           'Source sampling bucket is not a new visual error label',
                           'No thresholds tuned, no model promoted, no test data used']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    sources = [root/'records/validation/2026-10-15-localizer-threeway.json',
               root/'data/labels/negative-reviewed-v2.jsonl']
    result = summarize(json.loads(sources[0].read_text(encoding='utf-8')),
                       [json.loads(line) for line in sources[1].read_text(encoding='utf-8').splitlines()])
    result['date'] = '2026-10-16'
    result['sources'] = [{'path': path.relative_to(root).as_posix(),
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in sources]
    result['tool_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with a.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
