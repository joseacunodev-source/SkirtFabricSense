"""Single-worker bridge from owned image frames to the live controller."""
import threading
import time
from copy import deepcopy
from PIL import Image

from app.live_state import Frame, LiveController


class ImagePipeline:
    """Explicit validity inputs; no camera, skirt detector or automatic scene detector."""

    def __init__(self, predictor, *, max_frame_age, max_result_age, clock=time.monotonic):
        self.controller = LiveController(max_frame_age=max_frame_age, max_result_age=max_result_age, clock=clock)
        self.predictor = predictor
        self.clock = clock
        self._condition = threading.Condition()
        self._stopped = False
        self._next_id = 0
        self._last_error = None
        self.controller.set_connected(True)
        self._thread = threading.Thread(target=self._run, name='skirt-inference', daemon=True)
        self._thread.start()

    def submit(self, image, *, roi=None, valid, full_skirt_confirmed, captured_at=None, scene_changed=False):
        if any(type(v) is not bool for v in (valid, full_skirt_confirmed, scene_changed)):
            raise ValueError('Validity, confirmation and scene flags must be booleans')
        if not isinstance(image, Image.Image):
            raise ValueError('Expected a PIL image')
        # Own the pixels: a capture adapter may reuse its source buffer immediately.
        stamp = self.clock() if captured_at is None else captured_at
        payload = (image.copy(), deepcopy(roi) if isinstance(roi,dict) else tuple(roi) if roi is not None else None, full_skirt_confirmed)
        with self._condition:
            if self._stopped:
                raise RuntimeError('Pipeline is closed')
            if scene_changed:
                self.controller.invalidate('scene_changed')
            self._next_id += 1
            frame = Frame(self._next_id, stamp, payload)
            accepted = self.controller.submit(frame, valid=valid)
            self._condition.notify_all()
            return {'frame_id':frame.frame_id,'accepted':accepted}

    def set_connected(self, connected):
        with self._condition:
            if self._stopped:
                raise RuntimeError('Pipeline is closed')
            self.controller.set_connected(connected)
            self._condition.notify_all()

    def invalidate(self, reason='scene_changed'):
        with self._condition:
            if self._stopped:
                raise RuntimeError('Pipeline is closed')
            self.controller.invalidate(reason)
            self._condition.notify_all()

    def snapshot(self):
        with self._condition:
            return {**self.controller.snapshot(), 'worker_alive':self._thread.is_alive(),
                    'closed':self._stopped,'last_worker_error':self._last_error}

    def _run(self):
        while True:
            with self._condition:
                if self._stopped:
                    return
                work = self.controller.take()
                if work is None:
                    self._condition.notify_all()
                    self._condition.wait()
                    continue
            try:
                image, roi, confirmed = work.frame.payload
                prediction = self.predictor.predict(image, roi, confirmed)
                if not isinstance(prediction, dict):
                    raise ValueError('Predictor must return a dictionary')
            except Exception as exc:
                with self._condition:
                    self._last_error = type(exc).__name__ + ': ' + str(exc)
                    self.controller.finish(work, error=self._last_error)
                    self._condition.notify_all()
            else:
                with self._condition:
                    self.controller.finish(work, prediction)
                    self._condition.notify_all()

    def wait_idle(self, timeout=5.0):
        """Bounded test/CLI synchronization; preview code should use snapshot instead."""
        def idle():
            state = self.controller.snapshot()
            return state['active_frame_id'] is None and state['pending_frame_id'] is None
        with self._condition:
            return self._condition.wait_for(idle, timeout=timeout)

    def close(self, timeout=5.0):
        """Return False if a worker is still in inference; never claim it was killed."""
        with self._condition:
            self._stopped = True
            self.controller.set_connected(False)
            self._condition.notify_all()
        self._thread.join(timeout)
        return not self._thread.is_alive()
