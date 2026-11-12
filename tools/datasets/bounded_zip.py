"""Read selected ZIP/ZIP64 members through an exact inclusive-range callback.

No network access or extraction. Directory entries remain in the index for count
verification; read() refuses directories. All returned index values are copies.
"""
from __future__ import annotations

import stat
import struct
import zlib

CAP = 16 * 1024 * 1024


def _extra(raw):
    result = {}
    pos = 0
    while pos < len(raw):
        if pos + 4 > len(raw):
            raise ValueError('Truncated extra field')
        tag, length = struct.unpack_from('<HH', raw, pos)
        pos += 4
        if pos + length > len(raw) or tag in result:
            raise ValueError('Truncated or duplicate extra field')
        result[tag] = raw[pos:pos + length]
        pos += length
    return result


def _zip64(extra, values):
    data = extra.get(1, b'')
    pos = 0
    result = []
    for value, sentinel, width in values:
        if value == sentinel:
            if pos + width > len(data):
                raise ValueError('Missing ZIP64 extra value')
            value = int.from_bytes(data[pos:pos + width], 'little')
            pos += width
        result.append(value)
    return result


def _name(raw, flags):
    try:
        name = raw.decode('utf-8' if flags & 0x800 else 'cp437')
    except UnicodeDecodeError as exc:
        raise ValueError('Invalid ZIP name') from exc
    parts = name.rstrip('/').split('/')
    if (not name or name.startswith('/') or '\\' in name or ':' in name
            or any(p in ('', '.', '..') for p in parts)
            or any(ord(c) < 32 or ord(c) == 127 for c in name)):
        raise ValueError('Unsafe ZIP name')
    return name


class BoundedZip:
    def __init__(self, fetch, archive_size):
        if type(archive_size) is not int or archive_size < 22:
            raise ValueError('Invalid archive size')
        self.fetch = fetch
        self.archive_size = archive_size
        self._entries = None
        self.central_offset = None
        self.central_size = None

    def _get(self, start, length):
        if (start < 0 or length < 0 or length > CAP
                or start + length > self.archive_size):
            raise ValueError('Range out of bounds')
        if length == 0:
            return b''
        data = self.fetch(start, start + length - 1)
        if not isinstance(data, bytes) or len(data) != length:
            raise ValueError('Range callback did not return exact bytes')
        return data

    def index(self):
        if self._entries is not None:
            return {key: dict(value) for key, value in self._entries.items()}
        start = max(0, self.archive_size - 65557)
        tail = self._get(start, self.archive_size - start)
        pos = len(tail)
        while True:
            pos = tail.rfind(b'PK\x05\x06', 0, pos)
            if pos < 0:
                raise ValueError('Missing ZIP end record')
            if pos + 22 <= len(tail):
                end = struct.unpack_from('<4s4H2LH', tail, pos)
                if pos + 22 + end[-1] == len(tail):
                    break
        _, disk, cd_disk, disk_count, count, size, offset, _ = end
        if disk or cd_disk or disk_count != count:
            raise ValueError('Multidisk ZIP not supported')
        boundary = start + pos
        locator = self._get(boundary - 20, 20) if boundary >= 20 else b''
        is64 = locator.startswith(b'PK\x06\x07')
        if is64:
            _, zip_disk, record_offset, disks = struct.unpack('<4sLQL', locator)
            if zip_disk or disks != 1:
                raise ValueError('Multidisk ZIP64 not supported')
            header = self._get(record_offset, 56)
            fields = struct.unpack('<4sQ2H2L4Q', header)
            if (fields[0] != b'PK\x06\x06' or fields[1] < 44
                    or record_offset + 12 + fields[1] != boundary - 20):
                raise ValueError('Invalid ZIP64 end bounds')
            if fields[4] or fields[5] or fields[6] != fields[7]:
                raise ValueError('Multidisk ZIP64 not supported')
            new_count, new_size, new_offset = fields[7:10]
            for old, new, sentinel in ((count, new_count, 65535),
                                       (size, new_size, 0xffffffff),
                                       (offset, new_offset, 0xffffffff)):
                if old != sentinel and old != new:
                    raise ValueError('Inconsistent ZIP64 end record')
            count, size, offset = new_count, new_size, new_offset
            boundary = record_offset
        elif count == 65535 or size == 0xffffffff or offset == 0xffffffff:
            raise ValueError('Missing ZIP64 locator')
        if size > CAP or offset + size != boundary or count > size // 46:
            raise ValueError('Invalid central directory bounds/count')
        central = self._get(offset, size)
        entries = {}
        p = 0
        while p < size:
            if p + 46 > size:
                raise ValueError('Truncated central header')
            f = struct.unpack_from('<4s6H3L5H2L', central, p)
            if f[0] != b'PK\x01\x02':
                raise ValueError('Invalid central header')
            n, e, c = f[10:13]
            stop = p + 46 + n + e + c
            if stop > size:
                raise ValueError('Truncated central variable fields')
            flags, method = f[3:5]
            if flags & ~0x80e or method not in (0, 8):
                raise ValueError('Unsupported/encrypted ZIP member')
            raw_name = central[p + 46:p + 46 + n]
            name = _name(raw_name, flags)
            if name in entries:
                raise ValueError('Duplicate ZIP member')
            if stat.S_ISLNK(f[15] >> 16):
                raise ValueError('ZIP symlink refused')
            extras = _extra(central[p + 46 + n:p + 46 + n + e])
            usize, csize, local, member_disk = _zip64(extras, [
                (f[9], 0xffffffff, 8), (f[8], 0xffffffff, 8),
                (f[16], 0xffffffff, 8), (f[13], 65535, 4)])
            if member_disk or local + 30 + csize > offset:
                raise ValueError('Invalid member disk/bounds')
            entries[name] = dict(offset=local, compressed=csize, size=usize,
                                 crc=f[7], compression=method, flags=flags,
                                 raw_name=raw_name, directory=name.endswith('/'))
            p = stop
        if len(entries) != count:
            raise ValueError('Central directory count mismatch')
        self.central_offset, self.central_size = offset, size
        self._entries = entries
        return {key: dict(value) for key, value in entries.items()}

    def read(self, member):
        if self._entries is None:
            self.index()
        entry = self._entries[member]
        if entry['directory']:
            raise ValueError('Cannot read a directory')
        if entry['size'] > CAP or entry['compressed'] > CAP:
            raise ValueError('Member exceeds size cap')
        offset = entry['offset']
        f = struct.unpack('<4s5H3L2H', self._get(offset, 30))
        if (f[0] != b'PK\x03\x04' or f[2] != entry['flags']
                or f[3] != entry['compression']):
            raise ValueError('Inconsistent local header')
        n, e = f[9:11]
        payload = offset + 30 + n + e
        if payload + entry['compressed'] > self.central_offset:
            raise ValueError('Local member overlaps directory')
        variable = self._get(offset + 30, n + e)
        if variable[:n] != entry['raw_name']:
            raise ValueError('Inconsistent local name')
        extras = _extra(variable[n:])
        usize, csize = _zip64(extras, [(f[8], 0xffffffff, 8), (f[7], 0xffffffff, 8)])
        if not f[2] & 8 and (f[6] != entry['crc'] or usize != entry['size'] or csize != entry['compressed']):
            raise ValueError('Inconsistent local sizes/CRC')
        compressed = self._get(payload, entry['compressed'])
        if entry['compression'] == 0:
            result = compressed
        else:
            decoder = zlib.decompressobj(-15)
            try:
                result = decoder.decompress(compressed, entry['size'] + 1)
            except zlib.error as exc:
                raise ValueError('Invalid deflate stream') from exc
            if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
                raise ValueError('Incomplete/oversized deflate stream')
        if len(result) != entry['size'] or zlib.crc32(result) & 0xffffffff != entry['crc']:
            raise ValueError('Member size/CRC mismatch')
        return result
