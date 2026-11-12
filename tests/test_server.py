"""HTTP boundary tests: all inputs and review changes are synthetic/in memory."""
import base64
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest

from PIL import Image
from app.server import make_handler


class FakePredictor:
    def __init__(self):
        self.calls = []

    def predict(self, image, roi, full_skirt_confirmed):
        self.calls.append((image.size, image.mode, roi, full_skirt_confirmed))
        return {'style': {'status': 'provisional' if full_skirt_confirmed else 'unavailable'},
                'fabric': {'status': 'unavailable'}, 'length': {'status': 'unavailable'}}


class FakeReviewStore:
    def __init__(self):
        self.saved = []

    def queue(self):
        return {'items': [{'sample_id': 'synthetic'}]}

    def save(self, payload):
        self.saved.append(payload)
        return {'saved': True}

    def image_path(self, sample_id):
        raise ValueError('No real review images in this test')


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.predictor = FakePredictor()
        self.review = FakeReviewStore()
        self.start_server(self.review)

    def start_server(self, review):
        handler = make_handler(self.root, self.predictor, review)
        handler.log_message = lambda *args: None
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def tearDown(self):
        self.stop_server()

    def request(self, method, path, payload=None, headers=None, raw=None):
        connection = HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        self.addCleanup(connection.close)
        body = raw if raw is not None else json.dumps(payload).encode() if payload is not None else None
        connection.request(method, path, body=body,
                           headers=headers if headers is not None else {'Content-Type': 'application/json'})
        response = connection.getresponse()
        content = response.read()
        return response.status, json.loads(content), dict(response.getheaders())

    def image_payload(self, orientation=None):
        image = Image.new('RGB', (30, 10), (255, 0, 0))
        stream = io.BytesIO()
        if orientation:
            exif = Image.Exif()
            exif[274] = orientation
            image.save(stream, format='JPEG', exif=exif)
        else:
            image.save(stream, format='PNG')
        return {'image_base64': base64.b64encode(stream.getvalue()).decode(), 'full_skirt_confirmed': False}

    def test_status_has_no_camera_claim(self):
        status, body, headers = self.request('GET', '/api/status')
        self.assertEqual(status, 200)
        self.assertFalse(body['camera_enabled'])
        self.assertEqual(headers['Cache-Control'], 'no-store')

    def test_unconfirmed_flag_preserved(self):
        status, body, _ = self.request('POST', '/api/analyze', self.image_payload())
        self.assertEqual(status, 200)
        self.assertEqual(body['style']['status'], 'unavailable')
        self.assertEqual(self.predictor.calls, [((30, 10), 'RGB', None, False)])

    def test_confirmed_roi_preserved(self):
        payload = self.image_payload()
        payload.update(roi=[1, 2, 20, 9], full_skirt_confirmed=True)
        status, _, _ = self.request('POST', '/api/analyze', payload)
        self.assertEqual(status, 200)
        self.assertEqual(self.predictor.calls[0], ((30, 10), 'RGB', (1, 2, 20, 9), True))

    def test_exif_orientation_applied_before_inference(self):
        status, _, _ = self.request('POST', '/api/analyze', self.image_payload(6))
        self.assertEqual(status, 200)
        self.assertEqual(self.predictor.calls[0][0], (10, 30))

    def test_invalid_boolean_roi_and_image_rejected(self):
        for key, value in [('full_skirt_confirmed', 'false'), ('full_skirt_confirmed', 1),
                           ('roi', [True, 0, 20, 9]), ('roi', [0, 0, 20.5, 9]),
                           ('roi', [0, 0]), ('image_base64', 'not base64!')]:
            payload = self.image_payload()
            payload[key] = value
            with self.subTest(key=key, value=value):
                status, _, _ = self.request('POST', '/api/analyze', payload)
                self.assertEqual(status, 400)
        self.assertEqual(self.predictor.calls, [])

    def test_json_object_required(self):
        status, _, _ = self.request('POST', '/api/analyze', ['not', 'object'])
        self.assertEqual(status, 400)

    def test_cross_origin_refused_before_inference_or_review_write(self):
        for endpoint in ['/api/analyze', '/api/review']:
            status, _, _ = self.request('POST', endpoint, self.image_payload(),
                                        {'Content-Type': 'application/json', 'Origin': 'https://untrusted.example'})
            self.assertEqual(status, 403)
        self.assertEqual(self.predictor.calls, [])
        self.assertEqual(self.review.saved, [])

    def test_same_origin_allowed(self):
        status, _, _ = self.request('POST', '/api/analyze', self.image_payload(),
                                    {'Content-Type': 'application/json',
                                     'Origin': f'http://127.0.0.1:{self.server.server_port}'})
        self.assertEqual(status, 200)

    def test_non_json_content_type_rejected(self):
        status, _, _ = self.request('POST', '/api/analyze', self.image_payload(), {'Content-Type': 'text/plain'})
        self.assertEqual(status, 415)

    def test_review_fake_only(self):
        status, body, _ = self.request('GET', '/api/review')
        self.assertEqual((status, body), (200, {'items': [{'sample_id': 'synthetic'}]}))
        status, _, _ = self.request('POST', '/api/review', {'synthetic': True})
        self.assertEqual(status, 200)
        self.assertEqual(self.review.saved, [{'synthetic': True}])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_missing_review_returns_503(self):
        self.stop_server()
        self.start_server(None)
        for method, path, payload in [('GET', '/api/review', None),
                                       ('GET', '/api/review/image?id=synthetic', None),
                                       ('POST', '/api/review', {'synthetic': True})]:
            with self.subTest(method=method, path=path):
                status, body, _ = self.request(method, path, payload)
                self.assertEqual(status, 503)
                self.assertIn('error', body)


if __name__ == '__main__':
    unittest.main()
