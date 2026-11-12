# Negative candidate expansion v3

Date: October 17, 2026 (Asia/Manila). **180 original photographs acquired successfully**, with 60 pants, 60 shorts and 60 dresses; 12,667,960 image bytes, 180 member attempts and zero errors. This is candidate acquisition, not training admission or measured rejection improvement.

The bounded intake targets 180 new Fashionpedia original `train2020` photographs: 60 pants, 60 shorts and 60 dresses. Source annotation absence of skirt is selection evidence only; full-original visual review can still reject an incorrectly annotated, ambiguous or related example.

Frozen manifest SHA-256: `45c69c3db6697ca5b82eed9856d12c3cfde92ce85467f67be75c8e4f1f7209d7`. Acquisition verification found zero overlap with prior originals by source ID, canonical photograph URL, exact file hash or decoded RGB pixel hash. All five focused tests passed. Fifteen review pages were generated with 12 originals per page.

## Reproducible intake

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tools/datasets/expand_negatives_v3.py --count 180
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tools/datasets/expand_negatives_v3.py --verify-only
```

The script reuses the existing exact HTTP range ZIP reader. It downloads individual archive members, preserves their original bytes, validates ZIP length/CRC and decoded dimensions, and caps work at 204 attempted members with a stop after 24 failed/duplicate members. Four workers operate concurrently; the reader permits three bounded HTTP attempts per member. A frozen manifest is never silently extended or overwritten by a second acquisition run.

Source-ID and canonical Flickr photograph exclusions cover all prior candidate manifests and protected seed identities, including images previously quarantined. Exact file hashes and decoded RGB pixel hashes cover prior cached originals; each completed member is checked against prior and within-run identities/content before writing. These checks do not establish physical-garment independence or exclude visually similar photographs from one session.

Only exact source annotation license-name/URL pairs from the existing non-ND research policy are accepted. Original license records and source terms snapshot remain attached. Source-provided rights are preserved; individual photographs have not been freshly relicensed online, and this intake grants no dataset redistribution approval.

## Evidence and review

- [Acquisition report](../records/acquisitions/2026-10-17-negatives-v3/report.json) records actual downloaded count, bytes, bucket counts, errors, prior manifest hashes, source annotation/archive-index/code hashes and exclusion counts.
- [Candidate manifest](../data/manifests/negative-candidates-v3.jsonl) preserves each original's source identity, archive member, file/pixel hashes, source annotations and exact rights.
- [Review sheet index](../records/acquisitions/2026-10-17-negatives-v3/review-sheets.json) links up to 12 larger originals per page and each corresponding original path/hash. Sheets aid triage; original-image inspection is required before admission.
- [Focused tests](../tests/test_negative_expansion_v3.py) cover source exclusions, skirt exclusion, clipped selection, license pairing, reencoded pixel duplicates, prior-overlap/admission rejection, and 12-image review pagination.

All rows have `split: null`, no skirt-presence truth label, and `training_eligibility.approved: false`. Visual labels, presentation, garment/source-session grouping and perceptual near-duplicate audit must be resolved before a new frozen training/validation extension. Existing assignments and protected data stay unchanged. No dependencies were installed.
