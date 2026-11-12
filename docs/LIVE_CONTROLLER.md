# Live-processing controller

Implemented October 5, 2026: `app/live_state.py` supplies a thread-safe controller for a future capture adapter, inference worker and UI. It has no external dependencies, opens no camera, and is not yet connected to the file-image web application. The existing packaged application is unchanged.

## Ownership and flow

1. The capture adapter obtains a single full-skirt frame, assigns an increasing ID and capture timestamp from the shared monotonic clock, and provides its validity decision to `submit(Frame(...), valid=...)`. Payloads must remain immutable/owned until processing finishes. Preview rendering stays outside this controller.
2. `submit` replaces the one waiting frame. One worker claims it with `take()` and runs the model outside the controller lock. At most one inference claim is active; additional claims return no work. This drops superseded waiting frames instead of accumulating a video backlog.
3. The worker calls `finish(work, prediction)` or `finish(work, error=...)` with the exact claim object. The prediction preserves independent per-attribute statuses; a style result cannot create a fabric or length result.
4. The UI polls `snapshot()`. Results expire by age since original capture, including time spent waiting and computing. The UI must clear its display whenever snapshot result is absent. No background timer mutates the UI on its behalf.

An upstream adapter calls `invalidate` when the scene, ROI, model or calibration changes. Connection changes and invalid frames also invalidate pending results immediately. Generation numbers prevent a worker finishing an old scene from republishing its result. Invalidation does not pretend to cancel in-flight inference: the old claim must still finish before another begins. IDs remain increasing across reconnections during a controller's lifetime.

Age limits must be explicit finite positive values. Replay settings of one second for waiting input and two seconds for results are **test inputs**, not measured or calibrated product defaults. Capture and completion timestamps must use the same monotonic clock. Equal capture timestamps are allowed with increasing frame IDs; decreasing timestamps and duplicate IDs are rejected.

## Verification without hardware

```text
python -m unittest tests.test_live_state -v
python tools/replay_live_state.py --output records/validation/my-live-replay.json
```

The replay demonstrates replacement of an older waiting frame, rejection of old-scene and pre-disconnection completions, acceptance of a current result, expiry, invalid-frame clearing and worker errors. Values in the trace are explicitly synthetic; they are not classifier predictions. Output files cannot overwrite existing evidence.

## Remaining integration

The controller does not detect scene changes, skirts, blur, occlusion or camera loss. Those events must be supplied by future capture/quality/localization components. It does not perform temporal voting, score calibration, image copying, logging rotation or worker-process restart. A permanently hung worker requires a supervisor that terminates the worker before permitting new inference; simply clearing its claim could allow overlapping model calls. Real capture adapters, preview scheduling, UI polling/freshness, shutdown/recovery and measured age limits remain necessary. Camera/Pi acceptance is unverified.

No dataset, training split, model weights, installed package or old application bundle changed in this milestone.

Actual evidence: [16 controller tests](../records/validation/2026-10-05-live-controller-tests.json) and [seven replay checkpoints](../records/validation/2026-10-05-live-controller-replay.json) passed on October 5. Tests include a real two-thread claim race; all input frames and prediction values remain synthetic.

## Subsequent worker integration

The [image pipeline](IMAGE_PIPELINE.md) now owns image copies and drives the controller from a background model worker. Its real-model saved-image check passed. Camera adapters, automatic validity/scene events and UI polling remain separate work.
