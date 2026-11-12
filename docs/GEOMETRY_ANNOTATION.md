# Saved image geometry annotation

The [offline editor builder](../tools/geometry_annotation.py) prepares one complete saved original for a reviewer to mark visible waist, skirt hem and foot/floor contact bands. It needs no camera or running server. The browser downloads a **pending draft**; it does not modify labels, splits, models, calibration or the source image.

This closes the missing annotation-interface task R03. Independent reviewed geometry, measured calibration and automatic wearer detection remain separate unfinished tasks.

## Build and open an editor

Run from the project root in PowerShell using the existing bundled interpreter. The following example selects an existing development-validation inventory member; it does not make an observation or confirm that the references are visible in that image:

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B tools/geometry_annotation.py build --sample-id fashionpedia-train2020-12679 --output output/geometry-review/12679.html
Start-Process 'output/geometry-review/12679.html'
```

The default inventory is [the frozen readiness mapping](../records/geometry/2026-10-21-readiness/frozen-inventory.json), which contains 66 development-validation members. The builder deliberately rejects training, calibration, final-test and protected source roles. A different compatible inventory requires explicit `--inventory` and `--source-root` arguments; the tool validates all supplied group and image-hash assignments before opening a selected original. It does not create or change assignments.

The output file must be new. If one exists, retain it and choose another filename. The generated HTML embeds a complete EXIF-oriented RGB rendering of the original and works offline. That rendering is for display; the draft stays bound to the immutable original file hash and its oriented source dimensions. No resize or cropped coordinate system is substituted. The generated HTML contains a photograph: retain its original source attribution/terms and do not redistribute it without an applicable basis.

## Record an observation

1. View the complete original, including the wearer/garment association. Do not substitute a model output or a remembered label for what is visible.
2. Choose the reference: visible waist, skirt hem, or visible foot/floor contact. Drag vertically across the uncertainty band. The numeric low/high controls provide an alternative; values are source-image y coordinates, with zero at the top and the last row at `height - 1`.
3. For a reference outside the frame or occluded, select **Hidden or outside frame**. For an ambiguous reference, select **Uncertain or not established**. Both choices clear its interval. Do not infer a visible waist from hip keypoints or visible foot-floor contact from an ankle point. Marking an unknown reference is a useful observation, not a failure to complete the form.
4. Enter the actual reviewer name/type, observation date, and a short account of visible evidence and limitations. The date defaults to the browser's local date and can be corrected. Identity is self-reported, not authenticated. Confirm that you viewed the complete original.
5. Select **Download pending draft**. Keep the downloaded JSON in a new reviewer-specific location. The editor performs no automatic upload, save into the project event log, or admission. Changing a draft later is a new review version, not permission to overwrite prior evidence.

Dragging a band disables download until the gesture finishes. Cancelled gestures restore the previous band; they do not silently retain a partial mark. Numeric intervals must be finite, ordered and inside the oriented source frame. Hidden/uncertain references have null intervals. All three references start uncertain; no coordinates are prefilled as truth.

## Validate the downloaded draft

Use the actual download path:

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B tools/geometry_annotation.py validate --draft 'C:/Users/Administrator/Downloads/geometry-draft-fashionpedia-train2020-12679.json'
```

Validation reopens the original and frozen inventory, checks their hashes and source dimensions, enforces exact draft fields and requires the reviewer/date/evidence/attestation. Extra approval or guessed camera identity fields are rejected. A successful result is `valid_pending_draft`, with `reviewed=false`, `evaluator_approved=false` and `physical_calibration_verified=false`. It verifies structure and lineage, not the scientific correctness of a person's marks. Keep the original images and exact inventory available for subsequent validation; even a whitespace change to the inventory changes its hash.

## Independent reconciliation before evaluation

Drafts are deliberately incompatible with the evaluator's reviewed observation document. They contain no invented camera, rectification, reference, frame or person identifiers. Before a separate versioned annotation release, an independent reviewer must resolve band disagreements, actual wearer/garment association, visibility, source rights and all required geometry quality flags. Supply credible camera/reference/person/frame and projection evidence. An internet image cannot be declared rectified or physically calibrated merely because the editor displays it upright.

The [geometry evaluator](WORN_GEOMETRY_EVALUATION.md) requires reviewed observed annotations with documented identities and `upright_rectified_vertical` projection. It can retain unknown/unsupported examples as exclusions; do not drop them to inflate coverage. This editor does not auto-convert drafts into that approved document or generate calibration boundaries. The [measured calibration builder](MEASURED_CALIBRATION.md) uses its own separate calibration groups and evidence; the validation-only inventory here cannot be moved into that pool.

## Verification and limits

Fourteen focused Python tests pass for hash changes, EXIF dimensions, protected/training exclusions, cross-split grouping, source-bound intervals, explicit unknowns, required evidence, approval rejection, script-escape safety and output overwrite protection. The Edge browser roundtrip exercises real scaled-canvas pointer coordinates, numeric entry, cancellation rollback, export blocking during a gesture, an explicit observation date and hidden-floor export. Its download passes the Python validator and makes zero external network requests.

All verification uses synthetic temporary originals and agent identities, producing **zero production observations**. The previous browser evidence is preserved; [the final browser report](../records/validation/2026-11-11-geometry-editor/final/browser.json) and [source-bound verification record](../records/validation/2026-11-11-geometry-editor/final/verification.json) document the completed tests. No new dependency was installed and no server remains running.

To repeat software checks while preserving existing artifacts:

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -m unittest tests.test_geometry_annotation -v
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' tests/geometry_annotation_browser.cjs records/validation/geometry-browser-NEW-VERSION
```

The browser command requires the already installed bundled Playwright and Microsoft Edge; it refuses existing browser artifact filenames. Replace the output folder with a fresh version rather than overwriting evidence.
