"""Create context/ROI sheets for bounded independent visual review; no auto labels."""
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'records/review/batch-c'
OUT.mkdir(parents=True, exist_ok=True)
rows = sorted([json.loads(s) for s in (ROOT/'data/manifests/skirt_candidates.jsonl').read_text().splitlines()], key=lambda r:r['sample_id'])[667:1000]
index = []
for start in range(0,len(rows),16):
    sheet=Image.new('RGB',(1800,1440),'#eeeeee')
    d=ImageDraw.Draw(sheet)
    for j,r in enumerate(rows[start:start+16]):
        x=(j%4)*450; y=(j//4)*360
        im=Image.open(ROOT/r['original_path']).convert('RGB')
        bx,by,bw,bh=r['source_labels']['bbox']
        context=im.copy(); ImageDraw.Draw(context).rectangle((bx,by,bx+bw,by+bh),outline='red',width=3)
        roi=im.crop((max(0,bx-0.08*bw),max(0,by-0.08*bh),min(im.width,bx+1.08*bw),min(im.height,by+1.08*bh)))
        for pic,px,pw in [(context,x,150),(roi,x+150,300)]:
            pic=ImageOps.contain(pic,(pw-8,325)); sheet.paste(pic,(px+(pw-pic.width)//2,y+28))
        d.text((x+4,y+5),f'{start+j} | {r["sample_id"].split("-")[-1]}',fill='black')
        index.append({'index':start+j,'sample_id':r['sample_id'],'image_sha256':r['sha256'],'sheet':f'records/review/batch-c/sheet-{start//16:02d}.jpg'})
    sheet.save(OUT/f'sheet-{start//16:02d}.jpg',quality=92)
(OUT/'index.json').write_text(json.dumps(index,indent=2))
print(f'Created {len(rows)} image entries in {(len(rows)+15)//16} sheets')
