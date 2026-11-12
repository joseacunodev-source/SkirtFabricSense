import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
rows = sorted([json.loads(x) for x in (ROOT/'data/manifests/skirt_candidates.jsonl').read_text().splitlines()], key=lambda x:x['sample_id'])[:334]
out = ROOT/'records/review/batch-a'
out.mkdir(parents=True,exist_ok=True)
for page in range((len(rows)+11)//12):
    sheet = Image.new('RGB',(1800,1500),'white')
    draw=ImageDraw.Draw(sheet)
    for j,r in enumerate(rows[page*12:page*12+12]):
        x=(j%4)*450;y=(j//4)*500
        im=Image.open(ROOT/r['original_path']).convert('RGB')
        box=r['source_labels']['bbox']; im.thumbnail((438,462))
        sheet.paste(im,(x+(450-im.width)//2,y+30))
        draw.text((x+5,y+5),f"{page*12+j}: {r['sample_id']}",fill='black')
    sheet.save(out/f'page-{page+1:02d}.jpg',quality=90)
(out/'index.json').write_text(json.dumps([{'index':i,'sample_id':r['sample_id']} for i,r in enumerate(rows)],indent=2))
