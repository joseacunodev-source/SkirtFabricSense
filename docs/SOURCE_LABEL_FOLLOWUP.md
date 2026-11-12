# Source-label follow-up

October 17, 2026. All six unknown-presentation originals were opened individually and joined to their exact Fashionpedia train2020 annotations. This supplemental agent review preserves every historical label, group and split. It is not independent human confirmation. [Hash-bound observations and exact target polygons](../records/review/2026-10-17-source-label-followup.json).

| Sample image ID | Observed evidence | Source context and action |
|---|---|---|
| 26955 | Tan isolated fringed garment; upper edge reaches frame boundary. | Source skirt 309709 plus separate fringe annotation. No category correction justified; wearer geometry unavailable. |
| 29141 | Black isolated garment with regular pleats and broad upper band. | Source skirt 103476 includes accordion and pleat attributes. Construction agrees; display support remains unknown. |
| 34099 | Printed isolated lower garment has overlapping diagonal front and divided-looking lower outline. | Source skirt 209575 explicitly includes wrap (skirt). Shorts/skort construction remains possible but unconfirmed. Quarantine this sample from future new whole-image positive releases pending independent construction review; never convert it into a negative based on this view. |
| 46766 | Pink isolated fitted garment with continuous hem. | Source skirt 60780 includes hobble/peg descriptors. No category conflict established. |
| 49867 | Distressed blue lower garment with fly, pockets and continuous hem. | Source skirt 79026 plus belt/pocket/rivet annotations. No category conflict established; appearance cannot establish fiber composition. |
| 50322 | Separate black top and lower garment with white gap between them. | Source top 177433 and skirt 177435 are separate targets. Skirt bbox is `[1, 487, 387, 535]`; the upper top does not invalidate the source skirt ROI. Whole-image presence and ROI target must remain distinct. |

None of these six establishes a wearer, hanger, holder or mannequin. Their current `unknown` presentation and exclusion from the frozen worn subset remain appropriate. Six inspected originals are six source images, not six newly established physical garment identities. Source annotations describe regions; another garment or detail elsewhere in an image is not automatically a conflict in the selected region.

The earlier [root flag](../records/review/2026-10-17-root-presentation-qa.json) correctly requested follow-up for 34099, but its shorts suggestion is not confirmed. Exact source attributes provide a plausible wrap-skirt explanation. Retain historical training and metric denominators unchanged; any accepted correction must create a new versioned release with group/split checks and rerun affected experiments. The current worn subset already excludes this image, so it needs no membership change.

Run `python tools/datasets/source_label_followup.py` to reproduce the source join and hash checks. The helper verifies all six original bytes against both frozen baseline and presentation hashes and verifies target polygons against the official source before writing the supplemental record. It does not download images, alter dataset admissions, or install software. Human category/construction confirmation remains necessary to close label acceptance.
