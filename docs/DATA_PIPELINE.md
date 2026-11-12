# Data intake, audit and development splits

Implemented 2026-10-02. These tools prepare and inspect candidate data; they do not train a CNN or certify fabric composition. Use the existing Windows host Python 3.11.9 with Pillow 12.3.0. No new packages were installed for this work.

## Tools

| Tool | Purpose |
|---|---|
| tools/datasets/acquire_skirts.py | Select original Fashionpedia train2020 skirt images using bounded ZIP byte ranges; check decode, annotation dimensions, ZIP CRC and SHA-256 |
| tools/datasets/acquire_fabrics.py | Select FabNet-3k Cotton/Polyester source images using bounded ZIP ranges; keep source labels, ambiguous descriptions and unspecified source split |
| tools/datasets/audit_candidates.py | Decode images, check hashes/dimensions, find exact/pixel duplicates and perceptual duplicate candidates |
| tools/datasets/prepare_splits.py | Create deterministic grouped development assignments only for explicitly admitted tasks |
| tools/datasets/contact_sheet.py | Generate deterministic local visual QA sheets; derived thumbnails do not increase dataset counts |

## Candidate schema

Each JSONL record contains `sample_id`, `original_path`, `sha256`, `source_id`, `source_partition`, `source_item_id`, `source_url`, `terms_reference`, `group_id`, `garment_id`, `parent_sample_id`, `width`, `height`, `source_labels`, `project_labels`, and `training_eligibility`. Additional source attributes and archive provenance remain available.

`source_labels` preserves publisher assertions. A named development task can be admitted through:

```json
{
  "project_labels": {
    "source_skirt_presence": {"value": "skirt", "status": "approved", "evidence": "Official skirt category annotation"}
  },
  "training_eligibility": {
    "source_skirt_presence": {"approved": true, "reason": "Source annotation supports auxiliary development only"}
  }
}
```

This example is not approval for fabric, pleating or physical-length tasks. One positive class alone is not a complete skirt/non-skirt classifier dataset. Fashionpedia boxes/masks can support localization development after annotation and input checks. Admission never proves unique physical garments or device-domain performance.

## Audit command

```powershell
python tools/datasets/audit_candidates.py --manifest data/manifests/skirt_candidates.jsonl --manifest data/manifests/fabric_candidates.jsonl --output records/validation/expansion-audit.json
```

The audit returns nonzero on integrity errors. Reports are immutable: use a new output name on subsequent runs. It compares original file hashes and decoded RGB pixel hashes and flags dHash pairs at Hamming distance <=4. dHash similarity can group different plain fabrics or miss different views of one garment; it is a candidate signal requiring review, not verified garment identity.

## Protected partitions and split behavior

Source `train`, `training` and `train2020` are eligible partition names. Unknown partitions and source validation/test examples are excluded automatically, even if someone adds a task approval. A connected component linked to any protected sample is excluded as a whole. Include existing holdout manifests to detect cross-source duplication.

Groups connect explicit group/garment/specimen/session/video IDs, source-scoped item IDs, parent relationships, exact/pixel duplicates and perceptual candidates. All assignments in a connected component stay together. Hash-based assignment is deterministic but not class stratified; inspect actual class counts before using the split.

FabNet-3k's downloaded archive does not contain the README's advertised train/val folders. It remains `unspecified_in_archive` and candidate-only. A later, explicitly documented source-partition review and label review is required before creating development splits. Do not relabel the source partition as train just to bypass the safeguard.

## Checks

```powershell
python -m unittest discover -s tests -v
python tools/datasets/acquire_skirts.py --verify-only
python tools/datasets/acquire_fabrics.py --verify-only
```

Tests exercise file corruption, non-image bytes, path escapes, duplicate IDs, protected-source leakage through exact/near duplicates, transitive grouping, missing parents, task-specific approval, unknown partitions, deterministic assignment, immutable reports, and ZIP CRC/member identity/bounds. These are offline fixtures; they do not substitute for reviewing source terms or real labels.

## Remaining work

Review a meaningful sample of imagery and annotation quality; identify repeated physical garments/listings; resolve ambiguous fabric descriptions; establish project labels; collect full-skirt device-domain samples and negatives. Keep source-folder labels distinct from measured composition. Close-up fabric images may support a transfer-learning experiment but do not demonstrate full-skirt classification.
