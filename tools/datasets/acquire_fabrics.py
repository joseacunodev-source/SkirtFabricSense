"""Bounded, resumable FabNet-3k source-image intake using HTTP range ZIP reads.

No downloaded code is executed. Only selected images are stored, not the whole ZIP.
Source labels are retained as source labels, not laboratory composition evidence.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import io
import json
import os
import random
import struct
import zlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import time
import urllib.request
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data/external/fabric_expansion"
URL = "https://github.com/kolon3d-prog/FabNet-3k/releases/download/1.0.0/FabNet-3k.zip"
SIZE = 1673285719
SOURCE = "https://github.com/kolon3d-prog/FabNet-3k"
CLASSES = ("Cotton", "Linen", "Polyester", "Silk", "Wool")
MAX_IMAGE_BYTES = 16 * 1024 * 1024
RESOLVED_URL = None
MANIFEST = ROOT / 'data/manifests/fabric_candidates.jsonl'
REPORT = ROOT / 'records/acquisitions/fabric_expansion.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def remote_range(start, end):
    global RESOLVED_URL
    if start < 0 or end < start or end >= SIZE or end-start > MAX_IMAGE_BYTES * 2:
        raise ValueError("Invalid or excessive byte range")
    expected = f"bytes {start}-{end}/{SIZE}"
    last = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(RESOLVED_URL or URL, headers={"Range": f"bytes={start}-{end}"})
            with urllib.request.urlopen(request, timeout=45) as response:
                if response.status != 206 or response.headers.get("Content-Range") != expected:
                    raise ValueError("Server did not honor the exact requested range")
                RESOLVED_URL = response.url  # Temporary redirect stays in memory, never in records.
                data = response.read(end-start+2)
            if len(data) != end-start+1:
                raise ValueError("Truncated or excessive response")
            return data
        except Exception as exc:
            last = exc
            RESOLVED_URL = None
            time.sleep(attempt + 1)
    raise RuntimeError(f"Range request failed: {type(last).__name__}") from last


class RemoteZip(io.RawIOBase):
    def __init__(self):
        self.position = 0

    def seekable(self):
        return True

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else (self.position if whence == 1 else SIZE) + offset
        return self.position

    def tell(self):
        return self.position

    def read(self, count=-1):
        end = SIZE if count < 0 else min(self.position+count, SIZE)
        if end <= self.position:
            return b""
        data = remote_range(self.position, end-1)
        self.position = end
        return data


def inventory():
    with zipfile.ZipFile(RemoteZip()) as archive:
        rows = []
        for entry in archive.infolist():
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in entry.filename:
                raise ValueError("Unsafe archive entry")
            rows.append({"path": entry.filename, "bytes": entry.file_size,
                         "compressed_bytes": entry.compress_size, "offset": entry.header_offset,
                         "crc32": entry.CRC, "compression": entry.compress_type})
    atomic(BASE / "metadata/archive_inventory.json", json.dumps(rows, indent=2).encode())
    return rows


def extract(entry):
    if entry['bytes'] > MAX_IMAGE_BYTES or entry['compressed_bytes'] > MAX_IMAGE_BYTES:
        raise ValueError('Image exceeds intake bound')
    offset = entry['offset']
    body = remote_range(offset, min(SIZE - 1, offset + entry['compressed_bytes'] + 4095))
    header = struct.unpack_from('<4s5H3L2H', body)
    if header[0] != b'PK\x03\x04' or header[2] & 1:
        raise ValueError('Unsupported ZIP header')
    name_len, extra_len = header[-2:]
    name = body[30:30 + name_len].decode('utf-8' if header[2] & 0x800 else 'cp437')
    if name != entry['path']:
        raise ValueError('Archive member identity mismatch')
    start = 30 + name_len + extra_len
    compressed = body[start:start + entry['compressed_bytes']]
    if entry['compression'] == 8:
        decoder = zlib.decompressobj(-15)
        image = decoder.decompress(compressed, entry['bytes'] + 1)
        if not decoder.eof or decoder.unconsumed_tail:
            raise ValueError('Truncated or oversized deflate data')
    elif entry['compression'] == 0:
        image = compressed
    else:
        raise ValueError('Unsupported compression')
    if len(image) != entry['bytes'] or zlib.crc32(image) != entry['crc32']:
        raise ValueError('Archive member length/CRC mismatch')
    return image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--per-class", type=int, default=250)
    parser.add_argument('--workers', type=int, default=12)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.per_class <= 500 or not 1 <= args.workers <= 16:
        parser.error('per-class 1..500; workers 1..16')
    chosen = [json.loads(line) for line in MANIFEST.read_text(encoding='utf-8').splitlines()] if MANIFEST.exists() else []
    for record in chosen:
        path = (ROOT / record['original_path']).resolve()
        if not path.is_relative_to(BASE.resolve()) or digest(path.read_bytes()) != record['sha256']:
            raise ValueError('Cached image integrity failure')
        with Image.open(path) as image:
            image.load()
    if args.verify_only:
        print(json.dumps({'verified_images': len(chosen), 'unique_hashes': len({x['sha256'] for x in chosen}), 'network_used': False}))
        return
    inventory_path = BASE / 'metadata/archive_inventory.json'
    rows = json.loads(inventory_path.read_text()) if inventory_path.exists() else inventory()
    if args.inventory_only:
        print(json.dumps({'entries': len(rows)}))
        return
    # Record the publisher's terms and claims, without executing source code.
    readme_url = 'https://raw.githubusercontent.com/kolon3d-prog/FabNet-3k/main/README.md'
    with urllib.request.urlopen(readme_url, timeout=30) as response:
        readme = response.read(1024 * 1024)
    atomic(BASE / 'metadata/source_README.md', readme)
    existing_ids = {r['source_item_id'] for r in chosen}
    hashes = {r['sha256'] for r in chosen}
    errors = []

    def obtain(entry):
        member = entry['path']
        label = member.split('/')[0]
        destination = BASE / 'images' / label.lower() / (digest(member.encode())[:24] + '.jpg')
        body = destination.read_bytes() if destination.exists() else extract(entry)
        if len(body) != entry['bytes'] or zlib.crc32(body) != entry['crc32']:
            raise ValueError('Cached image does not match archive')
        with Image.open(io.BytesIO(body)) as image:
            image.load()
            width, height = image.size
        atomic(destination, body)
        return {'schema_version': 1, 'sample_id': 'fabnet3k-' + digest(member.encode())[:24],
                'original_path': destination.relative_to(ROOT).as_posix(), 'sha256': digest(body),
                'size_bytes': len(body), 'width': width, 'height': height,
                'source_id': 'fabnet3k-1.0.0', 'source_partition': 'unspecified_in_archive',
                'source_item_id': member, 'source_url': SOURCE, 'download_url': URL,
                'archive_member': member, 'source_labels': {'publisher_folder': label, 'description': PurePosixPath(member).stem},
                'terms_reference': [SOURCE + '#-license', 'https://creativecommons.org/licenses/by/4.0/'],
                'terms_status': 'publisher_declares_CC_BY_4.0; underlying individual-photo provenance not supplied',
                'group_id': 'fabnet3k-item-' + digest(member.encode())[:24], 'garment_id': None,
                'parent_sample_id': None, 'grouping_review_pending': True,
                'project_labels': {}, 'training_eligibility': {},
                'label_review_status': 'publisher fiber folder only; descriptions can mention other fibers or blends',
                'capture_domain': 'fabric_texture_closeup_not_full_skirt',
                'acquired_at_utc': datetime.now(timezone.utc).isoformat()}

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for label in ('Cotton', 'Polyester'):
            candidates = [r for r in rows if r['path'].startswith(label + '/') and r['path'].lower().endswith(('.jpg', '.jpeg')) and r['path'] not in existing_ids]
            random.Random(20261002).shuffle(candidates)
            cursor = 0
            while sum(r['source_labels']['publisher_folder'] == label for r in chosen) < args.per_class and cursor < len(candidates):
                needed = args.per_class - sum(r['source_labels']['publisher_folder'] == label for r in chosen)
                batch = candidates[cursor:cursor + min(needed, args.workers)]
                cursor += len(batch)
                futures = {pool.submit(obtain, entry): entry for entry in batch}
                for future in concurrent.futures.as_completed(futures):
                    try:
                        record = future.result()
                        if record['sha256'] in hashes:
                            errors.append({'member': record['source_item_id'], 'error': 'exact_duplicate_not_counted'})
                            continue
                        chosen.append(record)
                        hashes.add(record['sha256'])
                    except Exception as exc:
                        errors.append({'member': futures[future]['path'], 'error_type': type(exc).__name__})
                chosen.sort(key=lambda r: r['sample_id'])
                atomic(MANIFEST, ('\n'.join(json.dumps(r, ensure_ascii=False) for r in chosen) + '\n').encode())
                print(f'Fabric images: {len(chosen)}; errors: {len(errors)}', flush=True)
    report = {'schema_version': 1, 'source': SOURCE, 'release': '1.0.0', 'archive_url': URL,
              'archive_size_bytes': SIZE, 'images': len(chosen), 'unique_content_hashes': len(hashes),
              'publisher_label_counts': dict(Counter(r['source_labels']['publisher_folder'] for r in chosen)),
              'image_bytes': sum(r['size_bytes'] for r in chosen), 'manifest': MANIFEST.relative_to(ROOT).as_posix(),
              'manifest_sha256': digest(MANIFEST.read_bytes()), 'source_readme_sha256': digest(readme),
              'source_code_sha256': digest(Path(__file__).read_bytes()), 'errors': errors,
              'completed_at_utc': datetime.now(timezone.utc).isoformat(), 'new_packages_installed': False,
              'training_admitted': 0, 'verified_project_fabric_labels': 0,
              'limitations': ['README train/val split absent in actual archive; preserve unspecified source partition.',
                             'Publisher fiber labels may contain blends or apparent title conflicts; label review required.',
                             'Closeup texture images do not validate single full-skirt recognition.',
                             'Original photo creator/composition provenance not supplied; publisher CC BY claim recorded.']}
    atomic(REPORT, (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({'images': len(chosen), 'publisher_labels': report['publisher_label_counts']}))


if __name__ == "__main__":
    main()
