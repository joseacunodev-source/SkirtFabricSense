"""Write and verify a stable handoff without repeating completed training."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.station_package import verify_station
from tools.validate_records import validate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def ref(path):
    return {'path':path,'sha256':sha(ROOT/path)}


def save(path,record,exclusive=True):
    with (ROOT/path).open('x' if exclusive else 'w',encoding='utf-8',newline='\n') as stream:
        json.dump(record,stream,indent=2,ensure_ascii=False); stream.write('\n')


def main():
    registry = load('data/registry.json')
    run = load('records/experiments/20261021-category-presence-v1/run.json')
    review = load('records/validation/2026-10-21-category-presence-artifact-review.json')
    comparison = load('records/validation/2026-10-21-category-presence-comparison.json')
    if (run['status'] != 'completed' or review['checks_passed'] != 115 or review['checks_failed']
            or not all(review['checks'].values()) or registry['downloaded_totals']['photographs'] != 1932):
        raise ValueError('Completed evidence disagrees')
    metrics = comparison['metrics']['v2_plus_presence']
    if (metrics['positive_accepted'],metrics['correct_pleating'],metrics['negative_rejected']) != (44,38,42):
        raise ValueError('Research selection metrics disagree')
    for log_path,count,ending in (
        ('records/validation/2026-10-22-tests.log',464,'OK (skipped=3)'),
        ('records/validation/2026-10-21-wsl-tests.log',20,'OK')):
        text = (ROOT/log_path).read_text(encoding='utf-8-sig')
        if not re.search(r'Ran '+str(count)+r' tests',text) or ending not in text:
            raise ValueError('Expected test result missing')
    stations = {}
    for version,report in (('v1','2026-10-21-station-http.json'),('v2','2026-10-21-station-v2-http.json')):
        package = 'artifacts/stations/skirt-research-station-'+version
        verified = verify_station(ROOT/package)
        http = load('records/validation/'+report)
        if http['status'] != 'passed' or not http['all_owned_servers_stopped'] or not http['station_unchanged']:
            raise ValueError('Station runtime check failed')
        stations[version] = {'directory':package,'inventory':ref(package+'/station-inventory.json'),
                             'configuration':ref(package+'/station.json'),'payload_files':verified['payload_files'],
                             'desktop_http_jobs':12,'pi_verified':False}
    process_checks = []
    for pattern in ('[t]rain_category_presence.py','[a]pp.server.*1882[0-3]'):
        result = subprocess.run(['wsl','-d','Ubuntu-24.04','-u','skirttrain','--exec',
                                 '/usr/bin/pgrep','-af',pattern],capture_output=True,text=True,timeout=20)
        if result.returncode != 1 or result.stdout.strip():
            raise ValueError('Expected owned operation is active or process observation failed')
        process_checks.append({'pattern':pattern,'returncode':result.returncode,'matching_processes':0})
    paths = [
        'AGENTS.md','README.md','HANDOFF.md','docs/AGENT_HANDOFF.md','docs/DOCUMENTATION_INDEX.md',
        'docs/TASK_BOARD.md','docs/OCT22_INTEGRATION.md','docs/STATION_PACKAGE.md',
        'docs/CATEGORY_PRESENCE_RESULTS.md','docs/FABRIC_SOURCE_SEARCH_OCT21.md',
        'docs/WORN_GEOMETRY_EVALUATION.md','data/registry.json',
        'data/manifests/worn-pleating-development-v1.jsonl','data/labels/negative-reviewed-v3.jsonl',
        'data/manifests/source-skirt-development-splits.json',
        'artifacts/models/skirt-category-presence-v1/model.tflite',
        'artifacts/models/skirt-localizer-v2/model.tflite','artifacts/models/fabric-smoke-v1/model.tflite',
        'records/models/2026-10-21-skirt-category-presence-v1.json',
        'records/experiments/20261021-category-presence-v1/run.json',
        'records/experiments/20261021-category-presence-v1/inputs.json',
        'records/experiments/20261021-category-presence-v1/source-category-targets.json',
        'records/validation/2026-10-21-category-presence-artifact-review.json',
        'records/validation/2026-10-21-category-presence-comparison.json',
        'records/validation/2026-10-21-station-http.json',
        'records/validation/2026-10-21-station-v2-http.json',
        'records/validation/2026-10-21-geometry-readiness.json',
        'records/geometry/2026-10-21-readiness/mapping.json',
        'records/review/2026-10-20-fabric-source-attribute-audit.json',
        'records/review/2026-10-21-fabric-source-search.json',
        'records/validation/2026-10-22-tests.log','records/validation/2026-10-21-wsl-tests.log',
        'tools/validate_records.py','tools/station_package.py','tools/check_station_http.py',
        'tools/evaluate_worn_geometry.py','tools/training/train_presence_finetune.py',
        'tools/training/train_category_presence.py']
    metadata = ROOT/'records/acquisitions/2026-10-21-fabric-source-research'
    paths += [p.relative_to(ROOT).as_posix() for p in sorted(metadata.iterdir()) if p.is_file()]
    latest = ROOT/'records/continuation/latest.json'
    old = ROOT/'records/continuation/2026-10-21-integration-in-progress.json'
    if not old.exists():
        shutil.copyfile(latest,old)
    checkpoint = {
        'schema_version':1,'updated_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'status':'stable_desktop_research_checkpoint','project_complete':False,
        'supervised_demo_accepted':False,'completion_percentage':None,
        'entry_point':'HANDOFF.md','task_board':'docs/TASK_BOARD.md',
        'selected_research_station':stations['v2'],'rollback_station':stations['v1'],
        'selected_presence_model':'artifacts/models/skirt-category-presence-v1',
        'selected_research_metrics':metrics,
        'data':{'original_images':1932,'verified_physical_garments':None,
                'negative_development_admissions':207,'new_fabric_admissions':0,
                'verified_project_fabric_labels':0,'observed_geometry_examples':0},
        'last_hardware_confirmation':{'date':'2026-10-20','skirts_available':False,'raspberry_pi_available':False},
        'acceptance':{'fabric_model_accepted':False,'calibrated_length_verified':False,
                      'unseen_garment_camera_test_passed':False,'pi_verified':False,'demo_rehearsed':False},
        'tests':{'windows':{'run':464,'passed':461,'skipped':3},'focused_wsl':{'run':20,'passed':20}},
        'pending_operations':[],'active_operations':[],
        'process_observation_scope':'Category fit and owned HTTP check ports only; no unrelated process was terminated',
        'process_observations':process_checks,
        'open_tasks':['S01','S02','S03','S04','S05','S06','S07','P01','P02','P03','P04','P05','P06','P07','M01'],
        'next_actions':[
            {'task_id':'S04','action':'Resolve iMaterialist2018 photo terms, product grouping and skirt-specific material association before any bounded garment-image intake','needs_hardware':False},
            {'task_id':'S01','action':'Obtain independent human confirmation of flagged source/pleating labels; preserve historical freezes','needs_hardware':False},
            {'task_id':'P01/P05','action':'Obtain actual development/held-out garments and Pi; then camera, geometry/calibration and ARM64 acceptance can begin','needs_hardware':True}],
        'do_not_repeat':['Completed 20261021-category-presence-v1 fit','Completed station-v1/v2 builds and HTTP checks','Do not train fabric from missing or wrongly mapped labels'],
        'previous_checkpoint':ref(old.relative_to(ROOT).as_posix()),
        'references':[ref(p) for p in dict.fromkeys(paths)]}
    save('records/continuation/latest.json',checkpoint,False)
    output = ROOT/'records/validation/2026-10-22-records.json'
    checked = validate(ROOT,output)
    save(output.relative_to(ROOT).as_posix(),checked)
    if checked['errors']:
        raise ValueError('Record validation failed: '+str(checked['errors']))
    summary = {'date_asia_manila':'2026-10-22','status':'passed_research_recovery_and_handoff',
        'source_sha256':sha(Path(__file__)),'checkpoint':ref('records/continuation/latest.json'),
        'record_validation':ref('records/validation/2026-10-22-records.json'),
        'selected_research_station':stations['v2'],'rollback_station':stations['v1'],
        'metrics':metrics,'packages_installed':0,'camera_used':False,'pi_verified':False,
        'project_complete':False,'physical_acceptance_remains_open':True}
    save('records/validation/2026-10-22-integration.json',summary)
    print(json.dumps({'status':summary['status'],'record_validation':checked},indent=2))


if __name__ == '__main__':
    main()
