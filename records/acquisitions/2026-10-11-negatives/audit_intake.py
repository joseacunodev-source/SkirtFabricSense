"""Decoded-pixel duplication audit; no label or split changes."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
manifest = ROOT / 'data/manifests/negative-candidates-v1.jsonl'
rows = [json.loads(line) for line in manifest.read_text().splitlines()]
candidate_paths = { (ROOT/r['original_path']).resolve() for r in rows }
def pixel_hash(path):
    with Image.open(path) as im:
        rgb = im.convert('RGB')
        return hashlib.sha256(str(rgb.size).encode()+b'\x00'+rgb.tobytes()).hexdigest()
existing = defaultdict(list)
for path in (ROOT / 'data/external').rglob('*'):
    if path.is_file() and path.suffix.lower() in ('.jpg','.jpeg','.png','.webp') and path.resolve() not in candidate_paths:
        existing[pixel_hash(path)].append(path.relative_to(ROOT).as_posix())
seen = defaultdict(list)
results = []
for row in rows:
    digest = pixel_hash(ROOT/row['original_path'])
    seen[digest].append(row['source_item_id'])
    results.append({'source_item_id': row['source_item_id'], 'decoded_rgb_sha256': digest, 'matches_prior_cached_images': existing.get(digest, [])})
report = {'images': len(rows), 'unique_candidate_rgb_hashes': len(seen), 'other_cached_images_checked': sum(map(len,existing.values())), 'matches_existing': [r for r in results if r['matches_prior_cached_images']], 'candidate_duplicate_groups': [ids for ids in seen.values() if len(ids)>1], 'records': results, 'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(), 'limitations': 'Exact RGB equality only; near-duplicate and garment grouping unresolved. Candidate absence labels unverified.'}
(OUT/'pixel-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key: report[key] for key in ('images','unique_candidate_rgb_hashes','other_cached_images_checked','matches_existing','candidate_duplicate_groups')}))
