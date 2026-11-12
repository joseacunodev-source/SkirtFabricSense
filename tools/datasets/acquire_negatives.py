"""Bounded Fashionpedia train2020 non-skirt candidates; never training approval.

Reuses the existing ZIP range reader. Missing skirt annotations are candidate
evidence only. Visual and related-garment review must precede any split/admission.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acquire_skirts as source

ROOT = source.ROOT
BASE = ROOT / 'data/external/fashionpedia_negatives'
MANIFEST = ROOT / 'data/manifests/negative-candidates-v1.jsonl'
REPORT = ROOT / 'records/acquisitions/2026-10-11-negatives.json'
SEED = 20261011
BUCKETS = ('pants', 'shorts', 'dress')


def select_candidates(data, excluded_ids, seed=SEED):
    names = {c['id']: c['name'] for c in data['categories']}
    if names.get(8) != 'skirt' or any(x not in names.values() for x in BUCKETS):
        raise ValueError('Unexpected source taxonomy')
    by_image = defaultdict(list)
    for ann in data['annotations']:
        by_image[ann['image_id']].append(ann)
    buckets = {name: [] for name in BUCKETS}
    for meta in sorted(data['images'], key=lambda x: x['id']):
        anns = by_image[meta['id']]
        categories = {names[a['category_id']] for a in anns}
        if str(meta['id']) in excluded_ids or 'skirt' in categories:
            continue
        # Overlap is assigned once, to the first category in the declared order.
        for bucket in BUCKETS:
            if bucket in categories:
                buckets[bucket].append((meta, anns, bucket))
                break
    rng = random.Random(seed)
    for bucket in buckets.values():
        rng.shuffle(bucket)
    chosen = []
    for i in range(max(map(len, buckets.values()), default=0)):
        for bucket in BUCKETS:
            if i < len(buckets[bucket]):
                chosen.append(buckets[bucket][i])
    return chosen


def safe_filename(filename):
    if not filename or Path(filename).name != filename or '/' in filename or '\\' in filename:
        raise ValueError('Unsafe source filename')
    return filename


def verify_record(item):
    path = (ROOT / item['original_path']).resolve()
    if not path.is_relative_to(BASE.resolve()):
        raise ValueError('Candidate path escapes intake directory')
    body = path.read_bytes()
    if source.digest(body) != item['sha256']:
        raise ValueError('Cached image hash mismatch')
    source.validate_image(body, item)
    if item['source_partition'] != 'train2020' or item['training_eligibility']['approved']:
        raise ValueError('Candidate must remain unadmitted source train2020')
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=90)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.count <= 120:
        parser.error('Count must be 1..120')
    existing = [json.loads(line) for line in MANIFEST.read_text().splitlines()] if MANIFEST.exists() else []
    for row in existing:
        verify_record(row)
    if args.verify_only:
        print(json.dumps({'verified_images': len(existing), 'unique_hashes': len({x['sha256'] for x in existing}), 'network_used': False}))
        return
    if len(existing) > args.count:
        raise ValueError('Refusing to shrink an existing intake')
    annpath = source.BASE / 'instances_attributes_train2020.json'
    indexpath = source.BASE / 'archive_index.json'
    data = json.loads(annpath.read_text())
    index = json.loads(indexpath.read_text())
    excluded_ids = set()
    for path in (ROOT / 'data/manifests').glob('*.jsonl'):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if 'fashionpedia' in row.get('source_id', ''):
                excluded_ids.add(str(row['source_item_id']))
    # Hash all cached originals, including protected seeds, before downloading.
    excluded_hashes = set()
    for path in (ROOT / 'data/external').rglob('*'):
        if path.is_file() and path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
            excluded_hashes.add(source.digest(path.read_bytes()))
    names = {c['id']: c['name'] for c in data['categories']}
    licenses = {x['id']: x for x in data['licenses']}
    terms = source.request(source.TERMS)
    source.atomic(BASE / 'terms_snapshot.html', terms)
    rows = existing[:]
    errors = []
    candidates = select_candidates(data, excluded_ids)
    for meta, anns, bucket in candidates:
        if len(rows) >= args.count:
            break
        try:
            filename = safe_filename(meta['file_name'])
            member = 'train/' + filename
            entry = index[member]
            dest = BASE / 'images' / filename
            body = dest.read_bytes() if dest.exists() else source.extract(member, entry)
            width, height = source.validate_image(body, meta)
            if len(body) != entry['size'] or zlib.crc32(body) != entry['crc']:
                raise ValueError('Archive CRC mismatch')
            sha = source.digest(body)
            if sha in excluded_hashes:
                errors.append({'source_item_id': str(meta['id']), 'error': 'exact_duplicate_excluded'})
                continue
            source.atomic(dest, body)
            row = {'schema_version': 1, 'sample_id': f"fashionpedia-negative-candidate-{meta['id']}",
                   'source_id': 'fashionpedia-train2020', 'source_partition': 'train2020',
                   'source_item_id': str(meta['id']), 'source_url': meta['original_url'],
                   'download_url': source.ARCHIVE, 'archive_member': member,
                   'original_path': dest.relative_to(ROOT).as_posix(), 'sha256': sha,
                   'size_bytes': len(body), 'width': width, 'height': height,
                   'source_license': licenses[meta['license']],
                   'terms_reference': [source.TERMS, licenses[meta['license']].get('url', '')],
                   'terms_status': 'per_image_source_license_preserved_not_blanket_annotation_license',
                   'annotation_reference': annpath.relative_to(ROOT).as_posix(),
                   'sampling_bucket': bucket,
                   'source_labels': {'skirt_annotation_count': 0,
                                     'annotations': [{'id': a['id'], 'category_id': a['category_id'],
                                                      'category': names[a['category_id']], 'bbox': a['bbox']} for a in anns]},
                   'project_labels': {'skirt_presence': None, 'status': 'candidate_visual_review_pending'},
                   'training_eligibility': {'approved': False, 'reason': 'Annotation absence does not prove skirt absence; visual and garment grouping review pending'},
                   'split': None, 'group_id': 'fashionpedia-source-' + source.digest(meta['original_url'].encode())[:20],
                   'garment_id': None, 'parent_sample_id': None, 'grouping_review_pending': True,
                   'acquired_at_utc': datetime.now(timezone.utc).isoformat()}
            rows.append(row)
            excluded_hashes.add(sha)
            source.atomic(MANIFEST, (''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in rows)).encode())
            print(f'Acquired {len(rows)}/{args.count}', flush=True)
        except Exception as exc:
            errors.append({'source_item_id': str(meta['id']), 'error': str(exc)})
            if len(errors) >= 12:
                break
    report = {'schema_version': 1, 'completed_at_utc': datetime.now(timezone.utc).isoformat(),
              'requested_images': args.count, 'images': len(rows), 'unique_content_hashes': len({r['sha256'] for r in rows}),
              'image_bytes': sum(r['size_bytes'] for r in rows), 'source_partition': 'train2020',
              'manifest': MANIFEST.relative_to(ROOT).as_posix(), 'manifest_sha256': source.digest(MANIFEST.read_bytes()) if MANIFEST.exists() else None,
              'annotations': {'path': annpath.relative_to(ROOT).as_posix(), 'sha256': source.digest(annpath.read_bytes()), 'url': source.ANNOTATIONS},
              'archive': {'url': source.ARCHIVE, 'cached_index_path': indexpath.relative_to(ROOT).as_posix(), 'cached_index_sha256': source.digest(indexpath.read_bytes())},
              'terms': {'url': source.TERMS, 'path': (BASE / 'terms_snapshot.html').relative_to(ROOT).as_posix(), 'sha256': source.digest(terms)},
              'sampling': {'seed': SEED, 'round_robin_buckets': BUCKETS, 'overlap_policy': 'first matching bucket', 'eligible_remaining': len(candidates)},
              'bucket_counts': dict(Counter(r['sampling_bucket'] for r in rows)),
              'license_counts': dict(Counter(r['source_license']['name'] for r in rows)),
              'verified_negative_labels': 0, 'training_admitted': 0, 'verified_physical_garments': None,
              'verification': 'Original ZIP CRC and size, image decode and dimensions, SHA256; all cached image hashes excluded; no source validation/test acquisition',
              'limitations': 'Missing source skirt annotations are not ground truth. No visual suitability or near-duplicate/garment review yet. No split assigned.',
              'errors': errors, 'source_code_sha256': source.digest(Path(__file__).read_bytes()),
              'range_reader_sha256': source.digest(Path(source.__file__).read_bytes()), 'dependency_changes': []}
    source.save_json(REPORT, report)
    print(json.dumps({'images': len(rows), 'bucket_counts': report['bucket_counts'], 'errors': errors}))


if __name__ == '__main__':
    main()
