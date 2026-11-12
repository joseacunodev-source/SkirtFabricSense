# Completed recovery and continuation checkpoint — October 22, 2026

Historical recovery checkpoint: a later October22 batch selects station-v3 after a camera status fix and adds fabric-source identity/terms evidence. [Current batch](CAMERA_SOURCE_UPDATE_OCT22.md), [current handoff](AGENT_HANDOFF.md). The results below preserve the earlier v2 selection.

The October 20–21 interrupted software work is reconciled. Station-v2 is selected for **desktop research only**, with station-v1 preserved for rollback. Public demonstration, fabric quality, calibrated length and Raspberry Pi acceptance remain open. Another agent should start at [the handoff](AGENT_HANDOFF.md), [current checkpoint](../records/continuation/latest.json) and [task board](TASK_BOARD.md).

## Detection experiment

The October 21 category-aware run uses the same 538 frozen originals and fixed 0.5 threshold as v4. It adds publisher-supervised pants/shorts/dress scene targets while preserving source groups, partitions and all previous labels. Epoch7 is selected by the declared complete-chain rule. Sources, environment, targets, all eight epochs' probabilities and both Keras models/scalar TFLite are archived. No October 20 fitting run existed; that date's successful checks were export-only tests.

| Actual exported path | Accepted skirts /66 | Correct pleating /66 | Rejected negatives /52 |
|---|---:|---:|---:|
| Previous v4 path | 44 | 38 | 39 |
| Category-aware path | 44 | 38 | 42 |

The new path preserves aggregate skirt results and rejects three additional negatives. Individual cases change: four earlier negative errors are repaired, one new false accept appears, and nine remain. Positive coverage exchanges three gains for three losses. All denominators are retained. Ten negatives still receive skirt results and 22 skirt examples remain unavailable; this is not accepted camera-domain performance. [Detailed results](CATEGORY_PRESENCE_RESULTS.md), [actual comparison](../records/validation/2026-10-21-category-presence-comparison.json).

Independent review passed 115 checks, rehashed all 538 originals, replayed all 8×118 epoch probability records and reopened four-way Keras, scalar Keras and scalar TFLite on all 118 validation originals. Maximum scalar Keras/TFLite difference was 0.0000042319 against 0.001 tolerance. Scalar TFLite SHA256: `f47ddf148102f905d0a81e6a1fe3001b8a4944fd86e0c1c2d635d975f8fdc34d`. [Executable audit and evidence](../records/validation/2026-10-21-category-presence-artifact-review.json).

The archived run retains an inherited lineage sentence saying the cache lacks an explicit pleating hash. Its actual cache includes that hash and the independent audit verified it. Future source now verifies any explicit hash and records the correct basis; the immutable executed source/run was not rewritten. Regression tests cover matching and mismatched explicit identities. The original failed export-test harness is preserved separately from its corrected strict-FP32 result; tolerance was not relaxed.

## Portable application

Both packages contain28 inventoried payload files and the unchanged17-file research-v7 app. Station-v2 includes the category-aware gate, localizer-v2, pleating fine-tune v1 and the opt-in fabric smoke model. It includes no dataset photographs, dependency installer or calibration profile. [Launch and rollback instructions](STATION_PACKAGE.md).

Each package passed 12 actual saved-frame HTTP jobs: two accepted skirt examples and one gated negative, fabric off/on, with research fabric unloaded/loaded. Exact bundled HTML, model identities, ROI, labels and scores matched references. Length stayed unavailable, toggling fabric preserved style, both owned servers stopped and each inventory stayed unchanged. This tests direct server arguments produced by the verified launcher; wrapper-process shutdown was not separately measured. [Station-v1 evidence](../records/validation/2026-10-21-station-http.json), [station-v2 evidence](../records/validation/2026-10-21-station-v2-http.json).

Packaging review found and fixed two issues before these packages were built: static assets needed `--root application`, and output inside an immutable input directory had to be refused. The detection HTTP checker now also serves/checks the exact immutable bundled page. No application source or previous bundle was altered.

## Geometry and fabric preparation

The new [geometry evaluator](WORN_GEOMETRY_EVALUATION.md) replays hash-bound saved wearer/mask evidence against reviewed intervals. Its19 focused tests cover source/group/frame identity, observation semantics, exclusions, abstentions and interval discrepancies. The actual readiness mapping preserves331 source identities and splits, but has **zero observed geometry examples**, null coverage and 66 unannotated validation members. It runs no detector, supplies no anatomy and enables no live length. [Readiness evidence](../records/validation/2026-10-21-geometry-readiness.json).

The existing1,000-image Fashionpedia audit found no defensible expansion of the desired fabric classes; manufacturing/pattern labels were not converted into fabric truth. A bounded primary-source search saved15 public metadata responses totaling497,928 body bytes, including one observedHTTP403. It acquired zero garment images and admitted zero labels. iMaterialist2018 is the best next metadata lead, with photo terms, product grouping and skirt-specific material association unresolved. TextileNet's paper/README licence wording is preserved accurately; FashionGen's403 is not proof of a login requirement. [Existing-source audit](FABRIC_SOURCE_ATTRIBUTE_AUDIT_OCT20.md), [source search and next gate](FABRIC_SOURCE_SEARCH_OCT21.md).

Original image count remains **1,932**. Verified project fabric labels remain zero; no physical garment count is established. No training/test split or protected sample changed.

## Checks and continuation

The October 22 full Windows suite ran 464 tests:461 passed, three framework-dependent skips. The separate October 21 WSL suite passed 20 actual-framework checks. No new GPU fitting was needed for documentation or cache-provenance fixes. [Full log](../records/validation/2026-10-22-tests.log), [WSL log](../records/validation/2026-10-21-wsl-tests.log).

No dependencies were installed or changed. Each experiment preserves its own training environment snapshot; an ARM64 runtime/lock remains unverified. The user last reconfirmed neither actual skirts nor Pi on October 20.

AGENTS.md, README and root HANDOFF.md now route to the same documentation index, human-readable handoff and hash-bound machine checkpoint. `tools/validate_records.py` checks continuation evidence references as well as project records. Next: resolve the new fabric source's terms/grouping/material association before a bounded image intake; obtain actual garments and Pi for the remaining physical gates. Repeating fits on the reused development set cannot replace those inputs.
