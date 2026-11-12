"""One-off November 4 review integration; preserve the interrupted checkpoint."""
from pathlib import Path
import hashlib
import json
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.station_package import verify_station
from tools.validate_records import validate, verify_reference_tree

def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def ref(path):
    return {'path':path,'sha256':sha(path)}
def write(path, value):
    (ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def prepend(path, text):
    file=ROOT/path
    content=file.read_text(encoding='utf-8')
    title, rest=content.split('\n',1)
    file.write_text(title+'\n\n'+text+'\n'+rest,encoding='utf-8')
def replace(path, old, new):
    file=ROOT/path
    text=file.read_text(encoding='utf-8')
    if old not in text: raise ValueError('Missing replacement: '+path)
    file.write_text(text.replace(old,new),encoding='utf-8')

archive='records/continuation/2026-11-04-before-purchase-review.json'
with (ROOT/archive).open('xb') as f:
    f.write((ROOT/'records/continuation/latest.json').read_bytes())
link='[November 4 purchase/project review](PURCHASE_REVIEW_NOV04.md)'
prepend('docs/HARDWARE.md', 'Current recommendation: **Pi 5 8GB, official 27W supply, compatible active cooling, 64GB microSD and one autofocus USB webcam**. C920s is the economical candidate; Brio 4K is the higher-detail comparison if affordable. See '+link+' for sources, limits and setup order. Purchase is planned, not confirmed.')
replace('docs/HARDWARE.md','The existing fixed-focus webcam is available for initial framing and software work.', 'The user last confirmed no webcam on October 23 and plans to buy one as of November 4; older webcam access is historical.')
replace('docs/HARDWARE.md','| Existing fixed-focus webcam | 1 | Owned; initial pilot only |','| Previously used fixed-focus webcam | 0 confirmed available | Historical; no current availability |')
replace('docs/HARDWARE.md','Decide whether the deployment uses a hanging/mounted skirt or a worn skirt before final labeling. These are different measurement conditions.', 'The user has selected worn skirts as the primary workflow. Hanging, held and mannequin presentations remain secondary with separate reference conditions.')
replace('docs/HARDWARE.md','**Mounted baseline:**','**Secondary mounted mode:**')
replace('docs/HARDWARE.md','**Worn alternative:**','**Primary worn mode:**')
replace('docs/HARDWARE.md','1. Test the owned webcam and measure room/fixture geometry while the first dataset pilot is assembled.', '1. Obtain one suitable USB webcam and test it on the laptop at full-skirt/wearer framing; measure available room geometry and collect garment evidence.')
prepend('docs/RASPBERRY_PI_DEPLOYMENT.md', 'November 4: station-v6/research-v11 is the current verified desktop research payload; v5 is rollback. The user plans Pi/webcam purchase. Start with the '+link+'. Existing Interpreter loaders, edge preflight and station verification are implemented; clean ARM64 installation, full live benchmarks, service integration and physical acceptance remain unverified. Earlier dated package/runtime notes below are historical candidates, not a current tested Pi lock.')
prepend('README.md', 'November 4: reviewed the project before planned Pi/webcam purchase. [Buying recommendation and bring-up order](docs/PURCHASE_REVIEW_NOV04.md). Station-v6 inventory and 73 focused tests pass; fabric, wearer geometry and Pi acceptance remain open. No purchase, installation or new model improvement is claimed.')
for path in ['docs/AGENT_HANDOFF.md','docs/DOCUMENTATION_INDEX.md','docs/TASK_BOARD.md']:
    prepend(path, 'November 4 current review: '+link+'. Pi/webcam purchase is planned, not confirmed. Station-v6 remains selected; 73 focused tests and package verification pass. The interrupted October 23 records are reconciled; no preview/training process matched the scoped WSL check. Next software task: explicit camera-mode selection and negotiated-mode reporting, then actual camera/garment collection and ARM64 parity.')
replace('docs/TASK_BOARD.md','Updated October 23, 2026.', 'Updated November 4, 2026.')
replace('docs/AGENT_HANDOFF.md','# Agent handoff — October 23, 2026','# Agent handoff — November 4, 2026')
prepend('HANDOFF.md', 'November 4: [purchase/project review](docs/PURCHASE_REVIEW_NOV04.md) reconciles interrupted records and sets hardware bring-up order. No camera/Pi purchase is confirmed. Read the refreshed checkpoint before continuing.')
prepend('docs/REQUIREMENTS.md','November 4 review: R11/R13 gain reconciled evidence records; R15 includes the saved paired analysis of individual regressions. R01/R16 need explicit negotiated capture-mode controls before camera comparison. R03/R05/R14 remain unverified. '+link+'.')
prepend('docs/DECISIONS.md','## November 4 — Prepare a USB-camera Pi 5 station\n\nRecommend Pi 5 8GB with official power and active cooling; retain 4GB as a budget alternative pending measurements. Prefer one autofocus USB camera for laptop collection and Pi deployment. Defer accelerator/display commitments until full-frame capture and CPU timing are measured. Preserve worn-primary scope, nine hemline classes, fabric toggle and research-only model status. Add capture-mode selection as the next software task; advertised 4K does not prove negotiated 4K. '+link+'.')
prepend('CHANGELOG.md','## 2026-11-04 — Review before hardware purchase\n\n- Rechecked manufacturer camera/board specifications and documented the buying and bring-up plan.\n- Corrected stale webcam ownership and worn-secondary wording; reconciled four stale handoff hashes and interrupted October 23 evidence.\n- Verified station-v6 payload and reran 73 focused tests successfully. Preserved zero-photo acquisition failures and pending fabric reviews.\n- No installation, new model, hardware test or app behavior change. [Review](docs/PURCHASE_REVIEW_NOV04.md).')
prepend('docs/DATASETS.md','November 4 reconciliation: collection remains 1,932 registered originals. October 23 fabric queue preparation added zero labels/observations; COCO attempts added zero photographs after transport failures. Commons acquisition code is present but no completed acquisition record exists. [Fabric queue](FABRIC_EVIDENCE_REVIEW.md), '+link+'.')
paths=['docs/PURCHASE_REVIEW_NOV04.md','docs/FABRIC_EVIDENCE_REVIEW.md','docs/DETECTION_UNCERTAINTY_OCT23.md','tools/datasets/fabric_evidence_review.py','tools/datasets/acquire_coco_backgrounds.py','tools/report_detection_uncertainty.py','tests/test_fabric_evidence_review.py','tests/test_coco_background_intake.py','tests/test_detection_uncertainty.py','records/validation/2026-10-23-detection-uncertainty.json','records/review/2026-10-23-fabric-evidence-review/execution.json','records/review/2026-10-23-fabric-evidence-review/verification-final.json','records/review/2026-10-23-fabric-evidence-review/events.jsonl','records/acquisitions/2026-10-23-coco-backgrounds/acquisition.json','records/acquisitions/2026-10-23-coco-backgrounds/retry-official-gcp/acquisition.json','records/validation/2026-11-04-project-review/focused-tests.log','records/validation/2026-11-04-project-review/initial-checkpoint-audit.json','records/validation/2026-11-04-project-review/process-check.json','records/validation/2026-11-04-project-review/finalize.py']
station=verify_station(ROOT/'artifacts/stations/skirt-research-station-v6')
write('records/validation/2026-11-04-project-review/station-verification.json',station)
paths.append('records/validation/2026-11-04-project-review/station-verification.json')
batch={'date':'2026-11-04','status':'review_completed_hardware_acceptance_open','focused_tests':{'run':73,'passed':73,'failed':0},'station_verified':True,'new_images':0,'installs':0,'training_runs':0,'hardware_tested':False,'data_originals':1932,'acquisition_recovery':'COCO zero-photo failures preserved; Commons source exists but no acquisition record; do not auto-resume downloads','evidence':[ref(p) for p in paths]}
batchpath='records/validation/2026-11-04-project-review/review.json'
write(batchpath,batch)
registry=json.loads((ROOT/'data/registry.json').read_text())
registry['updated_date_asia_manila']='2026-11-04'
registry.setdefault('research_updates_oct22',{})['nov04_interrupted_work_reconciliation']=ref(batchpath)
write('data/registry.json',registry)
c=json.loads((ROOT/archive).read_text())
c['updated_at']='2026-11-04T00:00:00+08:00'
c['timestamp_precision']='Client date; exact review time not asserted'
c['previous_checkpoint']=ref(archive)
c['latest_batch']=ref(batchpath)
c['active_operations']=[]
c['process_observations']=[json.loads((ROOT/'records/validation/2026-11-04-project-review/process-check.json').read_text())]
c['last_hardware_confirmation']={'date':'2026-11-04','status':'user_plans_to_buy_pi_and_webcam_purchase_not_confirmed','last_confirmed_no_pi_or_webcam':'2026-10-23','last_confirmed_no_skirts':'2026-10-20'}
c['next_actions']=[{'task_id':'S07/P03','action':'Implement explicit capture mode selection/negotiated-mode reporting with freshness safeguards; then verify using purchased webcam','needs_hardware':False},{'task_id':'S01/S04','action':'Obtain real observations and independent label confirmation using prepared queues; preserve frozen memberships','needs_hardware':False},{'task_id':'P01/P02/P05/P06','action':'Follow November 4 purchase and bring-up sequence: garments, camera acceptance, Pi runtime/parity, geometry calibration, live benchmark','needs_hardware':True}]
c['pending_inputs']=['Exact camera/Pi SKUs and purchase/arrival confirmation','Actual garments and label evidence','Independent wearer/hem observations and measured calibration','ARM64 runtime and complete live acceptance']
c['tests']['nov04_review']=batch['focused_tests']
# Refresh only explicitly reviewed mutable central files, never silently bless changed models.
mutable={'HANDOFF.md','README.md','CHANGELOG.md','data/registry.json','docs/AGENT_HANDOFF.md','docs/DOCUMENTATION_INDEX.md','docs/TASK_BOARD.md','docs/HARDWARE.md','docs/RASPBERRY_PI_DEPLOYMENT.md','docs/REQUIREMENTS.md','docs/DECISIONS.md','docs/DATASETS.md'}
def refresh(v):
    if isinstance(v,dict):
        if v.get('path') in mutable and 'sha256' in v:v['sha256']=sha(v['path'])
        for x in v.values():refresh(x)
    elif isinstance(v,list):
        for x in v:refresh(x)
refresh(c)
existing={r['path'] for r in c['references']}
for p in sorted(set(paths)|mutable|{batchpath}):
    if p not in existing:c['references'].append(ref(p))
errors=[];verify_reference_tree(ROOT,c,errors)
if errors:raise ValueError(errors)
write('records/continuation/latest.json',c)
result=validate(ROOT,ROOT/'records/validation/2026-11-04-project-review/records-check.json')
write('records/validation/2026-11-04-project-review/records-check.json',result)
print(json.dumps(result,indent=2))
raise SystemExit(bool(result['errors']))
