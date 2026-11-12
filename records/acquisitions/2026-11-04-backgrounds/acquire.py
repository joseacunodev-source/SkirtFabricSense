"""Acquire a bounded, attributed Commons original-photo candidate set.

No image labels, development eligibility or project splits are inferred from
categories. Commons has no publisher train/validation partition. Download only
API-reported original JPEG bytes, never thumbnail substitutes.
"""
from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import io
import json
import re
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MIB = 1024 * 1024

RECORD = ROOT / 'records/acquisitions/2026-11-04-backgrounds'
PHOTOS = ROOT / 'data/candidates/backgrounds-20261104'
MANIFEST = ROOT / 'data/manifests/background-candidates-20261104.jsonl'
API = 'https://commons.wikimedia.org/w/api.php'
REUSE = 'https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia'
TOTAL_CAP = 120 * MIB
REQUEST_CAP = 40
PHOTO_CAP = 5 * MIB
MAX_IMAGES = 12
CATEGORIES = ('Category:Empty bedrooms', 'Category:Empty classrooms', 'Category:Empty rooms in the Netherlands', 'Category:Empty rooms in the United Kingdom')
EXCLUDE = re.compile(r'\b(person|persons|people|man|men|woman|women|boy|girl|child|children|baby|skirt|skirts|dress|dresses|clothing|garment|wearing|portrait|crowd)\b', re.I)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(body):
    return hashlib.sha256(body).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')


class BudgetFetcher:
    """All consumed success/error/overflow bytes count; redirects are refused."""
    def __init__(self, output, total_cap=TOTAL_CAP, request_cap=REQUEST_CAP, opener=None):
        self.output, self.total_cap, self.request_cap = Path(output), total_cap, request_cap
        self.used, self.requests = 0, []
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        self.opener = opener or urllib.request.build_opener(NoRedirect())

    def get(self, url, cap, name=None):
        if len(self.requests) >= self.request_cap or self.used >= self.total_cap:
            raise ValueError('Declared request/body budget exhausted')
        if cap <= 0:
            raise ValueError('Invalid response cap')
        event = {'url': url, 'started_at_utc': now(), 'response_cap_bytes': cap,
                 'consumed_body_bytes': 0, 'outcome': 'pending'}
        self.requests.append(event)
        body = bytearray()
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'SkirtFabricSense/1.0 (bounded educational photo intake)',
                                                       'Accept-Encoding': 'identity'})
            try:
                response = self.opener.open(req, timeout=40)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                event.update(status=response.status, resolved_url=response.url,
                             headers={k: response.headers[k] for k in ('Content-Length', 'Content-Type', 'Content-Encoding', 'ETag', 'Last-Modified', 'Location') if k in response.headers})
                if response.headers.get('Content-Encoding', 'identity').lower() not in ('identity', ''):
                    raise ValueError('Unexpected content encoding')
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
                if response.status != 200:
                    raise ValueError(f'HTTP {response.status}')
            event['outcome'] = 'success'
            return bytes(body), event
        except Exception as exc:
            event.update(outcome='failed', error=f'{type(exc).__name__}: {exc}')
            raise
        finally:
            event['finished_at_utc'] = now()
            event['sha256_consumed_body'] = sha(body)
            if body:
                target = self.output / (name or f'response-{len(self.requests):02d}.bin')
                if target.exists():
                    raise ValueError('Refusing existing response destination')
                target.write_bytes(body)
                event['body_path'] = target.relative_to(ROOT).as_posix() if target.is_relative_to(ROOT) else target.name
            write_json(self.output / 'requests.json', {'total_consumed_body_bytes': self.used, 'requests': self.requests})


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def text(value):
    parser = PlainText()
    parser.feed(value)
    return ' '.join(' '.join(parser.parts).split())


def api_url(**values):
    return API + '?' + urllib.parse.urlencode(dict(action='query', format='json', formatversion='2', **values))


def category_rows(payload, category):
    if 'error' in payload or not isinstance(payload.get('query', {}).get('categorymembers'), list):
        raise ValueError('Commons API error or unexpected category schema')
    rows = payload['query']['categorymembers']
    if len(rows) > 8:
        raise ValueError('Category response exceeded declared result bound')
    selected = []
    seen = set()
    for row in rows:
        if row.get('ns') != 6 or not isinstance(row.get('pageid'), int) or row['pageid'] <= 0 or row['pageid'] in seen:
            raise ValueError('Invalid/duplicate file category entry')
        seen.add(row['pageid'])
        title = row.get('title', '')
        if not title.startswith('File:'):
            raise ValueError('Non-file namespace title')
        if title.lower().endswith(('.jpg', '.jpeg')) and not EXCLUDE.search(title):
            selected.append({'pageid': row['pageid'], 'title': title, 'candidate_category': category})
    return sorted(selected, key=lambda row: (row['title'].casefold(), row['pageid']))


def photo_evidence(page, selected):
    if page.get('pageid') != selected['pageid'] or page.get('title') != selected['title'] or page.get('ns') != 6:
        raise ValueError('File identity changed between category and metadata')
    if page.get('missing') or len(page.get('imageinfo', [])) != 1 or len(page.get('revisions', [])) != 1:
        raise ValueError('Missing current file or description revision')
    info = page['imageinfo'][0]
    if info.get('mime') != 'image/jpeg' or info.get('mediatype') != 'BITMAP':
        raise ValueError('Original is not a JPEG bitmap')
    if type(info.get('size')) is not int or not 0 < info['size'] <= PHOTO_CAP:
        raise ValueError('Original photo outside 5MiB cap')
    if any(type(info.get(key)) is not int or not 0 < info[key] <= 16000 for key in ('width', 'height')):
        raise ValueError('Invalid/excessive original dimensions')
    url = info.get('url', '')
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.netloc != 'upload.wikimedia.org' or not parsed.path.startswith('/wikipedia/commons/') or '/thumb/' in parsed.path or not parsed.path.lower().endswith(('.jpg', '.jpeg')) or parsed.query or parsed.fragment:
        raise ValueError('Unexpected original URL or thumbnail substitution')
    revision = page['revisions'][0].get('revid')
    if not isinstance(revision, int) or revision <= 0:
        raise ValueError('Missing exact source-description revision')
    meta = info.get('extmetadata', {})
    values = {key: value.get('value', '') for key, value in meta.items() if isinstance(value, dict)}
    license_url = html.unescape(values.get('LicenseUrl', '')).replace('http://', 'https://').rstrip('/') + '/'
    if not re.fullmatch(r'https://creativecommons\.org/licenses/(by|by-sa)/(2\.0|2\.5|3\.0|4\.0)/', license_url):
        raise ValueError('No accepted per-file CC BY/BY-SA licence')
    match = re.fullmatch(r'https://creativecommons\.org/licenses/(by|by-sa)/([^/]+)/', license_url)
    expected_name = 'CC ' + match[1].upper() + ' ' + match[2]
    if text(values.get('LicenseShortName', '')).upper() != expected_name:
        raise ValueError('Per-file licence name/URL conflict or unresolved multi-licensing')
    artist_html = values.get('Artist', '')
    artist = text(artist_html)
    if not artist or artist.casefold() in ('unknown', 'anonymous', 'unknown author'):
        raise ValueError('Creator attribution unresolved')
    if text(values.get('Restrictions', '')).strip():
        raise ValueError('Additional source restrictions require separate review')
    if not re.fullmatch(r'[0-9a-f]{40}', info.get('sha1', '')):
        raise ValueError('Missing original file SHA1')
    source_page = 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(page['title'].replace(' ', '_'), safe=':')
    return dict(original_download_url=url, source_page=source_page,
                source_revision=revision, source_revision_url=f'https://commons.wikimedia.org/w/index.php?oldid={revision}',
                author=artist, author_html=artist_html, credit=text(values.get('Credit', '')),
                license_url=license_url, license_short_name=text(values.get('LicenseShortName', '')),
                usage_terms=text(values.get('UsageTerms', '')), original_sha1=info['sha1'],
                expected_size_bytes=info['size'], expected_width=info['width'], expected_height=info['height'],
                original_file_timestamp=info.get('timestamp'), source_uploader=info.get('user'),
                metadata_description=text(values.get('ImageDescription', '')),
                original_title=text(values.get('ObjectName', '')) or page['title'],
                modifications='None; original source JPEG bytes retained')


def verify(acquisition):
    for row in acquisition['artifacts']:
        path = (ROOT / row['path']).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file() or path.stat().st_size != row['size_bytes'] or sha(path.read_bytes()) != row['sha256']:
            raise ValueError(f'Artifact mismatch: {row["path"]}')
    return {'artifacts_verified': len(acquisition['artifacts']), 'images': acquisition['images_acquired'], 'network': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify(json.loads((RECORD / 'acquisition.json').read_text(encoding='utf-8')))))
        return
    if (RECORD / 'plan.json').exists() or PHOTOS.exists() or MANIFEST.exists():
        raise ValueError('Existing intake outputs; verify rather than overwrite/retry')
    RECORD.mkdir(parents=True, exist_ok=True)
    PHOTOS.mkdir(parents=True)
    plan = {'created_at_utc': now(), 'max_network_body_bytes_including_failures': TOTAL_CAP,
            'max_requests_including_failures': REQUEST_CAP, 'max_photos': MAX_IMAGES, 'max_individual_photo_bytes': PHOTO_CAP,
            'selection': 'Fixed category order, first8 direct file members sorted ascending source sortkey; JPEG title eligibility; per-category title/pageID ascending, deduplicate pageIDs; first12 eligible original JPEGs. No continuation/category recursion.',
            'categories': list(CATEGORIES), 'candidate_condition_is_not_absence_truth': True,
            'rights': 'Per-file CC BY/BY-SA2.0,2.5,3.0,4.0 only, named creator, source revision, no additional restrictions; retain attribution and exact source metadata.',
            'source_partition': 'not_applicable_public_photo_collection', 'project_split': None,
            'training_admitted': False, 'original_jpeg_only': True, 'no_thumbnail_fallback': True,
            'no_accounts_or_agreement_operations': True, 'purpose': 'Unadmitted empty-room/furniture/ordinary-object visual-review candidates, not camera-domain truth or benchmark accuracy.',
            'api': API, 'source_reuse_guidance': REUSE}
    write_json(RECORD / 'plan.json', plan)
    fetcher = BudgetFetcher(RECORD, total_cap=TOTAL_CAP, request_cap=REQUEST_CAP)
    report = {'started_at_utc': now(), 'status': 'running', 'images_acquired': 0, 'labels_added': 0,
              'training_admissions': 0, 'project_splits_assigned': 0, 'outcomes': [], 'artifacts': []}
    samples = []
    try:
        candidates, seen = [], set()
        for index, category in enumerate(CATEGORIES):
            raw, _ = fetcher.get(api_url(list='categorymembers', cmtitle=category, cmtype='file', cmlimit='8',
                                       cmsort='sortkey', cmdir='ascending'), MIB, name=f'category-{index+1}.json')
            for row in category_rows(json.loads(raw), category):
                if row['pageid'] not in seen:
                    candidates.append(row)
                    seen.add(row['pageid'])
        write_json(RECORD / 'candidate-selection.json', candidates)
        fetcher.get(REUSE, MIB, name='commons_reuse.html')
        from PIL import Image
        cached_licenses = set()
        for selected in candidates:
            if len(samples) >= MAX_IMAGES or len(fetcher.requests) >= REQUEST_CAP - 2 or fetcher.used >= TOTAL_CAP - PHOTO_CAP - MIB:
                break
            outcome = {'source_page_id': selected['pageid'], 'title': selected['title'], 'outcome': 'pending'}
            report['outcomes'].append(outcome)
            try:
                raw, request = fetcher.get(api_url(pageids=str(selected['pageid']), prop='imageinfo|revisions',
                    iiprop='url|size|sha1|mime|mediatype|extmetadata|timestamp|user', iilimit='1', rvprop='ids', rvlimit='1',
                    iiextmetadatafilter='Artist|Credit|LicenseShortName|LicenseUrl|UsageTerms|AttributionRequired|Copyrighted|ObjectName|ImageDescription|Restrictions'),
                    MIB, name=f'{selected["pageid"]}_metadata.json')
                payload = json.loads(raw)
                if 'error' in payload or len(payload.get('query', {}).get('pages', [])) != 1:
                    raise ValueError('Commons file metadata API schema/error')
                evidence = photo_evidence(payload['query']['pages'][0], selected)
                license_url = evidence['license_url']
                if license_url not in cached_licenses:
                    fetcher.get(license_url, MIB, name='licence-' + license_url.split('/licenses/')[1].replace('/', '-') + '.html')
                    cached_licenses.add(license_url)
                body, photo_request = fetcher.get(evidence['original_download_url'], PHOTO_CAP)
                if not body.startswith(b'\xff\xd8\xff') or len(body) != evidence['expected_size_bytes'] or hashlib.sha1(body).hexdigest() != evidence['original_sha1']:
                    raise ValueError('Original photo JPEG/size/SHA1 mismatch')
                with Image.open(io.BytesIO(body)) as image:
                    image.load()
                    width, height = image.size
                    if (width, height) != (evidence['expected_width'], evidence['expected_height']):
                        raise ValueError('Original photo dimensions mismatch')
                    pixel_sha = sha(struct.pack('>II', width, height) + image.convert('RGB').tobytes())
                target = PHOTOS / f'commons-{selected["pageid"]}.jpg'
                target.write_bytes(body)
                path = target.relative_to(ROOT).as_posix()
                samples.append({'sample_id': f'commons-background-20261104-{selected["pageid"]}', 'source': 'Wikimedia Commons',
                    'source_page_id': selected['pageid'], 'source_file_title': selected['title'], **evidence,
                    'path': path, 'original_path': path, 'sha256': sha(body), 'pixel_sha256': pixel_sha,
                    'size_bytes': len(body), 'width': width, 'height': height,
                    'metadata_evidence': request['body_path'], 'original_response_evidence': photo_request['body_path'],
                    'candidate_category': selected['candidate_category'], 'candidate_condition_is_label': False,
                    'source_partition': 'not_applicable_public_photo_collection', 'original_split': 'not_applicable_public_photo_collection',
                    'project_split': None, 'training_admitted': False, 'labels': {},
                    'review_status': 'awaiting_original_image_and_duplicate_review', 'source_creator_group': evidence['author_html'],
                    'physical_scene_id': None, 'physical_scene_identity': 'unresolved', 'garment_id': None, 'parent_frame_id': None,
                    'camera_domain': 'external_public_photo_not_project_station', 'source_terms': REUSE})
                outcome['outcome'] = 'acquired_pending_visual_review'
            except Exception as exc:
                outcome.update(outcome='excluded_or_failed', reason=f'{type(exc).__name__}: {exc}')
        report['status'] = 'completed_unadmitted_candidates' if samples else 'bounded_attempt_no_photos'
    except Exception as exc:
        report.update(status='bounded_failure', error=f'{type(exc).__name__}: {exc}')
    finally:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in samples), encoding='utf-8', newline='\n')
        report.update(finished_at_utc=now(), images_acquired=len(samples), requests_made=len(fetcher.requests),
                      consumed_network_body_bytes=fetcher.used, no_installs=True, no_inference=True,
                      independent_physical_scenes=None, protected_dataset_annotations_downloaded=0,
                      executed_source_sha256=sha(Path(__file__).read_bytes()),
                      fetcher_source='Embedded in this tool; no mutable COCO-tool dependency')
        (RECORD / 'executed_acquire_commons_backgrounds.py').write_bytes(Path(__file__).read_bytes())
        for path in sorted([p for p in RECORD.rglob('*') if p.is_file()] + list(PHOTOS.glob('*.jpg')) + [MANIFEST]):
            report['artifacts'].append({'path': path.relative_to(ROOT).as_posix(), 'size_bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())})
        write_json(RECORD / 'acquisition.json', report)
        print(json.dumps({key: report[key] for key in ('status', 'images_acquired', 'requests_made', 'consumed_network_body_bytes')}, indent=2))
    if report['status'] == 'bounded_failure':
        raise SystemExit(1)


if __name__ == '__main__':
    main()

