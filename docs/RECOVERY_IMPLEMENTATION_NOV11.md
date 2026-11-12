# Completed recovery and reviewer tools

November 11, 2026. All four requested software tasks R01–R04 are implemented and checked. **Station-v9 / research-v14** is selected for desktop research, with station-v8 as rollback. Model weights and thresholds are unchanged. The project remains a research prototype pending human labels, geometry/calibration and actual camera/Pi acceptance.

## Completed tasks

| Task | Delivered behavior | Verification |
|---|---|---|
| R01 Acquisition record recovery | Twenty-one original HTTP 429 response bodies and historical hashes preserved; typed text copies and a source-bound recovery index distinguish transport failures from parsed metadata | 14 recovery tests and three continuation tests; no folder-wide parse exclusion; zero added photos/admissions |
| R02 Fabric reviewer | Browser shows the complete original, records visible evidence, handles unknowns and supports explicit save or JSON download; repeated identical saves do not inflate events | 11 UI and 30 evidence tests, including a real Edge 14-check temporary-queue roundtrip; production queue remains 17 items / zero observations |
| R03 Geometry annotation editor | Offline editor for waist, hem and foot/floor uncertainty bands in original-image coordinates; hidden/unknown references retained; pending drafts with source/inventory hashes | 14 Python tests and real Edge drag, numeric, cancellation, date and export-to-validator checks; zero production observations |
| R04 Small-screen layout | Essential camera controls/settings, preview, four attribute values and fabric switch fit the initial 800 × 480 viewport; long guidance opens through native disclosures | 52 mocked lifecycle/score/motion/mode cases, six actual Edge layout scenarios, 30 package/release tests and 12 saved-image HTTP jobs on the new station |

The four Python test commands total **102 passing tests**; browser/layout case counts describe their own checks rather than additional garments. The saved-image HTTP test reuses three development originals in two configurations. No new accuracy result is claimed.

## Use the tools

For human fabric review, follow [the browser reviewer guide](FABRIC_REVIEW_UI.md). From the project directory:

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B tools/serve_fabric_review.py --port 8771
```

Open `http://127.0.0.1:8771/`. Review all 17 originals, use unknown when evidence is inadequate, and save only actual observations. Stop with Ctrl+C. The tool records pending evidence; it does not approve labels or verify composition.

For geometry review, [the editor guide](GEOMETRY_ANNOTATION.md) explains building and validating a draft. A ready-to-open editor for one existing validation original is at [output/geometry-review/12679.html](../output/geometry-review/12679.html). No bands or reviewer observations have been prefilled. The file embeds a source photograph for local review; retain its original source terms and attribution. Each reviewed draft requires independent reconciliation and credible reference/projection evidence before evaluation.

For the compact station, use [the current launch instructions](STATION_PACKAGE.md). [The updated 800 × 480 screenshot](../records/validation/2026-11-11-compact-layout/independent-review/camera-off-800x480.png) shows the camera-off state. Opening extended instructions can require scrolling. Physical text size, touch accuracy and live performance remain untested.

## Evidence and preserved history

- [Raw-response recovery design](ACQUISITION_RECOVERY_NOV11.md) and [explicit recovery index](../records/recoveries/raw-http-responses-v1.json).
- [Fabric reviewer validation](../records/validation/2026-11-11-fabric-reviewer/verified-r02/verification.json).
- [Geometry editor validation](../records/validation/2026-11-11-geometry-editor/final/verification.json).
- [Compact-layout validation](../records/validation/2026-11-11-compact-layout/independent-review/review.json).
- [Station-v9 saved-image HTTP check](../records/validation/2026-11-11-station-v9-http.json).

The failed background acquisition remains a completed zero-photo attempt. The source originals, assignments, historical acquisition records, old packages, thesis figures and earlier screenshots remain intact. No dependency was installed. All owned test servers were stopped.

## Work that follows

1. Human/groupmate review of the 17 fabric originals and available geometry images; independently reconcile observations before any new label release.
2. Resolve fabric semantics, material-to-skirt association, grouping and source rights; acquire suitable rare-class and hard-negative groups.
3. Predeclare and evaluate improved detection/fabric candidates on appropriate data, preserving frozen source/test partitions and separate coverage/error measures.
4. Obtain actual skirts, webcam and Pi. Validate wearer extraction, measure calibration, test unseen garments and verify the ARM64 runtime, display/touch and sustained live operation.

Completing these software tasks does not complete S01–S07 or physical acceptance. The next immediate action is human review using the completed tools.
