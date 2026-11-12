"""Review-only derivatives; these thumbnails are not additional specimens."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
manifest = ROOT / 'data/manifests/negative-candidates-v1.jsonl'
rows = [json.loads(line) for line in manifest.read_text().splitlines()]
font_path = Path('C:/Windows/Fonts/arial.ttf')
font = ImageFont.truetype(str(font_path), 16) if font_path.exists() else ImageFont.load_default()
inventory = []
for page, start in enumerate(range(0, len(rows), 24), 1):
    sheet = Image.new('RGB', (1200, 1000), 'white')
    draw = ImageDraw.Draw(sheet)
    selected = rows[start:start+24]
    for i, row in enumerate(selected):
        x, y = (i % 6)*200, (i // 6)*250
        with Image.open(ROOT / row['original_path']) as original:
            thumb = ImageOps.contain(original.convert('RGB'), (194, 214))
            sheet.paste(thumb, (x+(200-thumb.width)//2, y))
        draw.text((x+3,y+216), row['source_item_id']+' '+row['sampling_bucket'], fill='black', font=font)
        draw.text((x+3,y+234), 'Candidate; not GT', fill='#555555', font=font)
    path = OUT / f'contact-sheet-{page:02d}.jpg'
    sheet.save(path, quality=92)
    inventory.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'source_item_ids': [r['source_item_id'] for r in selected]})
(OUT / 'contact-sheets.json').write_text(json.dumps({'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(), 'image_count': len(rows), 'status': 'review_derivatives_not_new_specimens', 'sheets': inventory}, indent=2)+'\n')
print(json.dumps({'images': len(rows), 'contact_sheets': len(inventory)}))
