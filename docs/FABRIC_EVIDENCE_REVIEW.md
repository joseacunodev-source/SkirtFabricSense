# Offline fabric evidence review — October 23, 2026

The [offline review tool](../tools/datasets/fabric_evidence_review.py) prepares a blind review queue from the **17 existing frozen fabric-pilot-v1 originals**. It separates visible appearance observations from documentary composition claims and preserves the original source labels privately for later reconciliation. It does not select a final fabric taxonomy, change labels or splits, approve training, or start model fitting.

The prepared [blind queue](../records/review/2026-10-23-fabric-evidence-review/blind-queue.json) contains 17 items with **zero submitted observations**. It has 12 original development-training and five development-validation source groups. Source groups are not verified physical garments. [Verification](../records/review/2026-10-23-fabric-evidence-review/verification-final.json) checks all original image bytes, sizes, JPEG header dimensions, source terms and frozen assignments. Images are referenced in place; none were copied or downloaded. No dependencies were installed. This is evidence-intake preparation, not completed visual review or hardware validation.

## Reviewer and administrator separation

Give the reviewer only `blind-queue.json` and access to the original image files it references. Each blind row has an opaque `review_id` and the original image's path, hash, size and dimensions. Source labels, previous presentation observations, model scores, source groups and development split assignments are omitted from the blind rows. The same image is the complete original full-skirt view; the queue supplies no crop as a replacement.

The administrator file `bindings.private.json` preserves complete original source records, including their old appearance labels, source identities, terms, groups and splits. Its name describes the intended review workflow; it is **not access control or encryption**. The tool cannot verify that a reviewer avoided prior labels or predictions. A human/agent identity and original-viewing attestation are self-reported, not authenticated. A human actor selection never establishes independent human truth.

This queue includes development-validation images for blind annotation only. Their assignments remain fixed; submitted observations do not authorize a fit, threshold selection, relabeling or movement into training. Protected source `query`, `gallery`, `test` and other non-training partitions are rejected.

## What a review records

Open the actual original and record literal visible evidence. Keep skirt material separate from shirts, jackets, backgrounds, lining glimpses and held objects. Use `material_to_skirt_association: uncertain` if the observed material cannot confidently be assigned to the skirt; such a record must abstain from skirt appearance descriptors.

- `appearance_status`: `single_appearance`, `mixed_appearance` or `unknown`. Descriptor text preserves observations without imposing an exclusive material ontology. Use clear properties such as “smooth reflective surface” or “sheer sections”; visual fibre guesses are not composition evidence. Unknown requires an empty descriptor list. Mixed describes observed variation; it does not establish a verified fibre blend.
- `presentation`: worn, hanging, held, mannequin or unknown. Record full/partial/uncertain skirt visibility and sufficient/insufficient/uncertain texture detail separately.
- `notes`: describe the visible basis and limitations, including blur, print, lighting, folds, occlusion or garment confusion. A checkbox cannot replace evidence.
- `composition_evidence`: normally `not_observed` with a null claim. An `unverified_document_claim` requires a hash-bound local garment-tag or supplier document reference associated with the claimed skirt. It remains an unverified transcription; neither a source annotation nor a tag photo alone proves the item association, current composition or source rights.
- `source_evidence_references`: optional local path/SHA256/kind/item-association records. Each is rechecked when appending and verifying. These references preserve evidence for reconciliation; they grant no usage rights. Avoid opening prior source annotations before the blind appearance observation. Additional evidence or corrections should be separate appended events, never edits to earlier rows.

The appearance descriptors are free text evidence, not automatically accepted classifier targets. The tool cannot judge whether a sentence is scientifically correct. Later reconciliation must adjudicate disagreements, textile semantics, document-to-item association, rights, grouping and appropriate labels before any versioned dataset release. Cotton/polyester remain fibre terms; denim, chiffon and other construction/appearance terms are not forced into the same exclusive axis.

## Commands

Run from the project root using the existing bundled Python or another already documented Python environment. The CLI uses only Python's standard library.

```text
python -B tools/datasets/fabric_evidence_review.py verify --directory records/review/2026-10-23-fabric-evidence-review
python -B -m unittest tests.test_fabric_evidence_review -v
```

Build a distinct future queue only when needed; the output folder must be new and under `records/review`. There is no CLI switch to override frozen input hashes or choose another dataset.

```text
python -B tools/datasets/fabric_evidence_review.py build --output records/review/fabric-evidence-another-review
```

After actually opening an original, create a JSON submission outside the event log. Replace the placeholder identifiers/hashes from the blind queue and describe the actual evidence. The example below is a contract example, **not an observed review or a file to submit unchanged**.

```json
{
  "review_id": "COPY_REVIEW_ID_FROM_QUEUE",
  "queue_sha256": "COPY_EXACT_BLIND_QUEUE_FILE_SHA256",
  "image_sha256": "COPY_IMAGE_SHA256_FROM_QUEUE",
  "reviewer": {"display_name": "YOUR_REVIEWER_NAME", "actor_kind": "human"},
  "original_viewed": true,
  "observations": {
    "appearance_status": "unknown",
    "appearance_descriptors": [],
    "material_to_skirt_association": "uncertain",
    "presentation": "unknown",
    "full_skirt_visibility": "uncertain",
    "texture_detail": "insufficient",
    "notes": "REPLACE_WITH_ACTUAL_VISIBLE_EVIDENCE_AND_LIMITATIONS"
  },
  "composition_evidence": {"status": "not_observed", "unverified_claim": null},
  "source_evidence_references": []
}
```

```text
python -B tools/datasets/fabric_evidence_review.py append --directory records/review/2026-10-23-fabric-evidence-review --submission PATH_TO_ACTUAL_SUBMISSION.json
python -B tools/datasets/fabric_evidence_review.py verify --directory records/review/2026-10-23-fabric-evidence-review --output records/review/NEW_VERIFICATION_REPORT.json
```

`--output` on verification creates a new report and refuses to overwrite one. A correction/re-review appends another event for the same item. Event counts and distinct reviewed-item counts are reported separately. All accepted submissions have `status: pending_reconciliation`, `training_approved: false` and `composition_verified: false`; extra approval/truth fields are rejected.

## Integrity and limitations

Build/append/verify recheck the pinned pilot manifest, split manifest and saved terms; they verify image hashes, byte sizes, header dimensions, exact membership, duplicate sample/content/path restrictions and cross-split group isolation. The JPEG header check does not replace the earlier complete image decode audit or establish orientation/geometry. Existing images are pinned byte-for-byte, so a post-build image change prevents submission.

Events append to `events.jsonl` with UUID, UTC time, exact queue/image bindings and a SHA256 chain. A single-writer `.append.lock` and flush/fsync protect normal concurrent submissions. A leftover lock after a crash is not silently removed: first establish that no writer is active, preserve the partial log and investigate. An incomplete last line fails verification. The tool never repairs or truncates evidence automatically.

Hash chains detect changed, reordered and duplicated retained rows. They do not authenticate people, stop a writer with full workspace access from rewriting all evidence, or detect removal of the entire tail without a separately retained prior chain head/log hash. Preserve verification reports and continuation hashes outside the mutable log. Missing logs fail; an empty log created by build means zero reviews, not completion. A mid-write crash may require manual recovery into a separately versioned record after investigation.

Current data remains tiny: 17 source groups, three classes with one validation group each, unresolved final ontology and zero independently confirmed composition labels. This preparation does not repair rare-class coverage, justify another smoke fit or establish live-camera/Pi performance. See [fabric admission gates](FABRIC_NEXT_GATE.md), [source rules and grouping gate](FABRIC_SOURCE_GATE_OCT22.md), and [frozen fabric pilot](FABRIC_PILOT.md).
