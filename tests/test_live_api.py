"""Live HTTP contract with synthetic images and a real bounded worker."""
from http.server import ThreadingHTTPServer
from email.message import Message
import threading
from unittest.mock import Mock, patch

from tests import test_server as fixtures
from app.localization import AutomaticPredictor
from app.pipeline import ImagePipeline
from app.server import MAX_BODY, make_handler


class LiveApiTests(fixtures.ServerTests):
    def start_server(self, review):
        self.pipeline = ImagePipeline(AutomaticPredictor(self.predictor), max_frame_age=30, max_result_age=30)
        handler = make_handler(self.root, self.predictor, review, self.pipeline)
        handler.log_message = lambda *args: None
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()

    def stop_server(self):
        self.assertTrue(self.pipeline.close(2))
        super().stop_server()

    def live_payload(self, **options):
        payload = self.image_payload()
        del payload['full_skirt_confirmed']
        return {**payload, 'fabric_enabled': True, 'presentation': 'worn', **options}

    def test_live_without_manual_confirmation_completes_with_unavailable_outputs(self):
        for presentation in ('worn', 'hanging', 'mannequin', 'held'):
            status, job, _ = self.request('POST', '/api/live', self.live_payload(presentation=presentation))
            self.assertEqual(status, 202)
            self.assertTrue(self.pipeline.wait_idle(2))
            status, body, _ = self.request('GET', '/api/jobs?id=' + job['id'])
            self.assertEqual(status, 200)
            self.assertEqual(body['state'], 'complete')
            self.assertEqual(body['result']['style']['status'], 'unavailable')
            self.assertEqual(body['result']['metadata']['presentation'], presentation)
        self.assertEqual(self.predictor.calls, [])

    def test_fabric_disabled_survives_http_and_worker(self):
        _, job, _ = self.request('POST', '/api/live', self.live_payload(fabric_enabled=False))
        self.assertTrue(self.pipeline.wait_idle(2))
        body = self.request('GET', '/api/jobs?id=' + job['id'])[1]
        self.assertEqual(body['result']['fabric']['status'], 'disabled')

    def test_invalid_or_missing_live_options_rejected(self):
        for key, value in [('fabric_enabled', 1), ('fabric_enabled', 'false'),
                           ('fabric_enabled', None), ('presentation', 'flat'),
                           ('presentation', None), ('presentation', ['held'])]:
            with self.subTest(key=key, value=value):
                payload = self.live_payload(**{key: value})
                self.assertEqual(self.request('POST', '/api/live', payload)[0], 400)
        for missing in ('fabric_enabled', 'presentation'):
            payload = self.live_payload()
            del payload[missing]
            self.assertEqual(self.request('POST', '/api/live', payload)[0], 400)
        self.assertEqual(self.predictor.calls, [])
        self.assertIsNone(self.pipeline.snapshot()['result'])

    def test_live_cross_origin_rejected(self):
        status, _, _ = self.request('POST', '/api/live', self.live_payload(),
                                    {'Content-Type': 'application/json', 'Origin': 'https://untrusted.example'})
        self.assertEqual(status, 403)
        self.assertIsNone(self.pipeline.snapshot()['result'])

    def test_repeated_rejected_bodies_are_drained_without_processing(self):
        # Include invalid JSON and a body spanning several drain chunks. No image,
        # JSON, inference or review processing should run on rejected requests.
        body = b'invalid-json-' * 12000
        for attempt in range(20):
            with self.subTest(attempt=attempt):
                for headers, expected in [
                    ({'Content-Type':'application/json','Origin':'https://untrusted.example'},403),
                    ({'Content-Type':'text/plain'},415)]:
                    status, result, _ = self.request('POST','/api/live',raw=body,headers=headers)
                    self.assertEqual(status,expected)
                    self.assertIn('error',result)
        self.assertEqual(self.predictor.calls,[])
        self.assertEqual(self.review.saved,[])
        self.assertIsNone(self.pipeline.snapshot()['result'])

    def test_rejection_drain_rejects_unbounded_or_ambiguous_framing(self):
        handler_class = make_handler(self.root,self.predictor,self.review,self.pipeline)
        for length, extra in [(str(MAX_BODY+1),None),('-1',None),('broken',None),
                               ('100','chunked'),(None,None)]:
            with self.subTest(length=length,extra=extra):
                handler=object.__new__(handler_class)
                handler.headers=Message()
                if length is not None:handler.headers['Content-Length']=length
                if extra:handler.headers['Transfer-Encoding']=extra
                handler.rfile=Mock()
                handler.send=Mock()
                handler.reject_before_body(403,'refused')
                handler.rfile.read1.assert_not_called()
                handler.send.assert_called_once_with(403,{'error':'refused'})
                self.assertTrue(handler.close_connection)

    def test_rejection_drain_has_total_time_limit_and_restores_socket_timeout(self):
        handler=object.__new__(make_handler(self.root,self.predictor,self.review,self.pipeline))
        handler.headers=Message()
        handler.headers['Content-Length']='100'
        handler.connection=Mock()
        handler.connection.gettimeout.return_value=None
        handler.rfile=Mock()
        handler.rfile.read1.return_value=b'x'
        handler.send=Mock()
        with patch('app.server.time.monotonic',side_effect=[10,10.1,12.1]):
            handler.reject_before_body(403,'refused')
        handler.rfile.read1.assert_called_once_with(100)
        self.assertEqual(handler.connection.settimeout.call_args.args,(None,))
        handler.send.assert_called_once_with(403,{'error':'refused'})

    def test_cancelling_completed_live_job_clears_result(self):
        _, job, _ = self.request('POST', '/api/live', self.live_payload())
        self.assertTrue(self.pipeline.wait_idle(2))
        self.assertEqual(self.request('POST', '/api/jobs/cancel', {'id': job['id']})[0], 200)
        self.assertEqual(self.request('GET', '/api/jobs?id=' + job['id'])[1]['state'], 'cancelled')
        self.assertIsNone(self.pipeline.snapshot()['result'])


# Use the common fixture methods without rerunning its separate legacy suite.
for name in vars(fixtures.ServerTests):
    if name.startswith('test_'):
        setattr(LiveApiTests, name, None)
