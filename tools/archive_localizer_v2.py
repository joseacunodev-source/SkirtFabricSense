"""Archive actual localizer v2 artifacts and register the unpromoted development run."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('//wsl.localhost/Ubuntu-24.04/home/skirttrain/skirt-fabric-sense/runs/20261014-localizer-v2')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)}
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    report=json.loads((SOURCE/'run.json').read_text())
    if report['status']!='completed':raise ValueError('Incomplete run')
    archive=ROOT/'records/experiments/20261014-localizer-v2';models=ROOT/'artifacts/models/skirt-localizer-v2'
    archive.mkdir(exist_ok=False);models.mkdir(exist_ok=False)
    copied=[]
    for destination,names in [(archive,['run.json','environment.json','history.json','inputs.json','labelled-inputs.json','validation-predictions.json','validation-masks.npz','training_source.py']),
                              (models,['model.keras','model.tflite','run.json'])]:
        for name in names:
            source=SOURCE/name;target=destination/name;shutil.copyfile(source,target)
            if sha(source)!=sha(target):raise ValueError('Archive copy mismatch')
            copied.append(ref(target))
    if sha(archive/'training_source.py')!=report['source_sha256'] or sha(models/'model.tflite')!=report['export']['sha256']:
        raise ValueError('Executed source/model mismatch')
    save(archive/'archive-integrity.json',{'status':'passed','files':copied,'saved_model_retained_in_wsl':True})
    modelrecord=ROOT/'records/models/2026-10-14-skirt-localizer-v2.json'
    save(modelrecord,{'release_id':'skirt-localizer-v2','status':'experimental_not_promoted_rejection_regression',
        'run':ref(archive/'run.json'),'model':ref(models/'model.tflite'),'executed_source':ref(archive/'training_source.py'),
        'inputs':ref(archive/'labelled-inputs.json'),'comparison':ref(ROOT/'records/validation/2026-10-14-localizer-v2-comparison.json'),
        'input':{'shape':[1,224,224,3],'dtype':'float32','range':[0,255],'preprocessing':'Full RGB bilinear resize224; model normalization'},
        'output':{'shape':[1,56,56,1],'threshold':0.5},'pi_verified':False,'camera_accuracy_verified':False})
    registry_path=ROOT/'data/registry.json';registry=json.loads(registry_path.read_text())
    registry['label_preparation']['negative_extension']={'manifest':ref(ROOT/'data/labels/negative-reviewed-v2.jsonl'),
        'report':ref(ROOT/'data/labels/negative-reviewed-v2.report.json'),'admitted':75,'train':56,'validation':19,
        'new_admitted':63,'independent_human_review_complete':False}
    registry['development_experiments'].append(ref(modelrecord))
    registry['updated_date_asia_manila']='2026-10-14';save(registry_path,registry)
    print(json.dumps({'status':'archived','files':len(copied),'model_sha256':report['export']['sha256']}))
if __name__=='__main__':main()
