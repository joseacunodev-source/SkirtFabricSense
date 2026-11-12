"""Audit the full original-image pool plus the bounded second intake, offline."""
import json
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.datasets.audit_candidates import audit, load_records, sha256, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--negative-only', action='store_true', help='Explicitly exclude incomplete fabric intake')
    args = parser.parse_args()
    paths = [
        'data/manifests/skirt_candidates.jsonl',
        'data/manifests/fabric_candidates.jsonl',
        'data/provenance/external_holdout_samples.jsonl',
        'data/manifests/negative-candidates-v1.jsonl',
        'data/manifests/fullview-fabric-candidates-v1.jsonl',
        'data/manifests/negative-candidates-v2.jsonl',
        'data/manifests/fullview-fabric-candidates-v2.jsonl',
    ]
    new_paths = paths[-2:]
    if args.negative_only:
        paths = paths[:-1]
        new_paths = new_paths[:1]
    records = load_records([ROOT/p for p in paths])
    result = audit(records, ROOT)
    result['input_manifests'] = [{'path':p, 'sha256':sha256(ROOT/p)} for p in paths]
    result['audit_source_sha256'] = sha256(ROOT/'tools/datasets/audit_candidates.py')
    result['runner_source_sha256'] = sha256(__file__)
    new_ids = {r['sample_id'] for r in load_records([ROOT/p for p in new_paths])}
    result['new_sample_ids'] = sorted(new_ids)
    result['new_near_duplicate_candidates'] = [pair for pair in result['near_duplicate_candidates']
                                               if new_ids.intersection(pair['sample_ids'])]
    result['training_admitted'] = False
    write_json(args.output, result)
    print(json.dumps({'counts':result['counts'], 'new_near_pairs':len(result['new_near_duplicate_candidates'])}))
    raise SystemExit(bool(result['counts']['integrity_errors']))


if __name__ == '__main__':
    main()
