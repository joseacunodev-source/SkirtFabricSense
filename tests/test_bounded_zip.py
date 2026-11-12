import io
import stat
import struct
import unittest
import zipfile
import zlib

from tools.datasets.bounded_zip import BoundedZip, CAP


def archive(name='images/skirt.jpg', body=b'abc' * 100, method=8):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=method) as target:
        target.writestr(name, body)
    return stream.getvalue()


def reader(data):
    return BoundedZip(lambda start, end: data[start:end + 1], len(data))


def patch(data, offset, fmt, value):
    result = bytearray(data)
    struct.pack_into(fmt, result, offset, value)
    return bytes(result)


def zip64(body=b'zip64 member'):
    name = b'skirt.jpg'
    crc = zlib.crc32(body)
    extra = struct.pack('<HHQQ', 1, 16, len(body), len(body))
    local = struct.pack('<4s5H3L2H', b'PK\x03\x04', 45, 0, 0, 0, 0,
                        crc, 0xffffffff, 0xffffffff, len(name), len(extra)) + name + extra + body
    cextra = struct.pack('<HHQQQ', 1, 24, len(body), len(body), 0)
    central = struct.pack('<4s6H3L5H2L', b'PK\x01\x02', 45, 45, 0, 0, 0, 0,
                          crc, 0xffffffff, 0xffffffff, len(name), len(cextra), 0, 0, 0, 0, 0xffffffff) + name + cextra
    end64 = struct.pack('<4sQ2H2L4Q', b'PK\x06\x06', 44, 45, 45, 0, 0, 1, 1, len(central), len(local))
    locator = struct.pack('<4sLQL', b'PK\x06\x07', 0, len(local) + len(central), 1)
    end = struct.pack('<4s4H2LH', b'PK\x05\x06', 0, 0, 65535, 65535, 0xffffffff, 0xffffffff, 0)
    return local + central + end64 + locator + end


class BoundedZipTests(unittest.TestCase):
    def test_stored_and_deflated(self):
        for method in (0, 8):
            self.assertEqual(reader(archive(method=method)).read('images/skirt.jpg'), b'abc' * 100)

    def test_zip64(self):
        self.assertEqual(reader(zip64()).read('skirt.jpg'), b'zip64 member')

    def test_empty_and_directory(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w'):
            pass
        self.assertEqual(reader(stream.getvalue()).index(), {})
        r = reader(archive('images/', b''))
        self.assertTrue(r.index()['images/']['directory'])
        with self.assertRaises(ValueError):
            r.read('images/')

    def test_unsafe_names(self):
        for name in ('../a', '/a', 'a/../b', 'C:/a', 'a//b'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                reader(archive(name)).index()

    def test_backslash_name(self):
        data = archive('a/b').replace(b'a/b', b'a\\b')
        with self.assertRaises(ValueError):
            reader(data).index()

    def test_symlink(self):
        data = archive()
        cd = data.index(b'PK\x01\x02')
        with self.assertRaises(ValueError):
            reader(patch(data, cd + 38, '<L', (stat.S_IFLNK | 0o777) << 16)).index()

    def test_duplicates(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as target:
            target.writestr('a', b'a')
            target.writestr('a', b'b')
        with self.assertRaises(ValueError):
            reader(stream.getvalue()).index()

    def test_exact_callback(self):
        data = archive()
        with self.assertRaises(ValueError):
            BoundedZip(lambda s, e: data[s:e], len(data)).index()

    def test_multidisk(self):
        data = archive()
        with self.assertRaises(ValueError):
            reader(patch(data, len(data) - 18, '<H', 1)).index()

    def test_count_and_directory_bounds(self):
        data = archive()
        for rel, fmt, value in ((-12, '<H', 2), (-10, '<L', CAP + 1), (-6, '<L', len(data))):
            with self.subTest(rel=rel), self.assertRaises(ValueError):
                reader(patch(data, len(data) + rel, fmt, value)).index()

    def test_local_header_mismatches(self):
        data = archive()
        for offset, fmt, value in ((6, '<H', 1), (8, '<H', 0), (14, '<L', 0), (30, '<B', 120)):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                reader(patch(data, offset, fmt, value)).read('images/skirt.jpg')

    def test_crc_failure(self):
        data = archive(method=0)
        with self.assertRaises(ValueError):
            reader(patch(data, 30 + len('images/skirt.jpg'), '<B', 120)).read('images/skirt.jpg')

    def test_member_caps_and_bomb(self):
        data = archive(body=b'a' * 100000)
        cd = data.index(b'PK\x01\x02')
        for declared in (CAP + 1, 1):
            corrupted = patch(patch(data, cd + 24, '<L', declared), 22, '<L', declared)
            with self.subTest(declared=declared), self.assertRaises(ValueError):
                reader(corrupted).read('images/skirt.jpg')

    def test_zip64_malformed(self):
        data = zip64()
        for offset, fmt, value in ((len(data) - 38, '<L', 1), (len(data) - 34, '<Q', len(data)), (len(data) - 94, '<Q', 1)):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                reader(patch(data, offset, fmt, value)).index()

    def test_sparse_zip64_above_four_gib(self):
        data = zip64()
        cd = data.index(b'PK\x01\x02')
        new_cd = 5 * 1024 ** 3
        suffix = data[cd:]
        suffix = patch(suffix, len(suffix) - 50, '<Q', new_cd)
        suffix = patch(suffix, len(suffix) - 34, '<Q', new_cd + len(suffix) - 98)
        total = new_cd + len(suffix)
        requests = []

        def fetch(start, end):
            requests.append((start, end))
            result = bytearray(end - start + 1)
            for segment_start, segment in ((0, data[:cd]), (new_cd, suffix)):
                left, right = max(start, segment_start), min(end + 1, segment_start + len(segment))
                if left < right:
                    result[left - start:right - start] = segment[left - segment_start:right - segment_start]
            return bytes(result)

        r = BoundedZip(fetch, total)
        self.assertEqual(r.read('skirt.jpg'), b'zip64 member')
        self.assertEqual(r.central_offset, new_cd)
        self.assertTrue(all(end - start + 1 <= 65557 for start, end in requests))

    def test_streamed_data_descriptor(self):
        class Unseekable(io.BytesIO):
            def seek(self, *args):
                raise OSError('stream')
        stream = Unseekable()
        with zipfile.ZipFile(stream, 'w', compression=8) as target:
            target.writestr('skirt.jpg', b'descriptor')
        self.assertEqual(reader(stream.getvalue()).read('skirt.jpg'), b'descriptor')

    def test_missing_zip64_extra(self):
        data = zip64()
        cd = data.index(b'PK\x01\x02')
        with self.assertRaises(ValueError):
            reader(patch(data, cd + 46 + len('skirt.jpg'), '<H', 2)).index()

    def test_comment_with_signature(self):
        data = archive()
        comment = b'PK\x05\x06malformed fake end'
        data = patch(data, len(data) - 2, '<H', len(comment)) + comment
        self.assertEqual(reader(data).read('images/skirt.jpg'), b'abc' * 100)

    def test_encryption_and_compression(self):
        data = archive()
        cd = data.index(b'PK\x01\x02')
        for offset, value in ((cd + 8, 1), (cd + 10, 99)):
            with self.assertRaises(ValueError):
                reader(patch(data, offset, '<H', value)).index()

    def test_index_copy(self):
        r = reader(archive())
        r.index()['images/skirt.jpg']['size'] = 99
        self.assertEqual(len(r.read('images/skirt.jpg')), 300)


if __name__ == '__main__':
    unittest.main()
