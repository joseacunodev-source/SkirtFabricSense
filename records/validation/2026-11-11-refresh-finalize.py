"""Reconcile the review, task board and checkpoint without hiding failed evidence."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.validate_records import validate,verify_reference_tree
def ref(p):return {'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}
def write(p,v,mode='x'):
 with (ROOT/p).open(mode,encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
def prepend(p,t):
 f=ROOT/p;head,body=f.read_text(encoding='utf-8').split('\n',1);f.write_text(head+'\n\n'+t+'\n'+body,encoding='utf-8')
cp='records/continuation/latest.json';c=json.loads((ROOT/cp).read_text())
archive='records/continuation/2026-11-11-before-project-refresh.json'
with (ROOT/archive).open('xb') as f:f.write((ROOT/cp).read_bytes())
note=('November 11 current review: [recovery findings and ordered next tasks](PROJECT_REFRESH_NOV11.md). '
 'No unfinished GPU run or active scoped station/training process was found. Fabric reviewer server/HTML are partial, '
 'the geometry annotation editor is absent, and the completed background attempt acquired zero photos. '
 'Twenty-one raw HTTP error responses saved as JSON still fail record parsing. The user reconfirmed no Pi, webcam or skirts. '
 'Resume record recovery R01, then reviewer completion R02; do not restart completed fits.')
for p in ['docs/AGENT_HANDOFF.md','docs/DOCUMENTATION_INDEX.md']:prepend(p,note)
prepend('HANDOFF.md',note.replace('(PROJECT_REFRESH_NOV11.md)','(docs/PROJECT_REFRESH_NOV11.md)'))
prepend('README.md','November 11: [refreshed project status and next tasks](docs/PROJECT_REFRESH_NOV11.md). '
 'Station-v8 remains the desktop research selection. Recover interrupted evidence/reviewer work before more training; '
 'the user confirms no Pi, webcam or skirts yet.')
task=ROOT/'docs/TASK_BOARD.md';s=task.read_text(encoding='utf-8')
s=s.replace('Updated November 4, 2026. This is the active checklist.','Updated November 11, 2026. This is the active checklist.')
section='''## Immediate recovery and software preparation

The [November 11 review](PROJECT_REFRESH_NOV11.md) verifies saved work and defines the dependency order. No fit or acquisition is still active.

- [ ] **R01 — Recover background acquisition records.** The attempt finished with zero photos; 21 raw HTTP 429 text bodies have JSON filenames. Preserve bytes/historical hashes, add versioned typed recovery evidence and test the validator path. Do not silently delete failures or rerun the same output directory.
- [ ] **R02 — Finish and validate the fabric browser reviewer.** Server and HTML exist. UI tests, save/download/request checks and reviewer documentation are missing. Complete using temporary fixtures, then make the existing 17-item queue usable for the available human/groupmate reviewers. No human observations are submitted yet.
- [ ] **R03 — Implement the missing geometry annotation editor.** Design only; no editor/tool/test/guide files were found. Capture visible source-pixel intervals, uncertainty and unknowns with provenance; reconcile observations before evaluator admission. Physical calibration and automatic wearer detection remain separate gates.
- [ ] **R04 — Review 800 × 480 usability.** The actual viewport capture shows lower controls/reference content below the fold. Keep essential controls/results practical, then verify physical legibility/touch when hardware arrives.

'''
s=s.replace('## Next software and data work, in priority order',section+'## Next software and data work, in priority order',1)
s=s.replace('Latest availability: the user confirms no Pi or webcam on November 4; actual skirts were last confirmed unavailable on October 20.',
 'Latest availability: the user reconfirms no Raspberry Pi, webcam or actual skirts on November 11.')
task.write_text(s,encoding='utf-8')
handoff=ROOT/'docs/AGENT_HANDOFF.md';s=handoff.read_text(encoding='utf-8')
s=s.replace('# Agent handoff — November 4, 2026','# Agent handoff — November 11, 2026',1)
s=s.replace('| Pleating/detection | Selected station-v6:', '| Pleating/detection | Selected station-v8:')
s=s.replace('| Hardware | Laptop GPU training/export verified | No Pi or webcam on October 23; skirts last unavailable October 20.',
 '| Hardware | Laptop GPU training/export verified | No Pi, webcam or skirts on November 11.')
handoff.write_text(s,encoding='utf-8')
deploy=ROOT/'docs/RASPBERRY_PI_DEPLOYMENT.md';s=deploy.read_text(encoding='utf-8')
s=s.replace('November 4: station-v6/research-v11 is the current verified desktop research payload; v5 is rollback. The user plans Pi/webcam purchase.',
 'November 11 review: station-v8/research-v13 is the selected desktop research payload; station-v7 is rollback. The user reconfirms no Pi, webcam or skirts.')
deploy.write_text(s,encoding='utf-8')
hardware=ROOT/'docs/HARDWARE.md';s=hardware.read_text(encoding='utf-8')
s=s.replace('| Touch display, proposed 7-inch | 1 | Proposed; can follow model pilot |',
 '| Waveshare 5inch HDMI LCD (G), SKU 14447 | 1 | User selected; not physically verified |')
hardware.write_text(s,encoding='utf-8')
prepend('CHANGELOG.md','## 2026-11-11 — Refresh recovery status and future work\n\n'
 '- Verified 236 checkpoint references, selected station, 11 archived run records and 38 background-attempt artifact hashes; no active scoped job or started training record.\n'
 '- Identified partial fabric reviewer, absent geometry editor and completed zero-photo background attempt with 21 preserved raw-response parsing errors.\n'
 '- Passed 76 focused partition, fabric-evidence, geometry-evaluation and hemline tests. Updated recovery priorities and corrected stale deployment/display summaries.\n'
 '- User reconfirmed no Pi, webcam or skirts. No downloads, installs, labels, models or data splits changed. [Review](docs/PROJECT_REFRESH_NOV11.md).')
tests={'date':'2026-11-11','command':'python -B -m unittest tests.test_dataset_partitions tests.test_fabric_evidence_review tests.test_worn_geometry_evaluation tests.test_hemline -q',
 'interpreter':'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 'run':76,'passed':76,'stdout':'Ran 76 tests in 3.258s; OK',
 'scope':'Saved-data contracts and synthetic software checks, not camera/Pi acceptance',
 'sources':[ref(p) for p in ['tests/test_dataset_partitions.py','tests/test_fabric_evidence_review.py','tests/test_worn_geometry_evaluation.py','tests/test_hemline.py']]}
tp='records/validation/2026-11-11-refresh-focused-tests.json';write(tp,tests)
agent={'date':'2026-11-11','reviewer':'review_interrupted_ui','read_only':True,'underlying_evidence_tests_passed':30,
 'ui_specific_test_module_present':False,'production_review_events':0,
 'checks':{'cli_help':'passed','queue_load':'17 items / 0 observations','page_queue_image_http':'200',
 'private_bindings_http':'404','wrong_host_http':'403','save_download_browser_roundtrip':'not_tested'},
 'evidence_log_unchanged':True,'owned_test_server_stopped':True,
 'sources':[ref('tools/serve_fabric_review.py'),ref('tools/static/fabric_review.html')]}
ap='records/validation/2026-11-11-interrupted-fabric-review-audit.json';write(ap,agent)
mutable={'HANDOFF.md','README.md','CHANGELOG.md','docs/TASK_BOARD.md','docs/AGENT_HANDOFF.md','docs/DOCUMENTATION_INDEX.md',
 'docs/HARDWARE.md','docs/RASPBERRY_PI_DEPLOYMENT.md'}
paths=['docs/PROJECT_REFRESH_NOV11.md','records/validation/2026-11-11-refresh-audit.py',
 'records/validation/2026-11-11-refresh-audit.json','records/validation/2026-11-11-refresh-finalize.py',tp,ap,
 'tools/serve_fabric_review.py','tools/static/fabric_review.html','records/validation/2026-11-11-progress-screenshot-docx.json',
 'output/SkirtFabricSense_Progress_Report_Screenshots.docx']
rp='records/validation/2026-11-11-project-refresh.json'
report={'date':'2026-11-11','status':'review_completed_recovery_and_acceptance_open','evidence':[ref(p) for p in paths],
 'started_run_records':0,'active_scoped_jobs':0,'background_photos_added':0,'remaining_record_parse_errors':21,
 'partial_ui_accepted':False,'geometry_editor_exists':False,'focused_tests_passed':76,
 'models_or_thresholds_changed':False,'dependencies_changed':False,
 'hardware_confirmation':{'date':'2026-11-11','raspberry_pi_available':False,'webcam_available':False,'skirts_available':False}}
write(rp,report)
c.update(updated_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),latest_batch=ref(rp),previous_checkpoint=ref(archive),active_operations=[],pending_operations=[])
c['last_hardware_confirmation']=report['hardware_confirmation']
c['last_hardware_confirmation']['skirts_last_confirmed_unavailable']='2026-11-11'
c['next_actions']=[{'task_id':'R01','action':'Recover raw HTTP response evidence with preserved historical bytes/hashes and tested typed validation.','needs_hardware':False},
 {'task_id':'R02','action':'Complete reviewer browser, save/download/security tests and guide using temporary queues, then human review.','needs_hardware':False},
 {'task_id':'R03','action':'Implement source-pixel geometry editor and reviewed intake without fabricated references.','needs_hardware':False},
 {'task_id':'S02-S06','action':'Resolve labels/groups/rights, obtain suitable new data, predeclare candidate comparisons and independent evaluation.','needs_hardware':False},
 {'task_id':'P01-P07','action':'Obtain garments/camera/Pi, calibrate and test the real station before demonstration acceptance.','needs_hardware':True}]
c['open_tasks']=list(dict.fromkeys(['R01','R02','R03','R04']+c['open_tasks']))
c['tests']['refresh_nov11']={'run':76,'passed':76,'source':ref(tp)}
c['process_observations']={'date':'2026-11-11','scope':'Scoped WSL training/evaluation/station names; Windows Python/Node project names checked; no process stopped',
 'evidence':ref('records/validation/2026-11-11-refresh-audit.json'),'active_scoped_jobs':0}
c['record_integrity_issue']['status']='confirmed_open_recovery_R01'
def refresh(x):
 if isinstance(x,dict):
  if x.get('path') in mutable and 'sha256'in x:x['sha256']=ref(x['path'])['sha256']
  for v in x.values():refresh(v)
 elif isinstance(x,list):
  for v in x:refresh(v)
refresh(c);known={r['path'] for r in c['references']}
for p in sorted(set(paths)|mutable|{rp}):
 if p not in known:c['references'].append(ref(p))
errors=[];verify_reference_tree(ROOT,c,errors)
if errors:raise ValueError(errors)
write(cp,c,'w')
final=validate(ROOT);vp='records/validation/2026-11-11-refresh-record-validation.json';write(vp,final)
if len(final['errors'])!=21 or any('2026-11-04-backgrounds' not in e for e in final['errors']):raise ValueError(final['errors'])
print(json.dumps({'checkpoint_errors':errors,'document_links_checked':final['local_links_checked'],
 'remaining_known_parse_errors':len(final['errors']),'focused_tests_passed':76,'status':'review_complete_recovery_priorities_recorded'}))
