"""Archive authentic UI/source captures and the continuation evidence."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.validate_records import verify_reference_tree
from tools.station_package import verify_station
from PIL import Image
def ref(p):return {'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}
def write(p,v,mode='x'):
 with (ROOT/p).open(mode,encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
def prepend(p,t):
 f=ROOT/p;first,rest=f.read_text(encoding='utf-8').split('\n',1);f.write_text(first+'\n\n'+t+'\n'+rest,encoding='utf-8')
folder=ROOT/'output/progress_report_2026-11-11'
captures=json.loads((folder/'capture-record.json').read_text())
checks=[]
for item in captures['captures']:
 if ref(item['source'])['sha256']!=item['source_sha256']:raise ValueError('Changed source')
 with Image.open(folder/item['file']) as image:
  image.load();checks.append({'file':item['file'],'pixels':list(image.size),'source_matches':True})
verify_station(ROOT/'artifacts/stations/skirt-research-station-v8')
archive='records/continuation/2026-11-11-before-progress-screenshots.json'
with (ROOT/archive).open('xb') as f:f.write((ROOT/'records/continuation/latest.json').read_bytes())
caption='output/progress_report_2026-11-11/CAPTIONS_AND_PROGRESS.md'
guide=ROOT/'docs/PROGRESS_SCREENSHOTS_NOV11.md'
guide.write_text('# Progress-report screenshots — November 11, 2026\n\n'
 'Five screenshots and [captions with an adaptable progress paragraph](../'+caption+') are ready. '
 'Two images capture the selected station\'s actual camera-off UI; three render literal source excerpts with line numbers. '
 'No generated imagery, fake predictions, editor chrome, training or hardware tests were used. '
 'The 800 × 480 viewport requires scrolling for lower content; physical LCD acceptance remains open.\n\n'
 'The temporary local server was stopped after capture. Source/model/package files remained unchanged. '
 'The [initial full-record audit](../records/validation/2026-11-11-progress-screenshots-initial.json) found 21 pre-existing malformed '
 'metadata response files from the interrupted November 4 background intake. Preserve and recover those records separately; '
 'do not describe the full audit as passed. Screenshot/source checks and the selected station verification passed.\n\n'
 'Earlier pending fabric/geometry reviewer-tool work remains unaccepted; the user confirmed a human/groupmate can review saved images. '
 'No observations have been inferred from that availability.\n',encoding='utf-8')
note='November 11: [progress-report screenshots](PROGRESS_SCREENSHOTS_NOV11.md) capture the actual camera-off UI and implemented source. Five images visually reviewed; temporary server stopped. Earlier label, geometry and hardware acceptance tasks remain open.'
mutable={'docs/AGENT_HANDOFF.md','docs/DOCUMENTATION_INDEX.md','CHANGELOG.md'}
for p in ['docs/AGENT_HANDOFF.md','docs/DOCUMENTATION_INDEX.md']:prepend(p,note)
prepend('CHANGELOG.md','## 2026-11-11 — Capture progress-report evidence\n\n'
 '- Captured actual desktop and 800 × 480 camera-off UI from verified station-v8, plus three literal code excerpts.\n'
 '- Added captions and an adaptable progress paragraph; visually checked five images and stopped the owned local server.\n'
 '- Recorded pre-existing interrupted background metadata parse errors without changing those files. No training, installs or application/model changes. '
 '[Capture guide](docs/PROGRESS_SCREENSHOTS_NOV11.md).')
zip_path='output/SkirtFabricSense_Progress_Screenshots_2026-11-11.zip'
with zipfile.ZipFile(ROOT/zip_path,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for p in sorted(folder.iterdir()):
  if p.is_file():z.write(p,p.name)
paths=[p.relative_to(ROOT).as_posix() for p in folder.iterdir() if p.is_file()]+[
 zip_path,'docs/PROGRESS_SCREENSHOTS_NOV11.md','tools/capture_progress_screenshots.cjs',
 'records/validation/2026-11-11-progress-screenshots-initial.json']
rp='records/validation/2026-11-11-progress-screenshots.json'
report={'date':'2026-11-11','status':'captures_and_source_checks_passed_with_preexisting_record_errors',
 'captures':checks,'visual_review':'All five inspected; readable, no clipped code. Compact UI scroll limitation preserved.',
 'selected_station_verified':True,'temporary_server_stopped':True,'camera_used':False,'model_trained':False,
 'installs':[],'full_records_audit_passed':False,'preexisting_invalid_metadata_files':21,
 'evidence':[ref(p) for p in paths]}
write(rp,report)
cp='records/continuation/latest.json';c=json.loads((ROOT/cp).read_text())
c.update(updated_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),previous_checkpoint=ref(archive),latest_batch=ref(rp))
def refresh(x):
 if isinstance(x,dict):
  if x.get('path') in mutable and 'sha256'in x:x['sha256']=ref(x['path'])['sha256']
  for v in x.values():refresh(v)
 elif isinstance(x,list):
  for v in x:refresh(v)
refresh(c)
known={r['path'] for r in c['references']}
for p in sorted(set(paths)|mutable|{rp}):
 if p not in known:c['references'].append(ref(p))
c['record_integrity_issue']={'scope':'Interrupted November4 background intake metadata responses','invalid_json_files':21,
 'evidence':ref('records/validation/2026-11-11-progress-screenshots-initial.json'),'status':'requires_recovery_not_modified'}
c['reviewer_availability']={'confirmed':'2026-11-04','human_or_groupmate_can_review_saved_images':True,'does_not_establish_completed_reviews':True}
c['process_observations']={'date':'2026-11-11','scope':'Owned station app server PID373 stopped with SIGINT; launcher exited0; follow-up scoped pgrep returned1','active_capture_server':False}
errors=[];verify_reference_tree(ROOT,c,errors)
if errors:raise ValueError(errors)
write(cp,c,'w')
print(json.dumps({'status':report['status'],'screenshots':len(checks),'checkpoint_hash_errors':errors,'zip':zip_path}))
