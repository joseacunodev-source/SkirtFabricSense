"""Bind UI evidence, the selected package and its intentional loopback preview."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.station_package import verify_station
from tools.validate_records import validate
from PIL import Image


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path':path,'sha256':sha(ROOT/path)}


def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def save(path, value, exclusive=True):
    with (ROOT/path).open('x' if exclusive else 'w',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2); stream.write('\n')


def process(pattern):
    command = ['wsl','-d','Ubuntu-24.04','-u','skirttrain','--exec','/usr/bin/pgrep','-af',pattern]
    done = subprocess.run(command,capture_output=True,text=True,timeout=20)
    assert done.returncode in (0,1)
    return {'command':command,'returncode':done.returncode,'output':done.stdout.strip()}


def main():
    folder = 'artifacts/stations/skirt-research-station-v5'
    ui = folder+'/application/app/static/index.html'
    command = ['C:/Program Files/nodejs/node.exe','tests/camera_ui_lifecycle.cjs',ui]
    done = subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
    with (ROOT/'records/validation/2026-10-22-reference-ui/node.log').open('x',encoding='utf-8') as stream:
        stream.write(done.stdout+done.stderr)
    assert done.returncode == 0 and '18 camera/live-loop scenarios and 21 score cases passed' in done.stdout
    identities = {}
    for version in range(1,6):
        directory = f'artifacts/stations/skirt-research-station-v{version}'
        checked = verify_station(ROOT/directory)
        identities[f'v{version}'] = {'directory':directory,'inventory':ref(directory+'/station-inventory.json'),
            'configuration':ref(directory+'/station.json'),'payload_files':checked['payload_files'],
            'pi_verified':False,'selection':'selected' if version==5 else 'unselected_intermediate' if version==4 else 'preserved'}
    assert identities['v3']['inventory']['sha256'] == 'ec865f2c45a635f7e3abb9fe8bd17dbf0c5b389d47ae110182cf37bee90390f8'
    before = load('artifacts/releases/skirt-finetune-v1-desktop-research-v8/inventory.json')
    after = load('artifacts/releases/skirt-finetune-v1-desktop-research-v10/inventory.json')
    a = {r['path']:r['sha256'] for r in before['files']}
    b = {r['path']:r['sha256'] for r in after['files']}
    assert set(a) == set(b) and [p for p in a if a[p] != b[p]] == ['app/static/index.html']
    assert sha(ROOT/'app/static/index.html') == sha(ROOT/ui)
    http = load('records/validation/2026-10-22-station-v5-http.json')
    assert http['status'] == 'passed' and http['all_owned_servers_stopped'] and http['station_unchanged']
    assert http['http_inference_jobs'] == 12 and http['ui_sha256'] == sha(ROOT/ui)
    with urlopen('http://127.0.0.1:8766/',timeout=5) as response:
        served = response.read(200000)
    assert hashlib.sha256(served).hexdigest() == sha(ROOT/ui)
    active = process('[a]pp.server.*8766|[s]tation_package.py launch')
    lines = active['output'].splitlines()
    assert len(lines) == 2 and any(folder in line for line in lines)
    assert any('station_package.py launch . --port 8766' in line for line in lines)
    tests_stopped = process('[a]pp.server.*1882[89]')
    training = process('[t]rain_category_presence.py')
    assert tests_stopped['returncode'] == training['returncode'] == 1
    evidence = []
    for name in ('user-reference.jpg','desktop.png','mobile.png','fabric-off-held.png'):
        path = 'records/validation/2026-10-22-reference-ui/'+name
        with Image.open(ROOT/path) as picture:
            picture.load(); size = list(picture.size)
        evidence.append({**ref(path),'pixels':size,'role':'user_design_reference_not_training' if name.startswith('user-')
            else 'auxiliary_static_controls_before_final_startup_error_fix' if name.startswith('fabric-')
            else 'packaged_v5_camera_off_browser_screenshot'})
    preview = {'type':'loopback_research_preview','url':'http://127.0.0.1:8766/',
        'package':folder,'exec_session_id':21130,'host':'Ubuntu-24.04/skirttrain',
        'process_ids':[int(line.split()[0]) for line in lines],
        'camera_started_by_agent':False,'fabric_research_loaded':False,
        'operation':'Intentionally left running for user UI review; check actual processes before restarting'}
    report = {
        'recorded_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'status':'passed_reference_ui_batch',
        'source':ref('records/validation/2026-10-22-reference-ui-finalize.py'),
        'ui':ref(ui),'test_source':ref('tests/camera_ui_lifecycle.cjs'),
        'node':{'command':command,'returncode':done.returncode,'log':ref('records/validation/2026-10-22-reference-ui/node.log'),
                'lifecycle_scenarios':18,'score_cases':21,'independent_agent_rerun_passed':True},
        'regression':{'baseline_failure_observed':'Playback failure retained pleated instead of emdash',
            'fix':'Camera startup catch calls stop/invalidate before displaying the error; old track callbacks are superseded'},
        'packages':identities,'only_application_payload_changed_from_v8':'app/static/index.html',
        'http':ref('records/validation/2026-10-22-station-v5-http.json'),
        'browser':{'desktop_viewport':[1280,720],'mobile_viewport':[390,844],
            'mobile_client_width':375,'mobile_scroll_width':375,'mobile_overflow_elements':0,
            'camera_status_observed':'Camera off','viewport_override_reset':True,
            'fabric_off_and_held_guidance_checked':True,'real_app_saved_fabric_preference_preserved':True,
            'preview_ui_sha_matches_packaged_ui':True,'screenshots':evidence,
            'limits':'Camera-off/static control observations only; no real stream, detector box, centimetres or prediction performance'},
        'process_observations':[active,tests_stopped,training], 'active_preview':preview,
        'temporary_static_server':{'port':18770,'exec_session_id':51014,'stopped':True},
        'build_commands':[
            'python -B tools/build_release.py --include-app --output artifacts/releases/skirt-finetune-v1-desktop-research-v9',
            'python -B tools/station_package.py build --application artifacts/releases/skirt-finetune-v1-desktop-research-v9 --presence artifacts/models/skirt-category-presence-v1 --output artifacts/stations/skirt-research-station-v4',
            'python -B tools/build_release.py --include-app --output artifacts/releases/skirt-finetune-v1-desktop-research-v10',
            'python -B tools/station_package.py build --application artifacts/releases/skirt-finetune-v1-desktop-research-v10 --presence artifacts/models/skirt-category-presence-v1 --output artifacts/stations/skirt-research-station-v5'],
        'new_original_images':0,'training_admissions':0,'models_changed':False,'packages_installed':0,
        'camera_used':False,'pi_verified':False,'project_complete':False}
    save('records/validation/2026-10-22-reference-ui.json',report)
    previous = 'records/continuation/2026-10-22-before-reference-ui.json'
    assert not (ROOT/previous).exists()
    shutil.copyfile(ROOT/'records/continuation/latest.json',ROOT/previous)
    latest = load('records/continuation/latest.json')
    registry = load('data/registry.json')
    assert registry['downloaded_totals']['photographs'] == 1932
    registry['status'] = 'research_station_v5_desktop_verified_product_acceptance_open'
    registry['selected_research_station'].update(inventory=identities['v5']['inventory'],
        configuration=identities['v5']['configuration'],rollback=identities['v3']['directory'],deployment_approved=False)
    registry['research_updates_oct22']['reference_ui'] = ref('records/validation/2026-10-22-reference-ui.json')
    save('data/registry.json',registry,False)
    latest['rollback_station'] = latest['selected_research_station']
    latest['selected_research_station'] = {**identities['v5'],'desktop_http_jobs':12}
    latest['unselected_intermediate'] = identities['v4']
    latest['previous_checkpoint'] = ref(previous)
    latest['updated_at'] = report['recorded_at']
    latest['latest_batch'] = ref('records/validation/2026-10-22-reference-ui.json')
    latest['active_operations'] = [preview]
    latest['process_observations'] = report['process_observations']
    latest['process_observation_scope'] = 'Observed preview8766, owned test ports18828/18829 and category fit; unrelated processes untouched'
    latest['tests']['reference_ui'] = {'lifecycle_scenarios':18,'score_cases':21,'http_jobs':12,
        'camera_off_browser_checks':True,'source':ref('records/validation/2026-10-22-reference-ui.json')}
    paths = [r['path'] for r in latest['references']]+[
        'docs/REFERENCE_UI_OCT22.md','records/validation/2026-10-22-reference-ui.json',
        'records/validation/2026-10-22-reference-ui-finalize.py',
        'records/validation/2026-10-22-reference-ui/node.log',
        'records/validation/2026-10-22-station-v5-http.json',
        'records/validation/2026-10-22-station-v5-http.execution.json',
        'records/validation/2026-10-22-station-v5-http.server.log',
        'artifacts/releases/skirt-finetune-v1-desktop-research-v9/inventory.json',
        'artifacts/releases/skirt-finetune-v1-desktop-research-v10/inventory.json']
    paths += [entry['path'] for entry in evidence]
    for version in ('v4','v5'):
        paths += [identities[version][key]['path'] for key in ('inventory','configuration')]
    latest['references'] = [ref(p) for p in dict.fromkeys(paths)]
    save('records/continuation/latest.json',latest,False)
    output = 'records/validation/2026-10-22-reference-ui-records.json'
    validation = validate(ROOT,ROOT/output)
    save(output,validation)
    assert not validation['errors'], validation['errors']
    print(json.dumps({'status':report['status'],'validation':validation,'active_preview':preview},indent=2))


if __name__ == '__main__':
    main()
