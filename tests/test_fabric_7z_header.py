import lzma
import struct
import unittest
import zlib

from tools.datasets.inspect_fabric_7z_header import (
    Reader, ProbeError, compression_filter, decode_header, encoded_descriptor,
    index_header, join_metadata,
)


def uint(n):
    for extra in range(8):
        if n < 1 << (7 + 7 * extra):
            first = ((0xFF << (8 - extra)) & 0xFF) | (n >> (extra * 8))
            return bytes([first]) + n.to_bytes(8, 'little')[:extra]
    return b'\xff' + n.to_bytes(8, 'little')


def synthetic_index(names=('F0001.jpg', 'F0002.jpg')):
    # One Copy folder with two unpack substreams: a solid block.
    stream = b'\x06\x00\x01\x09\x07\x00\x07\x0b\x01\x00\x01\x01\x00\x0c\x07\x00'
    stream += b'\x08\x0d\x02\x09\x03\x00\x00'
    raw = b'\x00' + ('\x00'.join(names) + '\x00').encode('utf-16-le')
    return b'\x01\x04' + stream + b'\x05\x02\x11' + uint(len(raw)) + raw + b'\x00\x00'


class Fabric7zHeaderTests(unittest.TestCase):
    def test_uint_roundtrip_and_truncation(self):
        for value in (0, 127, 128, 255, 16383, 16384, 8315232282, 2**64 - 1):
            r = Reader(uint(value))
            self.assertEqual(r.uint(), value)
            r.done()
        with self.assertRaises(ProbeError):
            Reader(b'\xff\x01').uint()

    def test_real_saved_descriptor(self):
        from tools.datasets.inspect_fabric_7z_header import PROBE
        result = encoded_descriptor((PROBE / 'next-header.bin').read_bytes(), 8315255946, 8315255906)
        self.assertEqual((result['start'], result['length']), (8315232314, 23592))
        self.assertEqual(result['folder']['unpacked_size'], 97602)

    def test_dict_bound_and_unsupported_codec(self):
        for folder in ({'codec_hex': '030101', 'properties_hex': '5dffffffff'},
                       {'codec_hex': '21', 'properties_hex': '28'},
                       {'codec_hex': 'dead', 'properties_hex': ''}):
            with self.assertRaises(ProbeError):
                compression_filter(folder)

    def test_copy_and_lzma_decode_crc(self):
        raw = b'\x01test header data' * 100
        folder = {'codec_hex': '030101', 'properties_hex': '5d00800100',
                  'unpacked_size': len(raw), 'crc32': zlib.crc32(raw)}
        packed = lzma.compress(raw, format=lzma.FORMAT_RAW, filters=[compression_filter(folder)])
        descriptor = {'folder': folder, 'length': len(packed), 'packed_crc32': zlib.crc32(packed)}
        self.assertEqual(decode_header(packed, descriptor), raw)
        descriptor['folder'] = {**folder, 'crc32': 0}
        with self.assertRaisesRegex(ProbeError, 'CRC'):
            decode_header(packed, descriptor)

    def test_decode_output_bound(self):
        raw = b'x' * 10000
        folder = {'codec_hex': '030101', 'properties_hex': '5d00800100',
                  'unpacked_size': 2, 'crc32': 0}
        packed = lzma.compress(raw, format=lzma.FORMAT_RAW, filters=[compression_filter(folder)])
        with self.assertRaisesRegex(ProbeError, 'length mismatch'):
            decode_header(packed, {'folder': folder, 'length': len(packed), 'packed_crc32': None})

    def test_solid_file_index_and_exact_stem_join(self):
        result = index_header(synthetic_index())
        self.assertEqual([e['unpacked_size'] for e in result['entries']], [3, 4])
        self.assertTrue(result['streams']['folders'][0]['solid'])
        joined = join_metadata(result['entries'], [{'source_item_id': 'F0001'}])
        self.assertEqual([e['exact_skirt_item_id'] for e in joined], ['F0001', None])
        self.assertFalse(any(e['image_acquired'] or e['training_eligible'] for e in joined))

    def test_unsafe_duplicate_and_wrong_name_counts(self):
        for names in (('../F0001.jpg', 'F0002.jpg'), ('F0001.jpg', 'F0001.jpg'), ('F0001.jpg',)):
            with self.assertRaises(ProbeError):
                index_header(synthetic_index(names))

    def test_truncated_or_unsupported_header(self):
        for raw in (synthetic_index()[:-1], b'\x01\x03', b'\x01\x04\x00'):
            with self.assertRaises(ProbeError):
                index_header(raw)

    def test_repeated_dummy_padding_and_image_stream_bounds(self):
        raw = synthetic_index()
        marker = raw.index(b'\x11')
        padded = raw[:marker] + b'\x19\x02\x00\x00' + raw[marker:-2] + b'\x19\x00' + raw[-2:]
        self.assertEqual(len(index_header(padded, 39)['entries']), 2)
        with self.assertRaisesRegex(ProbeError, 'overlaps header'):
            index_header(raw, 38)


if __name__ == '__main__':
    unittest.main()
