"""Close the reviewed dataset-diagram and partition-check batch."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, subprocess, sys
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.validate_records import validate, verify_reference_tree

def ref(p): return {'path': p, 'sha256': hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}
def write(p, obj, mode='x'):
    with (ROOT/p).open(mode, encoding='utf-8') as f: json.dump(obj, f, indent=2); f.write('\n')
def prepend(p, text):
    f=ROOT/p; first,rest=f.read_text(encoding='utf-8').split('\n',1)
    f.write_text(first+'\n\n'+text+'\n'+rest, encoding='utf-8')

cp='records/continuation/latest.json'; c=json.loads((ROOT/cp).read_text(encoding='utf-8'))
archive='records/continuation/2026-11-04-before-dataset-diagrams.json'
with (ROOT/archive).open('xb') as f: f.write((ROOT/cp).read_bytes())
commands=[['wsl','-d','Ubuntu-24.04','-u','skirttrain','--exec','/usr/bin/pgrep','-af',
           '[t]rain_.*.py|[e]valuate_image_robustness.py|[a]pp.server.*8766|[s]tation_package.py launch'],
          ['C:/Program Files/PowerShell/7/pwsh.exe','-NoProfile','-Command',
           "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(python|pythonw|node)(\\.exe)?$' -and $_.CommandLine -match 'train_|evaluate_image_robustness|app.server|station_package.py launch' } | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"]]
observations=[]
for cmd in commands:
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
    if r.returncode not in ([0,1] if cmd[0]=='wsl' else [0]): raise RuntimeError(r.stderr)
    observations.append({'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
if any(r['stdout'].strip() for r in observations): raise RuntimeError('Scoped process found; review before closing')

note=('November 4 dataset follow-up: four additional [training/validation/test diagrams](THESIS_DATASET_DIAGRAMS.md) '
      'and [actual membership evidence](DATASET_PARTITION_EVIDENCE.md) are complete. '
      'The [partition auditor](DATA_PARTITION_AUDIT.md) passes 19 focused tests and five actual assignment-set checks. '
      'No model was retrained or promoted. Independent labels, final camera/garment tests, calibration and Pi acceptance remain open.')
for p in ['docs/AGENT_HANDOFF.md','docs/TASK_BOARD.md','docs/DOCUMENTATION_INDEX.md']: prepend(p,note)
prepend('README.md','November 4: added [training/validation/test diagrams](docs/THESIS_DATASET_DIAGRAMS.md) '
        'and verified actual per-model memberships with a read-only partition auditor. '
        'The 420/118 split belongs to category presence; final camera/garment testing remains uncollected. '
        '[Current continuation entry point](HANDOFF.md).')
prepend('docs/REQUIREMENTS.md','November 4 dataset follow-up: R11/R12/R13 gain '
        '[partition evidence](DATASET_PARTITION_EVIDENCE.md), [diagrams](THESIS_DATASET_DIAGRAMS.md) and '
        '[semantic metadata checks](DATA_PARTITION_AUDIT.md). Nineteen tests and five actual assignment sets pass. '
        'Independent-label, unseen-camera, calibrated-length and Pi acceptance remain open.')
prepend('docs/DECISIONS.md','## November 4 — Preserve actual subsystem partitions\n\n'
        'Report each selected model\'s recorded train/validation inputs separately. Do not impose a generic three-way '
        'ratio on frozen or reused development data. Protected source sanity photos remain distinct from the uncollected '
        'final camera/garment test. Add read-only semantic checks; conflicting aliases and frozen catalog reassignment fail. '
        'No weights, thresholds, labels or memberships changed. [Evidence](DATASET_PARTITION_EVIDENCE.md), '
        '[diagrams](THESIS_DATASET_DIAGRAMS.md), [auditor](DATA_PARTITION_AUDIT.md).')
prepend('docs/DATASETS.md','November 4: the [per-model partition audit](DATASET_PARTITION_EVIDENCE.md) '
        'and [dataset figures](THESIS_DATASET_DIAGRAMS.md) clarify actual memberships. Collection remains 1,932 originals; '
        'no acquisition, admission, label or split changed.')
prepend('CHANGELOG.md','## 2026-11-04 — Dataset diagrams and partition safeguards\n\n'
        '- Added four vector/300-dpi dataset diagrams, combined PDF and source-bound captions; independently reviewed every rendering.\n'
        '- Audited per-model inputs and protected source roles without opening held-out photographs or changing data.\n'
        '- Added connected-group, protected-provenance and frozen-assignment checks; fixed alias inconsistencies found in root review. Nineteen tests and five actual assignment sets pass.\n'
        '- Corrected the root handoff to station-v8/v7 rollback. No scoped training/preview job remains; no fit, promotion, installation or hardware test. '
        '[Figures](docs/THESIS_DATASET_DIAGRAMS.md), [auditor](docs/DATA_PARTITION_AUDIT.md).')
task=ROOT/'docs/TASK_BOARD.md'; text=task.read_text(encoding='utf-8')
text=text.replace('## Completed\n','## Completed\n\n'
    '- [x] Audit actual train/validation memberships and protected source roles; independently review four [dataset diagrams](THESIS_DATASET_DIAGRAMS.md).\n'
    '- [x] Add partition-leakage and frozen-assignment checks; fix review findings and pass 19 tests plus five actual input-set audits. [Evidence](DATA_PARTITION_AUDIT.md).\n',1)
task.write_text(text,encoding='utf-8')

mutable={'HANDOFF.md','README.md','CHANGELOG.md','docs/AGENT_HANDOFF.md','docs/TASK_BOARD.md',
         'docs/DOCUMENTATION_INDEX.md','docs/REQUIREMENTS.md','docs/DECISIONS.md','docs/DATASETS.md','docs/THESIS_FIGURES.md'}
paths=[p.relative_to(ROOT).as_posix() for p in sorted(OUT.iterdir()) if p.is_file()]
paths += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'output/thesis_dataset_diagrams').iterdir()) if p.is_file()]
paths += ['records/validation/2026-11-04-dataset-partitions-audit.json',
          'records/validation/2026-11-04-dataset-diagrams-initial-integrity.json',
          'docs/DATASET_PARTITION_EVIDENCE.md','docs/THESIS_DATASET_DIAGRAMS.md','docs/DATA_PARTITION_AUDIT.md',
          'tools/create_dataset_diagrams.py','tools/audit_dataset_partitions.py','tests/test_dataset_partitions.py']
rp='records/validation/2026-11-04-dataset-diagrams/review.json'
report={'date':'2026-11-04','status':'completed_reviewed_documentation_and_partition_checks',
        'tests_passed':19,'actual_assignment_sets_checked':5,'new_diagrams':4,
        'visual_reviewers':['root','split_evidence'],'evidence':[ref(p) for p in sorted(set(paths)|mutable)],
        'process_observations':observations,'active_operations':[],'pending_operations':[],
        'model_or_threshold_change':False,'accuracy_improvement_claimed':False,'data_or_split_change':False,
        'dependency_changes':[],'pi_verified':False,'remaining_inputs':c['pending_inputs']}
write(rp,report)
c.update(updated_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),previous_checkpoint=ref(archive),
         latest_batch=ref(rp),active_operations=[],pending_operations=[])
c['process_observation_scope']='Scoped Windows/WSL training, robustness evaluation and station preview names; no processes stopped.'
c['process_observations']={'date':'2026-11-04','checks':observations}
c['tests']['dataset_partitions_nov04']={'run':19,'passed':19,'actual_assignment_sets_checked':5,
                                      'source':ref('records/validation/2026-11-04-dataset-diagrams/verification.json')}
c['dataset_diagrams']={'guide':'docs/THESIS_DATASET_DIAGRAMS.md','new_figures':4,
                      'final_project_test':'not_collected_or_frozen',
                      'source':ref('records/validation/2026-11-04-dataset-partitions-audit.json')}
c['do_not_repeat'] += ['Completed 20261104-image-robustness diagnostic',
                       'Completed thesis figures and November 4 partition audits; preserve existing outputs']
def refresh(x):
    if isinstance(x,dict):
        if x.get('path') in mutable and 'sha256' in x: x['sha256']=ref(x['path'])['sha256']
        for value in x.values(): refresh(value)
    elif isinstance(x,list):
        for value in x: refresh(value)
refresh(c)
existing={r['path'] for r in c['references']}
for p in sorted(set(paths)|mutable|{rp}):
    if p not in existing: c['references'].append(ref(p))
errors=[];verify_reference_tree(ROOT,c,errors)
if errors: raise ValueError(errors)
write(cp,c,'w')
vp='records/validation/2026-11-04-dataset-diagrams/records-validation.json'
result=validate(ROOT,ROOT/vp);write(vp,result);print(json.dumps(result,indent=2))
raise SystemExit(bool(result['errors']))
