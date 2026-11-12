# Dataset intake and rejection diagnostic — October 11, 2026

There are now **1,627 original images**, verified by file hashes, decoded pixels and dimensions. No new images were admitted to training, no original protected partition was reassigned, and no model weights or thresholds changed. No dependencies were installed and no camera was activated in this work.

| Pool | Originals | Current use |
|---|---:|---|
| Fashionpedia skirt candidates | 1,000 | Existing development pool; frozen pleating pilot remains 292 train / 80 validation |
| FabNet texture candidates | 500 | Supplementary, not verified full-view fabric truth |
| Protected Fashionpedia seeds | 12 | Original holdout preserved |
| New Fashionpedia non-skirt candidates | 90 | Unadmitted development diagnostics: 30 pants, 30 shorts, 30 dresses |
| New DeepFashion-MultiModal candidates | 25 | Original train partition only; appearance/visibility review pending |

The [combined audit](../records/validation/2026-10-11-combined-intake-audit.json) decoded all 1,627 images with zero integrity errors and found 1,627 unique file hashes and decoded-pixel hashes. These are image counts, not verified independent physical garments. Two new perceptual-hash matches connect negative candidate 1632 to existing skirt images 1796 and 7330. Similar runway backgrounds and silhouettes are visible; these matches do not prove identical garments. Keep grouping unresolved until reviewed, rather than silently assigning new train/validation membership.

## Fabric source partition resolved

The official original InShop partition file downloaded successfully on October 11, superseding the prior quota-exceeded attempt. Its SHA-256 is `cfada103c44df866db5e2ee9ecc2301ca691a4d0cdb3c875fe4051b62570894c`. All 848 skirt annotation filenames matched exactly: **367 train, 224 query, 257 gallery**. There is no train/test source-item overlap. Query and gallery are retrieval test partitions and may share items; neither was used for this intake. [Partition join and source evidence](../records/review/2026-10-11-fabric-partition.json).

The 367 training rows contain 336 cotton-labelled, 20 denim, six leather and five chiffon images. Knitted and other-labelled skirt candidates occur only outside the original training subset. Do not move them into training to fill class gaps.

The new ZIP64 reader retrieves exact bounded byte ranges, checks directory/member bounds, headers, names, compression, decompression limits and CRC, and refuses unsupported/encrypted/path-unsafe entries. The [actual intake](../records/acquisitions/2026-10-11-fullview-fabric/report.json) retrieved **25 images from 25 source item IDs**: cotton-labelled 10, denim 9, leather 3 and chiffon 3. Selecting at most one image per source item prevented repeated views from inflating this sample; source item identity still does not verify a physical specimen. This bounded pilot did not download the whole 6.82 GB archive.

These source annotations describe visual appearance, not garment-tag fiber composition. Full skirt framing and label suitability remain unapproved. The contact sheet was inspected, and an apparent shorts/skirt ambiguity in item `id_00004335` was resolved by opening the original: it shows a continuous denim skirt hem. Some other waistbands are hidden by tops, and a seated example changes visible geometry. [Visual observations](../records/review/2026-10-11-intake-visual.json). This source is limited to non-commercial research and internal copying; retained originals are not a redistribution bundle.

## Non-skirt diagnostic

[Ninety original train2020 candidates](../records/acquisitions/2026-10-11-negatives.json) were selected deterministically from source pants, shorts and dress annotations, with no annotated skirt and no existing candidate IDs/hashes. Annotation absence does not prove skirt absence. Thumbnail review found cropped/occluded figures and background people, so no certified negative labels were created. Four source rights entries are all-rights-reserved/not-found; preserve those rights uncertainties before any training admission.

The unchanged experimental localizer produced a provisional ROI on **40/90 candidates (44.44%)**. It rejected 41 for multiple regions and nine for frame-edge contact. [Per-image diagnostic](../records/validation/2026-10-11-negative-diagnostic.json). This is candidate acceptance, not a final false-acceptance accuracy estimate. It demonstrates why the current localizer remains opt-in and why a connected component cannot be treated as evidence that a skirt is present. The uniform-image checks from October 10 were insufficient as a rejection evaluation.

## Verification and next implementation

Forty-four targeted tests passed across ZIP/ZIP64, dataset intake, source-partition selection and existing archive/data contracts. [Test log](../records/validation/2026-10-11-data-tests.log). The frozen pleating and localization models were not retrained or promoted; existing UI and Pi acceptance status remains unchanged.

Next: review full originals for negative truth and garment/source grouping; quarantine ambiguous labels and rights; create a versioned grouped development manifest for presence/localization training; train and compare a model that includes negative examples against the archived 80-image skirt evaluation and a separate negative validation pool. Preserve a future independent test pool. For fabric, review waist-to-hem visibility and source-label consistency, settle an appearance-only experiment vocabulary, and expand eligible source training coverage before attempting a defensible classifier. Physical calibration and Pi benchmarks still require the actual setup.
