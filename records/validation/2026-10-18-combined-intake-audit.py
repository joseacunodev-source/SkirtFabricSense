"""Immutable combined-original audit; does not alter source data or admissions."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.datasets import audit_candidates

OUTPUT = Path(__file__).with_suffix('.json')
PILOT = 'data/manifests/npcgi-pilot-candidates.jsonl'
SEED = 'data/provenance/external_holdout_samples.jsonl'


def manifest_paths(registry):
    """Deduplicate acquisition manifests even if pilot is already registered."""
    candidates = [(item['manifest']['path'], item['manifest'].get('sha256'))
                  for item in registry['expansion_acquisitions']]
    candidates += [(SEED, None), (PILOT, None)]
    unique = {}
    for relative, recorded_hash in candidates:
        path = (ROOT/relative).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise ValueError(f'Manifest is missing or escapes workspace: {relative}')
        key = str(path).casefold()
        actual = audit_candidates.sha256(path)
        if recorded_hash is not None and actual != recorded_hash:
            raise ValueError(f'Registered acquisition manifest changed: {relative}')
        unique[key] = path
    return list(unique.values())


def main():
    if OUTPUT.exists():
        raise FileExistsError(f'Immutable evidence already exists: {OUTPUT}')
    registry_path = ROOT/'data/registry.json'
    registry_bytes = registry_path.read_bytes()
    registry = json.loads(registry_bytes)
    manifests = manifest_paths(registry)
    inputs = [{'path': p.relative_to(ROOT).as_posix(), 'sha256': audit_candidates.sha256(p)}
              for p in manifests]
    records = audit_candidates.load_records(manifests)
    pilot_ids = {r['sample_id'] for r in audit_candidates.load_records([ROOT/PILOT])}
    # Existing auditor understands native_dimensions or width/height. The new
    # pilot uses dimensions; bridge that field in memory without editing a row.
    normalized = [{**r, 'native_dimensions': r['dimensions']}
                  if 'dimensions' in r and 'native_dimensions' not in r else r for r in records]
    report = audit_candidates.audit(normalized, ROOT, near_distance=4)
    for item in inputs:
        if audit_candidates.sha256(ROOT/item['path']) != item['sha256']:
            raise ValueError(f'Input manifest changed during audit: {item["path"]}')
    pilot_near = [pair for pair in report['near_duplicate_candidates']
                  if pilot_ids.intersection(pair['sample_ids'])]
    report.update(
        recorded_utc=datetime.now(timezone.utc).isoformat(),
        date_asia_manila='2026-10-18',
        status='completed' if report['counts']['integrity_errors'] == 0 else 'integrity_errors_found',
        input_manifests=inputs,
        input_registry={'path': 'data/registry.json', 'sha256': hashlib.sha256(registry_bytes).hexdigest(),
                        'snapshot_note': 'Hash of registry bytes read at audit start; registry may be updated by root afterward'},
        audit_source_sha256=audit_candidates.sha256(Path(audit_candidates.__file__)),
        runner_source={'path': Path(__file__).relative_to(ROOT).as_posix(),
                       'sha256': audit_candidates.sha256(Path(__file__))},
        environment={'executable': sys.executable, 'python': platform.python_version(),
                     'pillow': importlib.metadata.version('pillow'), 'platform': platform.platform(),
                     'role': 'codex-bundled-tooling-windows'},
        expected_original_records=1932,
        expected_count_matches=report['counts']['original_records'] == 1932,
        source_counts=dict(Counter(r.get('source_id', 'unknown') for r in records)),
        new_pilot={'manifest': PILOT, 'original_records': len(pilot_ids),
                   'near_duplicate_candidates_involving_pilot': pilot_near,
                   'exact_duplicate_groups_involving_pilot': [group for group in report['exact_duplicate_groups'] if pilot_ids.intersection(group)],
                   'pixel_duplicate_groups_involving_pilot': [group for group in report['pixel_duplicate_groups'] if pilot_ids.intersection(group)],
                   'training_admission_changed': False, 'split_changed': False},
        input_normalization='In-memory dimensions to native_dimensions when absent; original manifests remain byte-identical')
    audit_candidates.write_json(OUTPUT, report)
    print(json.dumps({'counts': report['counts'], 'report_sha256': audit_candidates.sha256(OUTPUT),
                      'manifest_count': len(manifests), 'pilot_involved_near_matches': pilot_near,
                      'expected_count_matches': report['expected_count_matches']}, indent=2))
    return int(bool(report['counts']['integrity_errors']) or not report['expected_count_matches'])


if __name__ == '__main__':
    raise SystemExit(main())
