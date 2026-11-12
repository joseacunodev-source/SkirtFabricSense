# Project review and next tasks

The review below describes the earlier recovery checkpoint. Its R01–R04 implementation tasks are now complete; see [the delivered behavior and next actions](RECOVERY_IMPLEMENTATION_NOV11.md).

Reviewed November 11, 2026. The selected system remains **station-v8 / research-v13**, with station-v7 as rollback. It is a working desktop research prototype. Reliable full-feature operation, calibrated length and Raspberry Pi acceptance remain unfinished.

## Verified current state

- All 236 referenced checkpoint files matched their hashes; the selected station inventory verified.
- Eleven archived experiment `run.json` files were inspected. None remained marked `started`; no scoped WSL training, robustness-evaluation or station-preview process was active.
- The registered collection remains 1,932 original images. This is not a count of independently verified garments.
- Selected detection-chain development results remain 44/66 skirt images accepted, 38/66 with correct pleating, and 42/52 non-skirt images rejected. Ten negatives were falsely accepted and 22 skirts unavailable. These reused development results do not establish independent camera accuracy.
- Fabric remains a 17-image source-appearance smoke experiment with five validation images. No accepted project fabric-composition model exists.
- Hemline rules, geometry adapters, replay evaluation and a measured-calibration builder exist. Actual observed geometry annotations remain zero.
- Five progress-report screenshots, their explanations, the five-page Word document and nine earlier thesis figures are available. Documentation completion does not close model or hardware acceptance.

[Root audit](../records/validation/2026-11-11-refresh-audit.json). It includes the experiment inventory, source hashes and actual process observation.

## Work interrupted at the usage limit

| Item | What actually exists | What remains |
|---|---|---|
| Fabric browser reviewer | `tools/serve_fabric_review.py` and `tools/static/fabric_review.html`; read-only page/queue/image checks pass | Missing UI-specific test module and reviewer documentation; browser interaction, save/download and request-security checks need temporary fixtures before acceptance |
| Geometry annotation editor | Design in conversation; existing geometry evaluator and contracts | No `tools/geometry_annotation.py`, editor HTML, dedicated tests or guide found; implement source-pixel interval annotation with explicit unknown states and provenance |
| Background intake | Completed bounded Commons attempt, 32 requests, zero acquired photos and zero admissions; all 38 recorded artifact hashes match | No visual review or model training can follow from this attempt; improve the source/transport plan before another versioned attempt |
| Background record recovery | Twenty-one retained HTTP 429 text responses have `.json` filenames | Preserve original response bytes and historical hashes; add a versioned recovery record and correctly typed parsing/validation before declaring record integrity restored |

The background acquisition is a completed failed attempt, not a running download. Its failures include URL eligibility, the size cap and rate limiting. Do not restart it in place or count its category/metadata references as photos. The source manifest is empty.

The fabric queue has **zero submitted observations**. The user confirmed that they or a groupmate can review saved images; that confirmation is not an annotation. A read-only audit of the partial server found no established critical defect, but does not validate saving or the complete browser flow. The underlying evidence tool's 30 tests passed during the independent audit; the separate UI test file is absent.

## Next implementation order without hardware

1. **R01 Record recovery.** Preserve and classify the 21 raw error responses, reconcile the completed zero-photo intake and document the recovery without rewriting historical acquisition evidence. Acceptance: a deliberate, tested validation path distinguishes raw transport evidence from parsed metadata; no unexplained record errors.
2. **R02 Fabric reviewer completion.** Add the missing UI tests and guide, test actual browser interactions and save/download using temporary queues, and preserve loopback/request and private-file protections. Acceptance: a human can review all 17 originals without editing JSON; production observations remain append-only and pending reconciliation.
3. **S01/S04 Human label review.** Have the available reviewers submit observations and resolve disputed cases, garment identity, material association and source rights. Keep visible appearance separate from verified fibre composition. Acceptance: an explicitly reviewed, versioned label release with unchanged protected memberships.
4. **R03 Geometry editor.** Build the missing saved-image editor for visible waist, hem and foot/floor uncertainty bands, with original-image hashes, source coordinates and unknown/hidden choices. Acceptance: reviewed observations can enter the existing evaluator without fabricated camera identities or calibration. This alone does not create validated automatic wearer detection.
5. **S02/S03 Better data and detection.** Obtain appropriately licensed new groups and hard negatives, preserve all existing splits, then predeclare one candidate comparison. Report coverage, class errors and non-skirt rejection together. Collect genuinely independent camera/garment evaluation separately; do not re-split reused validation and call it a new test.
6. **S05 Stronger fabric model.** Finalize label semantics and acquire enough credible full-skirt groups before fitting. Compare automatic same-frame crops and unsupported inputs, export the candidate and verify desktop parity before selection.
7. **R04 Small-screen usability.** Review the current 800 × 480 layout, especially camera-mode controls and reference information below the fold. Prioritize essential live controls and results; verify the proposed interaction in a browser before physical touch acceptance.

These items are feature and evidence dependencies, not a promise that a larger image count or another fit will meet accuracy targets. Keep training weights, thresholds and selected station unchanged until a justified candidate passes its declared checks.

## Future work with garments and hardware

1. Obtain and identify development and reserved test garments, with credible label evidence and consent where applicable. Freeze unseen garment groups before reviewing their predictions.
2. Test the actual camera at full-skirt framing; measure resolution, focus, lighting, usable texture detail and framing failures.
3. Annotate and validate wearer references/hem contours, measure calibration, and test all nine categories and boundary cases. Preserve worn-primary and secondary-mode reference policies.
4. Install the actual Pi station and selected Waveshare 14447 display. Record board, power, cooling, storage, OS, Python, ARM64 runtime, camera and screen settings. Produce a separate tested edge lock and installation record.
5. Verify exported predictions on the Pi, then measure live latency, memory, temperature, preview, scene changes, stale clearing, disconnection, offline operation and recovery.
6. Evaluate unseen garments end to end, fix documented failures, freeze the accepted configuration and rehearse the supervised capstone demonstration. Verify secondary presentations separately.

The user reconfirmed on November 11 that no Raspberry Pi, webcam or actual skirts are available. Software and saved-image preparation can continue; physical tasks remain dependent on obtaining these items. No new completion percentage or finish date is inferred.

## Continuation rule

Resume at **R01 then R02**, not another GPU fit. Before repeating an operation, verify its saved status and actual process state. Use [the task board](TASK_BOARD.md) and [current checkpoint](../records/continuation/latest.json). Keep all historical runs, failed requests, frozen source/test assignments and unaccepted reviewer work visible.
