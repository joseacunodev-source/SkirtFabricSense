# Dataset catalogue and collection plan

November 11 recovery: the completed zero-photo Commons attempt is reconciled through [typed failed-response evidence](ACQUISITION_RECOVERY_NOV11.md). Original bodies/hashes remain intact. Collection remains1,932 originals; no images, labels, admissions or frozen splits changed. The new reviewer tools have zero production observations.

November 4: the [per-model partition audit](DATASET_PARTITION_EVIDENCE.md) and [dataset figures](THESIS_DATASET_DIAGRAMS.md) clarify actual memberships. Collection remains 1,932 originals; no acquisition, admission, label or split changed.

November 4 reconciliation: collection remains 1,932 registered originals. October 23 fabric queue preparation added zero labels/observations; COCO attempts added zero photographs after transport failures. Commons acquisition code is present but no completed acquisition record exists. [Fabric queue](FABRIC_EVIDENCE_REVIEW.md), [November 4 purchase/project review](PURCHASE_REVIEW_NOV04.md).

Later October22: audited 155,393 cached TextileNet URL rows against the official Git blob, with 147,712 distinct exact URLs and 5,223 repeated URL groups. This adds no original photos, skirt labels or admissions; collection remains 1,932 originals. Original-source partitions and garment/material association remain unresolved. The actual 2018 rules were read, but not accepted. [Current gate and reproducible auditor](FABRIC_SOURCE_GATE_OCT22.md).

October22: collection remains **1,932 originals**, with unchanged frozen groups/partitions and zero new training admissions. The category experiment derives publisher-supervised scene targets for the same538 originals; these are not independently confirmed physical garment labels. Existing Fashionpedia fabric attributes were audited and new source metadata researched (497,928 direct-response bytes, zero garment photos). iMaterialist2018 photo terms, item grouping and skirt-specific material association remain unresolved. Geometry inventory mapping adds zero observed annotations. [Source search](FABRIC_SOURCE_SEARCH_OCT21.md), [category results](CATEGORY_PRESENCE_RESULTS.md), [current registry](../data/registry.json).

October19: **1,932 originals** are hash/decode audited, with no exact/pixel duplicates or integrity errors. The180 newly reviewed negative candidates yield132 new admissions; the frozen negative extension has207 admitted examples (155training/52validation), preserving all previous210 records/assignments. Five new NTNU composition-source photos contain two full-view flat-laid skirt candidates and three visual exclusions; all five remain unadmitted, zero worn examples and zero verified fabric labels. No new physical specimen count is established. [Recovery evidence](OCT19_RECOVERY.md), [new source rights and photo review](NPCGI_PILOT.md). Dated counts below are historical.

October 17 complete review: all372 pilot samples have supplemental presentation observations, comprising331 worn/27 hanging/8 mannequin/6 unknown. A versioned worn development subset preserves265training/66validation and excludes41 other/unknown presentations without moving existing groups/splits. Originals remain1,747; no new specimens or verified composition labels. [Evidence](OCT17_NEXT_MILESTONE.md).

October 17: registered supplemental presentation reviews, with no image-count, admission or split changes. Twelve of 372 pleating originals are explicitly reviewed as worn; 360 remain unknown. All 17 fabric smoke originals are reviewed as worn. Physical garment identity/composition and calibrated geometry remain unverified. [Worn audit](WORN_DATA_AUDIT.md), [fabric review](FABRIC_NEXT_GATE.md).

October15: image count remains1,747. New official fine-attribute metadata has680 skirt references, but original membership is422train/66validation/192test. Metadata inspection exposed broader-holdout annotation rows; none were used for training or evaluation. All422 original-train references have unresolved descriptive-folder overlap with original holdouts, leaving zero eligible under the conservative grouping policy. No new photographs acquired or admitted. [Source feasibility](ATTRIBUTE_SOURCE_FEASIBILITY.md).

October14 admission update: all120 new originals received agent original-image review;63 are admitted after conservative ambiguity/session/near-match exclusions. The combined negative pilot contains75 admitted examples,56training/19validation, with every earlier assignment preserved. Total originals remain1,747. No independent human truth or verified garment identity is claimed. [Extension and run](LOCALIZER_V2_RESULTS.md).

October 14 reconciliation: **1,747 originals** are manifested and audited with unique file/pixel hashes and zero decode/integrity errors. October 13 added 120 source-selected negatives (40 pants, 40 shorts, 40 dresses); all remain unadmitted. The non-skirt candidate pool is now 210; full-view fabric remains 25 because its latest attempt downloaded zero images. Four new perceptual near-match pairs and visual session/ambiguity flags require review before splitting. [Intake evidence](DATA_EXPANSION_OCT13.md). Historical counts below apply only to their stated dates.

October 12: original count remains 1,627. Negative review admits 12 of 90 (9 training / 3 development validation) and quarantines 78. Fabric review admits 17 of 25 source items (12/5) for an internal appearance pipeline smoke only. All admitted source images and groups retain original source partitions, rights evidence and hashes in the registry; no protected test examples moved into training. Neither admission establishes human-confirmed ground truth, fiber composition or independent physical garment identity. [Negative review](NEGATIVE_REVIEW.md), [fabric pilot](FABRIC_PILOT.md), [current integration](OCT12_INTEGRATION.md). Older dated entries are historical.

Updated 2026-10-02 (Asia/Manila). This is an engineering acquisition record, not a claim that model training has started. The machine-readable catalogue is [data/registry.json](../data/registry.json); exact download URLs, dates, byte counts and SHA-256 values are in [the acquisition manifest](../data/external/acquisition_manifest.json).

## Current collection after expansion

**1,512 distinct original images are now manifested and audited:** 1,000 new Fashionpedia training-source skirt images, 500 FabNet-3k texture candidates (250 publisher-labelled Cotton and 250 Polyester), and the original 12 held-out images. All 1,512 decode with no integrity errors and have unique file/pixel hashes. The audit found 11 perceptual near-duplicate candidate pairs; unique physical garment counts remain unknown.

The auxiliary source-skirt development split contains 810 training and 190 development-validation images in conservatively connected groups. This is a one-positive-category source task, not a finished skirt/fabric/length classifier. FabNet's unknown archive partition and ambiguous labels remain excluded from training admission. **No verified project fabric labels or full-project training release are claimed.**

Details: [skirt acquisition](SKIRT_ACQUISITION.md), [fabric acquisition](FABRIC_ACQUISITION.md), [independent review](DATASET_REVIEW.md), and [runnable audit/split tools](DATA_PIPELINE.md).

## Original seed acquisition (historical, retained)

The initial acquisition contains **33 downloaded artifacts, 16,863,279 bytes (about 16.1 MiB)**. All 33 files match their recorded hashes and sizes. This total excludes locally generated summaries, attributions, and the later provenance audit. **Only 12 of these artifacts are photographs; none has a verified project fabric label and none is admitted to training.** Image count is not a count of independent physical garments.

| Source | Files actually acquired | Verified local coverage | Intended use and admission status |
|---|---|---|---|
| Fashionpedia | Official `val2020` instance annotations, pinned source README, terms page; 12 Flickr JPEGs and 12 corresponding oEmbed records | Metadata: 1,158 images, 8,781 total annotated instances, 162 skirt instances in 162 images. Photographs: 12, including 2 with the source `pleat` attribute | External held-out sanity checks only. Do not train or tune on these validation photographs. Masks need registration to downloaded images. |
| TextileNet | Pinned fabric and fibre label dictionaries, README and repository LICENSE | 27 fabric-category names and 33 fibre-category names; **0 images** | Useful ontology reference and future candidate. Image usage terms and label evidence require resolution before admission. |
| Describable Textures Dataset (DTD) | README and labels-only archive | 31 text members, 5,640 image references and 47 texture categories; **0 images** | Optional texture pretraining research. Texture adjectives do not supply the project's fabric labels. |
| DeepFashion category/attribute benchmark | No dataset files | Official pages reviewed; local image/annotation count is **0** | Secondary candidate for skirt/style data after terms and grouping review. |
| Project camera captures | None registered | **0 verified garments, 0 admitted images** | Required source for the one-full-skirt-view pilot and final device-domain evaluation. |

The [verification audit](../data/provenance/seed_audit.json) records the check results. All 12 JPEGs were fully decoded successfully with the existing Pillow installation, and their dimensions match stored oEmbed metadata. Ten have dimensions different from Fashionpedia's annotation record. Even equal dimensions do not prove identical image content or mask alignment; visual registration remains unverified.

## Fashionpedia: source annotations and licensed seed

[Official source repository](https://github.com/cvdfoundation/fashionpedia) provides separate training and validation annotations. The downloaded validation file identifies category `8` as `skirt` and attribute `304` as `pleat`. Of its 162 skirt images, 20 are marked with license ID `0` (CC BY 2.0); the acquisition obtained 12 photographs after checking stored Flickr oEmbed license and author information. One recorded candidate request returned HTTP 404. The sample deliberately prioritizes pleat examples and is not a random or balanced benchmark.

The [Fashionpedia terms](https://fashionpedia.github.io/home/data_license.html) license annotations and ontology under CC BY 4.0; photographs retain their own source terms. Every acquired seed photograph has a stored CC BY 2.0 license URL and creator attribution in its oEmbed record. Preserve [image attribution](../data/external/fashionpedia/ATTRIBUTION.md), source links, license links, and modification notices when redistributing permitted images. Acquisition-time metadata is evidence of the observed license, not a fresh online check on every rerun.

The [sample manifest](../data/provenance/external_holdout_samples.jsonl) preserves original `val2020` membership, source IDs, author, source-page grouping, original attributes, dimensions, file hashes, and missing project labels. Photographer/source identity is retained for conservative duplicate investigations. Physical garment identity is unknown: 12 image IDs must never be advertised as 12 verified unique skirts. Two source images have blank titles; a title is attribution metadata, never a fabric or style label.

Original `val2020` membership is protected. These examples may support file loading, attribution, and annotation-registration checks. Do not use them for training, augmentation selection, classifier threshold selection, or camera tuning. They are not the final capstone test set. Obtain separate official training data for future model development, then audit related garments and duplicates across partitions. Missing `pleat` does not automatically prove the project's `non-pleated` label, and source length labels are not measured centimetres.

## TextileNet: relevant candidate, images not acquired

The [official TextileNet repository](https://github.com/hahashu/TextileNet) separates fabric categories from fibre categories. The saved dictionaries include chiffon, denim and satin in the fabric taxonomy and cotton and polyester in the fibre taxonomy. They are evidence that these labels belong to different annotation dimensions; they do not resolve the project's final class definitions.

The README links fabric and fibre archives and a supplementary acquisition script. Neither archive, supplementary image collection, pretrained checkpoint nor training code has been downloaded or executed in this workspace. Its MIT license applies to collection code; the README's CC BY statement refers to manuscripts and does not clearly establish a blanket license for underlying photographs. Resolve dataset-specific image permissions and source evidence before expanding the acquisition. Keep fibre composition and fabric construction separately labelled; do not infer composition from filenames, titles or appearance.

## DTD and secondary candidates

[DTD's official page](https://www.robots.ox.ac.uk/~vgg/data/dtd/) describes 5,640 images in 47 perceptual texture categories and makes the data available for research. The acquired archive contains labels only: its first train, validation and test split lists each contain 1,880 references and are disjoint. All ten official split definitions must remain intact if DTD is used. No archive contents were extracted or executed. DTD could support an optional pretraining comparison, but it cannot certify cotton, polyester, satin or other project material labels; it is lower priority than relevant garments.

[DeepFashion's attribute benchmark](https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion/AttributePrediction.html) is a possible source of clothing and attribute examples. Its [official agreement](https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html) limits use to non-commercial research and restricts redistribution, with a single-site internal-copy exception. Other benchmarks may require a signed release agreement. No account, agreement, email or dataset download was initiated. Assess the specific subset, source-item grouping, actual fabric annotation quality and usage terms before choosing it. A public download link is not permission to redistribute a dataset.

## Next acquisition and annotation steps

1. Resolve the versioned class vocabulary, blend policy and label-evidence rules. Keep construction, fibre composition, skirt style/pleating and measured length distinct. Unknown and conflicting evidence remain explicit.
2. Obtain a bounded Fashionpedia **training** subset for style/localization development after recording file sizes and image terms. Preserve original partitions and check source/garment/near-duplicate relationships; never recycle the downloaded validation seed as convenient training data.
3. Resolve TextileNet image terms and inspect a bounded relevant subset if usable. Record actual successful images and verified independent groups, not the advertised full dataset size. Avoid a bulk download solely to increase image count.
4. Collect the critical local pilot from one fixed full-skirt view. Follow [the training plan](TRAINING_PLAN.md) for provisional garment targets and camera geometry. All fabric patches are extracted from the original full-skirt frame. Record garment tags/supplier evidence and measured physical length separately from visible appearance.
5. Vary color, pattern, pleating, lighting and source within each fabric category. Record where a fabric is confounded with one skirt shape or one supplier. Store empty-station and non-skirt negatives from the same setup.
6. Review eligibility and grouping, then create immutable development and held-out manifests with SHA-256 values. No training-ready release exists until these gates pass.

Every admitted record needs `sample_id`, immutable source path/hash, source and terms references, `garment_id` or explicit unresolved identity, grouping evidence, source split, project split, parent frame/crop ID, labels with evidence and review status, native dimensions, and camera/session/calibration details when locally captured. Crops, frames and augmentations inherit their garment's split. Record both image counts and independent garment/group counts per class. Use perceptual/near-duplicate review in addition to exact-file hashes.

## Acquisition tooling limitations

[The seed script](../tools/datasets/acquire_seed.py) uses Python's standard library, has a 30 MiB per-response cap, and hashes existing tracked files. It does not install packages or execute downloaded source code. It is a bounded initial acquisition utility, not the production ingestion pipeline.

The October 2 hardening adds `--verify-only` for network-free hash/size checks. A completed 12-image cache is verified and reused without refreshing sources or rewriting attribution. Partial retries preserve completed image records. New artifact and manifest writes use atomic replacement; untracked destinations are rejected, image responses require a JPEG header, and path escapes and duplicate manifest paths are rejected during verification. Four standard-library tests cover corruption, path escape, network-free verification and failed-write preservation.

```text
python tools/datasets/acquire_seed.py --verify-only
python -m unittest discover -s tests -v
```

Remaining limits before expansion:

- Reused oEmbed metadata is cached; license checks refer to the original saved response. The utility does not claim live license revalidation.
- Present metadata has one skirt per skirt image. The utility rejects metadata with multiple skirts per image until an explicit instance sampling policy is implemented.
- Category/attribute IDs are checked against expected names. License IDs and source schema still need review when changing source versions.
- JPEG header checks do not fully decode images. The separate audit decoded the current 12 images; future intake needs the same decoder/dimension review.
- Image dimensions and visual identity must be registered before applying source polygons or boxes. Archive extraction must reject unsafe paths and enforce bounds if added later.
- Summaries and attribution documents are derived records; the provenance audit hashes them separately. Keep counts scoped to exactly the files being counted.

Changes to data must update this document, the registry, the acquisition/sample manifest and hashes together. Training records must reference a concrete release and split hash. Dataset licensing/provenance also belongs in the released model card and any Pi verification-image bundle.

## 2026-10-03 label preparation

Image totals remain 1,512. [Label preparation](LABEL_PREPARATION.md) records 1,000 queue entries, 612 source-manufacturing auxiliary examples (489/123), and 13 visually reviewed appearance candidates (12/1, second review pending). Only 48 skirt images were visually reviewed; 952 remain. Existing grouped splits and 12 protected seed images remain unchanged. [Fabric text triage](FABRIC_LABEL_REVIEW.md) covers all 500 candidates and identifies 56 high-priority records without granting training eligibility or composition truth. Registry references and hashes identify these artifacts; this is not a full-project training release.

## October 4 completed visual pass and frozen pilot

All 1,000 skirt images now have agent visual review; independent human confirmation remains outstanding. Merged counts: 533 non-pleated, 110 pleated, 357 unknown (including eight quarantined review disagreements). Full-view known candidates: 375. Suspected garment components were quarantined without resplitting, leaving 372 images: 292 train / 80 validation. Original totals remain 1,512 and no final-test or full-project release is claimed. Registry now tracks versioned reviews, frozen pilot and trained development-model record. [Detailed results and evidence](BASELINE_RESULTS.md). Fabric composition labels remain unverified.

## Physical garment availability and follow-up experiment

User confirmed on October4 that no physical skirts are currently available. No local images or specimens were added. The controlled fine-tuning experiment reused the same frozen372-image manifest without relabelling or resplitting. The [capture guide](WEBCAM_CAPTURE_GUIDE.md) covers borrowing and recording real garments; independent human labels remain pending.


## Human review intake (October 4)

The local `/review` screen exposes exactly the 1,000 original Fashionpedia train2020 candidates. Existing source/model/agent labels are hidden. `records/human-review/events.jsonl` is created only on actual submission; events include image, input-manifest and frozen-split hashes and remain pending reconciliation. This application milestone changes no dataset images, registry counts, labels or splits. No human review is inferred from software tests. Protected source validation samples are excluded from this queue.
# October 10 evidence update

Original image count remains **1,512**. The mask-localization pilot reuses the frozen 292/80 pleating development split and official polygons; masks/crops are not new specimens. [Model evidence](../records/models/2026-10-10-skirt-localizer-v1.json).

DeepFashion-MultiModal intake acquired official annotation metadata, terms and two bounded image-archive ranges, **zero complete additional images**. Its 848 skirt filename rows and 288 source item tokens are unadmitted candidates, not verified garments or fabric ground truth. Image archive range access works; the original InShop partition download returns quota-exceeded HTML, preventing a verified original-split join. [Acquisition and feasibility evidence](FABRIC_FEASIBILITY_UPDATE.md). Registry records preserve hashes and candidate status without changing image totals.
# October 11 intake

Current audited count: **1,627 original images**. Added 90 source-selected non-skirt candidates and 25 DeepFashion-MultiModal original-training candidates; no training admission or model change. Official fabric partition access is now resolved: all 848 candidate filenames joined exactly (367 train / 224 query / 257 gallery). Query/gallery remain protected. All files decode and have unique file/pixel hashes; physical specimen identities remain unverified. [Full intake, source terms, evidence and limits](DATA_INTAKE_OCT11.md).

