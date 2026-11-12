"""Root review of the camera fix, copied package and fabric metadata evidence."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.datasets.audit_textilenet_metadata import audit
from tools.station_package import verify_station


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path, "sha256": sha(ROOT/path)}


def save(path, value):
    with (ROOT/path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')


def main():
    observations = []
    commands = [
        [sys.executable, '-B', '-m', 'unittest', 'tests.test_textilenet_metadata', '-v'],
        ['C:/Program Files/nodejs/node.exe', 'tests/camera_ui_lifecycle.cjs',
         'artifacts/stations/skirt-research-station-v3/application/app/static/index.html'],
    ]
    for index, command in enumerate(commands):
        done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
        log = f'records/validation/2026-10-22-camera-source-check-{index}.log'
        with (ROOT/log).open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(done.stdout + done.stderr)
        observations.append({'command':command,'returncode':done.returncode,'output':ref(log)})
        if done.returncode:
            raise ValueError('Focused check failed: '+log)
    record = json.loads((ROOT/'records/review/2026-10-22-textilenet-gate-agent.json').read_text(encoding='utf-8'))
    actual = audit(ROOT/record['train_input']['path'])
    assert actual['train_input']['sha256'] == record['train_input']['sha256']
    assert actual['train_summary'] == record['train_summary']
    assert actual['source_sha256'] == record['source_sha256']
    assert actual['protected_overlap_checked'] is False
    assert actual['training_admissions'] == 0
    responses = record['bounded_primary_metadata_requests']['report_generation_requests']
    for response in responses:
        body = response['response_body_utf8'].encode('utf-8')
        assert len(body) == response['bytes']
        assert hashlib.sha256(body).hexdigest() == response['sha256']
    body = (ROOT/record['train_input']['path']).read_bytes()
    blob = hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
    assert blob == record['pinned_manifest_identity']['official_blob_sha1']
    tree_response = next(r for r in responses if r['key'] == 'repository_tree')
    tree = json.loads(tree_response['response_body_utf8'])
    official = next(r for r in tree['tree'] if r['path'] == 'json/fabric_train.json')
    assert official['sha'] == blob and official['size'] == len(body)
    stations = {}
    for version, expected in (
        ('v1','7e1e8fea3bfbd8d15614b1f457768d8cecb6bec059658079b0f20374e50ab0a4'),
        ('v2','19444a4ea1622a26822d795bfccb61c558a27383df3741ed84bbeea1544b38f4'),
        ('v3','ec865f2c45a635f7e3abb9fe8bd17dbf0c5b389d47ae110182cf37bee90390f8')):
        folder = 'artifacts/stations/skirt-research-station-'+version
        assert sha(ROOT/folder/'station-inventory.json') == expected
        checked = verify_station(ROOT/folder)
        stations[version] = {'directory':folder,'inventory':ref(folder+'/station-inventory.json'),
                             'payload_files':checked['payload_files']}
    ui = 'artifacts/stations/skirt-research-station-v3/application/app/static/index.html'
    assert sha(ROOT/ui) == sha(ROOT/'app/static/index.html')
    http = json.loads((ROOT/'records/validation/2026-10-22-station-v3-http.json').read_text())
    assert http['status'] == 'passed' and http['all_owned_servers_stopped'] and http['station_unchanged']
    assert http['ui_sha256'] == sha(ROOT/ui) and http['http_inference_jobs'] == 12
    process_checks = []
    for pattern in ('[t]rain_category_presence.py','[a]pp.server.*1882[0-5]'):
        done = subprocess.run(['wsl','-d','Ubuntu-24.04','-u','skirttrain','--exec',
                               '/usr/bin/pgrep','-af',pattern],capture_output=True,text=True,timeout=20)
        assert done.returncode == 1 and not done.stdout.strip()
        process_checks.append({'pattern':pattern,'returncode':done.returncode,'matching_processes':0})
    report = {
        'recorded_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'status':'passed_focused_root_review','source':ref('records/validation/2026-10-22-camera-source-check.py'),
        'commands':observations,'metadata_tests_passed':7,'packaged_camera_mock_scenarios_passed':17,
        'prior_console_observed_checks':[
            {'command':'python -B -m unittest tests.test_station_package tests.test_release_builder tests.test_release_verifier -v',
             'tests_run':30,'passed':30,'evidence_scope':'Root-observed console result earlier in this batch; no raw log retained'},
            {'command':'node tests/camera_ui_lifecycle.cjs before the camera fix',
             'outcome':'Expected regression failure: Camera on instead of Camera interrupted'},
            {'command':'python -B -m unittest tests.test_station_package tests.test_release -v',
             'outcome':'10 station tests passed, one import error because tests.test_release does not exist; corrected command above passed30 tests'}],
        'textilenet_report':ref('records/review/2026-10-22-textilenet-gate-agent.json'),
        'cached_metadata_recomputed':True,'embedded_primary_response_hashes_verified':len(responses),
        'pinned_git_blob_verified':blob,'new_images':0,'training_admissions':0,
        'stations':stations,'workspace_and_packaged_ui_identical':True,
        'http':ref('records/validation/2026-10-22-station-v3-http.json'),
        'process_observations':process_checks,'packages_installed':0,'camera_used':False,'pi_verified':False,
        'limitations':'Focused checks only; no new recognition accuracy, independent labels, measured geometry or physical acceptance.'}
    save('records/validation/2026-10-22-camera-source-check.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('commands','stations')},indent=2))


if __name__ == '__main__':
    main()
