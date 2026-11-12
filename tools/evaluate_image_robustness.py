"""Paired fixed-transform stress check of frozen development images and exports."""
import hashlib,json,os,platform,sys,time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
os.environ['CUDA_VISIBLE_DEVICES']='-1'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUTPUT=ROOT/'records/experiments/20261104-image-robustness'
ARCHIVE=ROOT/'records/experiments/20261021-category-presence-v1'
REFERENCE=ROOT/'records/validation/2026-10-21-category-presence-comparison.json'
CONDITIONS=('original','brightness_0.8','gaussian_blur_radius_1')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def transform(image,condition):
    from PIL import ImageEnhance,ImageFilter
    if condition=='original':return image.copy()
    if condition=='brightness_0.8':return ImageEnhance.Brightness(image).enhance(0.8)
    if condition=='gaussian_blur_radius_1':return image.filter(ImageFilter.GaussianBlur(radius=1))
    raise ValueError('Unknown predetermined transform')
def counts(rows):
    positive=[x for x in rows if x['target']==1];negative=[x for x in rows if x['target']==0]
    return {'positive_total':len(positive),'positive_accepted':sum(x['accepted'] for x in positive),
            'correct_pleating':sum(x['accepted'] and x['prediction']==x['truth'] for x in positive),
            'negative_total':len(negative),'negative_rejected':sum(not x['accepted'] for x in negative)}
def state(row):
    if row['target']==0:return 'false_accept' if row['accepted'] else 'rejected'
    if not row['accepted']:return 'unavailable'
    return 'correct' if row['prediction']==row['truth'] else 'wrong'
def paired(original,modified):
    if len(original)!=len(modified) or [r['sample_id'] for r in original]!=[r['sample_id'] for r in modified]:raise ValueError('Paired membership changed')
    out=Counter()
    for a,b in zip(original,modified):
        if (a['target'],a['truth'])!=(b['target'],b['truth']):raise ValueError('Paired truth changed')
        out[f"{state(a)} -> {state(b)}"]+=1
    return dict(sorted(out.items()))
def write_new(path,obj):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n')
def main():
    import numpy as np
    import tensorflow as tf
    from PIL import Image,__version__ as pillow_version
    from app.presence import PresenceGate
    from app.localization import SkirtLocalizer
    from app.inference import SkirtPredictor
    from tools.training.train_presence import validate
    tf.config.set_visible_devices([], 'GPU')
    run=json.loads((ARCHIVE/'run.json').read_text(encoding='utf-8'))
    inputs=ARCHIVE/'inputs.json';comparison=json.loads(REFERENCE.read_text(encoding='utf-8'))
    if run['status']!='completed' or sha(inputs)!=run['frozen_inputs_sha256'] or sha(inputs)!=comparison['inputs_sha256'] or run['split_hash']!=comparison['split_hash']:raise ValueError('Frozen archive mismatch')
    rows=json.loads(inputs.read_text(encoding='utf-8'));validate(rows)
    rows=[r for r in rows if r['split']=='development_validation']
    if len(rows)!=118 or len({r['sample_id'] for r in rows})!=118:raise ValueError('Expected exact validation membership')
    refs={r['sample_id']:r for r in comparison['results']}
    if len(refs)!=118 or set(refs)!={r['sample_id'] for r in rows}:raise ValueError('Reference membership mismatch')
    for r in rows:
        if sha(ROOT/r['original_path'])!=r['sha256']:raise ValueError('Image changed: '+r['sample_id'])
    if OUTPUT.exists():raise FileExistsError('Do not overwrite previous run')
    OUTPUT.mkdir(parents=True)
    protocol={'created_utc':datetime.now(timezone.utc).isoformat(),'status':'frozen_before_inference','scope':'source-domain reused development only',
      'input_sha256':sha(inputs),'split_hash':run['split_hash'],'reference_sha256':sha(REFERENCE),'source_sha256':sha(__file__),
      'selected_path':'presence category-v1 + localizer-v2 + pleating fine-v1','thresholds':{'presence':0.5,'mask':0.5},
      'conditions':{'original':'RGB source as archived','brightness_0.8':'Pillow ImageEnhance.Brightness factor 0.8','gaussian_blur_radius_1':'Pillow GaussianBlur radius 1 source pixel'},
      'seed':None,'validation_originals':118,'fit_or_tune':False,'final_test_used':False,'originals_count_as_new_data':False,
      'limitations':['Transforming images is not a measured webcam condition','Development data was used in checkpoint selection','Physical specimen independence and independent human truth not established','Performance remains unapproved for live or Pi use']}
    write_new(OUTPUT/'protocol.json',protocol)
    (OUTPUT/'executed_source.py').write_bytes(Path(__file__).read_bytes())
    write_new(OUTPUT/'status.json',{'state':'running','protocol_sha256':sha(OUTPUT/'protocol.json'),'started_utc':datetime.now(timezone.utc).isoformat()})
    gate=PresenceGate(ROOT/'artifacts/models/skirt-category-presence-v1')
    mask=SkirtLocalizer(ROOT/'artifacts/models/skirt-localizer-v2')
    classifier=SkirtPredictor(ROOT/'artifacts/releases/skirt-finetune-v1-desktop-research-v7')
    if (gate.sha256!=comparison['models']['presence'] or mask.sha256!=comparison['models']['masks']['v2'] or sha(ROOT/'artifacts/releases/skirt-finetune-v1-desktop-research-v7/model.tflite')!=comparison['models']['pleating']):raise ValueError('Selected model mismatch')
    results={k:[] for k in CONDITIONS};started=time.monotonic();mismatches=[]
    for row in rows:
        with Image.open(ROOT/row['original_path']) as opened:source=opened.convert('RGB')
        for condition in CONDITIONS:
            image=transform(source,condition);presence=gate.check(image);region=mask.locate(image)
            # Match historical comparator exactly: predict on localizer ROI before applying gate.
            mask_accept=region['status']=='provisional'
            prediction=classifier.predict(image,tuple(region['roi']),True)['style']['label'] if mask_accept else None
            accepted=mask_accept and presence['accepted'];prediction=prediction if accepted else None
            record={'sample_id':row['sample_id'],'group_id':row['group_id'],'image_sha256':row['sha256'],'original_path':row['original_path'],
                    'target':row['presence_target'],'truth':row['label'] if row['presence_target'] else None,
                    'accepted':accepted,'prediction':prediction,'presence':presence,'localization':region}
            results[condition].append(record)
            if condition=='original':
                previous=refs[row['sample_id']]['paths']['v2_plus_presence']
                if (accepted,prediction)!=(previous['accepted'],previous['pleating_prediction']):mismatches.append({'sample_id':row['sample_id'],'expected':previous,'observed':{'accepted':accepted,'pleating_prediction':prediction}})
    summary={k:counts(v) for k,v in results.items()}
    report={'status':'completed','recorded_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-started,
            'protocol_sha256':sha(OUTPUT/'protocol.json'),'executed_source_sha256':sha(OUTPUT/'executed_source.py'),
            'source_hashes':{p:sha(ROOT/p) for p in ('app/presence.py','app/localization.py','app/inference.py','tools/training/train_presence.py')},
            'model_hashes':{'presence':gate.sha256,'localizer':mask.sha256,'pleating':comparison['models']['pleating']},
            'runtime':{'python':sys.version,'platform':platform.platform(),'tensorflow':tf.__version__,'numpy':np.__version__,'pillow':pillow_version,'gpu_visible':False},
            'per_condition':summary,'paired_transitions':{k:paired(results['original'],results[k]) for k in CONDITIONS[1:]},
            'original_reference_mismatches':mismatches,'original_reference_match':not mismatches,'results':results,'deployment_approved':False,
            'limitations':protocol['limitations']}
    write_new(OUTPUT/'results.json',report)
    write_new(OUTPUT/'completion.json',{'status':'completed','results_sha256':sha(OUTPUT/'results.json'),'protocol_sha256':sha(OUTPUT/'protocol.json'),'source_sha256':sha(OUTPUT/'executed_source.py'),'original_reference_match':not mismatches})
    print(json.dumps({'counts':summary,'paired':report['paired_transitions'],'original_reference_mismatches':len(mismatches)},indent=2))
if __name__=='__main__':main()
