"""Read bounded encoded 7z header only, index filenames and metadata joins."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import re
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.datasets.probe_fabric_archive import RangeReader, ProbeError, parse_start, parse_next

PROBE = ROOT / 'records/acquisitions/2026-10-18-fabric-archive-probe'
META = ROOT / 'records/acquisitions/2026-10-17-fabric-source-resolution/skirt-metadata-candidates.jsonl'
OUT = ROOT / 'records/acquisitions/2026-10-18-fabric-archive-index'
DECODED_LIMIT = 8 * 1024 * 1024
DICT_LIMIT = 64 * 1024 * 1024
PACKED_LIMIT = 2 * 1024 * 1024 - 1
COUNT_LIMIT = 100000


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, n):
        if n < 0 or self.pos + n > len(self.data):
            raise ProbeError('Truncated 7z header')
        value = self.data[self.pos:self.pos + n]
        self.pos += n
        return value

    def byte(self):
        return self.take(1)[0]

    def uint(self):
        first, mask, value = self.byte(), 0x80, 0
        for index in range(8):
            if not first & mask:
                return value | ((first & (mask - 1)) << (8 * index))
            value |= self.byte() << (8 * index)
            mask >>= 1
        return value

    def count(self):
        value = self.uint()
        if value > COUNT_LIMIT:
            raise ProbeError('7z header count exceeds bound')
        return value

    def expect(self, tag):
        if self.byte() != tag:
            raise ProbeError('Unsupported 7z header property ordering')

    def done(self):
        if self.pos != len(self.data):
            raise ProbeError('Trailing 7z header bytes')


def bits(reader, count):
    raw = reader.take((count + 7) // 8)
    return [bool(raw[i // 8] & (0x80 >> (i % 8))) for i in range(count)]


def digests(reader, count):
    all_defined = reader.byte()
    if all_defined not in (0, 1):
        raise ProbeError('Invalid digest flags')
    defined = [True] * count if all_defined else bits(reader, count)
    return [struct.unpack('<I', reader.take(4))[0] if yes else None for yes in defined]


def coder(reader):
    if reader.count() != 1:
        raise ProbeError('Multiple coders in one folder unsupported')
    flags = reader.byte()
    if flags & 0xD0 or not 1 <= (flags & 0xF) <= 8:
        raise ProbeError('Complex or alternative 7z coder unsupported')
    codec = reader.take(flags & 0xF).hex()
    props = reader.take(reader.count()) if flags & 0x20 else b''
    if codec not in ('00', '030101', '21'):
        raise ProbeError('Unsupported 7z compression codec')
    return {'codec_hex': codec, 'properties_hex': props.hex()}


def streams(reader):
    result = {'pack_position': 0, 'pack_sizes': [], 'pack_crcs': [], 'folders': []}
    tag = reader.byte()
    if tag == 6:
        result['pack_position'] = reader.uint()
        count = reader.count()
        reader.expect(9)
        result['pack_sizes'] = [reader.uint() for _ in range(count)]
        result['pack_crcs'] = [None] * count
        tag = reader.byte()
        if tag == 10:
            result['pack_crcs'] = digests(reader, count)
            tag = reader.byte()
        if tag != 0:
            raise ProbeError('Unsupported pack property')
        tag = reader.byte()
    if tag != 7:
        raise ProbeError('Missing 7z unpack info')
    reader.expect(11)
    count = reader.count()
    reader.expect(0)  # External folder definitions unsupported.
    folders = [coder(reader) for _ in range(count)]
    if count != len(result['pack_sizes']):
        raise ProbeError('Only one packed stream per folder supported')
    reader.expect(12)
    for folder in folders:
        folder['unpacked_size'] = reader.uint()
        folder['crc32'] = None
        folder['substream_count'] = 1
    tag = reader.byte()
    if tag == 10:
        for folder, crc in zip(folders, digests(reader, count)):
            folder['crc32'] = crc
        tag = reader.byte()
    if tag != 0:
        raise ProbeError('Unsupported unpack property')
    tag = reader.byte()
    if tag == 8:
        tag = reader.byte()
        if tag == 13:
            for folder in folders:
                folder['substream_count'] = reader.count()
            tag = reader.byte()
        if sum(f['substream_count'] for f in folders) > COUNT_LIMIT:
            raise ProbeError('Total substreams exceed count bound')
        for folder in folders:
            n = folder['substream_count']
            sizes = [reader.uint() for _ in range(max(n - 1, 0))] if tag == 9 else []
            if n > 1 and tag != 9:
                raise ProbeError('Missing substream sizes')
            last = folder['unpacked_size'] - sum(sizes)
            if last < 0:
                raise ProbeError('Substream size exceeds folder size')
            folder['substream_sizes'] = sizes + ([last] if n else [])
        if tag == 9:
            tag = reader.byte()
        digest_count = sum(f['substream_count'] for f in folders
                           if f['substream_count'] != 1 or f['crc32'] is None)
        if tag == 10:
            sub_crcs = iter(digests(reader, digest_count))
            for folder in folders:
                folder['substream_crcs'] = ([folder['crc32']] if folder['substream_count'] == 1
                    and folder['crc32'] is not None else [next(sub_crcs) for _ in range(folder['substream_count'])])
            tag = reader.byte()
        if tag != 0:
            raise ProbeError('Unsupported substream property')
        tag = reader.byte()
    if tag != 0:
        raise ProbeError('Unsupported streams property')
    for folder in folders:
        folder.setdefault('substream_sizes', [folder['unpacked_size']])
        folder.setdefault('substream_crcs', [folder['crc32']] * folder['substream_count'])
    result['folders'] = folders
    return result


def encoded_descriptor(data, archive_size, next_start):
    reader = Reader(data)
    reader.expect(0x17)
    info = streams(reader)
    reader.done()
    if len(info['folders']) != 1:
        raise ProbeError('Encoded header requires one folder')
    start = 32 + info['pack_position']
    length = info['pack_sizes'][0]
    folder = info['folders'][0]
    if (not 0 < length <= PACKED_LIMIT or start < 32
            or start + length > next_start or start + length > archive_size
            or not 0 < folder['unpacked_size'] <= DECODED_LIMIT):
        raise ProbeError('Encoded header range or decoded size exceeds bound')
    return {'start': start, 'length': length, 'folder': folder,
            'packed_crc32': info['pack_crcs'][0]}


def compression_filter(folder):
    props = bytes.fromhex(folder['properties_hex'])
    codec = folder['codec_hex']
    if codec == '030101':
        if len(props) != 5 or props[0] >= 225:
            raise ProbeError('Invalid LZMA properties')
        lc, rem = props[0] % 9, props[0] // 9
        lp, pb = rem % 5, rem // 5
        dictionary = int.from_bytes(props[1:], 'little')
        result = {'id': lzma.FILTER_LZMA1, 'dict_size': dictionary, 'lc': lc, 'lp': lp, 'pb': pb}
    elif codec == '21':
        if len(props) != 1 or props[0] > 40:
            raise ProbeError('Invalid LZMA2 properties')
        dictionary = (0xFFFFFFFF if props[0] == 40 else (2 | (props[0] & 1)) << (props[0] // 2 + 11))
        result = {'id': lzma.FILTER_LZMA2, 'dict_size': dictionary}
    elif codec == '00':
        if props:
            raise ProbeError('Copy codec has unexpected properties')
        return None
    else:
        raise ProbeError('Unsupported compression codec')
    if not 0 < dictionary <= DICT_LIMIT:
        raise ProbeError('Decoder dictionary exceeds bound')
    return result


def decode_header(packed, descriptor):
    folder = descriptor['folder']
    expected = folder['unpacked_size']
    if not 0 < expected <= DECODED_LIMIT or len(packed) != descriptor['length']:
        raise ProbeError('Header decode size exceeds bound or packed length mismatch')
    crc = descriptor['packed_crc32']
    if crc is not None and zlib.crc32(packed) != crc:
        raise ProbeError('Packed-header CRC mismatch')
    filt = compression_filter(folder)
    if filt is None:
        data = packed
    else:
        decoder = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[filt])
        data = decoder.decompress(packed, max_length=expected + 1)
        if len(data) == expected and not decoder.needs_input and not decoder.eof:
            data += decoder.decompress(b'', max_length=1)
        if decoder.unused_data:
            raise ProbeError('Unexpected trailing compressed-header bytes')
    if len(data) != expected:
        raise ProbeError('Decoded header length mismatch')
    if folder['crc32'] is None or zlib.crc32(data) != folder['crc32']:
        raise ProbeError('Decoded-header CRC absent or mismatch')
    return data


def files(reader):
    count = reader.count()
    properties = {}
    while True:
        tag = reader.byte()
        if tag == 0:
            break
        if tag == 25:  # kDummy alignment padding can recur between properties.
            reader.take(reader.count())
            continue
        if tag in properties:
            raise ProbeError('Duplicate FilesInfo property')
        properties[tag] = reader.take(reader.count())
    if 17 not in properties:
        raise ProbeError('Missing filenames')
    names_raw = Reader(properties[17])
    names_raw.expect(0)
    try:
        names = names_raw.take(len(names_raw.data) - 1).decode('utf-16-le').split('\x00')
    except UnicodeDecodeError:
        raise ProbeError('Invalid UTF16 filenames') from None
    if names[-1] != '' or len(names) != count + 1:
        raise ProbeError('Filename count mismatch')
    names.pop()
    if len(set(names)) != len(names):
        raise ProbeError('Duplicate filenames')
    for name in names:
        if (not name or name.startswith(('/', '\\')) or '\\' in name or ':' in name
                or any(p in ('', '.', '..') for p in name.split('/'))
                or any(ord(c) < 32 for c in name)):
            raise ProbeError('Unsafe archive filename')
    empty = [False] * count
    if 14 in properties:
        er = Reader(properties[14])
        empty = bits(er, count)
        er.done()
    return [{'name': n, 'empty_stream': e} for n, e in zip(names, empty)]


def index_header(data, data_end=None):
    reader = Reader(data)
    reader.expect(1)
    reader.expect(4)
    info = streams(reader)
    reader.expect(5)
    entries = files(reader)
    reader.expect(0)
    reader.done()
    streams_flat = [(i, size, crc) for i, f in enumerate(info['folders'])
                    for size, crc in zip(f['substream_sizes'], f['substream_crcs'])]
    nonempty = [e for e in entries if not e['empty_stream']]
    if len(nonempty) != len(streams_flat):
        raise ProbeError('File/substream count mismatch')
    for entry, (folder, size, crc) in zip(nonempty, streams_flat):
        entry.update(folder_index=folder, unpacked_size=size, crc32=crc)
    offset = 32 + info['pack_position']
    for folder, size in zip(info['folders'], info['pack_sizes']):
        if size <= 0 or (data_end is not None and offset + size > data_end):
            raise ProbeError('Image stream range overlaps header or exceeds archive')
        folder['packed_start'] = offset
        folder['packed_size'] = size
        folder['solid'] = folder['substream_count'] > 1
        offset += size
    return {'entries': entries, 'streams': info}


def join_metadata(entries, metadata):
    ids = {row['source_item_id'] for row in metadata}
    result = []
    for entry in entries:
        if entry['empty_stream']:
            continue
        # Exact filename stem only; no fuzzy match or inferred identity.
        stem = PurePosixPath(entry['name']).stem
        matched = stem if stem in ids else None
        result.append({**entry, 'exact_skirt_item_id': matched,
                       'image_acquired': False, 'training_eligible': False})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--packed-header', type=Path, help='Decode an already acquired header stream offline')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    old = json.loads((PROBE / 'report.json').read_text())
    start_data = (PROBE / 'start-header.bin').read_bytes()
    next_data = (PROBE / 'next-header.bin').read_bytes()
    if (hashlib.sha256(start_data).hexdigest() != old['start_header_sha256']
            or hashlib.sha256(next_data).hexdigest() != old['next_header_sha256']):
        raise ProbeError('Historical probe header hash mismatch')
    start = parse_start(start_data, old['archive_size_bytes'])
    parse_next(next_data, start['next_header_crc32'])
    reader = RangeReader(old['publisher_url'], old['archive_size_bytes'])
    report = {'schema_version': 1, 'date_asia_manila': datetime.now(timezone(timedelta(hours=8))).date().isoformat(),
              'publisher_url': old['publisher_url'], 'archive_size_bytes': old['archive_size_bytes'],
              'header_probe_report_sha256': hashlib.sha256((PROBE / 'report.json').read_bytes()).hexdigest(),
              'budget': {'http_body_bytes': 2 * 1024 * 1024, 'requests': 4,
                         'decoded_header_bytes': DECODED_LIMIT, 'dictionary_bytes': DICT_LIMIT},
              'requests': reader.requests, 'original_images_acquired': 0, 'training_admissions': 0}
    try:
        desc = encoded_descriptor(next_data, old['archive_size_bytes'], start['next_header_start'])
        compression_filter(desc['folder'])  # Dictionary safety before network.
        report['encoded_descriptor'] = desc
        if args.packed_header:
            if args.packed_header.stat().st_size != desc['length']:
                raise ProbeError('Saved packed-header file size mismatch')
            packed = args.packed_header.read_bytes()
            report['offline_packed_header_source'] = args.packed_header.as_posix()
        else:
            packed = reader.fetch(desc['start'], desc['start'] + desc['length'] - 1)
        (args.output / 'packed-header.bin').write_bytes(packed)
        data = decode_header(packed, desc)
        (args.output / 'decoded-header.bin').write_bytes(data)
        report['decoded_header_size'] = len(data)
        report['decoded_header_sha256'] = hashlib.sha256(data).hexdigest()
        report['decoded_header_crc32_verified'] = True
        parsed = index_header(data, desc['start'])
        (args.output / 'archive-index.json').write_text(json.dumps(parsed, indent=2) + '\n', encoding='utf-8')
        metadata = [json.loads(line) for line in META.read_text().splitlines()]
        joined = join_metadata(parsed['entries'], metadata)
        (args.output / 'filename-joins.json').write_text(json.dumps(joined, indent=2) + '\n', encoding='utf-8')
        report.update(status='index_verified', archive_entries=len(parsed['entries']),
                      nonempty_entries=len(joined), skirt_filename_matches=sum(r['exact_skirt_item_id'] is not None for r in joined),
                      compression_folders=len(parsed['streams']['folders']),
                      solid_folders=sum(f['solid'] for f in parsed['streams']['folders']))
        matched_entries = [e for e in joined if e['exact_skirt_item_id'] is not None]
        folders = parsed['streams']['folders']
        independent_copy = all(f['codec_hex'] == '00' and not f['solid']
                               and f['packed_size'] == f['unpacked_size'] for f in folders)
        matched_sizes = [folders[e['folder_index']]['packed_size'] for e in matched_entries]
        report['independent_copy_streams'] = independent_copy
        report['matched_skirt_packed_sizes'] = {'min': min(matched_sizes, default=None),
                                               'max': max(matched_sizes, default=None)}
        report['photo_extraction_feasible'] = bool(matched_entries) and independent_copy
        report['conclusion'] = ('Independent Copy streams with exact source-ID filename joins permit separately bounded image ranges; no photo payload requested.'
                                if report['photo_extraction_feasible'] else
                                'Header index verified; selective photo extraction remains unresolved for this layout.')
    except (ProbeError, OSError, lzma.LZMAError, TimeoutError) as exc:
        report['status'] = 'stopped_unsupported_or_failed'
        report['reason'] = str(exc) if isinstance(exc, ProbeError) else type(exc).__name__
        report['photo_extraction_feasible'] = None
    report['body_bytes_read'] = reader.bytes_read
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
