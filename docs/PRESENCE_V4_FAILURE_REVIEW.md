# Presence-v4 failure review — October 19, 2026

The candidate improves aggregate development results, but its remaining errors show why it is not ready for demonstration approval. The counts below retain every frozen validation example. No label, split, model, threshold or acceptance criterion was changed after inspecting these failures.

## Negative scenes

All 13 false accepts were independently displayed at original resolution and joined by file hash to the acquisition manifest, curated negative freeze and archived training inputs. The [review](../records/review/2026-10-19-presence-v4-negative-failures.json) passed 115 integrity/membership checks. Category counts below cover all 52 negatives, not only the failures.

| Source category | Validation originals | Accepted by presence alone | Accepted by v2 mask alone | Accepted by combined path |
|---|---:|---:|---:|---:|
| Dress | 20 | 10 | 13 | 10 |
| Pants | 17 | 6 | 12 | 3 |
| Shorts | 15 | 1 | 6 | 0 |
| Total | 52 | 17 | 31 | 13 |

All ten dress failures show a connected bodice. Several have gathered or flared lower portions. The three pants failures include crops that select a long top/hip fragment or sweater/upper-thigh region while excluding most of the legs. These observations support investigating full-scene category evidence and ROI completeness; they do not prove the model learned a particular shortcut. Do not turn them into a simplistic seam or length rule.

Relative to the v1 baseline, 12 previously accepted negatives are now rejected, 11 remain falsely accepted, and two previously rejected negatives become false accepts. The two added failures are source IDs 5822 (long magenta top/hip fragment) and 27837 (fitted mini dress). Net rejection improves by ten, but aggregate improvement does not mean every earlier case is preserved.

## Positive coverage and pleating

Eight positive examples fail the presence gate. Among the remaining positives, nine fail the v2 mask's multiple-region rule and five fail its frame-edge rule. Thus 22/66 are unavailable. The other 44 include six wrong pleating labels. Localization reason codes describe model-mask behavior; they do not independently prove actual garment truncation or multiple garments.

All 28 positive failures were directly displayed as originals and hash-checked in the [positive review](../records/review/2026-10-19-presence-v4-positive-failures.json). Counting overlapping reasons separately gives six presence-only, 14 mask-only and two both. The mask rejects nine as multiple regions and seven as touching the frame edge, including the two also rejected by presence. All seven edge-flagged originals show actual skirt margins: the mask failure must not be reported as observed skirt truncation.

Visual observations include multiple-wearer scenes/reflections, coat occlusion, uncertain skirt/dress identity and ROIs that clip or include unrelated clothing. These are source-domain and annotation limitations requiring confirmation, not grounds to silently remove examples. One accepted mismatch (45873) has ambiguous pleats-versus-gathers evidence. Frozen truth and reported accuracy remain unchanged; no corrected-accuracy claim is made.

| Frozen pleating label | Validation originals | Accepted | Correct pleating | Correct / accepted |
|---|---:|---:|---:|---:|
| Pleated | 17 | 14 | 9 | 9/14 |
| Non-pleated | 49 | 30 | 29 | 29/30 |
| Total | 66 | 44 | 38 | 38/44 |

Five of the six wrong accepted predictions are frozen pleated examples. The apparent aggregate accuracy therefore hides weaker minority-class performance. These remain agent-reviewed labels requiring independent confirmation.

Of the 41 positive examples previously accepted by v1, 33 remain accepted and eight become unavailable. Eleven earlier rejections become accepted; 14 are unavailable through both paths. Coverage improves by three overall, with individual regressions preserved in the comparison.

## Next justified work

1. Obtain new grouped worn-dress and long-top/pants negatives with complete contextual views, plus empty/partial/multiple-garment scenes. Keep challenge groups separate from fitting before reviewing predictions.
2. Confirm rare pleated examples independently and expand distinct pleated garments across patterns, lighting and occlusion. Report per-class availability and correctness with overall counts.
3. Investigate mask components and border failures on annotated training/development images. Preserve a separate validity/visibility decision; a predicted mask touching the edge is not measured garment visibility.
4. A category-aware auxiliary model or full-frame/ROI consistency experiment is a hypothesis for a new declared protocol, not an already validated fix. Train only on admitted training groups and preserve every previous attempt.
5. Freeze the chosen research configuration before collecting unseen real-garment acceptance evidence. Repeatedly fitting these 118 development images cannot establish camera or Pi readiness.

Source metrics and all per-example predictions are retained in the [actual-export comparison](../records/validation/2026-10-19-detection-v4-comparison.json). [Independent model review](PRESENCE_V4_RESULTS.md), [active task board](TASK_BOARD.md).
