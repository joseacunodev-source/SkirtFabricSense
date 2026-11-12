from pathlib import Path
import hashlib,json,sys
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.validate_records import validate,verify_reference_tree
def h(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def ref(p): return {'path':p,'sha256':h(p)}
def write(p,v): (ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def prepend(p,text):
 f=ROOT/p;s=f.read_text(encoding='utf-8');a,b=s.split('\n',1);f.write_text(a+'\n\n'+text+'\n'+b,encoding='utf-8')
doc='[Waveshare 14447 layout](LCD_14447_LAYOUT.md)'
for p in ['docs/AGENT_HANDOFF.md','docs/TASK_BOARD.md','docs/DOCUMENTATION_INDEX.md','docs/CAMERA_UI.md','docs/REQUIREMENTS.md','docs/HARDWARE.md','docs/DECISIONS.md','docs/STATION_PACKAGE.md']:
 prepend(p,'November 4: user selected Waveshare 14447 (800 × 480, HDMI video and USB resistive touch). Station-v7/research-v12 contains the compact landscape UI, verified with 45 mocked cases and 12 saved-image HTTP jobs. Station-v6 is rollback. Physical screen, touch, camera and Pi performance remain unverified. '+doc+'.')
prepend('README.md','November 4: station-v7/research-v12 contains the compact 800 × 480 layout for the selected Waveshare 14447. [Layout and limitations](docs/LCD_14447_LAYOUT.md). Pi and physical screen verification remain open.')
prepend('CHANGELOG.md','## 2026-11-04 — Package the 5-inch screen layout\n\n- Adapted the landscape UI to the selected 800 × 480 Waveshare 14447 and preserved the scrollable nine-class guide.\n- Verified 45 mocked camera/score/motion cases, package inventory and 12 saved-image HTTP jobs. Station-v7 is selected for desktop research; v6 is rollback.\n- Physical display, touch and Pi performance remain unverified. [Evidence](docs/LCD_14447_LAYOUT.md).')
f=ROOT/'docs/LCD_14447_LAYOUT.md';s=f.read_text(encoding='utf-8');s=s.replace('The new CSS currently exists in mutable `app/static/index.html` only. Selected immutable station-v6 still serves its earlier interface. A future versioned station release requires packaging and verification; do not claim the selected station already contains this design.', 'The compact CSS is packaged in station-v7/research-v12, selected for desktop research after inventory verification and 12 saved-image HTTP jobs. Station-v6 remains rollback and retains its earlier interface.');f.write_text(s,encoding='utf-8')
report={'date':'2026-11-04','status':'desktop_research_verified','selected_station':'artifacts/stations/skirt-research-station-v7','rollback':'artifacts/stations/skirt-research-station-v6','mock_cases':45,'http_jobs':12,'physical_screen_tested':False,'pi_verified':False,'camera_used':False,'new_model_training':False,'evidence':[ref(p) for p in ['app/static/index.html','docs/LCD_14447_LAYOUT.md','records/validation/2026-11-04-lcd-layout/node.log','records/validation/2026-11-04-lcd-layout/preview-800x480.png','records/validation/2026-11-04-lcd-station-http.json','records/validation/2026-11-04-lcd-station-http.execution.json','artifacts/stations/skirt-research-station-v7/station-inventory.json','artifacts/stations/skirt-research-station-v7/station.json','artifacts/releases/skirt-finetune-v1-desktop-research-v12/inventory.json']]}
rp='records/validation/2026-11-04-lcd-layout/review.json';write(rp,report)
cp='records/continuation/latest.json';c=json.loads((ROOT/cp).read_text());c['previous_checkpoint']=ref('records/continuation/2026-11-04-before-lcd-layout.json');c['updated_at']=datetime.now(timezone(timedelta(hours=8))).isoformat();c.pop('timestamp_precision',None)
c['selected_research_station']={'directory':'artifacts/stations/skirt-research-station-v7','inventory':ref('artifacts/stations/skirt-research-station-v7/station-inventory.json'),'configuration':ref('artifacts/stations/skirt-research-station-v7/station.json'),'payload_files':28,'selection':'selected_desktop_research','pi_verified':False,'desktop_http_jobs':12,'evidence':ref('records/validation/2026-11-04-lcd-station-http.json')}
c['rollback_station']={'directory':'artifacts/stations/skirt-research-station-v6','inventory':ref('artifacts/stations/skirt-research-station-v6/station-inventory.json'),'configuration':ref('artifacts/stations/skirt-research-station-v6/station.json'),'selection':'rollback','pi_verified':False}
c['latest_batch']=ref(rp);c['active_operations']=[];c['pending_operations']=[];c['display']={'selection':'Waveshare 14447','resolution':'800x480','touch':'USB resistive','physical_tested':False}
c['next_actions']=[{'task_id':'S07','action':'Implement camera capture-mode selection and negotiated-resolution reporting with freshness checks.','needs_hardware':False},{'task_id':'P03/P05/P06','action':'Test actual Waveshare 14447 touch/readability and webcam on Pi 5, then verify ARM64 runtime, parity and performance.','needs_hardware':True},{'task_id':'S01/S04/P01/P02','action':'Obtain garment evidence, independent labels and measured wearer geometry/calibration.','needs_hardware':True}]
mutable={'app/static/index.html','README.md','CHANGELOG.md','docs/AGENT_HANDOFF.md','docs/TASK_BOARD.md','docs/DOCUMENTATION_INDEX.md','docs/CAMERA_UI.md','docs/REQUIREMENTS.md','docs/HARDWARE.md','docs/DECISIONS.md','docs/STATION_PACKAGE.md'}
def refresh(v):
 if isinstance(v,dict):
  if v.get('path') in mutable and 'sha256' in v:v['sha256']=h(v['path'])
  for x in v.values():refresh(x)
 elif isinstance(v,list):
  for x in v:refresh(x)
refresh(c)
existing={v['path'] for v in c['references']}
for p in sorted(mutable|{rp,'docs/LCD_14447_LAYOUT.md','records/validation/2026-11-04-lcd-layout/preview-800x480.png','records/validation/2026-11-04-lcd-station-http.json','artifacts/stations/skirt-research-station-v7/station-inventory.json','artifacts/stations/skirt-research-station-v7/station.json','artifacts/releases/skirt-finetune-v1-desktop-research-v12/inventory.json'}):
 if p not in existing:c['references'].append(ref(p))
errors=[];verify_reference_tree(ROOT,c,errors)
if errors:raise ValueError(errors)
write(cp,c)
result=validate(ROOT,ROOT/'records/validation/2026-11-04-lcd-layout/records-check.json');write('records/validation/2026-11-04-lcd-layout/records-check.json',result);print(json.dumps(result,indent=2));raise SystemExit(bool(result['errors']))
