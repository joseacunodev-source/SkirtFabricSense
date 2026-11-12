import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from tools.datasets.probe_fabric_archive import (
    HEADER_LIMIT, ProbeError, RangeReader, SIGNATURE, choose_archive,
    parse_next, parse_start, probe,
)


def start_header(offset=68, payload=b'\x17hello'):
    tail = struct.pack('<QQI', offset, len(payload), zlib.crc32(payload))
    return SIGNATURE + b'\x00\x04' + struct.pack('<I', zlib.crc32(tail)) + tail


class Response(io.BytesIO):
    def __init__(self, body, status=206, content_range='bytes 0-31/1000', **headers):
        super().__init__(body)
        self.status = status
        self.headers = {'Content-Range': content_range, **headers}
        self.read_calls = 0

    def read(self, size=-1):
        self.read_calls += 1
        if size < 0:
            raise AssertionError('Unbounded read')
        return super().read(size)


class Opener:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def open(self, req, timeout):
        self.calls.append((req.get_header('Range'), timeout))
        return next(self.responses)


class FabricArchiveProbeTests(unittest.TestCase):
    def test_ignored_range_rejected_without_body_read(self):
        response = Response(b'full archive must not be consumed', status=200)
        reader = RangeReader('https://zenodo.org/public', 1000, Opener([response]))
        with self.assertRaisesRegex(ProbeError, 'did not honor'):
            reader.fetch(0, 31)
        self.assertEqual(response.read_calls, 0)
        self.assertEqual(reader.bytes_read, 0)

    def test_malformed_content_range_rejected_before_read(self):
        response = Response(b'x' * 32, content_range='bytes 0-31/*')
        with self.assertRaisesRegex(ProbeError, 'Content-Range'):
            RangeReader('https://zenodo.org/public', 1000, Opener([response])).fetch(0, 31)
        self.assertEqual(response.read_calls, 0)

    def test_valid_start_and_encoded_next_crc(self):
        payload = b'\x17hello'
        parsed = parse_start(start_header(payload=payload), 1000)
        self.assertEqual(parsed['next_header_start'], 100)
        self.assertTrue(parse_next(payload, parsed['next_header_crc32'])['encoded_header'])

    def test_bad_signature_and_start_crc(self):
        good = start_header()
        for bad in (b'x' + good[1:], good[:12] + b'x' + good[13:]):
            with self.assertRaises(ProbeError):
                parse_start(bad, 1000)

    def test_bad_next_crc(self):
        with self.assertRaisesRegex(ProbeError, 'CRC'):
            parse_next(b'\x17hello', 0)

    def test_next_header_oversize_and_invalid_offset(self):
        tail = struct.pack('<QQI', 10, HEADER_LIMIT + 1, 0)
        header = SIGNATURE + b'\x00\x04' + struct.pack('<I', zlib.crc32(tail)) + tail
        with self.assertRaisesRegex(ProbeError, 'size exceeds'):
            parse_start(header, 10_000_000)
        with self.assertRaisesRegex(ProbeError, 'outside'):
            parse_start(start_header(offset=999), 1000)

    def test_budget_and_short_or_overlong_bodies(self):
        for body in (b'x' * 31, b'x' * 33):
            reader = RangeReader('https://zenodo.org/public', 1000, Opener([Response(body)]))
            with self.assertRaisesRegex(ProbeError, 'length mismatch'):
                reader.fetch(0, 31)
            self.assertEqual(reader.bytes_read, len(body))
        reader = RangeReader('https://zenodo.org/public', 1000, Opener([]))
        reader.requests = [{}, {}, {}]
        with self.assertRaisesRegex(ProbeError, 'budget'):
            reader.fetch(0, 31)

    def test_complete_probe_and_archive_selection(self):
        record = {'files': [
            {'key': 'NPCGI_Axxxx.7z', 'size': 2000, 'links': {'self': 'https://zenodo.org/a'}},
            {'key': 'NPCGI_Fxxxx.7z', 'size': 1000, 'links': {'self': 'https://zenodo.org/f'}}]}
        self.assertEqual(choose_archive(record)['key'], 'NPCGI_Fxxxx.7z')
        payload = b'\x17hello'
        opener = Opener([Response(start_header(payload=payload)),
                         Response(payload, content_range='bytes 100-105/1000')])
        with tempfile.TemporaryDirectory() as tmp:
            report = probe(record, Path(tmp) / 'fresh', opener)
            self.assertEqual(report['status'], 'header_probe_verified')
            self.assertEqual(report['body_bytes_read'], 38)
            self.assertEqual(report['original_images_downloaded'], 0)
            self.assertEqual(report['selective_extraction'], 'unresolved')
            self.assertEqual(len(opener.calls), 2)
            self.assertEqual(json.loads((Path(tmp) / 'fresh/report.json').read_text())['status'], report['status'])


if __name__ == '__main__':
    unittest.main()
