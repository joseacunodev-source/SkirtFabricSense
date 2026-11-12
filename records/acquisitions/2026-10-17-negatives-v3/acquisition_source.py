"""Acquire up to 180 new balanced candidate originals; never admit or split them."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import io
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import expand_negatives_v2 as previous
from PIL import Image, ImageDraw

source = previous.source
ROOT = source.ROOT
BASE = ROOT / 'data/external/fashionpedia_negatives_v3'
MANIFEST = ROOT / 'data/manifests/negative-candidates-v3.jsonl'
RECORD = ROOT / 'records/acquisitions/2026-10-17-negatives-v3'
SEED = 20261017
BUCKETS = previous.old.BUCKETS


def pixel_hash(body):
    with Image.open(io.BytesIO(body)) as im:
        im.load()
        rgb = im.convert('RGB')
        return source.digest(str(rgb.size).encode() + b'\0' + rgb.tobytes())


def exclusions():
    """Include seeds and all original candidate manifests, not only admitted labels."""
    ids, urls, hashes, pixels = set(), set(), set(), set()
    inputs = []
    paths = sorted((ROOT / 'data/manifests').glob('*.jsonl'))
    paths += [ROOT / 'data/provenance/external_holdout_samples.jsonl']
    for path in paths:
        if path == MANIFEST or not path.exists():
            continue
        inputs.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': source.digest(path.read_bytes())})
        for row in previous.read_rows(path):
            if 'fashionpedia' in row.get('source_id', ''):
                identity = row.get('source_item_id', row.get('source_image_id'))
                if identity is not None:
                    ids.add(str(identity))
            url = row.get('source_url') or row.get('source_page')
            if url:
                urls.add(previous.source_key(url))
    for path in (ROOT / 'data/external').rglob('*'):
        if path.is_file() and path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp') and not path.is_relative_to(BASE):
            body = path.read_bytes()
            hashes.add(source.digest(body))
            pixels.add(pixel_hash(body))
    return ids, urls, hashes, pixels, inputs


def select(data, ids, urls):
    # previous.select uses its module seed; feed a local explicit seed without
    # mutating the imported module or permitting concurrent configuration races.
    licenses = {x['id']: x for x in data['licenses']}
    blocked = set(urls)
    selected = []
    for meta, anns, bucket in previous.old.select_candidates(data, ids, SEED):
        key = previous.source_key(meta['original_url'])
        if key in blocked or not previous.permitted_license(licenses[meta['license']]):
            continue
        targets = [a for a in anns if a['category_id'] in (6, 7, 10)]
        if len(targets) != 1:
            continue
        x, y, w, h = targets[0]['bbox']
        if min(w, h) <= 0 or w*h/(meta['width']*meta['height']) < .10:
            continue
        if x <= 2 or y <= 2 or x+w >= meta['width']-2 or y+h >= meta['height']-2:
            continue
        selected.append((meta, anns, bucket))
        blocked.add(key)
    return selected


def verify(rows, prior=None):
    prior = exclusions() if prior is None else prior
    ids, urls, hashes, pixels, _ = prior
    seen_ids, seen_urls, seen_hashes, seen_pixels = set(), set(), set(), set()
    for row in rows:
        path = (ROOT / row['original_path']).resolve()
        if not path.is_relative_to(BASE.resolve()):
            raise ValueError('Path outside v3 intake')
        body = path.read_bytes()
        digest, pixel = source.digest(body), pixel_hash(body)
        key, identity = previous.source_key(row['source_url']), row['source_item_id']
        if digest != row['sha256'] or pixel != row['decoded_pixel_sha256'] or len(body) != row['size_bytes']:
            raise ValueError('Content hash or byte count mismatch')
        if identity in ids | seen_ids or key in urls | seen_urls or digest in hashes | seen_hashes or pixel in pixels | seen_pixels:
            raise ValueError('Prior or within-intake identity/content duplicate')
        if row['source_partition'] != 'train2020' or row['split'] is not None or row['training_eligibility']['approved']:
            raise ValueError('Candidates cannot become admitted or assigned')
        if not previous.permitted_license(row['source_license']) or key != row['canonical_source_key']:
            raise ValueError('Invalid source license or canonical identity')
        previous.validate_image(body, row)
        seen_ids.add(identity); seen_urls.add(key); seen_hashes.add(digest); seen_pixels.add(pixel)


def sheets(rows):
    pages = []
    for start in range(0, len(rows), 12):
        page = Image.new('RGB', (1440, 1664), 'white')
        draw = ImageDraw.Draw(page)
        members = []
        for i, row in enumerate(rows[start:start+12]):
            x, y = i % 3 * 480, i // 3 * 416
            with Image.open(ROOT / row['original_path']) as image:
                image = image.convert('RGB'); image.thumbnail((470, 380))
                page.paste(image, (x + (480-image.width)//2, y))
            draw.text((x+5, y+384), row['source_item_id'] + ' ' + row['sampling_bucket'], fill='black')
            members.append({'sample_id':row['sample_id'], 'original_path':row['original_path'], 'sha256':row['sha256']})
        path = RECORD / f'review-{start//12+1:02d}.jpg'
        page.save(path, quality=94)
        pages.append({'path':path.relative_to(ROOT).as_posix(), 'sha256':source.digest(path.read_bytes()), 'members':members})
    source.save_json(RECORD/'review-sheets.json', pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=180)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if not 3 <= args.count <= 180 or args.count % 3:
        parser.error('Count must be divisible by three, within 3..180')
    prior = exclusions()
    if args.verify_only:
        rows = previous.read_rows(MANIFEST); verify(rows, prior)
        print(json.dumps({'verified_images':len(rows), 'network_used':False, 'prior_id_url_file_pixel_overlap':0})); return
    if MANIFEST.exists():
        raise ValueError('Intake already exists; use --verify-only')
    RECORD.mkdir(parents=True, exist_ok=True)
    annpath = source.BASE/'instances_attributes_train2020.json'
    indexpath = source.BASE/'archive_index.json'
    data = json.loads(annpath.read_text()); index = json.loads(indexpath.read_text())
    candidates = select(data, prior[0], prior[1])
    licenses = {x['id']:x for x in data['licenses']}
    names = {x['id']:x['name'] for x in data['categories']}
    rows, errors = [], []
    counts = Counter(); target = args.count//3
    hashes, pixels = set(prior[2]), set(prior[3])
    terms = source.request(source.TERMS); source.atomic(RECORD/'terms_snapshot.html', terms)
    def fetch(candidate):
        meta, anns, bucket = candidate
        try:
            member = 'train/' + previous.old.safe_filename(meta['file_name'])
            body = source.extract(member, index[member]); previous.validate_image(body, meta)
            return candidate, body, None
        except Exception as exc:
            return candidate, None, str(exc)
    pending = candidates[:]
    attempts = 0
    # Max 204 member attempts and 24 failed/duplicate members, four requests
    # concurrently. Existing exact-range reader caps each member and retries3.
    with ThreadPoolExecutor(max_workers=4) as pool:
        while pending and len(rows) < args.count and attempts < 204 and len(errors) < 24:
            batch = []
            reserved = Counter()
            while pending and len(batch) < min(4, 204-attempts):
                candidate = pending.pop(0)
                bucket = candidate[2]
                if counts[bucket]+reserved[bucket] < target:
                    batch.append(candidate); reserved[bucket] += 1
            if not batch:
                break
            for (meta, anns, bucket), body, error in pool.map(fetch, batch):
                attempts += 1
                if error:
                    errors.append({'source_item_id':str(meta['id']), 'error':error}); continue
                digest, pixel = source.digest(body), pixel_hash(body)
                if digest in hashes or pixel in pixels:
                    errors.append({'source_item_id':str(meta['id']), 'error':'duplicate_file_or_pixels'}); continue
                dest = BASE/'images'/previous.old.safe_filename(meta['file_name']); source.atomic(dest,body)
                row = {'schema_version':1, 'sample_id':f"fashionpedia-negative-v3-{meta['id']}", 'source_id':'fashionpedia-train2020', 'source_partition':'train2020', 'source_item_id':str(meta['id']),
                    'source_url':meta['original_url'], 'canonical_source_key':previous.source_key(meta['original_url']), 'download_url':source.ARCHIVE, 'archive_member':'train/'+meta['file_name'],
                    'original_path':dest.relative_to(ROOT).as_posix(), 'sha256':digest, 'decoded_pixel_sha256':pixel, 'size_bytes':len(body), 'width':meta['width'], 'height':meta['height'],
                    'source_license':licenses[meta['license']], 'terms_reference':[source.TERMS,licenses[meta['license']]['url']],
                    'terms_status':'exact_source_non_ND_license_pair_internal_research_not_redistribution_approval', 'annotation_reference':annpath.relative_to(ROOT).as_posix(), 'sampling_bucket':bucket,
                    'source_labels':{'skirt_annotation_count':0, 'annotations':[{'id':a['id'],'category_id':a['category_id'],'category':names[a['category_id']],'bbox':a['bbox']} for a in anns]},
                    'project_labels':{'skirt_presence':None,'status':'candidate_visual_review_pending'}, 'training_eligibility':{'approved':False,'reason':'Full-original label, grouping and near-duplicate review pending'},
                    'split':None, 'group_id':'fashionpedia-source-'+source.digest(meta['original_url'].encode())[:20], 'garment_id':None,'parent_sample_id':None,'grouping_review_pending':True,
                    'acquired_at_utc':datetime.now(timezone.utc).isoformat()}
                rows.append(row); counts[bucket] += 1; hashes.add(digest); pixels.add(pixel)
                source.atomic(MANIFEST, ''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows).encode())
            source.save_json(RECORD/'progress.json', {'images':len(rows),'attempts':attempts,'bucket_counts':dict(counts),'errors':errors})
            print(f'Acquired {len(rows)}/{args.count}', flush=True)
    if rows:
        verify(rows, prior); sheets(rows)
    report = {'schema_version':1,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'requested_images':args.count,'images':len(rows),'attempts':attempts,'image_bytes':sum(r['size_bytes'] for r in rows),'bucket_counts':dict(counts),
        'manifest':MANIFEST.relative_to(ROOT).as_posix() if rows else None,'manifest_sha256':source.digest(MANIFEST.read_bytes()) if rows else None,
        'source_code_sha256':source.digest(Path(__file__).read_bytes()),'selector_v2_sha256':source.digest(Path(previous.__file__).read_bytes()),'range_reader_sha256':source.digest(Path(source.__file__).read_bytes()),
        'annotations':{'path':annpath.relative_to(ROOT).as_posix(),'sha256':source.digest(annpath.read_bytes())},'archive':{'url':source.ARCHIVE,'index_sha256':source.digest(indexpath.read_bytes())},
        'terms':{'url':source.TERMS,'path':(RECORD/'terms_snapshot.html').relative_to(ROOT).as_posix(),'sha256':source.digest(terms)}, 'prior_manifests':prior[4],
        'prior_exclusion_counts':dict(zip(('source_ids','canonical_urls','file_hashes','pixel_hashes'),map(len,prior[:4]))), 'prior_id_url_file_pixel_overlap':0,
        'seed':SEED,'eligible_after_filters':len(candidates),'source_partition':'train2020','training_admitted':0,'verified_physical_garments':None,'errors':errors,'dependency_changes':[],
        'limitations':'Source-provided rights preserved; per-photo online relicensing not checked. No split/admission. Physical identity and visual/session/near-duplicate review pending. No full archive downloaded.'}
    source.save_json(RECORD/'report.json', report)
    print(json.dumps({'images':len(rows),'buckets':dict(counts),'errors':len(errors)}))


if __name__ == '__main__':
    main()
