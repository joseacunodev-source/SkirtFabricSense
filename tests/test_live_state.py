"""Deterministic lifecycle checks; no camera or model is required."""
from dataclasses import replace
import threading
import unittest

from app.live_state import Frame, LiveController


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class LiveStateTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.controller = LiveController(max_frame_age=2, max_result_age=5, clock=self.clock)
        self.controller.set_connected(True)

    def submit(self, frame_id, *, valid=True, captured_at=None):
        return self.controller.submit(
            Frame(frame_id, self.clock() if captured_at is None else captured_at, b'frame'),
            valid=valid,
        )

    def publish(self, frame_id=1):
        self.submit(frame_id)
        claim = self.controller.take()
        self.assertTrue(self.controller.finish(claim, {'style': {'label': 'pleated', 'score': .8}}))
        return claim

    def test_latest_pending_replaces_older_without_replacing_active(self):
        self.submit(1)
        first = self.controller.take()
        self.submit(2)
        self.submit(3)
        self.assertIsNone(self.controller.take())
        state = self.controller.snapshot()
        self.assertEqual((state['active_frame_id'], state['pending_frame_id'], state['dropped_frames']), (1, 3, 1))
        self.controller.finish(first, {'style': 'first'})
        self.assertEqual(self.controller.take().frame.frame_id, 3)

    def test_simultaneous_workers_obtain_only_one_claim(self):
        self.submit(1)
        barrier = threading.Barrier(3)
        claims = []

        def worker():
            barrier.wait()
            claims.append(self.controller.take())

        workers = [threading.Thread(target=worker) for _ in range(2)]
        for thread in workers:
            thread.start()
        barrier.wait()
        for thread in workers:
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
        self.assertEqual(sum(claim is not None for claim in claims), 1)

    def test_scene_change_keeps_busy_slot_but_rejects_old_completion(self):
        self.publish()
        self.submit(2)
        old = self.controller.take()
        self.submit(3)
        self.controller.invalidate('scene_changed')
        self.submit(4)
        self.assertIsNone(self.controller.snapshot()['result'])
        self.assertIsNone(self.controller.take())
        self.assertFalse(self.controller.finish(old, {'style': 'old scene'}))
        self.assertIsNone(self.controller.snapshot()['result'])
        new = self.controller.take()
        self.assertEqual(new.frame.frame_id, 4)
        self.assertTrue(self.controller.finish(new, {'style': 'new scene'}))

    def test_disconnect_reconnect_rejects_old_completion(self):
        self.submit(1)
        old = self.controller.take()
        self.controller.set_connected(False)
        self.assertFalse(self.submit(2))
        self.assertIsNone(self.controller.take())
        self.assertEqual(self.controller.snapshot()['reason'], 'camera_disconnected')
        self.controller.set_connected(True)
        self.submit(3)
        self.assertIsNone(self.controller.take())
        self.assertFalse(self.controller.finish(old, {'style': 'stale'}))
        self.assertIsNone(self.controller.snapshot()['result'])
        self.assertEqual(self.controller.take().frame.frame_id, 3)

    def test_invalid_frame_clears_prediction_and_invalidates_running_work(self):
        self.publish()
        self.submit(2)
        old = self.controller.take()
        self.submit(3)
        self.assertFalse(self.submit(4, valid=False))
        state = self.controller.snapshot()
        self.assertIsNone(state['result'])
        self.assertIsNone(state['pending_frame_id'])
        self.assertEqual(state['reason'], 'invalid_frame')
        self.assertFalse(self.controller.finish(old, {'style': 'late'}))
        self.assertIsNone(self.controller.snapshot()['result'])

    def test_expiry_uses_capture_not_completion_time(self):
        self.submit(1)
        work = self.controller.take()
        self.clock.advance(4)
        self.assertTrue(self.controller.finish(work, {'style': 'pleated'}))
        self.assertEqual(self.controller.snapshot()['result']['age_seconds'], 4)
        self.clock.advance(1)
        self.assertIsNotNone(self.controller.snapshot()['result'])
        self.clock.advance(.01)
        state = self.controller.snapshot()
        self.assertIsNone(state['result'])
        self.assertEqual(state['reason'], 'result_expired')

    def test_result_already_expired_at_completion_is_never_published(self):
        self.submit(1)
        work = self.controller.take()
        self.clock.advance(5.1)
        self.assertFalse(self.controller.finish(work, {'style': 'pleated'}))
        self.assertIsNone(self.controller.snapshot()['result'])
        self.assertIsNone(self.controller.snapshot()['active_frame_id'])

    def test_pending_frame_can_expire_while_waiting_for_worker(self):
        self.submit(1)
        work = self.controller.take()
        self.submit(2)
        self.clock.advance(2.1)
        self.controller.finish(work, {'style': 'pleated'})
        self.assertIsNone(self.controller.take())
        self.assertEqual(self.controller.snapshot()['dropped_frames'], 1)
        self.assertIsNone(self.controller.snapshot()['pending_frame_id'])

    def test_stale_submission_is_dropped_before_inference(self):
        self.assertFalse(self.submit(1, captured_at=97))
        self.assertIsNone(self.controller.take())
        self.assertEqual(self.controller.snapshot()['dropped_frames'], 1)

    def test_inference_error_clears_previous_result_and_releases_worker(self):
        self.publish()
        self.submit(2)
        work = self.controller.take()
        self.submit(3)
        self.assertFalse(self.controller.finish(work, error='interpreter failed'))
        state = self.controller.snapshot()
        self.assertIsNone(state['result'])
        self.assertEqual(state['reason'], 'inference_error')
        self.assertEqual(self.controller.take().frame.frame_id, 3)

    def test_fake_and_duplicate_claims_cannot_release_or_overwrite_work(self):
        self.submit(1)
        real = self.controller.take()
        with self.assertRaises(ValueError):
            self.controller.finish(replace(real), {'style': 'forged'})
        self.assertEqual(self.controller.snapshot()['active_frame_id'], 1)
        self.assertTrue(self.controller.finish(real, {'style': 'real'}))
        with self.assertRaises(ValueError):
            self.controller.finish(real, {'style': 'duplicate'})
        self.assertEqual(self.controller.snapshot()['result']['prediction']['style'], 'real')

    def test_prediction_and_returned_snapshot_are_defensively_copied(self):
        self.submit(1)
        prediction = {'style': {'scores': [.2, .8]}}
        self.controller.finish(self.controller.take(), prediction)
        prediction['style']['scores'][0] = 999
        snapshot = self.controller.snapshot()
        self.assertEqual(snapshot['result']['prediction']['style']['scores'], [.2, .8])
        snapshot['result']['prediction']['style']['scores'].clear()
        self.assertEqual(self.controller.snapshot()['result']['prediction']['style']['scores'], [.2, .8])

    def test_malformed_inputs_do_not_consume_pending_frame(self):
        self.submit(1)
        for frame in [Frame(True, 100, None), Frame(-1, 100, None), Frame(2, float('nan'), None),
                      Frame(2, 101, None), Frame(1, 100, None), Frame(2, 99, None)]:
            with self.subTest(frame=frame), self.assertRaises(ValueError):
                self.controller.submit(frame, valid=True)
        with self.assertRaises(ValueError):
            self.controller.submit(Frame(2, 100, None), valid=1)
        self.assertEqual(self.controller.take().frame.frame_id, 1)

    def test_malformed_completion_keeps_claim_for_valid_retry(self):
        self.submit(1)
        work = self.controller.take()
        for kwargs in ({}, {'prediction': []}, {'error': ''}, {'error': False}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.controller.finish(work, **kwargs)
        self.assertEqual(self.controller.snapshot()['active_frame_id'], 1)
        self.assertTrue(self.controller.finish(work, {'style': 'valid'}))

    def test_repeated_connection_notification_preserves_result(self):
        self.publish()
        generation = self.controller.snapshot()['generation']
        self.controller.set_connected(True)
        self.assertEqual(self.controller.snapshot()['generation'], generation)
        self.assertIsNotNone(self.controller.snapshot()['result'])

    def test_age_limits_and_connection_types_are_validated(self):
        for value in (0, -1, True, float('inf'), float('nan'), '1'):
            for field in ('max_frame_age', 'max_result_age'):
                limits = {'max_frame_age': 1, 'max_result_age': 1, field: value}
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    LiveController(**limits)
        with self.assertRaises(ValueError):
            self.controller.set_connected(1)
        with self.assertRaises(ValueError):
            self.controller.invalidate(' ')


if __name__ == '__main__':
    unittest.main()
