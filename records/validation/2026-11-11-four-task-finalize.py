"""Integrate R01-R04 evidence, selected station and a clean continuation record."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.validate_records import validate,verify_reference_tree
from tools.raw_http_records import verified_raw_responses
from tools.station_package import verify_station
def ref(p):return {'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}
def write(p,v,mode='x'):
 with (ROOT/p).open(mode,encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
def prepend(p,t):
 f=ROOT/p;first,rest=f.read_text(encoding='utf-8').split('\n',1);f.write_text(first+'\n\n'+t+'\n'+rest,encoding='utf-8')
cp='records/continuation/latest.json';c=json.loads((ROOT/cp).read_text())
archive='records/continuation/2026-11-11-before-four-task-implementation.json'
with (ROOT/archive).open('xb') as f:f.write((ROOT/cp).read_bytes())
raw=verified_raw_responses(ROOT)
if len(raw)!=21:raise ValueError('Recovery must account for exactly21 retained failures')
for p in ['artifacts/stations/skirt-research-station-v8','artifacts/stations/skirt-research-station-v9']:verify_station(ROOT/p)
reports=['records/validation/2026-11-11-fabric-reviewer/verified-r02/verification.json',
 'records/validation/2026-11-11-geometry-editor/final/verification.json',
 'records/validation/2026-11-11-compact-layout/independent-review/review.json']
for p in reports:
 errors=[];verify_reference_tree(ROOT,json.loads((ROOT/p).read_text()),errors)
 if errors:raise ValueError(errors)
http=json.loads((ROOT/'records/validation/2026-11-11-station-v9-http.json').read_text())
if http['status']!='passed' or http['http_inference_jobs']!=12 or not http['all_owned_servers_stopped']:raise ValueError('Station check incomplete')
prod='records/review/2026-10-23-fabric-evidence-review/events.jsonl'
if (ROOT/prod).read_bytes()!=b'':raise ValueError('Unexpected production review observations; preserve and investigate')
acq=json.loads((ROOT/'records/acquisitions/2026-11-04-backgrounds/acquisition.json').read_text())
for r in acq['artifacts']:
 if ref(r['path'])['sha256']!=r['sha256'] or (ROOT/r['path']).stat().st_size!=r['size_bytes']:raise ValueError('Historical acquisition changed')
cmd=['wsl','-d','Ubuntu-24.04','-u','skirttrain','--exec','/usr/bin/pgrep','-af','[a]pp.server|[s]tation_package.py launch|[t]rain_.*.py']
p=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
if p.returncode!=1 or p.stdout.strip():raise ValueError('Unexpected scoped WSL process state')
note=('November 11 implementation: **R01–R04 software tasks are complete**. [Recovery and tool instructions](RECOVERY_IMPLEMENTATION_NOV11.md). '
 'Station-v9/research-v14 is selected, with v8 rollback. The 21 raw HTTP failures are preserved and verified as transport evidence; '
 'fabric/geometry reviewer tools are tested and documented; essential controls/results fit800 ×480. '
 'Human labels, automatic wearer geometry/calibration and physical camera/Pi acceptance remain open.')
for path in ['docs/AGENT_HANDOFF.md','docs/DOCUMENTATION_INDEX.md','docs/REQUIREMENTS.md','docs/DECISIONS.md','docs/ARCHITECTURE.md','docs/STATION_PACKAGE.md','docs/CAMERA_UI.md','docs/LCD_14447_LAYOUT.md','docs/RASPBERRY_PI_DEPLOYMENT.md']:
 prepend(path,note)
prepend('HANDOFF.md',note.replace('(RECOVERY_IMPLEMENTATION_NOV11.md)','(docs/RECOVERY_IMPLEMENTATION_NOV11.md)'))
prepend('README.md','November 11 implementation: [all four recovery/software tasks are complete](docs/RECOVERY_IMPLEMENTATION_NOV11.md). '
 'Station-v9/research-v14 is selected for desktop research; v8 is rollback. Human review, model-quality and physical acceptance remain open.')
prepend('docs/TASK_BOARD.md',note)
prepend('docs/PROJECT_REFRESH_NOV11.md','The review below describes the earlier recovery checkpoint. '
 'Its R01–R04 implementation tasks are now complete; see [the delivered behavior and next actions](RECOVERY_IMPLEMENTATION_NOV11.md).')
prepend('docs/DATASETS.md','November 11 recovery: the completed zero-photo Commons attempt is reconciled through '
 '[typed failed-response evidence](ACQUISITION_RECOVERY_NOV11.md). Original bodies/hashes remain intact. '
 'Collection remains1,932 originals; no images, labels, admissions or frozen splits changed. The new reviewer tools have zero production observations.')
prepend('CHANGELOG.md','## 2026-11-11 — Complete four recovery and software tasks\n\n'
 '- Preserve and classify21 raw HTTP429 bodies with checked typed copies/index; keep JSON validation strict for unclassified files.\n'
 '- Complete browser fabric review and offline geometry annotation, fixing duplicate-save/in-flight-edit and cancelled-gesture issues. Tests use temporary synthetic data; production queue unchanged.\n'
 '- Fit essential controls and four output states at800 ×480, with accessible disclosures for extended guidance.\n'
 '- Select station-v9/research-v14 after30 package tests and12 saved-image HTTP jobs; retain v8 rollback. '
 'Four focused Python commands total102 passing tests, plus recorded browser/mock checks. No training, downloads, installations or hardware tests. '
 '[Instructions and evidence](docs/RECOVERY_IMPLEMENTATION_NOV11.md).')
task=ROOT/'docs/TASK_BOARD.md';s=task.read_text(encoding='utf-8')
start=s.index('- [ ] **R01');end=s.index('## Next software and data work',start)
s=s[:start]+'''- [x] **R01 — Recover acquisition records.** All21 HTTP failure bodies and historical hashes are preserved with typed copies and a checked index. Ordinary malformed JSON still fails. [Recovery](ACQUISITION_RECOVERY_NOV11.md).
- [x] **R02 — Finish the fabric reviewer.** Complete browser save/download/unknown/security checks and reviewer guide;41 tests pass. Production17-item queue still awaits actual observations. [Use the reviewer](FABRIC_REVIEW_UI.md).
- [x] **R03 — Build the geometry annotation editor.** Full-original bands/unknowns, hash-bound pending export, cancellation/date handling and guide complete;14 tests and browser roundtrip pass. [Use the editor](GEOMETRY_ANNOTATION.md).
- [x] **R04 — Improve800 ×480 usability.** Essential preview/settings/actions/four values/fabric switch fit without initial scrolling. Source mocked/browser checks and station-v9 HTTP/inventory checks pass; physical LCD/touch testing remains open. [Layout](COMPACT_LAYOUT_NOV11.md).

'''+s[end:]
s=s.replace('The [November 11 review](PROJECT_REFRESH_NOV11.md) verifies saved work and defines the dependency order. No fit or acquisition is still active.',
 'All four requested software items are complete. [Implementation evidence and next actions](RECOVERY_IMPLEMENTATION_NOV11.md). No fit, acquisition or test server remains active.')
s=s.replace('S07 — Freeze an accepted full-feature release.** Station-v8','S07 — Freeze an accepted full-feature release.** Station-v9')
s=s.replace('v7 is rollback. Fabric/reference/calibration acceptance remains missing.','v8 is rollback. Fabric/reference/calibration acceptance remains missing.')
task.write_text(s,encoding='utf-8')
station_doc=ROOT/'docs/STATION_PACKAGE.md';s=station_doc.read_text(encoding='utf-8')
s=s.replace('artifacts/stations/skirt-research-station-v8 --exec','artifacts/stations/skirt-research-station-v9 --exec')
s=s.replace('For rollback, replace `skirt-research-station-v8` with `skirt-research-station-v7`','For rollback, replace `skirt-research-station-v9` with `skirt-research-station-v8`')
station_doc.write_text(s,encoding='utf-8')
selected={'directory':'artifacts/stations/skirt-research-station-v9','inventory':ref('artifacts/stations/skirt-research-station-v9/station-inventory.json'),
 'configuration':ref('artifacts/stations/skirt-research-station-v9/station.json'),'payload_files':28,
 'selection':'selected_desktop_research','pi_verified':False,'desktop_http_jobs':12,'evidence':ref('records/validation/2026-11-11-station-v9-http.json')}
rollback={'directory':'artifacts/stations/skirt-research-station-v8','inventory':ref('artifacts/stations/skirt-research-station-v8/station-inventory.json'),
 'configuration':ref('artifacts/stations/skirt-research-station-v8/station.json'),'selection':'rollback','pi_verified':False}
regpath='data/registry.json';registry=json.loads((ROOT/regpath).read_text())
registry['updated_date_asia_manila']='2026-11-11';registry['status']='research_station_v9_desktop_verified_product_acceptance_open'
registry['selected_research_station']={'inventory':selected['inventory'],'configuration':selected['configuration'],
 'scope':'Desktop research only; full-feature demonstration and Pi acceptance remain open','rollback':rollback['directory'],'deployment_approved':False}
registry['evidence_recoveries']={'failed_background_acquisition':ref('records/acquisitions/2026-11-04-backgrounds/acquisition.json'),
 'raw_http_index':ref('records/recoveries/raw-http-responses-v1.json'),'photos_added':0,'admissions_added':0,'historical_files_changed':False}
write(regpath,registry,'w')
mutable={'HANDOFF.md','README.md','CHANGELOG.md','docs/TASK_BOARD.md','docs/PROJECT_REFRESH_NOV11.md','docs/DATASETS.md','data/registry.json',
 'docs/AGENT_HANDOFF.md','docs/DOCUMENTATION_INDEX.md','docs/REQUIREMENTS.md','docs/DECISIONS.md','docs/ARCHITECTURE.md',
 'docs/STATION_PACKAGE.md','docs/CAMERA_UI.md','docs/LCD_14447_LAYOUT.md','docs/RASPBERRY_PI_DEPLOYMENT.md',
 'app/static/index.html','tools/validate_records.py','tools/serve_fabric_review.py','tools/static/fabric_review.html'}
paths=['tools/raw_http_records.py','tests/test_raw_http_records.py','records/recoveries/raw-http-responses-v1.json',
 'docs/ACQUISITION_RECOVERY_NOV11.md','docs/FABRIC_REVIEW_UI.md','docs/GEOMETRY_ANNOTATION.md','docs/COMPACT_LAYOUT_NOV11.md','docs/RECOVERY_IMPLEMENTATION_NOV11.md',
 'tools/geometry_annotation.py','tools/static/geometry_annotation.html','tests/test_geometry_annotation.py','tests/geometry_annotation_browser.cjs',
 'tests/test_fabric_review_ui.py','tests/fabric_review_browser.cjs','tests/compact_layout_browser.cjs',
 'records/validation/2026-11-11-four-task-finalize.py','records/validation/2026-11-11-station-v9-http.json',
 'records/validation/2026-11-11-station-v9-http.execution.json','records/validation/2026-11-11-raw-response-recovery-preintegration.json',
 'artifacts/releases/skirt-finetune-v1-desktop-research-v14/inventory.json','output/geometry-review/12679.html']+reports
for folder in ['records/recoveries/http-bodies-20261111','records/validation/2026-11-11-fabric-reviewer/verified-r02',
 'records/validation/2026-11-11-geometry-editor/final','records/validation/2026-11-11-compact-layout/independent-review']:
 paths += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT/folder).rglob('*')) if p.is_file()]
rp='records/validation/2026-11-11-four-task-completion.json'
report={'date':'2026-11-11','status':'all_four_requested_software_tasks_complete','tasks_completed':['R01','R02','R03','R04'],
 'raw_response_bodies_verified':21,'historical_acquisition_artifacts_verified':len(acq['artifacts']),
 'python_tests':{'recovery_and_continuation':17,'fabric_reviewer_and_evidence':41,'geometry_editor':14,'package_and_release':30,'total':102},
 'browser_checks':{'mocked_camera_cases':52,'layout_scenarios':6,'fabric_browser_checks':14,'geometry_roundtrip':'passed'},
 'station_http_jobs':12,'selected_station':selected,'rollback':rollback,'evidence':[ref(p) for p in sorted(set(paths)|mutable)],
 'process_observation':{'command':cmd,'exit_code':p.returncode,'stdout':p.stdout,'scope':'Scoped WSL training and station names'},
 'production_fabric_observations':0,'production_geometry_observations':0,'images_added':0,'models_or_thresholds_changed':False,
 'dependencies_installed':[],'pi_verified':False,'physical_lcd_tested':False,'owned_test_servers_stopped':True}
write(rp,report)
c.update(updated_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),previous_checkpoint=ref(archive),latest_batch=ref(rp),
 selected_research_station=selected,rollback_station=rollback,active_operations=[],pending_operations=[])
c['open_tasks']=[t for t in c['open_tasks'] if t not in {'R01','R02','R03','R04'}]
c['record_integrity_issue']={'status':'resolved_by_verified_typed_raw_response_recovery','preserved_http_failures':21,
 'recovery_index':ref('records/recoveries/raw-http-responses-v1.json'),'historical_failures_erased':False}
c['next_actions']=[{'task_id':'S01/S04','action':'Human/groupmate review of the17 fabric originals; independent reconciliation and credible textile semantics/rights/grouping before a new label release.','needs_hardware':False},
 {'task_id':'S06','action':'Use offline geometry editor for genuine source-pixel observations; independently reconcile reference/projection evidence before evaluator admission.','needs_hardware':False},
 {'task_id':'S02/S03/S05','action':'Acquire appropriate new groups and predeclare candidate comparisons; preserve genuinely independent garment evaluation.','needs_hardware':False},
 {'task_id':'P01-P07','action':'Obtain garments/webcam/Pi; measure calibration and verify actual ARM64/live/display acceptance.','needs_hardware':True}]
c['tests']['four_task_recovery_nov11']={'python_passed':102,'mocked_cases':52,'layout_scenarios':6,'http_jobs':12,'source':ref(rp)}
c['process_observations']={'date':'2026-11-11','active_scoped_jobs':0,'test_servers_stopped':True,'source':ref(rp)}
def refresh(x):
 if isinstance(x,dict):
  if x.get('path') in mutable and 'sha256'in x:x['sha256']=ref(x['path'])['sha256']
  for v in x.values():refresh(v)
 elif isinstance(x,list):
  for v in x:refresh(v)
refresh(c);known={r['path'] for r in c['references']}
for path in sorted(set(paths)|mutable|{rp,'artifacts/stations/skirt-research-station-v9/station-inventory.json','artifacts/stations/skirt-research-station-v9/station.json'}):
 if path not in known:c['references'].append(ref(path))
errors=[];verify_reference_tree(ROOT,c,errors)
if errors:raise ValueError(errors)
write(cp,c,'w')
vp='records/validation/2026-11-11-four-task-record-validation.json'
validation=validate(ROOT,ROOT/vp);write(vp,validation);print(json.dumps(validation,indent=2))
raise SystemExit(bool(validation['errors']))
