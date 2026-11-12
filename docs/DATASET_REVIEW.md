# Expansion review

Reviewed by root on 2026-10-02, after separate agents prepared acquisition and pipeline work. Agents hit usage limits; root completed the fabric downloader, executed both acquisitions, added archive tests, and performed the integrated audit. Completion was determined from files and tests, not agent status messages.

## Counts and technical checks

- 1,000 Fashionpedia training-source skirt images.
- 500 FabNet-3k texture candidates, publisher-labelled 250 Cotton / 250 Polyester.
- 12 original external-validation images, kept separate.
- **1,512 manifest images, 1,512 unique file hashes and 1,512 unique decoded-pixel hashes; zero integrity errors.**
- 11 perceptual near-duplicate candidate pairs found across the combined collection. These are conservatively connected for split generation; exact uniqueness does not prove unique garments.
- No verified physical garment IDs and no final-project fabric/physical-length ground truth in this internet collection.

Evidence: [combined audit](../records/validation/dataset-expansion-combined-audit.json), [skirt report](../records/acquisitions/skirt_expansion.json), [fabric report](../records/acquisitions/fabric_expansion.json).

## Visual sample review

Root inspected two deterministic 24-image contact sheets (seed 42): [skirts](../records/review/skirt-contact-sheet.jpg), [fabric](../records/review/fabric-contact-sheet.jpg). The associated JSON files preserve sample IDs and positions. This is a 48-image inspection, not a claim of manual review of every image.

Skirt findings: diverse backgrounds and poses, runway/event imagery, multiple sizes of garment region, hidden waistbands and partial hemlines. In the inspected sample, IDs `fashionpedia-train2020-5665` and `fashionpedia-train2020-4106` have clearly truncated lower views and require exclusion/review for a full-waistband-to-hem task. Some source skirt annotations occur in dress-like outfits; project-specific label review remains necessary. Original annotations and images have not been silently changed.

Fabric findings: all 24 inspected samples show fabric surfaces/folds/patterns rather than full skirts. Appearance varies in weave scale, reflectivity and print. No visual inspection can certify their fiber composition. Publisher descriptions and cross-folder duplicate evidence require label review.

## Software review

18 offline tests pass, covering seed hash integrity, atomic-write preservation, path escape, archive CRC and member identity, byte bounds, real image decoding, dimensions, duplicate IDs, exact/near holdout leakage, transitive groups, missing parents, task-specific admission, unknown partitions and deterministic splits.

The acquisition scripts execute no downloaded code. Data are written atomically and original archive bytes are retained. Long-lived manifests use public source URLs, not expiring signed redirect URLs. Software scripts are reusable, but no model or Pi benchmark is claimed.

## Training readiness

The Fashionpedia auxiliary source task can receive conservative development assignments using official training membership and source annotations. It has one positive category; it is not a finished multi-class project classifier. Source boxes/masks remain useful for localization work.

FabNet's unspecified partition and ambiguous labels are deliberately excluded by current split admission. To use it, first record a reviewed source-partition policy, verify source labels for the intended auxiliary task, group duplicate/product relationships, and create a new versioned manifest. Do not simply set every record to train.

The full project still requires a coherent fabric ontology, full-view pilot captures with label evidence, reliable project style labels, and calibrated physical length. These are genuine data requirements, not solved by increasing the downloaded image count.
