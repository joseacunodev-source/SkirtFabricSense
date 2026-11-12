# Background analysis in the web application

The saved-image interface now submits work to `ImagePipeline` and polls for results. The server's single worker runs the real model outside HTTP request handling. This integrates the controller, file-image adapter and browser request flow; no live camera is enabled.

## API and cancellation

- `POST /api/jobs`: same base64 image, optional integer ROI and boolean framing confirmation as the original analysis input. Returns HTTP 202 with an opaque job ID and source frame ID.
- `GET /api/jobs?id=...`: returns pending, complete with per-attribute prediction, cancelled or unavailable. Unknown/superseded jobs return HTTP 409.
- `POST /api/jobs/cancel`: accepts a job ID and invalidates it only if it is still current. A delayed cancellation cannot clear a newer submission.

One current job is retained for the station, with at most one active model invocation and one newest waiting frame. Multiple browser tabs share that station: a newer submission supersedes the old one. This is not a multi-user job service. Images remain in memory; no history queue is saved.

Image/ROI/confirmation changes clear the browser output and cancel its current job. If an upload response arrives after the selection changed, its returned job is cancelled. Poll responses carry a browser generation check before display. The browser polls every 200 ms while pending and stops with an error after its 35-second polling deadline. These values and the pipeline's 30-second input/result age limits are file-image development settings, not measured camera/Pi targets. HTTP/network fetch timeouts and full browser interaction testing remain additional hardening work.

Completed results are labelled saved-image results and remain displayed for the unchanged selection. They are not a live scene assertion. A future camera screen must continually poll freshness and clear expired results even without user interaction.

The default server no longer accepts the old synchronous `/api/analyze` route (HTTP 410). The factory's legacy mode remains for earlier unit fixtures; the user-facing server uses the worker. `tools/check_application.py` now exercises job submission/polling.

## Running and packaging

Use the command in [application setup](APPLICATION_SETUP.md). A new immutable bundle at `artifacts/releases/skirt-finetune-v1-desktop-async-v2` includes the worker/controller and updated UI. The original desktop bundle is preserved for comparison; model weights and model ID are unchanged. Application revisions are distinguished by bundle directory and inventory hashes.

No dependencies were installed. Camera/localization/quality detection, automatic fabric recognition, calibrated length and Pi acceptance remain pending. Validity here means a decoded file submitted by the operator, not automatic evidence that it contains a complete skirt.

[Validation record](../records/validation/2026-10-05-async-application.json): 24 tests passed, JavaScript syntax passed, nine bundled payload hashes matched, and three actual TFLite API outputs exactly matched archived scores. One initial Windows socket abort is preserved in the record. Full browser upload/ROI interaction remains unverified.
