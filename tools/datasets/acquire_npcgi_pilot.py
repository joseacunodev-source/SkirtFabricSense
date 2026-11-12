"""Predeclare and retrieve five bounded NPCGI image candidates by verified Copy ranges."""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request
import zlib

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.datasets.probe_fabric_archive import NoRedirect, ProbeError, parse_start, parse_next
from tools.datasets.inspect_fabric_7z_header import encoded_descriptor, decode_header, index_header, META, PROBE

INDEX = ROOT / 'records/acquisitions/2026-10-18-fabric-archive-index'
OUT = ROOT / 'records/acquisitions/2026-10-18-npcgi-pilot'
IMAGES = ROOT / 'data/external/npcgi_pilot'
MANIFEST = ROOT / 'data/manifests/npcgi-pilot-candidates.jsonl'
BYTE_LIMIT = 32 * 1024 * 1024
FILE_LIMIT = 8 * 1024 * 1024
REQUEST_LIMIT = 5

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verified_index():
    probe = json.loads((PROBE / 'report.json').read_text())
    start = (PROBE / 'start-header.bin').read_bytes()
    nxt = (PROBE / 'next-header.bin').read_bytes()
    if sha(start) != probe['start_header_sha256'] or sha(nxt) != probe['next_header_sha256']:
        raise ProbeError('Probe evidence hash mismatch')
    head = parse_start(start, probe['archive_size_bytes'])
    parse_next(nxt, head['next_header_crc32'])
    descriptor = encoded_descriptor(nxt, probe['archive_size_bytes'], head['next_header_start'])
    decoded = decode_header((INDEX / 'packed-header.bin').read_bytes(), descriptor)
    parsed = index_header(decoded, descriptor['start'])
    saved = json.loads((INDEX / 'parsed/archive-index.json').read_text())
    if parsed != saved:
        raise ProbeError('Saved index differs from verified archive header')
    return probe, parsed

def select_candidates(parsed, metadata):
    by_id = {r['source_item_id']: r for r in metadata}
    if len(by_id) != len(metadata):
        raise ProbeError('Duplicate source item IDs')
    candidates = []
    for entry in parsed['entries']:
        item = Path(entry['name']).stem
        if item not in by_id or entry['empty_stream']:
            continue
        raw = by_id[item]['source_row']
        folder = parsed['streams']['folders'][entry['folder_index']]
        if (folder['codec_hex'] != '00' or folder['solid'] or folder['substream_count'] != 1
                or folder['packed_size'] != entry['unpacked_size'] or entry['crc32'] is None
                or not 0 < entry['unpacked_size'] <= FILE_LIMIT):
            raise ProbeError('Matched candidate is not a bounded CRC-defined independent Copy stream')
        candidates.append({'source_item_id': item, 'archive_filename': entry['name'],
            'range_start': folder['packed_start'], 'size_bytes': entry['unpacked_size'],
            'crc32': entry['crc32'], 'source_row': raw})
    readable = [r for r in candidates if r['source_row'].get('Care Label Present (0,1)') == '1'
                and r['source_row'].get('Readable label (0,1)') == '1']
    # Interleave first-fibre groups, each sorted by source item ID, before inspecting images.
    groups = [[r for r in sorted(readable, key=lambda x:x['source_item_id'])
               if r['source_row'].get('Fibre 1 Layer 1') == fibre] for fibre in ('cotton', 'polyester')]
    selected = []
    while len(selected) < 5 and any(groups):
        for group in groups:
            if group and len(selected) < 5:
                selected.append(group.pop(0))
    if len(selected) != 5 or sum(r['size_bytes'] + 1 for r in selected) > BYTE_LIMIT:
        raise ProbeError('Insufficient preferred candidates or total byte budget exceeded')
    return selected

class BoundedImages:
    def __init__(self, url, size, opener=None):
        self.url, self.size = url, size
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        self.bytes_read, self.requests = 0, []

    def fetch(self, start, length):
        end = start + length - 1
        if (type(start) is not int or type(length) is not int or start < 32 or end >= self.size
                or not 0 < length <= FILE_LIMIT or self.bytes_read + length + 1 > BYTE_LIMIT
                or len(self.requests) >= REQUEST_LIMIT):
            raise ProbeError('Image range or acquisition budget exceeded')
        event = {'start': start, 'end': end, 'status': None, 'body_bytes_read': 0}
        self.requests.append(event)
        req = urllib.request.Request(self.url, headers={'Range': f'bytes={start}-{end}',
            'Accept-Encoding':'identity', 'User-Agent':'SkirtFabricSense-bounded-photo-research/1'})
        try:
            response = self.opener.open(req, timeout=30)
        except urllib.error.HTTPError as exc:
            event['status'] = exc.code
            exc.close()
            raise ProbeError('HTTP error or redirect; no body read') from None
        with response:
            event['status'] = response.status
            if (response.status != 206 or response.headers.get('Content-Range') != f'bytes {start}-{end}/{self.size}'
                    or response.headers.get('Content-Encoding','identity').lower() != 'identity'
                    or response.headers.get('Content-Length') not in (None,str(length))):
                raise ProbeError('Unexpected range response; no body read')
            chunks, remaining = [], length + 1
            while remaining:
                chunk = response.read(min(65536, remaining))
                if not chunk:
                    break
                self.bytes_read += len(chunk)
                event['body_bytes_read'] += len(chunk)
                chunks.append(chunk)
                remaining -= len(chunk)
            data = b''.join(chunks)
            if len(data) != length:
                raise ProbeError('Image body length mismatch')
            return data

def acquire(output=OUT, images=IMAGES, manifest=MANIFEST):
    from PIL import Image
    output, images, manifest = Path(output), Path(images), Path(manifest)
    if output.exists() or images.exists() or manifest.exists():
        raise ProbeError('Refusing to overwrite acquisition evidence or original images')
    probe, parsed = verified_index()
    metadata = [json.loads(line) for line in META.read_text().splitlines()]
    selected = select_candidates(parsed, metadata)
    output.mkdir(parents=True)
    images.mkdir(parents=True)
    selection = {'selection_rule':'Five readable-label IDs interleaved cotton then polyester; each group lexicographically sorted; predeclared before any image payload/view.',
                 'selected': selected, 'archive_index_sha256': sha((INDEX/'parsed/archive-index.json').read_bytes()),
                 'metadata_sha256':sha(META.read_bytes()), 'selected_before_image_acquisition':True}
    (output/'selection.json').write_text(json.dumps(selection,indent=2)+'\n',encoding='utf-8')
    reader = BoundedImages(probe['publisher_url'], probe['archive_size_bytes'])
    report = {'schema_version':1, 'date_asia_manila':datetime.now(timezone(timedelta(hours=8))).date().isoformat(),
              'publisher_url':probe['publisher_url'], 'archive_size_bytes':probe['archive_size_bytes'],
              'budget':{'body_bytes':BYTE_LIMIT,'per_image_bytes':FILE_LIMIT,'requests':REQUEST_LIMIT},
              'selection_sha256':sha((output/'selection.json').read_bytes()), 'requests':reader.requests,
              'original_images_acquired':0,'training_admissions':0,'status':'started'}
    rows = []
    try:
        for candidate in selected:
            data = reader.fetch(candidate['range_start'],candidate['size_bytes'])
            if zlib.crc32(data) != candidate['crc32']:
                raise ProbeError('Archive image CRC mismatch')
            with Image.open(io.BytesIO(data)) as im:
                if im.format != 'JPEG' or im.width * im.height > 40_000_000:
                    raise ProbeError('Unexpected image format or excessive decoded dimensions')
                im.load()
                dimensions = [im.width,im.height]
                pixels = sha(im.convert('RGB').tobytes())
            path = images/(candidate['source_item_id']+'.jpg')
            path.write_bytes(data)
            rows.append({**candidate, 'sample_id':'npcgi-v1.1:'+candidate['source_item_id'],
                'source_id':'npcgi-v1.1','source_version':'1.1','source_url':'https://zenodo.org/records/20440761',
                'source_archive_url':probe['publisher_url'], 'license_id':'CC-BY-SA-4.0',
                'license_url':'https://creativecommons.org/licenses/by-sa/4.0/',
                'attribution':'Pettersen, Aarak, Peña Benítez and Nourin Moury; Norway post-consumer garment data and images, version 1.1',
                'changes':'None; exact original JPEG bytes selectively extracted from publisher archive.',
                'original_path':path.relative_to(ROOT).as_posix(), 'sha256':sha(data),
                'decoded_rgb_sha256':pixels,'dimensions':dimensions,'crc32_verified':True,
                'group_id':'NPCGI:'+candidate['source_item_id'],'split':None,'source_split':None,
                'training_eligible':False,'label_status':'candidate_unreviewed',
                'presentation':'unknown','full_garment_visible':None,
                'fabric_appearance_label':None,'fiber_evidence':'Publisher care-label transcription; raw multilayer fields retained; unverified against photo.'})
            manifest.parent.mkdir(parents=True,exist_ok=True)
            manifest.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
            report['original_images_acquired'] = len(rows)
        report['status'] = 'five_candidates_acquired_unadmitted'
    except (ProbeError,OSError,TimeoutError) as exc:
        report['status'] = 'stopped'
        report['reason'] = str(exc) if isinstance(exc,ProbeError) else type(exc).__name__
    report['body_bytes_read'] = reader.bytes_read
    report['manifest_sha256'] = sha(manifest.read_bytes()) if manifest.exists() else None
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(acquire(),indent=2))
