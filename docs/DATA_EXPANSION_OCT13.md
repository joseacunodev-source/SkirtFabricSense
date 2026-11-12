# Data expansion recovery — October 13, 2026

The interrupted acquisition work is now reconciled. The collection contains **1,747 original images**, all decoded and hash-checked: 1,000 Fashionpedia skirt candidates, 500 supplementary texture candidates, 12 protected seeds, 210 non-skirt candidates and 25 full-view fabric candidates. File and decoded-pixel hashes are unique; that does not establish 1,747 independent garments.

## Completed negative intake

Acquired **120 new original train2020 images**, balanced by source-selection category: 40 pants, 40 shorts and 40 dresses. Total image bytes: 8,955,830. The manifest preserves source URLs, exact source licence metadata, annotations, grouping keys and hashes. These are candidates, not certified no-skirt labels. No training split or admission was assigned.

The recovery fixed protected-seed identity handling, canonical Flickr photo identifiers, licence-name/URL consistency, predecode pixel bounds and balanced sampling after filtering. The initial failed launch is retained in the execution record. No package installation occurred.

Root inspected all four contact sheets, covering 120 thumbnails. Ambiguous lower garments and possible shared sessions were flagged, including a shorts annotation that visually resembles a skirt. No full-original approval is inferred. Group review must consider the visual flags as well as automated hashes.

- [Acquisition and actual counts](../records/acquisitions/2026-10-13-negatives-v2/report.json)
- [Root visual triage](../records/review/2026-10-13-root-negative-v2-triage.json)
- [Negative expansion details](NEGATIVE_EXPANSION_V2.md)
- [Independent code and source review](EXPANSION_REVIEW_OCT13.md)

## Fabric attempt and source limit

The source-partition assessment selected 30 unused cotton-labelled training items from 106 available groups. The remote archive attempt made no observable image progress and was stopped. **Zero new fabric images** were downloaded; there is no v2 fabric manifest. The exact network cause was not established. The [attempt record](../records/acquisitions/2026-10-13-fabric-v2/report.json) preserves that outcome separately from successful acquisition.

All available original-training denim, leather and chiffon groups from this source are already represented in the earlier 25-image intake. Further cotton images would not fix rare-class coverage. Do not import protected query/gallery groups or count alternate views as new garments. [Fabric expansion status](FABRIC_EXPANSION_V2.md).

## Validation and next work

The [combined audit](../records/validation/2026-10-13-expansion-v2-audit.json) decoded all 1,747 originals with zero integrity errors and found four new perceptual near-match pairs, all among isolated shorts product photographs. They are similarity candidates rather than proof of a shared garment. Visual session flags include relationships the perceptual audit did not detect. All new images remain unadmitted pending original-image, grouping and label review.

Root reran **39 targeted data/archive tests**, all passing. [Test log](../records/validation/2026-10-13-expansion-tests.log). Independent review also found no canonical-source or exact-file overlap between the new 120 and the prior 1,627 originals.

Next: review all proposed negative admissions at full resolution, resolve session/garment groups and ambiguity, then freeze a grouped extension without altering existing validation assignments. Train only after that admission gate. Fabric needs another suitable source of rare-class groups or labelled physical garments. The failed presence candidate and tiny fabric smoke remain disabled in the live app; no app, model, camera or Pi behavior changed in this step.
