"""Bounded, train-only COCO background candidate intake; never admits labels.

Run from the project root. This records failed requests too, refuses full ZIP
fallback, and requires matching public Flickr attribution/CC evidence before
each photo. Missing person words in captions are candidate triage, not absence
truth. The shared BoundedZip parser is reused without raising its global caps.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.datasets.bounded_zip import BoundedZip, _extra, _zip64

MIB = 1024 * 1024
TOTAL_CAP = 80 * MIB
INFLATED_CAP = 180 * MIB
COMPRESSED_CAP = 40 * MIB
IMAGE_CAP = 3 * MIB
MAX_IMAGES = 12
MAX_REQUESTS = 40
MEMBER = 'annotations/captions_train2017.json'
ARCHIVE = 'https://images.cocodataset.org/annotations/annotations_trainval2017.zip'
RECORD = ROOT / 'records/acquisitions/2026-10-23-coco-backgrounds'
PHOTOS = ROOT / 'data/external/coco_background_candidates_v1'
MANIFEST = ROOT / 'data/manifests/coco-background-candidates-v1.jsonl'
LICENSES = {4: 'https://creativecommons.org/licenses/by/2.0/',
            5: 'https://creativecommons.org/licenses/by-sa/2.0/'}
SOURCES = [
    ('coco_terms.html', 'https://raw.githubusercontent.com/cocodataset/cocodataset.github.io/master/dataset/termsofuse.htm'),
    ('coco_download.html', 'https://raw.githubusercontent.com/cocodataset/cocodataset.github.io/master/dataset/download.htm'),
    ('flickr_cc.html', 'https://www.flickr.com/creativecommons/'),
    ('cc_by_2.html', LICENSES[4]),
    ('cc_by_sa_2.html', LICENSES[5]),
]
EXCLUDE = re.compile(r'\b(person|persons|people|man|men|woman|women|boy|boys|girl|girls|child|children|baby|babies|kid|kids|human|humans|wear|wears|wearing|worn|clothes|clothing|garment|garments|skirt|skirts|dress|dresses|pants|trousers|shorts|shirt|shirts|shoe|shoes|jacket|jackets|suit|suits|uniform|uniforms|bride|groom|player|players|crowd|someone|anyone|he|she|his|her|sleeve|sleeves|coat|coats|tie|ties|sock|socks|hat|hats|outfit|outfits|jeans|sweater|sweaters|bikini|swimsuit|costume|costumes)\b', re.I)
ROOM = re.compile(r'\b(room|kitchen|bedroom|bathroom|office|furniture|couch|sofa|bed|desk|chair|chairs|cabinet|refrigerator|toilet|sink)\b', re.I)
OBJECT = re.compile(r'\b(table|vase|bottle|bowl|plate|cup|mug|clock|laptop|computer|keyboard|book|books|television|tv|microwave|oven|toaster)\b', re.I)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(body):
    return hashlib.sha256(body).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')


class BudgetFetcher:
    """Count consumed body bytes, including errors/overflow, and every hop.

    Redirects are refused rather than silently spending unrecorded requests.
    """
    def __init__(self, output, total_cap=TOTAL_CAP, request_cap=MAX_REQUESTS, opener=None):
        self.output, self.total_cap, self.request_cap = Path(output), total_cap, request_cap
        self.used = 0
        self.requests = []
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        self.opener = opener or urllib.request.build_opener(NoRedirect())

    def get(self, url, cap, expected_range=None, name=None):
        if len(self.requests) >= self.request_cap or self.used >= self.total_cap:
            raise ValueError('Declared request/body budget exhausted')
        if cap <= 0:
            raise ValueError('Invalid response cap')
        headers = {'User-Agent': 'SkirtFabricSense-bounded-research/1.0', 'Accept-Encoding': 'identity'}
        if expected_range:
            headers['Range'] = f'bytes={expected_range[0]}-{expected_range[1]}'
        event = {'url': url, 'started_at_utc': now(), 'range': list(expected_range) if expected_range else None,
                 'response_cap_bytes': cap, 'consumed_body_bytes': 0, 'outcome': 'pending'}
        self.requests.append(event)
        body = bytearray()
        try:
            req = urllib.request.Request(url, headers=headers)
            try:
                response = self.opener.open(req, timeout=40)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                event.update(status=response.status, resolved_url=response.url,
                             headers={k: response.headers[k] for k in ('Content-Length', 'Content-Range', 'Content-Type', 'Content-Encoding', 'ETag', 'Last-Modified', 'Location') if k in response.headers})
                # Refuse ignored ranges before reading any full-archive bytes.
                if expected_range:
                    match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range', ''))
                    if response.status != 206 or not match or tuple(map(int, match.groups()[:2])) != expected_range:
                        raise ValueError('Server did not honor exact inclusive byte range; full fallback refused')
                    event['archive_size_bytes'] = int(match.group(3))
                    if expected_range[1] >= int(match.group(3)):
                        raise ValueError('Range exceeds advertised archive length')
                if response.headers.get('Content-Encoding', 'identity').lower() not in ('identity', ''):
                    raise ValueError('Unexpected content encoding')
                # At most cap+1 bytes are consumed, so oversized bodies are recorded.
                limit = min(cap + 1, self.total_cap - self.used)
                while len(body) < limit:
                    chunk = response.read(min(65536, limit - len(body)))
                    if not chunk:
                        break
                    body.extend(chunk)
                    self.used += len(chunk)
                    event['consumed_body_bytes'] += len(chunk)
                if len(body) > cap:
                    raise ValueError('Response exceeded declared per-response cap')
                if self.used >= self.total_cap and len(body) == limit:
                    raise ValueError('Total network-body cap reached')
                if response.status not in (200, 206):
                    raise ValueError(f'HTTP {response.status}')
                if expected_range and len(body) != expected_range[1] - expected_range[0] + 1:
                    raise ValueError('Truncated byte range')
            event['outcome'] = 'success'
            return bytes(body), event
        except Exception as exc:
            event.update(outcome='failed', error=f'{type(exc).__name__}: {exc}')
            raise
        finally:
            event['finished_at_utc'] = now()
            event['sha256_consumed_body'] = sha(body)
            if body:
                filename = name or f'response-{len(self.requests):02d}.bin'
                target = self.output / filename
                if target.exists():
                    raise ValueError('Refusing existing response destination')
                target.write_bytes(body)
                event['body_path'] = target.relative_to(ROOT).as_posix() if target.is_relative_to(ROOT) else target.name
            write_json(self.output / 'requests.json', {'total_consumed_body_bytes': self.used, 'requests': self.requests})


def read_train_captions(reader):
    """Read this member only, with independent compressed/inflated caps and CRC.

    BoundedZip.index validates ZIP structure. Chunked payload requests keep its
    16MiB fetch cap; neither global cap nor shared module is modified.
    """
    entries = reader.index()
    if MEMBER not in entries:
        raise ValueError('Official train captions member missing')
    entry = entries[MEMBER]
    if entry['directory'] or entry['size'] > INFLATED_CAP or entry['compressed'] > COMPRESSED_CAP:
        raise ValueError('Train captions member exceeds predeclared bounds')
    offset = entry['offset']
    fields = struct.unpack('<4s5H3L2H', reader._get(offset, 30))
    if fields[0] != b'PK\x03\x04' or fields[2] != entry['flags'] or fields[3] != entry['compression']:
        raise ValueError('Inconsistent local member header')
    n, e = fields[9:11]
    payload = offset + 30 + n + e
    if payload + entry['compressed'] > reader.central_offset:
        raise ValueError('Train member overlaps central directory')
    variable = reader._get(offset + 30, n + e)
    if variable[:n] != entry['raw_name']:
        raise ValueError('Inconsistent local member name')
    extras = _extra(variable[n:])
    usize, csize = _zip64(extras, [(fields[8], 0xffffffff, 8), (fields[7], 0xffffffff, 8)])
    if not fields[2] & 8 and (fields[6] != entry['crc'] or usize != entry['size'] or csize != entry['compressed']):
        raise ValueError('Inconsistent local size/CRC')
    decoder = zlib.decompressobj(-15) if entry['compression'] == 8 else None
    result = bytearray()
    for start in range(0, entry['compressed'], 8 * MIB):
        part = reader._get(payload + start, min(8 * MIB, entry['compressed'] - start))
        decoded = decoder.decompress(part, entry['size'] - len(result) + 1) if decoder else part
        result.extend(decoded)
        if len(result) > entry['size'] or decoder and (decoder.unconsumed_tail or decoder.unused_data):
            raise ValueError('Oversized/trailing train member stream')
    if decoder and not decoder.eof:
        raise ValueError('Incomplete deflate stream')
    if len(result) != entry['size'] or zlib.crc32(result) & 0xffffffff != entry['crc']:
        raise ValueError('Train member size/CRC mismatch')
    return bytes(result), entry


def select_candidates(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('images'), list) or not isinstance(payload.get('annotations'), list):
        raise ValueError('Unexpected train caption schema')
    licenses = {item['id']: item for item in payload.get('licenses', [])}
    for key, url in LICENSES.items():
        if key not in licenses or licenses[key].get('url', '').replace('http://', 'https://') != url:
            raise ValueError('Source license ID/name mapping changed')
    images = {}
    for image in payload['images']:
        image_id = image['id']
        if image_id in images or not isinstance(image_id, int):
            raise ValueError('Duplicate/invalid source image ID')
        if image['file_name'] != f'{image_id:012d}.jpg' or f'/train2017/{image_id:012d}.jpg' not in image.get('coco_url', ''):
            raise ValueError('Image not explicitly in original train2017 partition')
        images[image_id] = image
    captions = {}
    annotation_ids = set()
    for row in payload['annotations']:
        if row['id'] in annotation_ids or row['image_id'] not in images or not isinstance(row.get('caption'), str):
            raise ValueError('Duplicate/broken train caption join')
        annotation_ids.add(row['id'])
        captions.setdefault(row['image_id'], []).append({'id': row['id'], 'caption': row['caption']})
    selected = []
    for image_id in sorted(images):
        image, rows = images[image_id], captions.get(image_id, [])
        if image.get('license') not in LICENSES or len(rows) < 2 or any(EXCLUDE.search(r['caption']) for r in rows):
            continue
        room = sum(bool(ROOM.search(r['caption'])) for r in rows)
        objects = sum(bool(OBJECT.search(r['caption'])) for r in rows)
        if room < 2 and objects < 2:
            continue
        selected.append({'image': image, 'captions': rows, 'condition': 'furniture_or_room' if room >= 2 else 'ordinary_objects',
                         'candidate_only_not_absence_truth': True})
    return selected


def attribution(image, meta):
    expected = LICENSES[image['license']]
    photo_match = re.search(r'/(\d+)_[^/]+\.jpg$', image.get('flickr_url', ''))
    photo_id = photo_match.group(1) if photo_match else None
    page = meta.get('web_page', '')
    if not photo_id or not re.fullmatch(r'https://www\.flickr\.com/photos/[^/]+/' + photo_id + r'/?', page):
        raise ValueError('Flickr photo identity not established')
    if meta.get('license_url', '').replace('http://', 'https://') != expected:
        raise ValueError('Current public Flickr licence differs from permitted source licence')
    if not meta.get('author_name') or not re.fullmatch(r'https://www\.flickr\.com/photos/[^/]+/?', meta.get('author_url', '')):
        raise ValueError('Creator attribution missing/invalid')
    return dict(flickr_photo_id=photo_id, source_page=page, author=meta['author_name'], author_url=meta['author_url'],
                title=meta.get('title', ''), license_url=expected, modifications='none; COCO-provided source JPEG retained')


def main():
    global RECORD, MANIFEST, ARCHIVE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--retry-official-gcp', action='store_true',
                        help='Use documented public GCP bucket after preserving/verifying original attempt; aggregate original budgets')
    args = parser.parse_args()
    prior = None
    source_record = RECORD
    if args.retry_official_gcp:
        prior = json.loads((RECORD / 'acquisition.json').read_text(encoding='utf-8'))
        for item in prior['artifacts']:
            path = (ROOT / item['path']).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file() or path.stat().st_size != item['size_bytes'] or sha(path.read_bytes()) != item['sha256']:
                raise ValueError('Original attempt artifact changed; refusing retry')
        download = (RECORD / 'coco_download.html').read_text(encoding='utf-8')
        if 'gs://images.cocodataset.org/annotations' not in download or 'train2017' not in download:
            raise ValueError('Saved official GCP annotation/train host evidence missing')
        RECORD = RECORD / 'retry-official-gcp'
        MANIFEST = ROOT / 'data/manifests/coco-background-candidates-v2.jsonl'
        ARCHIVE = 'https://storage.googleapis.com/images.cocodataset.org/annotations/annotations_trainval2017.zip'
    if args.verify_only:
        acquisition = json.loads((RECORD / 'acquisition.json').read_text(encoding='utf-8'))
        for item in acquisition['artifacts']:
            path = (ROOT / item['path']).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file() or path.stat().st_size != item['size_bytes'] or sha(path.read_bytes()) != item['sha256']:
                raise ValueError(f'Artifact mismatch: {item["path"]}')
        print(json.dumps({'verified_artifacts': len(acquisition['artifacts']), 'images': acquisition['images_acquired'], 'network': False}))
        return
    if RECORD.exists() or MANIFEST.exists() or PHOTOS.exists() and (not args.retry_official_gcp or any(PHOTOS.iterdir())):
        raise ValueError('Intake outputs already exist; verify instead of overwriting/retrying')
    RECORD.mkdir(parents=True)
    PHOTOS.mkdir(parents=True, exist_ok=args.retry_official_gcp)
    plan = {'created_at_utc': now(), 'network_body_cap_bytes': TOTAL_CAP, 'requests_cap': MAX_REQUESTS,
            'expanded_json_cap_bytes': INFLATED_CAP, 'compressed_train_member_cap_bytes': COMPRESSED_CAP,
            'individual_photo_cap_bytes': IMAGE_CAP, 'max_photos': MAX_IMAGES, 'only_annotation_member_allowed': MEMBER,
            'original_partition': 'train2017', 'protected_annotations_read': False,
            'full_zip_fallback': False, 'source_urls': dict(SOURCES), 'archive_url': ARCHIVE,
            'training_admitted': False, 'project_split': None,
            'selection': 'Ascending source image ID; at least two room/furniture/object captions, no person/clothing word in any caption; CC BY2.0/CC BY-SA2.0 plus matching Flickr oEmbed author/licence/photo identity before photo.',
            'source_identity': 'One original COCO photo ID; scene/physical object identity unresolved; source author retained for conservative grouping.'}
    if prior:
        plan.update(prior_attempt={'path': (source_record / 'acquisition.json').relative_to(ROOT).as_posix(),
                                   'sha256': sha((source_record / 'acquisition.json').read_bytes())},
                    aggregate_prior_network_body_bytes=prior['total_consumed_network_body_bytes'],
                    aggregate_prior_requests=prior['requests_made'],
                    source_use_basis='Root reviewed saved official CC BY4.0 annotation terms and per-photo Flickr conditions; existing user internet-dataset instruction authorizes ordinary public licensed intake. No account or click-through acceptance action.',
                    official_transport_evidence={'path': (source_record / 'coco_download.html').relative_to(ROOT).as_posix(),
                                                 'sha256': sha((source_record / 'coco_download.html').read_bytes()),
                                                 'documented_bucket': 'gs://images.cocodataset.org',
                                                 'transport': 'HTTPS public GCP object endpoint; same documented bucket/object; TLS verification retained'})
    write_json(RECORD / 'plan.json', plan)
    fetcher = BudgetFetcher(RECORD)
    if prior:
        previous_requests = json.loads((source_record / 'requests.json').read_text(encoding='utf-8'))
        if previous_requests['total_consumed_body_bytes'] != prior['total_consumed_network_body_bytes'] or len(previous_requests['requests']) != prior['requests_made']:
            raise ValueError('Original request accounting mismatch')
        fetcher.used = prior['total_consumed_network_body_bytes']
        fetcher.requests = previous_requests['requests']
    report = {'started_at_utc': now(), 'status': 'running', 'images_acquired': 0, 'training_admitted': 0,
              'new_labels': 0, 'project_splits_assigned': 0, 'caption_triage_is_not_absence_truth': True,
              'candidate_outcomes': [], 'artifacts': []}
    samples = []
    try:
        if not prior:
            for name, url in SOURCES:
                fetcher.get(url, MIB, name=name)
        _, probe = fetcher.get(ARCHIVE, 1, (0, 0), 'archive-probe.bin')
        archive_size = probe['archive_size_bytes']
        def ranged(start, end):
            body, event = fetcher.get(ARCHIVE, end - start + 1, (start, end))
            if event['archive_size_bytes'] != archive_size:
                raise ValueError('Archive length changed during intake')
            if event['headers'].get('ETag') != probe['headers'].get('ETag'):
                raise ValueError('Archive ETag changed during intake')
            return body
        reader = BoundedZip(ranged, archive_size)
        captions, entry = read_train_captions(reader)
        (RECORD / 'captions_train2017.json').write_bytes(captions)
        write_json(RECORD / 'selected-member.json', {'name': MEMBER, 'archive_size_bytes': archive_size,
                   'compressed_bytes': entry['compressed'], 'expanded_bytes': entry['size'], 'crc32': entry['crc'],
                   'sha256': sha(captions), 'protected_members_extracted': [], 'index_names_are_not_annotation_content': True})
        payload = json.loads(captions)
        candidates = select_candidates(payload)
        report.update(train_images_in_metadata=len(payload['images']), train_captions_in_metadata=len(payload['annotations']),
                      caption_eligible_candidates=len(candidates))
        write_json(RECORD / 'candidate-selection.json', candidates[:24])
        from PIL import Image
        for candidate in candidates[:24]:
            if len(samples) >= MAX_IMAGES or len(fetcher.requests) >= MAX_REQUESTS - 1:
                break
            image = candidate['image']
            result = {'coco_image_id': image['id'], 'outcome': 'pending'}
            report['candidate_outcomes'].append(result)
            try:
                match = re.search(r'/(\d+)_[^/]+\.jpg$', image.get('flickr_url', ''))
                if not match:
                    raise ValueError('No original Flickr photo ID')
                photo_page = 'https://www.flickr.com/photo.gne?id=' + match.group(1)
                url = 'https://www.flickr.com/services/oembed/?' + urllib.parse.urlencode({'format': 'json', 'url': photo_page})
                raw, meta_request = fetcher.get(url, MIB, name=f'{image["id"]:012d}_oembed.json')
                meta = json.loads(raw)
                credit = attribution(image, meta)
                image_url = image['coco_url'].replace('http://', 'https://')
                if image_url != f'https://images.cocodataset.org/train2017/{image["id"]:012d}.jpg':
                    raise ValueError('Unexpected original train image host/path')
                if args.retry_official_gcp:
                    image_url = image_url.replace('https://images.cocodataset.org/', 'https://storage.googleapis.com/images.cocodataset.org/')
                body, photo_request = fetcher.get(image_url, IMAGE_CAP)
                if not body.startswith(b'\xff\xd8\xff'):
                    raise ValueError('Photo is not a source JPEG')
                with Image.open(io.BytesIO(body)) as im:
                    im.load()
                    width, height = im.size
                    rgb = im.convert('RGB')
                    pixel_sha = sha(struct.pack('>II', width, height) + rgb.tobytes())
                if (width, height) != (image['width'], image['height']):
                    raise ValueError('COCO annotation/source dimensions differ')
                target = PHOTOS / image['file_name']
                target.write_bytes(body)
                sample = {'sample_id': f'coco-train2017-background-{image["id"]:012d}', 'source': 'COCO2017',
                          'original_split': 'train2017', 'source_image_id': image['id'], 'path': target.relative_to(ROOT).as_posix(),
                          'original_path': target.relative_to(ROOT).as_posix(),
                          'sha256': sha(body), 'pixel_sha256': pixel_sha, 'size_bytes': len(body), 'width': width, 'height': height,
                          'download_url': image_url, 'original_flickr_url': image['flickr_url'], 'source_licence_id': image['license'],
                          **credit, 'attribution_evidence': meta_request['body_path'], 'image_request_body': photo_request['body_path'],
                          'annotation_evidence': (RECORD / 'captions_train2017.json').relative_to(ROOT).as_posix(),
                          'source_captions': candidate['captions'], 'candidate_condition': candidate['condition'],
                          'candidate_condition_is_label': False, 'training_admitted': False, 'project_split': None,
                          'garment_id': None, 'physical_scene_id': None, 'scene_identity_status': 'unresolved',
                          'source_author_group': credit['author_url'], 'parent_frame_id': None, 'labels': {},
                          'review_status': 'awaiting_original_image_review', 'source_terms': dict(SOURCES)}
                samples.append(sample)
                result['outcome'] = 'downloaded_pending_visual_review'
            except Exception as exc:
                result.update(outcome='excluded_or_failed', reason=f'{type(exc).__name__}: {exc}')
        report['status'] = 'completed_candidates_only' if samples else 'bounded_attempt_no_photos'
    except Exception as exc:
        report.update(status='bounded_failure', error=f'{type(exc).__name__}: {exc}')
    finally:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in samples), encoding='utf-8', newline='\n')
        report.update(finished_at_utc=now(), images_acquired=len(samples), total_consumed_network_body_bytes=fetcher.used,
                      requests_made=len(fetcher.requests), no_installs=True, no_training=True,
                      executed_source={'path': Path(__file__).relative_to(ROOT).as_posix(), 'sha256': sha(Path(__file__).read_bytes())},
                      shared_zip_parser={'path': 'tools/datasets/bounded_zip.py', 'sha256': sha((ROOT / 'tools/datasets/bounded_zip.py').read_bytes())})
        (RECORD / 'executed_acquire_coco_backgrounds.py').write_bytes(Path(__file__).read_bytes())
        for path in sorted([p for p in RECORD.rglob('*') if p.is_file()] + list(PHOTOS.glob('*.jpg')) + [MANIFEST]):
            report['artifacts'].append({'path': path.relative_to(ROOT).as_posix(), 'size_bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())})
        write_json(RECORD / 'acquisition.json', report)
        print(json.dumps({key: report[key] for key in ('status', 'images_acquired', 'requests_made', 'total_consumed_network_body_bytes')}, indent=2))


if __name__ == '__main__':
    main()
