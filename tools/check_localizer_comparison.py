"""Paired exported localizer evaluation on frozen development inputs, no tuning."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PIL import Image
from app.localization import SkirtLocalizer
from app.inference import SkirtPredictor
from tools.training.train_presence import validate

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    run=json.loads((a.candidate/'run.json').read_text())
    source=a.candidate/'labelled-inputs.json'
    if sha(source)!=run['labelled_inputs_sha256']:raise ValueError('Changed inputs')
    rows=json.loads(source.read_text())
    validate([{**r,'presence_target':int(r['label']!='no_skirt')} for r in rows])
    rows=[r for r in rows if r['split']=='development_validation']
    models={'baseline':SkirtLocalizer(ROOT/'artifacts/models/skirt-localizer-v1'),'candidate':SkirtLocalizer(a.candidate)}
    pleating=SkirtPredictor(ROOT/'artifacts/releases/skirt-finetune-v1-desktop-research-v4')
    results=[]
    for row in rows:
        path=ROOT/row['original_path']
        if sha(path)!=row['sha256']:raise ValueError('Changed image')
        with Image.open(path) as im:image=im.convert('RGB')
        item={'sample_id':row['sample_id'],'positive':row['label']!='no_skirt','expected':row['label']}
        for name,model in models.items():
            region=model.locate(image);accepted=region['status']=='provisional'
            prediction=pleating.predict(image,tuple(region['roi']),True)['style']['label'] if accepted else None
            item[name]={'accepted':accepted,'prediction':prediction,'region':region}
        results.append(item)
    metrics={}
    for name in models:
        positive=[r for r in results if r['positive']];negative=[r for r in results if not r['positive']]
        accepted=[r for r in positive if r[name]['accepted']]
        correct=sum(r[name]['prediction']==r['expected'] for r in accepted)
        metrics[name]={'positive_count':len(positive),'accepted_skirts':len(accepted),'coverage':len(accepted)/len(positive),
            'correct_pleating':correct,'accepted_accuracy':correct/len(accepted) if accepted else None,
            'negative_count':len(negative),'rejected_negatives':sum(not r[name]['accepted'] for r in negative)}
    report={'recorded_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':sha(__file__),
        'inputs_sha256':sha(source),'models':{k:m.sha256 for k,m in models.items()},'metrics':metrics,'results':results,
        'limitations':['Agent-reviewed source-domain development only','No threshold tuning in this comparison','No independent human/camera/Pi accuracy','No promotion inferred']}
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(metrics))

if __name__=='__main__':main()
