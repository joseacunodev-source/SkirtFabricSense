"""Verify remote archive extraction against local ZIP fixtures without network."""
import io
import unittest
import zipfile
from unittest.mock import patch

from tools.datasets import acquire_skirts as skirts
from tools.datasets import acquire_fabrics as fabrics


class ArchiveIntakeTests(unittest.TestCase):
    def fixture(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('train/example.jpg', b'fixture image content' * 20)
            archive.writestr('padding', bytes(8192))
        body = buffer.getvalue() + bytes(8192)
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
            item = archive.getinfo('train/example.jpg')
        return body, item

    def test_skirt_range_extract_and_crc_rejection(self):
        body, item = self.fixture()
        entry = {'offset': item.header_offset, 'compressed': item.compress_size,
                 'size': item.file_size, 'crc': item.CRC, 'compression': item.compress_type}
        with patch.object(skirts, 'request', side_effect=lambda url, start, end, **kw: body[start:end+1]):
            self.assertEqual(skirts.extract(item.filename, entry), b'fixture image content' * 20)
            entry['crc'] ^= 1
            with self.assertRaisesRegex(ValueError, 'CRC'):
                skirts.extract(item.filename, entry)

    def test_fabric_range_extract_and_identity_rejection(self):
        body, item = self.fixture()
        entry = {'path': item.filename, 'offset': item.header_offset, 'compressed_bytes': item.compress_size,
                 'bytes': item.file_size, 'crc32': item.CRC, 'compression': item.compress_type}
        with patch.object(fabrics, 'remote_range', side_effect=lambda start, end: body[start:end+1]):
            self.assertEqual(fabrics.extract(entry), b'fixture image content' * 20)
            entry['path'] = 'other.jpg'
            with self.assertRaisesRegex(ValueError, 'identity'):
                fabrics.extract(entry)

    def test_oversized_member_rejected_before_network(self):
        with patch.object(fabrics, 'remote_range', side_effect=AssertionError('Network forbidden')):
            with self.assertRaisesRegex(ValueError, 'bound'):
                fabrics.extract({'bytes': 17 * 1024 * 1024, 'compressed_bytes': 1})


if __name__ == '__main__':
    unittest.main()
