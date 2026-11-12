"""Reconcile the completed camera/source batch into the continuation pointer."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.station_package import verify_station
from tools.validate_records import validate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path':path,'sha256':sha(ROOT/path)}


def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def save(path, value, exclusive=True):
    with (ROOT/path).open('x' if exclusive else 'w',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2); stream.write('\n')


def main():
    checked = load('records/validation/2026-10-22-camera-source-check.json')
    http = load('records/validation/2026-10-22-station-v3-http.json')
    assert checked['status'] == 'passed_focused_root_review'
    assert http['status'] == 'passed' and http['all_owned_servers_stopped'] and http['station_unchanged']
    folder = 'artifacts/stations/skirt-research-station-v3'
    station = verify_station(ROOT/folder)
    old_app = ROOT/'artifacts/releases/skirt-finetune-v1-desktop-research-v7'
    new_app = ROOT/'artifacts/releases/skirt-finetune-v1-desktop-research-v8'
    before = load(str(old_app.relative_to(ROOT))+'/inventory.json')
    after = load(str(new_app.relative_to(ROOT))+'/inventory.json')
    a = {r['path']:r['sha256'] for r in before['files']}
    b = {r['path']:r['sha256'] for r in after['files']}
    assert set(a) == set(b) and [p for p in a if a[p] != b[p]] == ['app/static/index.html']
    assert http['ui_sha256'] == b['app/static/index.html']
    latest = load('records/continuation/latest.json')
    archived = 'records/continuation/2026-10-22-before-camera-source.json'
    assert not (ROOT/archived).exists()
    shutil.copyfile(ROOT/'records/continuation/latest.json',ROOT/archived)
    registry = load('data/registry.json')
    assert registry['downloaded_totals']['photographs'] == 1932
    registry['status'] = 'research_station_v3_desktop_verified_product_acceptance_open'
    registry['selected_research_station'].update(
        inventory=ref(folder+'/station-inventory.json'), configuration=ref(folder+'/station.json'),
        rollback='artifacts/stations/skirt-research-station-v2', deployment_approved=False)
    registry['research_updates_oct22'].update({
        'fabric_source_gate':ref('records/review/2026-10-22-imaterialist2018-terms.json'),
        'textilenet_metadata_audit':ref('records/review/2026-10-22-textilenet-gate-agent.json'),
        'textilenet_cached_metadata':ref('data/external/fabric_expansion/metadata/fabric_train.json'),
        'textilenet_rows_audited':155393,'new_original_images':0,'new_training_admissions':0,
        'source_splits_changed':False,'verified_fabric_labels_added':0,
        'source_gate_scope':'Observed source conditions and cached URL identities; not image permissions, garment truth or admissions'})
    save('data/registry.json',registry,False)
    selected = {'directory':folder,'inventory':ref(folder+'/station-inventory.json'),
                'configuration':ref(folder+'/station.json'),'payload_files':station['payload_files'],
                'desktop_http_jobs':12,'pi_verified':False}
    latest['rollback_station'] = latest['selected_research_station']
    latest['selected_research_station'] = selected
    latest['updated_at'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
    latest['previous_checkpoint'] = ref(archived)
    latest['latest_batch'] = ref('records/validation/2026-10-22-camera-source-check.json')
    latest['tests']['windows']['scope'] = 'Earlier full suite before this later batch; retained evidence, not rerun'
    latest['tests']['camera_source_focused'] = {'python_tests':37,'python_passed':37,
        'packaged_ui_mock_scenarios':17,'station_v3_http_jobs':12,
        'scope':'30 package/release and7 metadata tests,17 mocked camera scenarios and12 saved-frame jobs; no new camera accuracy'}
    latest['process_observations'] = checked['process_observations']
    latest['process_observation_scope'] = 'Category fit and owned HTTP check ports18820..18825 only; no unrelated process terminated'
    latest['next_actions'][0]['action'] = ('Satisfy the observed2018 source-rule acceptance gate or another applicable permission basis; '
        'resolve photo attribution and original source/product partitions, then plan bounded training-only skirt/material review. '
        'Do not run TextileNet upstream downloader or interpret155393 metadata rows as photos.')
    latest['pending_inputs'] = ['Applicable source terms/acceptance and attribution before new fabric intake',
        'Independent human label confirmation','Observed wearer references and measured calibration',
        'Actual garments and Raspberry Pi for physical acceptance']
    paths = [r['path'] for r in latest['references']]
    paths += [
        'CHANGELOG.md','docs/REQUIREMENTS.md','docs/DECISIONS.md','docs/ARCHITECTURE.md','docs/DATASETS.md',
        'docs/CAMERA_UI.md','docs/PROJECT_PROGRESS.md','docs/FABRIC_NEXT_GATE.md','docs/CAMERA_SOURCE_UPDATE_OCT22.md',
        'docs/FABRIC_SOURCE_GATE_OCT22.md','records/review/2026-10-22-imaterialist2018-terms.json',
        'records/review/2026-10-22-textilenet-gate-agent.json','data/external/fabric_expansion/metadata/fabric_train.json',
        'tools/datasets/audit_textilenet_metadata.py','tests/test_textilenet_metadata.py',
        'tests/test_station_package.py','tests/camera_ui_lifecycle.cjs','app/static/index.html',
        'artifacts/releases/skirt-finetune-v1-desktop-research-v8/inventory.json',
        folder+'/station-inventory.json',folder+'/station.json',
        'records/validation/2026-10-22-station-v3-http.json',
        'records/validation/2026-10-22-station-v3-http.execution.json',
        'records/validation/2026-10-22-station-v3-http.server.log',
        'records/validation/2026-10-22-camera-source-check.py',
        'records/validation/2026-10-22-camera-source-check.json',
        'records/validation/2026-10-22-camera-source-check-0.log',
        'records/validation/2026-10-22-camera-source-check-1.log',
        'records/validation/2026-10-22-camera-source-finalize.py']
    latest['references'] = [ref(p) for p in dict.fromkeys(paths)]
    save('records/continuation/latest.json',latest,False)
    output = 'records/validation/2026-10-22-camera-source-records.json'
    validation = validate(ROOT,ROOT/output)
    save(output,validation)
    if validation['errors']:
        raise ValueError('Record validation failed: '+str(validation['errors']))
    summary = {'status':'passed_camera_source_batch','recorded_at':latest['updated_at'],
        'checkpoint':ref('records/continuation/latest.json'),'record_validation':ref(output),
        'root_review':ref('records/validation/2026-10-22-camera-source-check.json'),
        'selected_station':selected,'only_app_payload_change':'app/static/index.html',
        'packages_installed':0,'new_originals':0,'training_admissions':0,
        'camera_used':False,'pi_verified':False,'project_complete':False}
    save('records/validation/2026-10-22-camera-source-integration.json',summary)
    print(json.dumps({'status':summary['status'],'validation':validation},indent=2))


if __name__ == '__main__':
    main()
