"""Join already evaluated identical development samples; no retraining or tuning."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
p2=ROOT/'records/validation/2026-10-14-localizer-v2-comparison.json'
p3=ROOT/'records/validation/2026-10-15-localizer-v3-comparison.json'
a=json.loads(p2.read_text());b=json.loads(p3.read_text())
assert a['inputs_sha256']==b['inputs_sha256']
assert a['models']['baseline']==b['models']['baseline']
rows2={r['sample_id']:r for r in a['results']};rows3={r['sample_id']:r for r in b['results']}
assert len(rows2)==len(rows3)==99 and rows2.keys()==rows3.keys()
rows=[]
for sid,r in rows2.items():
 s=rows3[sid]
 for k in ['expected','positive','baseline']:assert r[k]==s[k],(sid,k)
 rows.append({'sample_id':sid,'expected':r['expected'],'positive':r['positive'],'v1':r['baseline'],'v2':r['candidate'],'v3':s['candidate']})
out=ROOT/'records/validation/2026-10-15-localizer-threeway.json'
save(out,{'date':'2026-10-15','method':'Exact sample-id join of saved exported-runtime evaluations; inputs hashes and each baseline output verified identical','sources':[ref(p2),ref(p3)],'models':{'v1':a['models']['baseline'],'v2':a['models']['candidate'],'v3':b['models']['candidate']},'metrics':{'v1':a['metrics']['baseline'],'v2':a['metrics']['candidate'],'v3':b['metrics']['candidate']},'results':rows,'decision':'Do not promote v3: lower positive coverage, correct pleating count and negative rejection than v2; negative rejection worse than v1','limitations':b['limitations']})
record=ROOT/'records/models/2026-10-15-skirt-localizer-v3.json'
save(record,{'release_id':'skirt-localizer-v3','status':'experimental_not_promoted_rejection_regression','run':ref(ROOT/'records/experiments/20261015-localizer-v3/run.json'),'model':ref(ROOT/'artifacts/models/skirt-localizer-v3/model.tflite'),'executed_source':ref(ROOT/'records/experiments/20261015-localizer-v3/training_source.py'),'inputs':ref(ROOT/'records/experiments/20261015-localizer-v3/labelled-inputs.json'),'comparison':ref(out),'input':{'shape':[1,224,224,3],'dtype':'float32','range':[0,255],'preprocessing':'Full RGB bilinear resize224; model normalization'},'output':{'shape':[1,56,56,1],'threshold':.5},'pi_verified':False,'camera_accuracy_verified':False})
print(json.dumps({'model_record':ref(record),'comparison':ref(out)}))
