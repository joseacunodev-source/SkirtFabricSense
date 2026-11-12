"""Preserve this interrupted acquisition without claiming unobserved network outcomes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'records/acquisitions/2026-10-13-fabric-v2'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__ == '__main__':
    report_path = OUT / 'report.json'
    if report_path.exists():
        raise FileExistsError(report_path)
    destination = ROOT / 'data/external/deepfashion_multimodal_candidates_v2'
    manifest = ROOT / 'data/manifests/fullview-fabric-candidates-v2.jsonl'
    if manifest.exists() or any(destination.iterdir()):
        raise ValueError('Actual partial outputs require reconciliation')
    selection = json.loads((OUT / 'selection.json').read_text())
    report = dict(date_asia_manila='2026-10-13', recorded_utc=datetime.now(timezone.utc).isoformat(),
                  status='interrupted_no_images', error='External process stopped after no completed image progress; precise network stage and cause unobserved',
                  selected_groups=len(selection['selected']), selection=selection['assessment'],
                  requested_limit=30, complete_images=0, images=[], label_counts={}, training_admitted=False,
                  manifest=None, range_requests=None,
                  range_requests_note='Original process retained request telemetry in memory until completion; no request completion evidence was persisted',
                  source_url='https://drive.google.com/uc?export=download&id=1U2PljA7NE57jcSSzPs21ZurdIPXdYZtN',
                  source_sha256=sha(OUT / 'acquisition_source.py'),
                  selection_sha256=sha(OUT / 'selection.json'),
                  partition_join_sha256=sha(ROOT / 'records/acquisitions/2026-10-11-fabric-partition/skirt-partition-join.jsonl'),
                  existing_manifest_sha256=sha(ROOT / 'data/manifests/fullview-fabric-candidates-v1.jsonl'),
                  terms_sha256=sha(ROOT / 'records/acquisitions/2026-10-09-deepfashion-multimodal/LICENSE'),
                  reader_sha256=sha(ROOT / 'tools/datasets/bounded_zip.py'),
                  retry_attempted=False, retry_reason='No specific transient cause established; avoid repeating an unobservable stalled request',
                  dependency_changes=[])
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('selection', 'source_url')}, indent=2))
