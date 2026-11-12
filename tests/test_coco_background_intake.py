import io
from contextlib import redirect_stdout
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from tools.datasets import acquire_coco_backgrounds as intake
from tools.datasets.bounded_zip import BoundedZip


def make_zip(body=b'{"train": true}', extra=False):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(intake.MEMBER, body)
        if extra:
            z.writestr('annotations/captions_val2017.json', b'PROTECTED')
    return stream.getvalue()


def payload(captions=('An empty kitchen with a sink.', 'A kitchen with cabinets.')):
    return {'licenses': [{'id': k, 'url': v} for k, v in intake.LICENSES.items()],
            'images': [{'id': 1, 'file_name': '000000000001.jpg', 'coco_url': 'http://images.cocodataset.org/train2017/000000000001.jpg',
                        'license': 4, 'flickr_url': 'http://farm1.staticflickr.com/1/123_abc.jpg'}],
            'annotations': [{'id': i, 'image_id': 1, 'caption': caption} for i, caption in enumerate(captions)]}


class Response:
    def __init__(self, body, status=200, headers=None):
        self.status, self.headers, self.url = status, headers or {}, 'https://example.test/data'
        self.stream = io.BytesIO(body)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self, count):
        return self.stream.read(count)


class Opener:
    def __init__(self, response):
        self.response = response
    def open(self, request, timeout):
        return self.response


class CocoBackgroundIntakeTests(unittest.TestCase):
    def test_reads_only_train_payload_not_protected_member(self):
        body = b'{"train": true}'
        data = make_zip(body, True)
        calls = []
        def get(start, end):
            calls.append((start, end))
            return data[start:end + 1]
        reader = BoundedZip(get, len(data))
        reader.index()
        calls.clear()
        result, _ = intake.read_train_captions(reader)
        self.assertEqual(result, body)
        protected = reader.index()['annotations/captions_val2017.json']
        protected_start = protected['offset']
        protected_end = protected_start + 30 + len(protected['raw_name']) + protected['compressed'] - 1
        self.assertFalse(any(start <= protected_end and end >= protected_start for start, end in calls))

    def test_inflated_cap_before_payload_read(self):
        data = make_zip(b'x' * 100)
        with patch.object(intake, 'INFLATED_CAP', 20), self.assertRaisesRegex(ValueError, 'bounds'):
            intake.read_train_captions(BoundedZip(lambda s, e: data[s:e + 1], len(data)))

    def test_crc_corruption_rejected(self):
        data = bytearray(make_zip())
        central = data.index(b'PK\x01\x02')
        struct.pack_into('<L', data, central + 16, 1234)
        with self.assertRaises(ValueError):
            intake.read_train_captions(BoundedZip(lambda s, e: bytes(data[s:e + 1]), len(data)))

    def test_triage_is_deterministic_and_not_truth(self):
        first = intake.select_candidates(payload())
        self.assertEqual(first, intake.select_candidates(payload()))
        self.assertEqual(len(first), 1)
        self.assertTrue(first[0]['candidate_only_not_absence_truth'])
        self.assertEqual(first[0]['condition'], 'furniture_or_room')

    def test_person_or_clothing_in_any_caption_excludes(self):
        for caption in ('A man in a kitchen.', 'An empty room containing skirts.', 'A person behind a couch.'):
            with self.subTest(caption=caption):
                self.assertEqual(intake.select_candidates(payload(('An empty kitchen.', 'A kitchen with cabinets.', caption))), [])

    def test_single_relevant_caption_not_enough(self):
        self.assertEqual(intake.select_candidates(payload(('A kitchen.', 'A beautiful picture.'))), [])

    def test_protected_partition_rejected(self):
        data = payload()
        data['images'][0]['coco_url'] = 'http://images.cocodataset.org/val2017/000000000001.jpg'
        with self.assertRaisesRegex(ValueError, 'train2017'):
            intake.select_candidates(data)

    def test_missing_or_nonpermissive_licence_not_selected(self):
        data = payload()
        data['images'][0]['license'] = 1
        self.assertEqual(intake.select_candidates(data), [])
        data['licenses'][0]['url'] = 'https://example.test/other'
        with self.assertRaisesRegex(ValueError, 'mapping'):
            intake.select_candidates(data)

    def test_exact_photo_creator_and_current_license_required(self):
        image = payload()['images'][0]
        good = dict(web_page='https://www.flickr.com/photos/creator/123/', author_url='https://www.flickr.com/photos/creator/',
                    author_name='Creator', title='Kitchen', license_url=intake.LICENSES[4])
        self.assertEqual(intake.attribution(image, good)['flickr_photo_id'], '123')
        for key, value in [('license_url', intake.LICENSES[5]), ('author_name', ''), ('web_page', 'https://www.flickr.com/photos/creator/999/')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                intake.attribution(image, {**good, key: value})
        with self.assertRaisesRegex(ValueError, 'accounts differ'):
            intake.attribution(image, {**good, 'author_url': 'https://www.flickr.com/photos/unrelated-creator/'})

    def test_ignored_range_never_reads_body(self):
        response = Response(b'ARCHIVE-BODY', 200)
        with tempfile.TemporaryDirectory() as tmp:
            fetcher = intake.BudgetFetcher(tmp, opener=Opener(response))
            with self.assertRaisesRegex(ValueError, 'full fallback refused'):
                fetcher.get('https://example.test/file.zip', 1, (0, 0))
            self.assertEqual(response.stream.tell(), 0)
            self.assertEqual(fetcher.used, 0)
            self.assertEqual(fetcher.requests[0]['outcome'], 'failed')

    def test_failed_body_counts_and_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            fetcher = intake.BudgetFetcher(tmp, opener=Opener(Response(b'not found', 404)))
            with self.assertRaisesRegex(ValueError, 'HTTP 404'):
                fetcher.get('https://example.test/missing', 20)
            self.assertEqual(fetcher.used, 9)
            self.assertEqual((Path(tmp) / 'response-01.bin').read_bytes(), b'not found')

    def test_budget_and_overflow_record_actual_consumed_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            fetcher = intake.BudgetFetcher(tmp, total_cap=4, request_cap=1, opener=Opener(Response(b'abcdef')))
            with self.assertRaises(ValueError):
                fetcher.get('https://example.test/file', 10)
            self.assertEqual(fetcher.used, 4)
            with self.assertRaisesRegex(ValueError, 'budget exhausted'):
                fetcher.get('https://example.test/file', 10)
            self.assertEqual(len(fetcher.requests), 1)
        with tempfile.TemporaryDirectory() as tmp:
            fetcher = intake.BudgetFetcher(tmp, opener=Opener(Response(b'abcdef')))
            with self.assertRaisesRegex(ValueError, 'per-response cap'):
                fetcher.get('https://example.test/file', 2)
            self.assertEqual(fetcher.used, 3)

    def test_exact_range_length_and_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            response = Response(b'ab', 206, {'Content-Range': 'bytes 1-2/99'})
            fetcher = intake.BudgetFetcher(tmp, opener=Opener(response))
            body, event = fetcher.get('https://example.test/file', 2, (1, 2))
            self.assertEqual(body, b'ab')
            self.assertEqual(event['archive_size_bytes'], 99)

    def test_failed_intake_reports_failure_and_returns_nonzero_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'tools/datasets/acquire_coco_backgrounds.py'
            source.parent.mkdir(parents=True)
            source.write_bytes(Path(intake.__file__).read_bytes())
            (source.parent / 'bounded_zip.py').write_bytes(b'synthetic parser identity only')
            record = root / 'records/acquisition'
            with patch.multiple(intake, ROOT=root, RECORD=record,
                                PHOTOS=root / 'data/photos',
                                MANIFEST=root / 'data/manifests/candidates.jsonl',
                                SOURCES=[], __file__=str(source)), \
                    patch.object(sys, 'argv', ['synthetic-intake']), \
                    patch.object(intake.BudgetFetcher, 'get', side_effect=ValueError('synthetic range failure')), \
                    redirect_stdout(io.StringIO()):
                exit_code = intake.main()
            result = json.loads((record / 'acquisition.json').read_text(encoding='utf-8'))
            self.assertEqual(exit_code, 1)
            self.assertEqual(result['status'], 'bounded_failure')
            self.assertEqual(result['images_acquired'], 0)
            self.assertEqual(result['total_consumed_network_body_bytes'], 0)
            self.assertTrue((record / 'executed_acquire_coco_backgrounds.py').is_file())


if __name__ == '__main__':
    unittest.main()
