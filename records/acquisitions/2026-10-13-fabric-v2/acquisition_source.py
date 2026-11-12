"""Acquire bounded new original-train fabric groups; never admits training data."""
import argparse
from collections import Counter, defaultdict
import hashlib
import io
import json
import re
from pathlib import Path
import sys
from urllib.request import Request, urlopen
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.datasets.acquire_fullview_fabric import JOIN, NAMES, PUBLIC_URL, SIZE, resolve_download
from tools.datasets.bounded_zip import BoundedZip
OLD = ROOT / 'data/manifests/fullview-fabric-candidates-v1.jsonl'
OUT = ROOT / 'records/acquisitions/2026-10-13-fabric-v2'
MANIFEST = ROOT / 'data/manifests/fullview-fabric-candidates-v2.jsonl'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def select(rows, old, limit=30):
    if not 1 <= limit <= 60:
        raise ValueError('Bound selection to 1..60 groups')
    used = {r['official_item_id'] for r in old}
    blocked = {r['official_item_id'] for r in rows if r['official_split'] != 'train'}
    groups = defaultdict(list)
    for row in rows:
        if not re.fullmatch(r'WOMEN-Skirts-id_\d+-[^/\\]+\.jpg', row['filename']):
            raise ValueError('Unexpected skirt source filename')
        if row['official_split'] == 'train' and row['official_item_id'] not in used | blocked:
            groups[row['official_item_id']].append(row)
    by_class = defaultdict(list)
    conflicts = []
    for item, views in sorted(groups.items()):
        codes = {v['lower_fabric_source_code'] for v in views}
        if len(codes) != 1 or not codes <= set(range(7)):
            conflicts.append(item)
            continue
        # Prefer a full view when available, then frontal views. Visibility is unreviewed.
        view = min(views, key=lambda v: ('_full.' not in v['filename'], '_front.' not in v['filename'], v['filename']))
        by_class[next(iter(codes))].append(view)
    counts = {NAMES[k]: len(v) for k, v in by_class.items()}
    chosen = []
    while len(chosen) < limit and any(by_class.values()):
        for code in sorted(by_class):
            if by_class[code] and len(chosen) < limit:
                chosen.append(by_class[code].pop(0))
    return chosen, {'remaining_eligible_groups_by_source_label': counts,
                    'excluded_existing_groups': len(used), 'protected_groups': len(blocked),
                    'conflicting_or_unsupported_groups': conflicts}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=30)
    args = parser.parse_args()
    joins = list(map(json.loads, JOIN.read_text().splitlines()))
    old = list(map(json.loads, OLD.read_text().splitlines()))
    chosen, assessment = select(joins, old, args.limit)
    destination = ROOT / 'data/external/deepfashion_multimodal_candidates_v2'
    for path in (OUT, destination, MANIFEST):
        if path.exists():
            raise FileExistsError(path)
    OUT.mkdir(parents=True)
    destination.mkdir(parents=True)
    report = {'date_asia_manila': '2026-10-13', 'selection': assessment, 'requested_limit': args.limit,
              'selected_groups': len(chosen), 'source_url': PUBLIC_URL,
              'partition_join_sha256': sha(JOIN), 'existing_manifest_sha256': sha(OLD),
              'source_sha256': sha(Path(__file__)), 'reader_sha256': sha(ROOT/'tools/datasets/bounded_zip.py'),
              'training_admitted': False, 'range_requests': [], 'images': []}
    (OUT/'selection.json').write_text(json.dumps({'assessment': assessment, 'selected': chosen}, indent=2)+'\n')
    error = None
    try:
        url = resolve_download()
        def fetch(start, end):
            if not 0 <= start <= end < SIZE or end-start+1 > 16*1024*1024:
                raise ValueError('Range outside bounds')
            with urlopen(Request(url, headers={'Range': f'bytes={start}-{end}'}), timeout=45) as response:
                if response.status != 206 or response.headers.get('Content-Range') != f'bytes {start}-{end}/{SIZE}':
                    raise ValueError('Server did not honor exact archive range')
                body = response.read(end-start+2)
            if len(body) != end-start+1:
                raise ValueError('Truncated/oversized range response')
            report['range_requests'].append({'start': start, 'end': end, 'bytes': len(body),
                                             'sha256': hashlib.sha256(body).hexdigest()})
            return body
        archive = BoundedZip(fetch, SIZE)
        names = {}
        for member in archive.index():
            name = member.rsplit('/', 1)[-1]
            if name in names:
                raise ValueError('Ambiguous archive basenames')
            names[name] = member
        for candidate in chosen:
            filename = candidate['filename']
            body = archive.read(names[filename])
            with Image.open(io.BytesIO(body)) as image:
                if image.width*image.height > 20_000_000:
                    raise ValueError('Oversized image')
                image.load()
                width, height = image.size
            path = destination/filename
            path.write_bytes(body)
            item = candidate['official_item_id']
            row = {'sample_id': 'deepfashion-multimodal-'+filename[:-4],
                   'original_path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path),
                   'size_bytes': len(body), 'width': width, 'height': height,
                   'source_id': 'deepfashion-multimodal', 'source_url': PUBLIC_URL,
                   'archive_member': names[filename], 'source_item_token': candidate['filename_item_token'],
                   'official_item_id': item, 'group_id': 'deepfashion-inshop-WOMEN-Skirts-'+item,
                   'physical_garment_verified': False, 'source_partition': 'train', 'project_split': None,
                   'source_lower_fabric_label_id': candidate['lower_fabric_source_code'],
                   'source_lower_fabric_label': NAMES[candidate['lower_fabric_source_code']],
                   'label_semantics': 'Source visual appearance annotation; not verified fiber composition',
                   'full_skirt_visibility': 'unreviewed', 'training_admitted': False,
                   'terms_reference': 'records/acquisitions/2026-10-09-deepfashion-multimodal/LICENSE'}
            with MANIFEST.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(row)+'\n')
            report['images'].append(row)
            print(f'Acquired {len(report["images"])} / {len(chosen)}', flush=True)
    except Exception as exc:
        error = type(exc).__name__  # Never serialize transient signed URLs.
        if isinstance(exc, (ValueError, KeyError)):
            error += ': '+str(exc)
    report.update(status='completed' if error is None else 'partial_or_failed', error=error,
                  complete_images=len(report['images']),
                  label_counts=dict(Counter(r['source_lower_fabric_label'] for r in report['images'])))
    if MANIFEST.exists():
        report['manifest'] = {'path': MANIFEST.relative_to(ROOT).as_posix(), 'sha256': sha(MANIFEST)}
    for page in range((len(report['images'])+14)//15):
        sheet = Image.new('RGB', (1000, 960), 'white')
        draw = ImageDraw.Draw(sheet)
        for offset, row in enumerate(report['images'][page*15:page*15+15]):
            x, y = (offset%5)*200, (offset//5)*320
            with Image.open(ROOT/row['original_path']) as image:
                image = image.convert('RGB'); image.thumbnail((196, 285))
                sheet.paste(image, (x+(200-image.width)//2, y))
            draw.text((x+3, y+286), row['official_item_id'], fill='black')
            draw.text((x+3, y+301), row['source_lower_fabric_label'], fill='black')
        sheet.save(OUT/f'contact-sheet-{page+1}.jpg')
    (OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return 0 if error is None else 1

if __name__ == '__main__':
    raise SystemExit(main())
