# Negative-candidate review — October 11, 2026

All 90 acquired candidates received a conservative single-agent review using the four archived contact sheets. Twenty-two full originals were inspected; this includes every admitted image. This is not human-confirmed ground truth. The frozen review manifest keeps all 90 rows: **12 admitted, 78 quarantined**. Load only rows where `training_eligibility.approved` is true. Quarantined rows have null label and split.

The admitted set contains four pants, three shorts and five dresses, with **nine training / three validation images**. Each validation category contains one image. This is enough to exercise negative training and export, but far too small to claim reliable rejection. A correct prediction on all three would still be weak evidence. There are no empty-room, blur, partial-skirt or webcam-domain negatives.

## Label definition and exclusions

`no_skirt` means no visible separate skirt garment in the reviewed source frame. A continuous bodice-to-hem dress is a negative for the separate-skirt target, even though its lower portion resembles a skirt. A romper is a negative where separate leg openings are visible. Labels describe visible evidence; they do not establish hidden clothing.

Each admitted original has a written observation in `label_evidence`. Cropped or obscured garment evidence, additional partially seen people, crowded runway audiences and unresolved source/session correlation were excluded. Full-original inspection rejected some candidates that appeared clear in thumbnails: the first pants image includes another cropped person; an event dress has partially seen attendants. Repeated `eyestrain` watermarks on 15267/32440/13916 were conservatively quarantined pending cross-pool source audit. Candidate1632 remains excluded because the combined perceptual audit links it to existing skirt1796/7330; similarity is not proof of the same garment.

## Rights and grouping

Admission uses the original source-provided license entries for CC BY, BY-SA, BY-NC, BY-NC-SA or public-domain dedication only. ND-restricted entries and uncertain/non-CC terms are excluded under this pilot's conservative policy. This is not a legal determination that other licenses forbid training. Source URLs, terms references and license metadata remain attached. No source images are approved for redistribution; attribution completion and any distribution review remain separate. Noncommercial restrictions remain applicable to the internal pilot.

Original source URL groups and content hashes are retained. The combined 1,627-image audit found no exact-file or decoded-pixel duplicates. Its known new cross-pool perceptual candidate is quarantined. Admitted records have no hash or source-group overlap with the frozen 372-image positive pilot. Physical garment/session identity is not independently verified. Visually recurring sessions were excluded instead of invented as independent examples.

The preparation tool assigns whole source groups by category, ranks each group with seed text `negative-v1-seed-20261011`, and holds out the nearest 25% per category (at least one where possible). The assignment is deterministic and invariant to row order. It never changes the existing positive or protected source splits. This development validation is not a new independent final test set.

## Reproduction and checks

- Frozen labels: `data/labels/negative-reviewed-v1.jsonl`
- Counts, source/manifest/code/split hashes: `data/labels/negative-reviewed-v1.report.json`
- Preparation: `python tools/datasets/prepare_negative_pilot.py` (refuses to overwrite frozen files; alternative output/report paths can reproduce)
- Checks: `python -m unittest tests.test_negative_admission -v`

Eight tests passed using the installed Windows Python 3.11.9. They cover source integrity, deterministic reconstruction, label/rights admission, quarantine exclusion, category holdouts, group disjointness, positive-group collision and input-order independence. No packages were installed, no original image was modified, and no GPU or camera was used by this review task.

Next data priority is acquiring more clear, rights-documented negative originals with enough independently grouped examples per category. Do not relax these exclusions simply to improve apparent dataset size. The root experiment may train this explicitly small pilot, but promotion requires broader rejection evidence.
