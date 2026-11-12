"""HTTP integration with a real worker and controlled synthetic predictor."""
from http.server import ThreadingHTTPServer
import threading
from tests import test_server as fixtures
from tests.test_pipeline import BlockingPredictor
from app.pipeline import ImagePipeline
from app.server import make_handler


class AsyncServerTests(fixtures.ServerTests):
    # Reuse request/image fixtures, not legacy endpoint test cases.
    def start_server(self, review):
        self.predictor = BlockingPredictor()
        self.pipeline = ImagePipeline(self.predictor,max_frame_age=30,max_result_age=30)
        handler=make_handler(self.root,self.predictor,review,self.pipeline)
        handler.log_message=lambda *args:None
        self.server=ThreadingHTTPServer(('127.0.0.1',0),handler)
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01},daemon=True)
        self.thread.start()

    def stop_server(self):
        for gate in self.predictor.release:gate.set()
        self.pipeline.close(2)
        super().stop_server()

    def test_jobs_remain_responsive_and_old_cancellation_cannot_cancel_new(self):
        status,first,_=self.request('POST','/api/jobs',self.image_payload())
        self.assertEqual(status,202)
        self.assertTrue(self.predictor.entered[0].wait(2))
        self.assertEqual(self.request('GET','/api/jobs?id='+first['id'])[1]['state'],'pending')
        self.assertEqual(self.request('GET','/api/status')[0],200)
        status,new,_=self.request('POST','/api/jobs',self.image_payload())
        self.assertEqual(status,202)
        self.request('POST','/api/jobs/cancel',{'id':first['id']})
        self.assertEqual(self.request('GET','/api/jobs?id='+first['id'])[0],409)
        self.predictor.release[0].set()
        self.assertTrue(self.predictor.entered[1].wait(2))
        self.predictor.release[1].set()
        self.assertTrue(self.pipeline.wait_idle(2))
        self.assertEqual(self.request('GET','/api/jobs?id='+new['id'])[1]['state'],'complete')

    def test_cancel_current_rejects_late_worker_result(self):
        _,job,_=self.request('POST','/api/jobs',self.image_payload())
        self.assertTrue(self.predictor.entered[0].wait(2))
        self.request('POST','/api/jobs/cancel',{'id':job['id']})
        self.predictor.release[0].set()
        self.assertTrue(self.pipeline.wait_idle(2))
        self.assertEqual(self.request('GET','/api/jobs?id='+job['id'])[1]['state'],'cancelled')
        self.assertIsNone(self.pipeline.snapshot()['result'])

    def test_worker_mode_disables_legacy_endpoint(self):
        self.assertEqual(self.request('POST','/api/analyze',self.image_payload())[0],410)

# Only the three worker-specific checks run here; legacy checks have their own suite.
for name in list(vars(fixtures.ServerTests)):
    if name.startswith('test_'):
        setattr(AsyncServerTests,name,None)
