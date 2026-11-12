"""Freeze R02 results without creating any real reviewer event."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tools.datasets import fabric_evidence_review as review

def reference(p):
    path=ROOT/p
    return {'path':p,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

production=review.verify(ROOT,ROOT/'records/review/2026-10-23-fabric-evidence-review')
if production['queue_records']!=17 or production['observations_submitted']!=0:
    raise ValueError('Unexpected production observations; investigate before freezing')
if production['event_log_sha256']!=hashlib.sha256(b'').hexdigest():
    raise ValueError('Production event log changed')
paths=['tools/serve_fabric_review.py','tools/static/fabric_review.html',
       'tests/test_fabric_review_ui.py','tests/fabric_review_browser.cjs',
       'docs/FABRIC_REVIEW_UI.md','tools/datasets/fabric_evidence_review.py',
       'records/validation/2026-11-11-fabric-reviewer/verified-r02/browser-result.json',
       'records/validation/2026-11-11-fabric-reviewer/verified-r02/browser-synthetic-review.png',
       'records/validation/2026-11-11-fabric-reviewer/verified-r02/download.json']
report={
 'recorded_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),
 'status':'completed_software_and_temporary_browser_validation',
 'test_command':'python -B -m unittest tests.test_fabric_review_ui tests.test_fabric_evidence_review -v',
 'tests':{'run':41,'passed':41,'ui':11,'underlying_evidence':30,'browser_checks':14},
 'observed_test_output':'Ran 41 tests in 12.971s; OK',
 'browser':'Existing Microsoft Edge using bundled Playwright',
 'synthetic_fixtures_only':True,
 'production_queue_verification':production,
 'production_observations_added':0,
 'source_and_artifact_references':[reference(p) for p in paths],
 'visual_review':'Synthetic reviewer screenshot inspected; full original panel and form are readable and no overlapping controls found.',
 'owned_servers_stopped':True,
 'dependencies_installed':[],
 'remaining_work':['Human observations and independent reconciliation','Credible rare-class groups and final textile ontology','Accepted fabric model and real camera/Pi evaluation'],
 'limits':'Software evidence only; no composition verification, approved label release or final model accuracy.',
}
with (OUT/'verification.json').open('x',encoding='utf-8') as f:
    json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'status':report['status'],'tests_passed':41,'production_events':production['observations_submitted']}))
