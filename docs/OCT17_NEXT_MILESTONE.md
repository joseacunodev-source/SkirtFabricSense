# Completed presentation review and optional attribute research

October 17, 2026. User asked to proceed with the remaining presentation reviews, rejection improvement, fabric/wearer detection, calibration and physical testing. This milestone completes the available visual review and adds executable research integration. Actual garments and Raspberry Pi remain unavailable according to the last user confirmation; no new physical test was performed.

## Presentation review completed

All 360 pending samples now have explicit visual observations, combined with the earlier twelve. Agents viewed thirty full-frame inspection sheets. Ten individual originals were subsequently opened: all six ambiguous product views and four hanging/mannequin spot checks. Root independently checked two sheets and flagged a suspected source-label error for future review. The final overlay has 22 direct-original reviews and 350 sheet reviews; these methods remain distinct.

| Presentation | Training | Development validation | Total |
|---|---:|---:|---:|
| Worn | 265 | 66 | 331 |
| Hanging | 19 | 8 | 27 |
| Mannequin | 4 | 4 | 8 |
| Unknown isolated product presentation | 4 | 2 | 6 |
| Total | 292 | 80 | 372 |

There are zero unreviewed records, while six presentations remain uncertain after original inspection. These are single-agent observations, not independent human truth. Visibility flags do not establish calibration suitability. No related group or existing frozen split moved.

- [Complete hash-bound audit](../records/review/2026-10-17-presentation-complete-audit.json)
- [Merged observations](../records/review/2026-10-17-presentation-complete.jsonl) and [merge provenance](../records/review/2026-10-17-presentation-complete.sources.json)
- [Frozen worn development subset](../data/manifests/worn-pleating-development-v1.jsonl), [exclusions/provenance](../data/manifests/worn-pleating-development-v1.json)
- [Root source-label flag](../records/review/2026-10-17-root-presentation-qa.json)

Subset joins of the archived outputs yield v1:41/66 accepted,33 correct; v2:50 accepted,44 correct; v3:46 accepted,38 correct. These are development subsets from models selected on the broader mixed pool, not independent worn-camera accuracy. They do not override negative-rejection failures. Reproduce with `python tools/check_worn_subset.py --output NEW_JSON`. [Evidence](../records/validation/2026-10-17-worn-subset-reproduced.json).

## Rejection experiment completed without promotion

Presence v2 uses the reviewed56 negative training/19 validation examples with the unchanged292/80 positive pool. Seed42, ten epochs, frozen MobileNetV2 backbone and class-balanced loss/selection are preserved from v1; only the expanded reviewed negative manifest changes. The selected checkpoint is epoch2. Float export has maximum absolute difference3.09944e-6 against tolerance0.001.

The combined path rejects15/19 negatives versus10/19 for the unchanged localizer, but accepted skirts fall48/80 to27/80 and correct pleating38 to20. This is unacceptable loss of coverage, so presence v2 stays disabled by default. No threshold tuning or final-test use occurred. [Paired results](../records/validation/2026-10-17-presence-v2-comparison.json), [model/run/source/environment record](../records/models/2026-10-17-skirt-presence-v2.json).

## Optional fabric and body-keypoint paths implemented

`--experimental-fabric artifacts/models/fabric-smoke-v1` requires `--experimental-localizer`. It uses the same original frame and unexpanded automatic skirt ROI. The switch skips inference when off. Output is explicitly `research_only`, preserves `source_*_appearance` names, and reports unverified composition/approval. Fabric failure preserves pleating. This is an opt-in research connection, not promotion of the17-group pilot. The default application still reports fabric unavailable. [Contract, actual five-image comparison and launch example](FABRIC_AUTOMATIC_EVALUATION.md).

The actual fabric comparison is4/5 manual-ROI correct, versus4/5 automatic availability and3/5 correct overall. This tiny source-domain result is insufficient for demonstration accuracy or a composition claim. More suitable independent source groups and camera-domain data are still needed.

`--experimental-pose artifacts/models/movenet-lightning-f16-v4` supplies same-frame body-keypoint candidates only in worn mode. The official downloaded model has been hash-checked, its input/output inspected and six saved training images invoked through the adapter. Independent review corrected a half-pixel coordinate offset and added loader-contract tests. All keypoints remain `observed=false` and `geometry_eligible=false`: model scores cannot prove visibility, single-person scene, wearer association, waistband position or foot-floor contact. Hips are not relabelled as waist; ankles are not floor. [Corrected runtime check](../records/validation/2026-10-17-pose-candidates-corrected.json), [model/terms record](../records/models/2026-10-17-movenet-candidates.json).

Publisher reference: [TensorFlow MoveNet tutorial](https://www.tensorflow.org/hub/tutorials/movenet). Exact float16-v4 publisher model card and Apache-2.0 terms are preserved with their immutable source commit and content hash. No package was installed. Pose and fabric model files remain separate from the application bundle.

## Calibration preparation

The [measured calibration builder](MEASURED_CALIBRATION.md) derives eight boundaries only from reviewed nine-class development measurements with strict frame/reference association, conservative uncertainty and declared calibration-group isolation. It supplies no default anatomical proportions. It cannot produce a real calibrated station without measured observations. All successful test profiles are temporary synthetic fixtures.

## Package and verification

Research-v7 contains17 payload files and the unchanged selected pleating model. Inventory SHA-256: `0128196438e5b3fb61ba2bab224b351b3de9e9b1e6eb50a171711804bc231eb5`. The default saved-frame HTTP check matches all three archived outputs. Optional research HTTP checks verify fabric on/off, unchanged pleating, same-frame pose/fabric identities, secondary-mode pose skipping and unavailable length. Both private servers were stopped and bundle inventories passed again.

- [Default HTTP evidence](../records/validation/2026-10-17-v7-default-http.json)
- [Optional research HTTP evidence](../records/validation/2026-10-17-v7-research-http.json)
- [338-test desktop run, one TensorFlow-specific skip](../records/validation/2026-10-17-next-milestone-tests.log); fourteen mocked camera lifecycle scenarios also passed.

No package installation, webcam activation, real calibration or Pi test occurred. Saved-image HTTP checks do not prove browser acquisition-age performance, recognition quality or ARM64 compatibility.

## Remaining work

The360-review task is complete. Better usable non-skirt rejection remains unresolved despite the new experiment. Fabric remains a research pilot requiring more independent groups/label evidence. Actual wearer/waist/foot-contact and hem-contour validation, measured calibration, unseen-garment checks and real Pi installation/performance/recovery remain open. Additional software work can proceed on source diversity and reference validation, but physical acceptance needs actual materials.

## Post-review calibration provenance fix

Independent review required exact source-image bindings for measured annotations. Calibration examples and frozen assignments now require matching canonical source paths and SHA-256 hashes; file builds verify original bytes under the declared source root before output creation. [Fourteen focused tests passed after this fix](../records/validation/2026-10-17-calibration-provenance-tests.log), including source replacement, traversal and mismatched identity. No real profile was generated. The earlier338-test run remains dated before this tool-only fix; the application bundle and its HTTP evidence are unchanged.
