"""Reproduce batch B visual review sheets; no labels inferred from source attributes."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'records/review/batch-b'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = sorted((json.loads(x) for x in (ROOT/'data/manifests/skirt_candidates.jsonl').read_text().splitlines()), key=lambda r:r['sample_id'])[334:667]
    index=[]
    for start in range(0,len(rows),12):
        canvas=Image.new('RGB',(1600,1320),'white'); d=ImageDraw.Draw(canvas)
        for j,r in enumerate(rows[start:start+12]):
            x=(j%4)*400; y=(j//4)*440
            im=Image.open(ROOT/r['original_path']).convert('RGB')
            box=r['source_labels']['bbox']; a,b,w,h=box
            roi=im.crop((max(0,a-w*.08),max(0,b-h*.08),min(im.width,a+w*1.08),min(im.height,b+h*1.08)))
            context=ImageOps.contain(im,(130,390)); roi=ImageOps.contain(roi,(260,390))
            canvas.paste(context,(x,y+30)); canvas.paste(roi,(x+135,y+30))
            d.text((x+5,y+5),f'{start+j}: '+r['sample_id'].split('-')[-1],fill='black')
            index.append({'index':start+j,'sample_id':r['sample_id'],'image_sha256':r['sha256'],'review_artifact':f'records/review/batch-b/sheet-{start//12+1:02}.jpg'})
        canvas.save(OUT/f'sheet-{start//12+1:02}.jpg',quality=92)
    (OUT/'index.json').write_text(json.dumps(index,indent=2)+'\n')
    print(len(rows))

if __name__=='__main__': main()
