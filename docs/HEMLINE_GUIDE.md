# Requested hemline categories

On October 9, 2026 the user supplied a skirt hemline illustration and requested automatic live hemline identification plus pleated/non-pleated output. This supersedes the earlier tentative short/long or four-combination taxonomy. The single-camera full-skirt requirement remains fixed.

Ordered labels: **Micro, Mini, Above knee, On knee, Below knee, Midi, Tea, Maxi, Full**. Preserve these names from the supplied guide. Pleating is an independent binary appearance output; non-pleated does not imply straight silhouette. Fabric remains in scope unless the user explicitly removes it.

The machine-readable [taxonomy](../config/hemline-guide-v1.json) records the [supplied illustration](references/skirt-length-guide.jpg) and its hash. It is a semantic reference, not a labelled training dataset or calibration ruler. Original authorship/reuse terms are unknown; do not redistribute as a project-authored asset. No training dataset or original-image count changed.

## Geometry still to confirm

These are body-relative hem positions rather than physical centimetres. The user explicitly requires worn, hanging, mannequin and held presentations. Hanging/held garments use a calibrated standard mannequin/body reference, selected by the user; results must be labelled as estimates. A hanging skirt alone does not establish where its hem would fall on a particular wearer. A standardized mannequin/reference-body mode can be defined separately, with its own declared calibration.

For a worn-skirt mode, the proposed input is one view covering the waist through feet. The system would localize the skirt, identify its hem and associate it with the same person's body reference. Occluded knees, overlapping people, asymmetric hems, bent legs and camera tilt require explicit handling or abstention. Long skirts may hide knee landmarks; pose estimates behind clothing cannot be treated as measured ground truth.

The illustration supplies category order and approximate visual meaning, not defensible numerical thresholds. Do not divide the image into nine equal strips or treat pixel coordinates in the illustration as universal body ratios. Record annotated examples and boundary cases, fit thresholds using development data, then freeze and evaluate them on held-out garments. Borderline positions must be reported as uncertain instead of forced into an adjacent category.

## Implementation status

The camera UI now names the outputs Pleating and Hemline length and lists all nine requested categories. Actual automatic hemline/pleating inference is not connected to preview yet. The existing trained model supplies pleating scores only when given a suitable skirt crop; it cannot locate hems, detect skirts or identify body landmarks. No hemline accuracy is claimed and no geometry thresholds have been invented.

Next dependent work is choosing presentation geometry, obtaining appropriate skirt/body annotations, implementing localization and reference estimation, and integrating frame-to-result freshness with the existing worker. Live fabric recognition remains a separate unfinished output.

## Geometry rule implementation

`app/hemline.py` accepts a hem uncertainty interval in a named calibrated waist-to-floor coordinate and eight explicitly supplied ordered class boundaries. It refuses missing/mismatched references, unsupported presentations, invalid bounds and out-of-range geometry; intervals touching class boundaries produce uncertain output. All four modes are supported by the contract, not yet verified by detectors. No production calibration profile exists. Eight unit tests use synthetic boundaries only; their numbers must not be copied into a production profile. No live feed classification has been added by this change.

October 9 clarification: user selected a calibrated standard mannequin/body reference for hanging and held skirts; outputs must be labelled as estimates relative to that reference. The physical dimensions, camera calibration and class boundaries are not yet established. Fabric recognition remains required with an operator on/off switch. The camera UI switch persists locally and shows disabled or model-unavailable states; no fabric inference is claimed.
