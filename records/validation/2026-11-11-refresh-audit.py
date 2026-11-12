"""Read-only recovery audit; no fitting, network requests or image admissions."""
from pathlib import Path
import hashlib,json,subprocess,sys
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.validate_records import verify_reference_tree,validate
from tools.station_package import verify_station
def ref(p):return {'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}
c=json.loads((ROOT/'records/continuation/latest.json').read_text())
errors=[];n=verify_reference_tree(ROOT,c,errors)
station=verify_station(ROOT/c['selected_research_station']['directory'])
runs=[]
for p in sorted((ROOT/'records/experiments').glob('*/run.json')):
 d=json.loads(p.read_text(encoding='utf-8-sig'))
 runs.append({'path':p.relative_to(ROOT).as_posix(),'status':d.get('status'),'run_id':d.get('run_id')})
acq=json.loads((ROOT/'records/acquisitions/2026-11-04-backgrounds/acquisition.json').read_text())
acq_errors=[]
for item in acq['artifacts']:
 p=ROOT/item['path']
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
  acq_errors.append(item['path'])
partial_paths=['tools/serve_fabric_review.py','tools/static/fabric_review.html','tests/test_fabric_review_ui.py',
 'docs/FABRIC_REVIEW_UI.md','tools/geometry_annotation.py','tools/static/geometry_annotation.html',
 'tests/test_geometry_annotation.py','docs/GEOMETRY_ANNOTATION.md']
partial=[{'path':p,'exists':(ROOT/p).exists(),**({'sha256':ref(p)['sha256']} if (ROOT/p).is_file() else {})} for p in partial_paths]
events=ROOT/'records/review/2026-10-23-fabric-evidence-review/events.jsonl'
review_events=sum(bool(line.strip()) for line in events.read_text().splitlines())
cmd=['wsl','-d','Ubuntu-24.04','-u','skirttrain','--exec','/usr/bin/pgrep','-af',
 '[a]pp.server|[s]tation_package.py launch|[t]rain_.*.py|[e]valuate_image_robustness.py']
proc=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
result=validate(ROOT)
report={'date':datetime.now(timezone(timedelta(hours=8))).isoformat(),'status':'review_complete_with_open_recovery_items',
 'checkpoint_references_checked':n,'checkpoint_errors':errors,'selected_station_verified':station,
 'experiment_runs':runs,'started_run_records':[r for r in runs if r['status']=='started'],
 'process_observation':{'command':cmd,'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr},
 'background_acquisition':{'source':ref('records/acquisitions/2026-11-04-backgrounds/acquisition.json'),
 'status':acq['status'],'images_acquired':acq['images_acquired'],'training_admissions':acq['training_admissions'],
 'artifact_hash_errors':acq_errors,'artifacts_checked':len(acq['artifacts'])},
 'interrupted_outputs':partial,'fabric_review_events':review_events,'record_validation':result,
 'dataset_or_models_changed':False,'new_training':False,'dependencies_changed':False}
out=ROOT/'records/validation/2026-11-11-refresh-audit.json'
with out.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'checkpoint_references_checked':n,'checkpoint_errors':errors,'started_runs':report['started_run_records'],
 'experiments_checked':len(runs),'scoped_processes':proc.stdout,'background_artifact_errors':acq_errors,
 'background_artifacts_checked':len(acq['artifacts']),'fabric_review_events':review_events,
 'record_errors':len(result['errors'])},indent=2))
