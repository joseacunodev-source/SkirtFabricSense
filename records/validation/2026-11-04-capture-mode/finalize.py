from pathlib import Path
import hashlib,json,sys
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.validate_records import validate,verify_reference_tree
def digest(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def ref(p):return {'path':p,'sha256':digest(p)}
def write(p,v): (ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def prepend(p,t):
 f=ROOT/p;s=f.read_text(encoding='utf-8');a,b=s.split('\n',1);f.write_text(a+'\n\n'+t+'\n'+b,encoding='utf-8')
for p in ['docs/AGENT_HANDOFF.md','docs/TASK_BOARD.md','docs/DOCUMENTATION_INDEX.md','docs/CAMERA_UI.md','docs/REQUIREMENTS.md','docs/DECISIONS.md','docs/ARCHITECTURE.md','docs/STATION_PACKAGE.md','docs/LCD_14447_LAYOUT.md']:
 prepend(p,'November 4 latest: station-v8/research-v13 adds requested camera modes and actual decoded-size reporting; v7 is rollback. The user reconfirmed no Pi or webcam. Fifty-two mocked checks and 12 saved-image HTTP jobs pass; physical camera/display and Pi acceptance remain open. [Camera mode evidence](CAMERA_MODE_NOV04.md).')
for p in ['docs/AGENT_HANDOFF.md','docs/TASK_BOARD.md','docs/DOCUMENTATION_INDEX.md']:
 f=ROOT/p;s=f.read_text(encoding='utf-8').replace('November 4 current review:', 'Earlier November 4 review (historical):').replace('Current motion checkpoint:', 'Earlier motion checkpoint:');f.write_text(s,encoding='utf-8')
f=ROOT/'docs/TASK_BOARD.md';s=f.read_text(encoding='utf-8').replace('S07 — Freeze an accepted full-feature release.** Station-v6 includes the reference-inspired UI and tested motion, honest score display and startup-failure clearing; v5 is rollback.', 'S07 — Freeze an accepted full-feature release.** Station-v8 includes the compact UI and camera-mode controls; v7 is rollback.').replace('Latest availability: the user confirms no Pi or webcam on October 23;', 'Latest availability: the user confirms no Pi or webcam on November 4;');f.write_text(s,encoding='utf-8')
f=ROOT/'docs/STATION_PACKAGE.md';s=f.read_text(encoding='utf-8').replace('artifacts/stations/skirt-research-station-v7 --exec','artifacts/stations/skirt-research-station-v8 --exec').replace('For rollback, replace `skirt-research-station-v7` with `skirt-research-station-v6`','For rollback, replace `skirt-research-station-v8` with `skirt-research-station-v7`');f.write_text(s,encoding='utf-8')
prepend('README.md','November 4 latest: station-v8/research-v13 requests camera modes and displays actual decoded dimensions. [Details](docs/CAMERA_MODE_NOV04.md). No Pi or webcam is currently available.')
prepend('CHANGELOG.md','## 2026-11-04 — Add camera mode controls\n\n- Added automatic, 720p, 1080p and 4K ideal requests and actual decoded-size reporting; mode changes stop the stream and invalidate results.\n- Added size/freshness guards, verified 52 mocked cases and 12 saved-image HTTP jobs. Station-v8 is selected for desktop research; v7 is rollback.\n- No camera, LCD or Pi was tested and no dependencies or models changed. [Details](docs/CAMERA_MODE_NOV04.md).')
paths=['docs/CAMERA_MODE_NOV04.md','app/static/index.html','tests/camera_ui_lifecycle.cjs','records/validation/2026-11-04-capture-mode/node.log','records/validation/2026-11-04-capture-mode-http.json','records/validation/2026-11-04-capture-mode-http.execution.json','artifacts/stations/skirt-research-station-v8/station-inventory.json','artifacts/stations/skirt-research-station-v8/station.json','artifacts/releases/skirt-finetune-v1-desktop-research-v13/inventory.json']
report={'date':'2026-11-04','status':'desktop_research_verified','mock_cases':52,'http_jobs':12,'actual_camera_tested':False,'pi_verified':False,'physical_lcd_tested':False,'new_training':False,'installs':0,'evidence':[ref(p) for p in paths]};rp='records/validation/2026-11-04-capture-mode/review.json';write(rp,report)
cpath='records/continuation/latest.json';c=json.loads((ROOT/cpath).read_text());c['previous_checkpoint']=ref('records/continuation/2026-11-04-before-capture-mode.json');c['updated_at']=datetime.now(timezone(timedelta(hours=8))).isoformat();c['latest_batch']=ref(rp)
c['selected_research_station']={'directory':'artifacts/stations/skirt-research-station-v8','inventory':ref('artifacts/stations/skirt-research-station-v8/station-inventory.json'),'configuration':ref('artifacts/stations/skirt-research-station-v8/station.json'),'payload_files':28,'selection':'selected_desktop_research','pi_verified':False,'desktop_http_jobs':12,'evidence':ref('records/validation/2026-11-04-capture-mode-http.json')}
c['rollback_station']={'directory':'artifacts/stations/skirt-research-station-v7','inventory':ref('artifacts/stations/skirt-research-station-v7/station-inventory.json'),'configuration':ref('artifacts/stations/skirt-research-station-v7/station.json'),'selection':'rollback','pi_verified':False}
c['last_hardware_confirmation']={'date':'2026-11-04','raspberry_pi_available':False,'webcam_available':False,'skirts_last_confirmed_unavailable':'2026-10-20'};c['pending_operations']=[];c['active_operations']=[]
c['next_actions']=[{'task_id':'S01/S04','action':'Independent human confirmation and credible rare-class full-view fabric data with rights and group identity; do not repeat smoke training.','needs_hardware':False},{'task_id':'S06','action':'Prepare and independently review actual saved-image wearer geometry observations before implementing a validated producer.','needs_hardware':False},{'task_id':'P01-P07','action':'When garments, webcam and Pi arrive, capture and calibrate, test selected LCD, ARM64 parity and sustained end-to-end operation.','needs_hardware':True}]
mutable={'app/static/index.html','tests/camera_ui_lifecycle.cjs','README.md','CHANGELOG.md','docs/AGENT_HANDOFF.md','docs/TASK_BOARD.md','docs/DOCUMENTATION_INDEX.md','docs/CAMERA_UI.md','docs/REQUIREMENTS.md','docs/DECISIONS.md','docs/ARCHITECTURE.md','docs/STATION_PACKAGE.md','docs/LCD_14447_LAYOUT.md'}
def refresh(x):
 if isinstance(x,dict):
  if x.get('path') in mutable and 'sha256' in x:x['sha256']=digest(x['path'])
  for y in x.values():refresh(y)
 elif isinstance(x,list):
  for y in x:refresh(y)
refresh(c);existing={r['path'] for r in c['references']}
for p in sorted(set(paths)|mutable|{rp}):
 if p not in existing:c['references'].append(ref(p))
errors=[];verify_reference_tree(ROOT,c,errors)
if errors:raise ValueError(errors)
write(cpath,c);out='records/validation/2026-11-04-capture-mode/records-check.json';r=validate(ROOT,ROOT/out);write(out,r);print(json.dumps(r,indent=2));raise SystemExit(bool(r['errors']))
