from pathlib import Path
import hashlib,json,sys
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.validate_records import validate,verify_reference_tree
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def ref(p):return {'path':p,'sha256':sha(p)}
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def prepend(p,t):
 f=ROOT/p;s=f.read_text(encoding='utf-8');a,b=s.split('\n',1);f.write_text(a+'\n\n'+t+'\n'+b,encoding='utf-8')
review=json.loads((ROOT/'records/validation/2026-11-04-thesis-figures.json').read_text())
for r in review['artifacts']:
 if sha(r['path'])!=r['sha256']:raise ValueError('Figure mismatch: '+r['path'])
completion=json.loads((ROOT/'records/experiments/20261104-image-robustness/completion.json').read_text())
for key,p in [('results_sha256','results.json'),('protocol_sha256','protocol.json'),('source_sha256','executed_source.py')]:
 if completion[key]!=sha('records/experiments/20261104-image-robustness/'+p):raise ValueError('Experiment mismatch: '+p)
for p in ['docs/AGENT_HANDOFF.md','docs/TASK_BOARD.md','docs/DOCUMENTATION_INDEX.md','docs/TRAINING_PLAN.md','docs/EVALUATION.md']:
 prepend(p,'November 4: the existing selected chain was assessed on fixed synthetic brightness and blur changes to the same 118 reused development originals. No model was trained or promoted. [Robustness results](IMAGE_ROBUSTNESS_NOV04.md); [thesis figure pack](THESIS_FIGURES.md). Physical camera, independently verified labels, calibrated length and Pi acceptance remain open.')
prepend('README.md','November 4: five [thesis figures](docs/THESIS_FIGURES.md) and a [saved-image robustness diagnostic](docs/IMAGE_ROBUSTNESS_NOV04.md) are available. This is reused development evidence, not improved or independent accuracy.')
prepend('CHANGELOG.md','## 2026-11-04 — Evaluate image sensitivity and create thesis figures\n\n- Evaluated fixed brightness and blur on 118 development originals using unchanged exports; original predictions match the archived comparison. No fitting, promotion or hardware test.\n- Created five vector PDF and 300-dpi PNG figures with source data and captions. [Evidence](docs/IMAGE_ROBUSTNESS_NOV04.md), [figures](docs/THESIS_FIGURES.md).')
paths=['docs/IMAGE_ROBUSTNESS_NOV04.md','docs/THESIS_FIGURES.md','tools/evaluate_image_robustness.py','tests/test_image_robustness.py','tools/create_thesis_figures.py','records/validation/2026-11-04-thesis-figures.json','records/experiments/20261104-image-robustness/protocol.json','records/experiments/20261104-image-robustness/results.json','records/experiments/20261104-image-robustness/completion.json','records/experiments/20261104-image-robustness/executed_source.py']+[r['path'] for r in review['artifacts']]
report={'date':'2026-11-04','status':'completed_diagnostic_and_figures','original_reference_mismatches':0,'synthetic_conditions':2,'original_parents':118,'new_training':False,'accuracy_improvement_established':False,'pi_verified':False,'figure_count':5,'evidence':[ref(p) for p in paths]};rp='records/validation/2026-11-04-figures-and-robustness.json';write(rp,report)
cp='records/continuation/latest.json';c=json.loads((ROOT/cp).read_text());c['previous_checkpoint']=ref('records/continuation/2026-11-04-before-robustness-figures.json');c['updated_at']=datetime.now(timezone(timedelta(hours=8))).isoformat();c['latest_batch']=ref(rp);c['pending_operations']=[];c['active_operations']=[]
c['next_actions']=[{'task_id':'S01/S04','action':'Obtain independent label confirmation and credible rare-class fabric groups; no retrain from unsupported labels.','needs_hardware':False},{'task_id':'S03','action':'Use robustness failures to inform a predeclared candidate only after suitable new data; preserve a genuinely independent garment test.','needs_hardware':False},{'task_id':'P01-P07','action':'Obtain garments, webcam and Pi for measured calibration, unseen-camera evaluation and ARM64 acceptance.','needs_hardware':True}]
mutable={'README.md','CHANGELOG.md','docs/AGENT_HANDOFF.md','docs/TASK_BOARD.md','docs/DOCUMENTATION_INDEX.md','docs/TRAINING_PLAN.md','docs/EVALUATION.md'}
def refresh(x):
 if isinstance(x,dict):
  if x.get('path') in mutable and 'sha256' in x:x['sha256']=sha(x['path'])
  for v in x.values():refresh(v)
 elif isinstance(x,list):
  for v in x:refresh(v)
refresh(c);existing={x['path'] for x in c['references']}
for p in sorted(set(paths)|mutable|{rp}):
 if p not in existing:c['references'].append(ref(p))
errors=[];verify_reference_tree(ROOT,c,errors)
if errors:raise ValueError(errors)
write(cp,c);out='records/validation/2026-11-04-figures-and-robustness-records.json';result=validate(ROOT,ROOT/out);write(out,result);print(json.dumps(result,indent=2));raise SystemExit(bool(result['errors']))
