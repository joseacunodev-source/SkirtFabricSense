# Recovered data and presence improvement — October 19, 2026

The selected presence-v4 export passes the relative development criteria when combined with localizer v2. The saved-frame application check also passes. This is an optional research configuration; deployment defaults and the immutable research-v7 bundle are unchanged. Fabric quality, actual wearer geometry, measured calibration and real-garment/Pi acceptance remain open.

## Completed data work

All 180 newly acquired negative originals received original-image review. Conservative ambiguity, near-match and recurring-session exclusions leave 132 new admissions. The frozen extension contains 390 records, 207 admitted: 155 training and 52 validation. All earlier 210 records and split assignments are preserved. Raw acquisition candidates remain separate from curated admissions. [Preparation](NEGATIVE_EXPANSION_V3.md), [admission audit](../records/validation/2026-10-18-negative-v3-admission-audit.json).

The full pool contains **1,932 original images**: 1,000 skirt-source candidates, 500 texture candidates, 390 non-skirt candidates, 25 earlier full-view fabric candidates, five new composition-source pilot originals and 12 protected seeds. All decode and have unique file and decoded-pixel hashes; zero integrity errors. The 34 perceptual near-match pairs remain candidate relationships, not proof of garment identity. None involves the five new pilot photos. No count of verified physical specimens is available. [Combined audit](../records/validation/2026-10-18-combined-intake-audit.json).

Source follow-up checked six uncertain originals against their exact annotations. In particular, sample 34099 is annotated wrap/skirt by the source; a visual suspicion is insufficient to relabel it as a negative. Frozen historical labels remain unchanged and independent confirmation is pending. [Review](SOURCE_LABEL_FOLLOWUP.md).

## Presence experiments and actual exports

Both runs use the same 420 training images (265 worn skirts, 155 negatives) and 118 validation images (66 worn skirts, 52 negatives), seed 42 and fixed 0.5 thresholds. They train a MobileNetV2 presence model for three head epochs and five upper-backbone epochs, freezing BatchNormalization. Every frozen-layer invariant and early/final export parity check passes.

V3 selects epoch 7 by balanced validation BCE. Its stronger rejection loses skirt coverage, so it remains unpromoted. V4 changes checkpoint selection to the prespecified complete-chain criteria, then ranks eligible epochs by rejection, correct pleating, coverage and BCE. It selects epoch 5; no fallback is used. The data and optimization sequence stay fixed, but deterministic execution across runs is not established merely by the shared seed. [V3 review](PRESENCE_V3_RESULTS.md), [V4 protocol](PRESENCE_JOINT_SELECTION_PROTOCOL.md).

| Actual exported path | Accepted skirts / 66 | Correct pleating / 66 | Rejected negatives / 52 |
|---|---:|---:|---:|
| Localizer v1 baseline | 41 | 33 | 29 |
| Localizer v2 | 50 | 44 | 21 |
| Localizer v2 + presence v3 | 39 | 33 | 42 |
| Localizer v2 + presence v4 | **44** | **38** | **39** |

V4 improves the baseline by three accepted skirts, five correct pleating results and ten rejected negatives on these reused development groups. It still rejects 22/66 source-domain skirt examples, misclassifies six accepted skirts, and accepts 13/52 negatives. Its 86.36% accuracy among accepted skirts must be accompanied by its 66.67% coverage; neither is overall project completion or public-use accuracy. [Actual 118-image comparison](../records/validation/2026-10-19-detection-v4-comparison.json). The [failure review](PRESENCE_V4_FAILURE_REVIEW.md) preserves individual gains/regressions, category counts and visual observations.

V4 float TFLite SHA256 is `7bf9df9b1bacc757956c069f688345ff154ee480a65198ee5948fbe80bbcdb87`, 9,186,664 bytes. All 118 validation outputs match Keras within 0.001; maximum absolute difference is 0.0000046492. An independent review reran every validation original through saved Keras and TFLite, passing 71 checks with maximum error 0.0000039935. [Detailed results](PRESENCE_V4_RESULTS.md), [archived run](../records/experiments/20261018-presence-v4/run.json), [archive integrity](../records/validation/2026-10-18-presence-v4-archive.json). Training occurred October 18; export-chain and HTTP verification occurred October 19.

Checkpoint selection reuses development outcomes already used to motivate the follow-up. This introduces selection optimism. No locked final test or camera-domain measurement was used, and no promotion to an accepted product is implied.

## Fabric-source recovery

The interrupted selective archive parser is repaired and its failed report preserved. A CRC-verified index identifies 2,066 independent Copy streams and 25 exact skirt-metadata filename joins in the Trondheim archive. Five predeclared JPEG originals were selectively acquired in five exact HTTP 206 responses totaling 19,643,287 body bytes. No full archive or new package was downloaded. [Archive evidence](FABRIC_ARCHIVE_INDEX.md).

Actual photo review finds two contained flat-laid skirt candidates, one dress conflicting with its source skirt category, one bunched garment and one clipped at the image edge. All five remain unadmitted with null splits; none is worn. Publisher care-label transcriptions retain blends/layers and are not converted into appearance labels or independently verified fibre composition. Preserve source attribution and CC BY-SA4.0 terms. [Pilot and rights](NPCGI_PILOT.md). A second independent agent inspected all five originals and passed 111 integrity/lineage checks. [Review](../records/validation/2026-10-19-npcgi-pilot-independent-review.json).

This resolves selective acquisition feasibility, not the worn-domain fabric-data gap. More flat-laid images alone cannot establish full-skirt live fabric performance.

## Application and verification

The HTTP checker now explicitly validates model identities, fixed thresholds, source hashes, ROI, scores, labels and attribute states; mismatches fail even under Python optimization. Two accepted positive frames and one gated negative reproduce the desktop comparison. The private test server stops afterward, and the 17-file research-v7 bundle verifies before and after. Fabric is disabled and calibrated length remains unavailable in these three checks. [HTTP evidence](../records/validation/2026-10-19-presence-v4-http.json). No camera was activated.

The complete bundled-Windows suite ran 418 tests, with 416 passing and two TensorFlow-specific skips. [Log](../records/validation/2026-10-19-tests.log). All 34 focused training/selection/HTTP checks passed in WSL, including the actual Keras freeze configuration. [Training-environment log](../records/validation/2026-10-19-training-tests.log). The other Windows skip is the existing localizer scene-loss framework check, which this batch does not change. No dependencies were installed or changed in this batch; each run preserves its environment snapshot.

## Next acceptance work

Continue independent label confirmation and camera-domain negative diversity; do not replace missing empty-scene/real-garment evidence with repeated catalog samples. Fabric needs an operational label vocabulary and credible worn examples before a stronger candidate is justified. Wearer/skirt association, visible waistband/floor references and hem uncertainty still need annotated development validation. Measured calibration, real-camera evaluation, held-out garments, ARM64 installation/benchmarking and a supervised rehearsal require the missing physical materials. See the [active task board](TASK_BOARD.md).
