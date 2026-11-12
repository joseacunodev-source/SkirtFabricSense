"""Record the presentation-only motion update and refresh its continuation state."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.station_package import verify_station
from tools.validate_records import validate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path':path,'sha256':sha(ROOT/path)}


def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def save(path,value,exclusive=True):
    with (ROOT/path).open('x' if exclusive else 'w',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2);stream.write('\n')


def main():
    folder='artifacts/stations/skirt-research-station-v6'
    ui=folder+'/application/app/static/index.html'
    command=['C:/Program Files/nodejs/node.exe','tests/camera_ui_lifecycle.cjs',ui]
    run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
    log='records/validation/2026-10-22-ui-motion/node.log'
    with (ROOT/log).open('x',encoding='utf-8') as stream:stream.write(run.stdout+run.stderr)
    assert run.returncode==0 and '18 camera/live-loop scenarios, 21 score cases and 6 motion cases passed' in run.stdout
    latest=load('records/continuation/latest.json')
    old=latest['selected_research_station']
    assert old['directory'].endswith('station-v5')
    assert sha(ROOT/old['inventory']['path'])==old['inventory']['sha256']
    verify_station(ROOT/old['directory'])
    checked=verify_station(ROOT/folder)
    before=load('artifacts/releases/skirt-finetune-v1-desktop-research-v10/inventory.json')
    after=load('artifacts/releases/skirt-finetune-v1-desktop-research-v11/inventory.json')
    a={r['path']:r['sha256'] for r in before['files']};b={r['path']:r['sha256'] for r in after['files']}
    assert set(a)==set(b) and [p for p in a if a[p]!=b[p]]==['app/static/index.html']
    assert sha(ROOT/ui)==sha(ROOT/'app/static/index.html')
    with urlopen('http://127.0.0.1:8766/',timeout=5) as response:body=response.read(200000)
    assert hashlib.sha256(body).hexdigest()==sha(ROOT/ui)
    argv=['wsl','-d','Ubuntu-24.04','-u','skirttrain','--exec','/usr/bin/pgrep','-af','[a]pp.server.*8766|[s]tation_package.py launch']
    processes=subprocess.run(argv,capture_output=True,text=True,timeout=20)
    lines=processes.stdout.strip().splitlines()
    assert processes.returncode==0 and len(lines)==2 and any(folder in line for line in lines)
    preview={'type':'loopback_research_preview','url':'http://127.0.0.1:8766/','package':folder,
        'exec_session_id':66571,'host':'Ubuntu-24.04/skirttrain','process_ids':[int(line.split()[0]) for line in lines],
        'camera_started_by_agent':False,'fabric_research_loaded':False,
        'operation':'Intentionally running for UI review; verify actual state before restarting'}
    report={'recorded_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'status':'passed_ui_motion_update',
        'source':ref('records/validation/2026-10-22-ui-motion-finalize.py'),
        'ui':ref(ui),'test_source':ref('tests/camera_ui_lifecycle.cjs'),
        'node':{'command':command,'returncode':run.returncode,'log':ref(log),'lifecycle_scenarios':18,
            'score_cases':21,'motion_cases':6,'independent_agent_review_and_rerun':True},
        'browser_observations':{'header_animation':'interface-in','header_duration_seconds':.28,
            'panel_animation':'interface-in','control_transition_seconds':.15,'switch_thumb_transition_seconds':.18,
            'fabric_toggle_checked_and_saved_off_restored':True,'camera_state':'Camera off','score':'—',
            'screenshot':ref('records/validation/2026-10-22-ui-motion/preview.png')},
        'only_application_payload_changed':'app/static/index.html','models_and_backend_unchanged':True,
        'fresh_http_inference_jobs':0,'prior_http_evidence':ref('records/validation/2026-10-22-station-v5-http.json'),
        'exact_served_ui_verified':True,'process_check':{'command':argv,'output':processes.stdout.strip()},
        'active_preview':preview,'old_preview_exec_session':21130,'old_preview_stopped':True,
        'packages_installed':0,'new_training_images':0,'camera_used':False,'pi_verified':False,
        'limits':'Mock animation/lifecycle checks and camera-off browser verification; no new ML accuracy or hardware performance claim.'}
    report_path='records/validation/2026-10-22-ui-motion.json';save(report_path,report)
    archived='records/continuation/2026-10-22-before-ui-motion.json'
    assert not (ROOT/archived).exists();shutil.copyfile(ROOT/'records/continuation/latest.json',ROOT/archived)
    registry=load('data/registry.json')
    registry['status']='research_station_v6_desktop_verified_product_acceptance_open'
    registry['selected_research_station'].update(inventory=ref(folder+'/station-inventory.json'),
        configuration=ref(folder+'/station.json'),rollback=old['directory'],deployment_approved=False)
    registry['research_updates_oct22']['ui_motion']=ref(report_path);save('data/registry.json',registry,False)
    latest['rollback_station']=old
    latest['selected_research_station']={'directory':folder,'inventory':ref(folder+'/station-inventory.json'),
        'configuration':ref(folder+'/station.json'),'payload_files':checked['payload_files'],'selection':'selected',
        'pi_verified':False,'desktop_http_jobs':0,'exact_served_ui_verified':True,
        'prior_model_http_evidence':ref('records/validation/2026-10-22-station-v5-http.json')}
    latest['updated_at']=report['recorded_at'];latest['previous_checkpoint']=ref(archived)
    latest['latest_batch']=ref(report_path);latest['active_operations']=[preview]
    latest['process_observations']=[report['process_check']]
    latest['process_observation_scope']='Owned loopback preview8766; no unrelated process stopped'
    latest['tests']['ui_motion']={'lifecycle_scenarios':18,'score_cases':21,'motion_cases':6,'source':ref(report_path)}
    paths=[r['path'] for r in latest['references']]+[
        'docs/UI_MOTION_OCT22.md',report_path,'records/validation/2026-10-22-ui-motion-finalize.py',log,
        'records/validation/2026-10-22-ui-motion/preview.png',folder+'/station-inventory.json',folder+'/station.json',
        'artifacts/releases/skirt-finetune-v1-desktop-research-v11/inventory.json']
    latest['references']=[ref(path) for path in dict.fromkeys(paths)]
    save('records/continuation/latest.json',latest,False)
    output='records/validation/2026-10-22-ui-motion-records.json'
    validation=validate(ROOT,ROOT/output);save(output,validation)
    assert not validation['errors'],validation['errors']
    print(json.dumps({'status':report['status'],'validation':validation,'preview':preview},indent=2))


if __name__=='__main__':main()
