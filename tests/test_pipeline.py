"""Deterministic worker integration checks, using owned synthetic PIL frames."""
import threading
import unittest

from PIL import Image

from app.pipeline import ImagePipeline


class BlockingPredictor:
    def __init__(self, outcomes=None):
        self.entered = [threading.Event() for _ in range(8)]
        self.release = [threading.Event() for _ in range(8)]
        self.calls = []
        self.outcomes = outcomes or {}

    def predict(self, image, roi, confirmed):
        index = len(self.calls)
        self.calls.append(None)
        self.entered[index].set()
        if not self.release[index].wait(5):
            raise TimeoutError('Test did not release fake inference')
        self.calls[index] = (image.getpixel((0, 0)), roi, confirmed)
        outcome = self.outcomes.get(index, {'pixel': self.calls[index][0]})
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.predictor = BlockingPredictor()
        self.pipeline = ImagePipeline(self.predictor, max_frame_age=2,
                                      max_result_age=5, clock=lambda: 100.0)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        for gate in self.predictor.release:
            gate.set()
        self.assertTrue(self.pipeline.close(2))

    def submit(self, color=1, **kwargs):
        return self.pipeline.submit(Image.new('RGB', (8, 8), (color, 0, 0)),
                                    valid=True, full_skirt_confirmed=True, **kwargs)

    def started(self, index=0):
        self.assertTrue(self.predictor.entered[index].wait(2), 'Worker did not start')

    def finish(self, index=0):
        self.predictor.release[index].set()
        self.assertTrue(self.pipeline.wait_idle(2))

    def test_latest_waiting_frame_replaces_middle_without_overlapping_inference(self):
        self.submit(1)
        self.started()
        self.submit(2)
        third = self.submit(3)
        state = self.pipeline.snapshot()
        self.assertEqual((state['active_frame_id'], state['pending_frame_id']), (1, 3))
        self.assertFalse(self.predictor.entered[1].is_set())
        self.predictor.release[0].set()
        self.started(1)
        self.finish(1)
        self.assertEqual([call[0][0] for call in self.predictor.calls], [1, 3])
        self.assertEqual(self.pipeline.snapshot()['result']['frame_id'], third['frame_id'])

    def test_submit_owns_pixels_and_roi_before_capture_buffer_is_reused(self):
        image = Image.new('RGB', (8, 8), (19, 0, 0))
        roi = [0, 0, 7, 7]
        self.pipeline.submit(image, roi=roi, valid=True, full_skirt_confirmed=True)
        self.started()
        image.paste((255, 255, 255), (0, 0, 8, 8))
        roi[2] = 1
        image.close()
        self.finish()
        self.assertEqual(self.predictor.calls[0], ((19, 0, 0), (0, 0, 7, 7), True))

    def test_scene_change_discards_old_completion_while_new_work_waits(self):
        self.submit(1)
        self.started()
        self.submit(2, scene_changed=True)
        self.predictor.release[0].set()
        self.started(1)
        self.assertIsNone(self.pipeline.snapshot()['result'])
        self.finish(1)
        self.assertEqual(self.pipeline.snapshot()['result']['prediction']['pixel'], (2, 0, 0))

    def test_explicit_invalidation_discards_active_and_pending_work(self):
        self.submit()
        self.started()
        self.submit(2)
        self.pipeline.invalidate('garment_removed')
        self.finish()
        state = self.pipeline.snapshot()
        self.assertIsNone(state['result'])
        self.assertEqual(state['reason'], 'garment_removed')
        self.assertEqual(len(self.predictor.calls), 1)

    def test_disconnect_reconnect_rejects_pre_disconnect_completion(self):
        self.submit()
        self.started()
        self.pipeline.set_connected(False)
        self.assertFalse(self.submit(2)['accepted'])
        self.pipeline.set_connected(True)
        self.submit(3)
        self.predictor.release[0].set()
        self.started(1)
        self.assertIsNone(self.pipeline.snapshot()['result'])
        self.finish(1)
        self.assertEqual(self.pipeline.snapshot()['result']['prediction']['pixel'], (3, 0, 0))

    def test_predictor_exception_clears_result_and_worker_recovers(self):
        self.predictor.outcomes[0] = RuntimeError('synthetic failure')
        self.submit()
        self.started()
        self.finish()
        state = self.pipeline.snapshot()
        self.assertIsNone(state['result'])
        self.assertEqual(state['reason'], 'inference_error')
        self.assertIn('synthetic failure', state['last_worker_error'])
        self.submit(2)
        self.started(1)
        self.finish(1)
        self.assertEqual(self.pipeline.snapshot()['result']['prediction']['pixel'], (2, 0, 0))

    def test_non_dictionary_prediction_is_recoverable_error(self):
        self.predictor.outcomes[0] = ['invalid output']
        self.submit()
        self.started()
        self.finish()
        self.assertEqual(self.pipeline.snapshot()['reason'], 'inference_error')
        self.assertTrue(self.pipeline.snapshot()['worker_alive'])

    def test_wait_idle_timeout_is_truthful_while_predictor_is_blocked(self):
        self.submit()
        self.started()
        self.assertFalse(self.pipeline.wait_idle(0))
        self.finish()
        self.assertTrue(self.pipeline.wait_idle(0))

    def test_close_timeout_then_completion_never_publishes_or_restarts(self):
        self.submit()
        self.started()
        self.submit(2)
        self.assertFalse(self.pipeline.close(0))
        state = self.pipeline.snapshot()
        self.assertTrue(state['closed'])
        self.assertTrue(state['worker_alive'])
        self.assertIsNone(state['pending_frame_id'])
        for action in (lambda: self.submit(), lambda: self.pipeline.set_connected(True),
                       lambda: self.pipeline.invalidate()):
            with self.assertRaises(RuntimeError):
                action()
        self.predictor.release[0].set()
        self.assertTrue(self.pipeline.close(2))
        state = self.pipeline.snapshot()
        self.assertFalse(state['worker_alive'])
        self.assertIsNone(state['result'])
        self.assertEqual(len(self.predictor.calls), 1)

    def test_invalid_frame_clears_prior_result_without_predicting(self):
        self.submit()
        self.started()
        self.finish()
        result = self.pipeline.submit(Image.new('RGB', (8, 8)), valid=False,
                                      full_skirt_confirmed=False)
        self.assertFalse(result['accepted'])
        self.assertIsNone(self.pipeline.snapshot()['result'])
        self.assertEqual(len(self.predictor.calls), 1)


if __name__ == '__main__':
    unittest.main()
