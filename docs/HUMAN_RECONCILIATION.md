# Human review reconciliation audit

Implemented October 9, 2026. This read-only audit prepares evidence for a human decision; it does not approve labels, relabel images, resplit data, or trigger training.

Run from the project root with the existing Python environment:

```powershell
python tools/datasets/reconcile_human_reviews.py --output records/validation/2026-10-09-human-review-audit.json
python -m unittest discover -s tests -p test_review_reconciliation.py -v
```

The output must not already exist. The command exits 1 when event/image integrity errors are present, and refuses invalid or changing source manifests. A missing event file is a valid `no_human_events` outcome, not completed annotation. No dependencies are installed.

The audit verifies all candidate image bytes against recorded hashes, original Fashionpedia train2020 membership, matching frozen assignment IDs, and separation of frozen source groups. For every submitted event it checks the content hash, event identity, image and manifest hashes, source partition, group and development split, annotation fields, timestamp, and pending/unapproved status. Development validation samples remain validation samples; protected source validation/test samples cannot be admitted by this tool.

Every event remains in the report, including malformed raw lines and invalid events. Valid events are grouped by sample; repeated submissions under the same self-reported reviewer name are listed as revisions. Any difference in historical pleating or full-view judgements is flagged, even if a later submission agrees. No latest-write-wins or majority-vote label is generated. Invalid evidence is retained but excluded from disagreement summaries.

Before a future versioned training release, a human must resolve conflicting judgements, establish reviewer independence, confirm full-view and garment grouping evidence, and explicitly approve the release. Matching self-reported names are not authenticated identity. SHA-256 checks detect inconsistency; they do not prove that an attacker has not rewritten all inputs. This tool does not create human judgement where none exists.
