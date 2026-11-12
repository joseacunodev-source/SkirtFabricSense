"""Offline integrity and partition audit; does not grant label admission."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(root=ROOT):
    paths = [root / f'data/manifests/fullview-fabric-candidates-v{v}.jsonl' for v in (1, 2)]
    manifests = [list(map(json.loads, p.read_text(encoding='utf-8').splitlines())) for p in paths]
    joins = {r['filename']: r for r in map(json.loads, (root / 'records/acquisitions/2026-10-11-fabric-partition/skirt-partition-join.jsonl').read_text().splitlines())}
    hashes, pixels, groups = {}, {}, {}
    duplicates = []
    records = []
    for version, rows in enumerate(manifests, 1):
        for row in rows:
            path = (root / row['original_path']).resolve()
            if not path.is_relative_to(root.resolve()):
                raise ValueError('Image path leaves workspace')
            if sha(path) != row['sha256'] or path.stat().st_size != row['size_bytes']:
                raise ValueError('Image integrity mismatch')
            join = joins[path.name]
            if join['official_split'] != 'train' or join['official_item_id'] != row['official_item_id']:
                raise ValueError('Official partition or group mismatch')
            if join['lower_fabric_source_code'] != row['source_lower_fabric_label_id']:
                raise ValueError('Source label mismatch')
            if row['training_admitted'] is not False or row['project_split'] is not None:
                raise ValueError('Candidate unexpectedly admitted')
            with Image.open(path) as image:
                image.load()
                if image.size != (row['width'], row['height']):
                    raise ValueError('Dimensions mismatch')
                rgb = image.convert('RGB')
                digest = hashlib.sha256(f'{rgb.width}x{rgb.height}:RGB:'.encode() + rgb.tobytes()).hexdigest()
            for kind, value, seen in [('file', row['sha256'], hashes), ('pixels', digest, pixels), ('source_group', row['official_item_id'], groups)]:
                if value in seen:
                    duplicates.append({'kind': kind, 'first': seen[value], 'second': row['sample_id']})
                seen[value] = row['sample_id']
            records.append({'sample_id': row['sample_id'], 'manifest_version': version, 'sha256': row['sha256'], 'rgb_pixel_sha256': digest})
    terms = root / 'records/acquisitions/2026-10-09-deepfashion-multimodal/LICENSE'
    return {'audit_utc': datetime.now(timezone.utc).isoformat(), 'status': 'passed' if not duplicates else 'duplicates_found',
            'manifest_counts': [len(r) for r in manifests], 'total_images': len(records),
            'new_source_label_counts': dict(Counter(r['source_lower_fabric_label'] for r in manifests[1])),
            'manifest_sha256': [sha(p) for p in paths], 'terms_sha256': sha(terms),
            'independent_physical_garments_verified': False, 'training_admitted': False,
            'near_duplicates_reviewed': False, 'duplicates': duplicates, 'images': records}

if __name__ == '__main__':
    result = verify()
    output = ROOT / 'records/acquisitions/2026-10-13-fabric-v2/integrity.json'
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'images'}, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)
