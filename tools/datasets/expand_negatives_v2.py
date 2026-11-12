"""Bounded rights-filtered intake; source annotation absence is not ground truth."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import io
import json
from pathlib import Path
import re
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acquire_negatives as old
import acquire_skirts as source
from PIL import Image, ImageDraw

ROOT = source.ROOT
BASE = ROOT / 'data/external/fashionpedia_negatives_v2'
MANIFEST = ROOT / 'data/manifests/negative-candidates-v2.jsonl'
RECORD = ROOT / 'records/acquisitions/2026-10-13-negatives-v2'
SEED = 20261012
ALLOWED = {'Attribution License', 'Attribution-ShareAlike License', 'Attribution-NonCommercial License', 'Attribution-NonCommercial-ShareAlike License', 'Public Domain Dedication'}
LICENSE_URLS = dict(zip(
    ['Attribution License', 'Attribution-ShareAlike License', 'Attribution-NonCommercial License', 'Attribution-NonCommercial-ShareAlike License', 'Public Domain Dedication'],
    ['https://creativecommons.org/licenses/by/2.0/', 'https://creativecommons.org/licenses/by-sa/2.0/', 'https://creativecommons.org/licenses/by-nc/2.0/', 'https://creativecommons.org/licenses/by-nc-sa/2.0/', 'https://creativecommons.org/publicdomain/mark/1.0/']))

def permitted_license(license):
    return license.get('name') in LICENSE_URLS and license.get('url') == LICENSE_URLS[license['name']]

def source_key(url):
    # Static Flickr size variants share a photo identifier.
    match = re.search(r'/([0-9]+)_[0-9a-f]+(?:_[a-z0-9]+)?\.', url)
    if not match:
        match = re.search(r'https?://(?:www\.)?flickr\.com/photos/[^/]+/([0-9]+)(?:/|$)', url)
    return 'flickr-photo-' + match.group(1) if match else url

def validate_image(body, meta):
    with Image.open(io.BytesIO(body)) as im:
        if min(im.size) <= 0 or im.width * im.height > 24_000_000:
            raise ValueError('Decoded image exceeds pixel bound')
        if im.size != (meta['width'], meta['height']):
            raise ValueError('Dimensions mismatch')
        im.load()
        return im.size

def select(data, excluded_ids, excluded_urls):
    excluded_urls = set(excluded_urls)
    licenses = {x['id']: x for x in data['licenses']}
    chosen = []
    for meta, anns, bucket in old.select_candidates(data, excluded_ids, SEED):
        license = licenses[meta['license']]
        if not permitted_license(license):
            continue
        key = source_key(meta['original_url'])
        if key in excluded_urls:
            continue
        # Prefer one substantial unclipped target; this is selection, not review.
        targets = [a for a in anns if a['category_id'] in (6, 7, 10)]
        if len(targets) != 1:
            continue
        x, y, w, h = targets[0]['bbox']
        if min(w, h) <= 0 or w*h/(meta['width']*meta['height']) < .10:
            continue
        if x <= 2 or y <= 2 or x+w >= meta['width']-2 or y+h >= meta['height']-2:
            continue
        chosen.append((meta, anns, bucket))
        excluded_urls.add(key)
    buckets = {name: [row for row in chosen if row[2] == name] for name in old.BUCKETS}
    return [buckets[name][i] for i in range(max(map(len, buckets.values()), default=0))
            for name in old.BUCKETS if i < len(buckets[name])]

def read_rows(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x]

def verify(rows):
    hashes = set()
    identities = set()
    canonical = set()
    for r in rows:
        p = (ROOT/r['original_path']).resolve()
        if not p.is_relative_to(BASE.resolve()):
            raise ValueError('Path outside intake')
        body = p.read_bytes()
        if source.digest(body) != r['sha256'] or r['sha256'] in hashes:
            raise ValueError('Hash mismatch or duplicate')
        validate_image(body, r)
        if r['source_partition'] != 'train2020' or r['split'] is not None or r['training_eligibility']['approved']:
            raise ValueError('Intake cannot admit training data')
        if not permitted_license(r['source_license']):
            raise ValueError('Disallowed source terms')
        key = source_key(r['source_url'])
        if r['sample_id'] in identities or key in canonical or key != r['canonical_source_key']:
            raise ValueError('Repeated or inconsistent source identity')
        if len(body) != r['size_bytes']:
            raise ValueError('Size mismatch')
        identities.add(r['sample_id']); canonical.add(key)
        hashes.add(r['sha256'])

def sheets(rows):
    pages = []
    for start in range(0, len(rows), 30):
        page = Image.new('RGB', (1200, 1260), 'white')
        draw = ImageDraw.Draw(page)
        members = []
        for i, r in enumerate(rows[start:start+30]):
            with Image.open(ROOT/r['original_path']) as im:
                im = im.convert('RGB'); im.thumbnail((195, 220))
                x, y = i%6*200, i//6*252
                page.paste(im, (x+(200-im.width)//2, y))
            draw.text((x+3,y+222), r['source_item_id']+' '+r['sampling_bucket'], fill='black')
            members.append(r['sample_id'])
        p = RECORD/f'contact-{start//30+1}.jpg'; page.save(p, quality=88)
        pages.append({'path':p.relative_to(ROOT).as_posix(),'sha256':source.digest(p.read_bytes()),'sample_ids':members})
    source.save_json(RECORD/'contact-sheets.json', pages)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count',type=int,default=120)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    if not 1 <= args.count <= 120: parser.error('Count must be 1..120')
    if args.verify_only:
        rows=read_rows(MANIFEST); verify(rows); print(json.dumps({'verified':len(rows),'network_used':False})); return
    if MANIFEST.exists(): raise ValueError('Frozen intake exists; use --verify-only')
    annpath=source.BASE/'instances_attributes_train2020.json'
    indexpath=source.BASE/'archive_index.json'
    data=json.loads(annpath.read_text()); index=json.loads(indexpath.read_text())
    existing=[]
    for p in [*(ROOT/'data/manifests').glob('*.jsonl'), ROOT/'data/provenance/external_holdout_samples.jsonl']:
        if p.exists(): existing.extend(read_rows(p))
    ids={str(r.get('source_item_id',r.get('source_image_id'))) for r in existing if 'fashionpedia' in r.get('source_id','')}
    urls={source_key(r.get('source_url') or r['source_page']) for r in existing if r.get('source_url') or r.get('source_page')}
    hashes={source.digest(p.read_bytes()) for p in (ROOT/'data/external').rglob('*') if p.is_file() and p.suffix.lower() in ('.jpg','.jpeg','.png','.webp')}
    candidates=select(data,ids,urls)
    licenses={x['id']:x for x in data['licenses']}; names={x['id']:x['name'] for x in data['categories']}
    RECORD.mkdir(parents=True,exist_ok=True)
    terms=source.request(source.TERMS); source.atomic(RECORD/'terms_snapshot.html',terms)
    rows=[]; errors=[]; attempts=0
    def fetch(candidate):
        meta,anns,bucket=candidate
        try:
            filename=old.safe_filename(meta['file_name']); member='train/'+filename
            entry=index[member]; body=source.extract(member,entry)
            validate_image(body,meta)
            if len(body)!=entry['size'] or zlib.crc32(body)!=entry['crc']: raise ValueError('CRC or size mismatch')
            return candidate,body,None
        except Exception as exc: return candidate,None,str(exc)
    # At most 132 member attempts, four concurrent; the reader retries up to three
    # HTTP requests per member. Each compressed/uncompressed member is <=16MiB.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for start in range(0,min(len(candidates),132),4):
            if len(rows)>=args.count or len(errors)>=12: break
            batch=candidates[start:start+min(4,args.count-len(rows))]
            for (meta,anns,bucket),body,error in pool.map(fetch,batch):
                attempts+=1
                if error: errors.append({'source_item_id':str(meta['id']),'error':error}); continue
                digest=source.digest(body)
                if digest in hashes: errors.append({'source_item_id':str(meta['id']),'error':'duplicate_hash'}); continue
                dest=BASE/'images'/old.safe_filename(meta['file_name']); source.atomic(dest,body)
                r={'schema_version':1,'sample_id':f"fashionpedia-negative-v2-{meta['id']}",'source_id':'fashionpedia-train2020','source_partition':'train2020','source_item_id':str(meta['id']),
                   'source_url':meta['original_url'],'canonical_source_key':source_key(meta['original_url']),'download_url':source.ARCHIVE,'archive_member':'train/'+meta['file_name'],
                   'original_path':dest.relative_to(ROOT).as_posix(),'sha256':digest,'size_bytes':len(body),'width':meta['width'],'height':meta['height'],
                   'source_license':licenses[meta['license']],'terms_reference':[source.TERMS,licenses[meta['license']]['url']],
                   'terms_status':'source_license_allows_selected_non_ND_internal_research_policy_not_redistribution_approval',
                   'annotation_reference':annpath.relative_to(ROOT).as_posix(),'sampling_bucket':bucket,
                   'source_labels':{'skirt_annotation_count':0,'annotations':[{'id':a['id'],'category_id':a['category_id'],'category':names[a['category_id']],'bbox':a['bbox']} for a in anns]},
                   'project_labels':{'skirt_presence':None,'status':'candidate_visual_review_pending'},'training_eligibility':{'approved':False,'reason':'Full-original visual and source-session grouping review pending'},
                   'split':None,'group_id':'fashionpedia-source-'+source.digest(meta['original_url'].encode())[:20],'garment_id':None,'parent_sample_id':None,'grouping_review_pending':True,
                   'acquired_at_utc':datetime.now(timezone.utc).isoformat()}
                rows.append(r); hashes.add(digest)
                source.atomic(MANIFEST,(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)).encode())
            print(f'Acquired {len(rows)}/{args.count}',flush=True)
    if not rows:
        source.save_json(RECORD/'failure.json', {'images':0,'attempts':attempts,'errors':errors})
        raise RuntimeError('No images acquired; see failure.json')
    verify(rows); sheets(rows)
    source.save_json(RECORD/'report.json',{'schema_version':1,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'images':len(rows),'requested_images':args.count,'attempts':attempts,'image_bytes':sum(r['size_bytes'] for r in rows),'bucket_counts':dict(Counter(r['sampling_bucket'] for r in rows)),
        'license_counts':dict(Counter(r['source_license']['name'] for r in rows)),'manifest':MANIFEST.relative_to(ROOT).as_posix(),'manifest_sha256':source.digest(MANIFEST.read_bytes()),'source_code_sha256':source.digest(Path(__file__).read_bytes()),
        'annotations':{'path':annpath.relative_to(ROOT).as_posix(),'sha256':source.digest(annpath.read_bytes())},'archive':{'url':source.ARCHIVE,'index_sha256':source.digest(indexpath.read_bytes())},
        'terms':{'url':source.TERMS,'path':(RECORD/'terms_snapshot.html').relative_to(ROOT).as_posix(),'sha256':source.digest(terms)},'range_reader_sha256':source.digest(Path(source.__file__).read_bytes()),
        'seed':SEED,'eligible_after_filters':len(candidates),'source_partition':'train2020','training_admitted':0,'verified_physical_garments':None,'errors':errors,'dependency_changes':[],
        'limitations':'Rights are source-provided, not freshly verified per photograph. No new split; visual/grouping and near-duplicate review required before admission. No whole-archive download.'})

if __name__=='__main__': main()
