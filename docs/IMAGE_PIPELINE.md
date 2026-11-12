# Image worker integration

`app/pipeline.py` connects the latest-frame controller to a single background inference thread. It uses the existing Pillow dependency and a supplied predictor implementing `predict(image, roi, full_skirt_confirmed)`. No camera or web-server endpoint is activated by this module.

## Adapter contract

Create `ImagePipeline(predictor, max_frame_age=..., max_result_age=...)` with explicit age limits. The constructor starts one worker and marks the input source connected. `submit` copies the PIL image before returning so the capture adapter may reuse its buffer. Input timestamps must use the same monotonic clock; if omitted, the timestamp is taken before the copy. EXIF orientation must already be applied by file adapters before ROI coordinates are assigned; camera adapters supply decoded pixel orientation.

Each submission requires explicit boolean `valid` and `full_skirt_confirmed`. Those flags are evidence supplied by an adapter or reviewer, not decisions made by this pipeline. Use `scene_changed=True` for a known new scene or call `invalidate` for an ROI/model/calibration change. The pipeline does not detect skirts, compute blur thresholds or infer scene transitions. Invalid input clears results through the controller. Confirmation is forwarded unchanged to the predictor, which abstains when it is absent.

The worker claims the newest waiting frame and calls the predictor outside the condition lock. Producer submissions and snapshots can continue while inference runs. Predictor exceptions release the claim, clear eligible results and retain a diagnostic in `last_worker_error`; subsequent valid frames can run. That diagnostic is historical and does not imply that the latest result failed. Snapshot result metadata includes frame ID, capture/start/finish times and controller generation. Per-attribute unavailable states remain intact.

`wait_idle(timeout)` is for CLI/tests and returns false on timeout. A UI should poll `snapshot` and clear its display whenever result is absent. `close(timeout)` invalidates results, disconnects the source, discards waiting work and requests worker shutdown. It returns false if inference is still running; it does not forcibly terminate a Python thread. Submitting or reconnecting after close is rejected. A second close can join a previously busy worker after it exits. Process supervision remains necessary for a permanently hung runtime.

## Actual integration check

From the workspace in the existing WSL training environment:

```text
python tools/check_pipeline.py --bundle artifacts/releases/skirt-finetune-v1-desktop --output records/validation/my-pipeline-check.json
```

The check uses three fixed existing development images, source annotation ROIs and explicit validity/scene flags. It compares model scores to archived TFLite predictions, verifies source-frame result IDs and unavailable fabric/length outputs, clears output on disconnect and checks worker shutdown. The 30-second age limits are smoke-test configuration, not product defaults or measured latency targets.

The [real-model record](../records/validation/2026-10-05-pipeline-real-model.json) passed with zero score difference on all three images. This verifies saved-image integration, not new accuracy, automatic framing or camera-domain behavior. No dataset, model weight, package version or existing application bundle changed. The current web UI still uses its existing synchronous file-image endpoint; browser polling and real camera integration remain outstanding.

Verification completed: **26 tests passed** (16 controller, 10 worker). Worker checks cover frame replacement, pixel/ROI ownership, scene invalidation, reconnection, predictor-error recovery and truthful close/idle timeouts. Root reviewed and ran the tests after the test agent hit its usage limit. [Test evidence](../records/validation/2026-10-05-pipeline-tests.json). No new dependencies installed.
