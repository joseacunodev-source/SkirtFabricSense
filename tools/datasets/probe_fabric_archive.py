"""Bounded 7z range-header probe; never downloads or extracts archive images."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import urllib.error
import urllib.request
from urllib.parse import urlsplit
import zlib

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'records/acquisitions/2026-10-17-fabric-source-resolution/zenodo-record.json'
OUT = ROOT / 'records/acquisitions/2026-10-18-fabric-archive-probe'
HEADER_LIMIT = 1024 * 1024
BYTE_BUDGET = 2 * 1024 * 1024
REQUEST_LIMIT = 3
TIMEOUT = 20
SIGNATURE = b'7z\xbc\xaf\x27\x1c'


class ProbeError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def choose_archive(record):
    candidates = [f for f in record['files']
                  if re.fullmatch(r'NPCGI_[A-F]xxxx\.7z', f['key'])]
    if not candidates:
        raise ProbeError('No publisher image archive found')
    chosen = min(candidates, key=lambda f: f['size'])
    url = chosen['links']['self']
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.netloc != 'zenodo.org'
            or parsed.query or parsed.fragment or type(chosen['size']) is not int
            or chosen['size'] < 32):
        raise ProbeError('Invalid publisher archive record')
    return chosen


class RangeReader:
    def __init__(self, url, size, opener=None):
        self.url, self.size = url, size
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        self.bytes_read = 0
        self.requests = []

    def fetch(self, start, end):
        length = end - start + 1
        if (type(start) is not int or type(end) is not int or start < 0
                or end >= self.size or length <= 0
                or self.bytes_read + length + 1 > BYTE_BUDGET
                or len(self.requests) >= REQUEST_LIMIT):
            raise ProbeError('Range or probe budget exceeded')
        event = {'start': start, 'end': end, 'status': None, 'body_bytes_read': 0}
        self.requests.append(event)
        request = urllib.request.Request(self.url, headers={
            'Range': f'bytes={start}-{end}', 'Accept-Encoding': 'identity',
            'User-Agent': 'SkirtFabricSense-bounded-header-research/1'})
        try:
            response = self.opener.open(request, timeout=TIMEOUT)
        except urllib.error.HTTPError as exc:
            event['status'] = exc.code
            exc.close()
            raise ProbeError('Publisher HTTP error or redirect; no body read') from None
        with response:
            event['status'] = response.status
            # Check headers before any body read: HTTP200 could be the full 8GB file.
            if response.status != 206:
                raise ProbeError('Publisher did not honor exact range; no body read')
            content_range = response.headers.get('Content-Range', '')
            if content_range != f'bytes {start}-{end}/{self.size}':
                raise ProbeError('Unexpected Content-Range; no body read')
            if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
                raise ProbeError('Unexpected Content-Encoding; no body read')
            declared = response.headers.get('Content-Length')
            if declared is not None and declared != str(length):
                raise ProbeError('Unexpected Content-Length; no body read')
            chunks = []
            remaining = length + 1
            while remaining:
                chunk = response.read(min(65536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                self.bytes_read += len(chunk)
                event['body_bytes_read'] += len(chunk)
                remaining -= len(chunk)
            data = b''.join(chunks)
            if len(data) != length:
                raise ProbeError('Range body length mismatch')
            return data


def parse_start(data, archive_size):
    if len(data) != 32 or data[:6] != SIGNATURE:
        raise ProbeError('Invalid 7z signature or start length')
    if data[6] != 0:
        raise ProbeError('Unsupported 7z major version')
    start_crc, = struct.unpack_from('<I', data, 8)
    if zlib.crc32(data[12:32]) != start_crc:
        raise ProbeError('Start-header CRC mismatch')
    offset, size, crc = struct.unpack_from('<QQI', data, 12)
    if not 0 < size <= HEADER_LIMIT:
        raise ProbeError('Next-header size exceeds bounded policy or is empty')
    start = 32 + offset
    if start < 32 or start + size > archive_size:
        raise ProbeError('Next-header offset outside archive')
    return {'version': [data[6], data[7]], 'start_crc32_verified': True,
            'next_header_start': start, 'next_header_size': size,
            'next_header_crc32': crc}


def parse_next(data, expected_crc):
    if not data or zlib.crc32(data) != expected_crc:
        raise ProbeError('Next-header CRC mismatch')
    marker = data[0]
    return {'next_crc32_verified': True, 'first_marker_hex': f'{marker:02x}',
            'encoded_header': marker == 0x17, 'plain_header': marker == 0x01,
            'next_header_sha256': hashlib.sha256(data).hexdigest()}


def probe(record, output, opener=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    chosen = choose_archive(record)
    reader = RangeReader(chosen['links']['self'], chosen['size'], opener)
    observed = datetime.now(timezone(timedelta(hours=8)))
    report = {'schema_version': 1, 'date_asia_manila': observed.date().isoformat(),
              'observed_at_asia_manila': observed.isoformat(),
              'publisher_record': 'https://zenodo.org/records/20440761',
              'publisher_url': chosen['links']['self'], 'archive': chosen['key'],
              'archive_size_bytes': chosen['size'], 'publisher_checksum': chosen.get('checksum'),
              'budget': {'bytes': BYTE_BUDGET, 'requests': REQUEST_LIMIT,
                         'timeout_seconds_per_request': TIMEOUT, 'next_header_bytes': HEADER_LIMIT},
              'requests': reader.requests, 'original_images_downloaded': 0,
              'training_admissions': 0, 'selective_extraction': 'unresolved',
              'status': 'started'}
    try:
        start = reader.fetch(0, 31)
        (output / 'start-header.bin').write_bytes(start)
        report['start_header_sha256'] = hashlib.sha256(start).hexdigest()
        report.update(parse_start(start, chosen['size']))
        position, length = report['next_header_start'], report['next_header_size']
        data = reader.fetch(position, position + length - 1)
        (output / 'next-header.bin').write_bytes(data)
        report.update(parse_next(data, report['next_header_crc32']))
        report['status'] = 'header_probe_verified'
        report['conclusion'] = (
            'Encoded header requires bounded stream decoding and solid-block analysis before selective image extraction can be established.'
            if report['encoded_header'] else
            'Header bytes verified; filenames, stream/block layout and selective extraction remain unparsed.')
    except (ProbeError, OSError, TimeoutError) as exc:
        report['status'] = 'probe_stopped'
        # Never persist arbitrary network exceptions or redirect URLs.
        report['reason'] = str(exc) if isinstance(exc, ProbeError) else type(exc).__name__
        report['conclusion'] = 'Selective image extraction remains unresolved; no full archive requested.'
    report['body_bytes_read'] = reader.bytes_read
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    record = json.loads(args.source.read_text(encoding='utf-8'))
    result = probe(record, args.output)
    print(json.dumps({key: result[key] for key in ('status', 'archive', 'body_bytes_read', 'conclusion')}))


if __name__ == '__main__':
    main()
