"""Camera-independent latest-frame scheduling and result freshness.

This controller does not capture, recognize scene changes, or run inference.
Adapters supply validity/scene events and use one monotonic clock. Submitted
payloads must be immutable or owned by the adapter until inference completes.
"""
from copy import deepcopy
from dataclasses import dataclass
import math
import threading
import time
from typing import Any


@dataclass(frozen=True)
class Frame:
    frame_id: int
    captured_at: float
    payload: Any


@dataclass(frozen=True)
class Work:
    token: int
    generation: int
    frame: Frame
    started_at: float


class LiveController:
    """One active inference plus at most one waiting frame; no inference under lock."""

    def __init__(self, *, max_frame_age: float, max_result_age: float, clock=time.monotonic):
        for value in (max_frame_age, max_result_age):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError('Age limits must be finite positive seconds')
        self.max_frame_age = max_frame_age
        self.max_result_age = max_result_age
        self.clock = clock
        self._lock = threading.Lock()
        self._connected = False
        self._generation = 0
        self._next_token = 0
        self._last_frame_id = -1
        self._last_capture = -math.inf
        self._pending = None
        self._active = None
        self._result = None
        self._reason = 'camera_disconnected'
        self._dropped = 0

    def _invalidate(self, reason):
        self._generation += 1
        if self._pending is not None:
            self._dropped += 1
        self._pending = None
        self._result = None
        self._reason = reason
        # Retain active work until it finishes: invalidation is not cancellation.

    def set_connected(self, connected: bool):
        if type(connected) is not bool:
            raise ValueError('Connection state must be boolean')
        with self._lock:
            if connected != self._connected:
                self._connected = connected
                self._invalidate('waiting_for_frame' if connected else 'camera_disconnected')

    def invalidate(self, reason='scene_changed'):
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError('Invalidation reason is required')
        with self._lock:
            self._invalidate(reason)

    def submit(self, frame: Frame, *, valid: bool):
        """Replace the waiting frame. Invalid frames immediately clear predictions."""
        if not isinstance(frame, Frame) or type(frame.frame_id) is not int or frame.frame_id < 0:
            raise ValueError('Frame requires a nonnegative integer ID')
        if type(valid) is not bool:
            raise ValueError('Frame validity must be boolean')
        with self._lock:
            now = self.clock()
            stamp = frame.captured_at
            if isinstance(stamp, bool) or not isinstance(stamp, (int, float)) or not math.isfinite(stamp) or stamp > now:
                raise ValueError('Capture time must be finite and not in the future')
            if frame.frame_id <= self._last_frame_id or stamp < self._last_capture:
                raise ValueError('Frame IDs and capture times must stay ordered')
            if not self._connected:
                return False
            self._last_frame_id, self._last_capture = frame.frame_id, stamp
            if not valid:
                self._invalidate('invalid_frame')
                return False
            if now-stamp > self.max_frame_age:
                self._dropped += 1
                return False
            if self._pending is not None:
                self._dropped += 1
            self._pending = frame
            return True

    def take(self):
        """Nonblocking claim by an inference worker; preview never waits for inference."""
        with self._lock:
            if not self._connected or self._active is not None or self._pending is None:
                return None
            frame, self._pending = self._pending, None
            now = self.clock()
            if now-frame.captured_at > self.max_frame_age:
                self._dropped += 1
                return None
            self._next_token += 1
            self._active = Work(self._next_token, self._generation, frame, now)
            return self._active

    def finish(self, work: Work, prediction: dict | None = None, *, error: str | None = None):
        """Release exactly the claimed work; stale results cannot reappear."""
        if error is None and not isinstance(prediction, dict):
            raise ValueError('Supply a prediction dictionary or an error')
        if error is not None and (not isinstance(error, str) or not error.strip()):
            raise ValueError('Error must be a nonempty string')
        with self._lock:
            if work is not self._active or work is None:
                raise ValueError('Work is not the current active claim')
            self._active = None
            now = self.clock()
            if not self._connected or work.generation != self._generation:
                return False
            if error is not None:
                self._result = None
                self._reason = 'inference_error'
                return False
            if now-work.frame.captured_at > self.max_result_age:
                self._result = None
                self._reason = 'result_expired'
                return False
            self._result = {'frame_id':work.frame.frame_id, 'captured_at':work.frame.captured_at,
                            'started_at':work.started_at, 'finished_at':now,
                            'generation':work.generation, 'prediction':deepcopy(prediction)}
            self._reason = 'current_result'
            return True

    def snapshot(self):
        """Expire using capture time, not inference completion time."""
        with self._lock:
            now = self.clock()
            if self._result is not None and now-self._result['captured_at'] > self.max_result_age:
                self._result = None
                self._reason = 'result_expired'
            result = deepcopy(self._result)
            if result is not None:
                result['age_seconds'] = now-result['captured_at']
            return {'connected':self._connected,'generation':self._generation,
                    'active_frame_id':self._active.frame.frame_id if self._active else None,
                    'pending_frame_id':self._pending.frame_id if self._pending else None,
                    'dropped_frames':self._dropped,'reason':self._reason,'result':result}
