# Development review — October 12, 2026

The interrupted October 11 runs were recovered from saved artifacts. No retraining is inferred from a resumed conversation. Original images remain unchanged at **1,627**; crops and experiment copies do not increase that count.

## Data and training

The 90 negative candidates were reviewed conservatively: **12 admitted (9 training / 3 development validation), 78 quarantined**. All admitted originals received agent inspection, with source terms and grouping retained. This is not independent human confirmation. See [negative review](NEGATIVE_REVIEW.md).

The presence pilot trained against the unchanged 292 positive training images and nine admitted negatives. Its selected checkpoint recognizes **45/80 validation skirts**, and rejects **2/3 validation negatives** at the fixed 0.5 threshold. A successful export does not make this a successful product model. The candidate remains experimental and disabled by default; it does not replace or improve the existing mask geometry.

The [paired TFLite comparison](PRESENCE_RESULTS.md) accepts 48/80 skirts with the current localizer and 25/80 with the added gate; correct pleating outputs fall from 38 to 19. Rejection changes from 1/3 to 3/3 negatives. Neither three negatives nor improved rejection at that coverage loss justify promotion.

The fabric review admits **17 source items (12 training / 5 validation)** for a pipeline smoke experiment only. The source categories describe appearance, including a source cotton label that is not verified fiber composition. The saved run predicts **4/5** validation items correctly, but five examples cannot establish reliable fabric recognition. It is not connected to live inference.

[Fabric records and independent desktop parity](FABRIC_PILOT.md) preserve the actual run and source-label limitations. Original training code remains archived separately from later admission hardening.

## Application boundary

The optional presence gate precedes mask localization. Existing live inference remains the selected pleating model with optional experimental localization unless an operator explicitly supplies the new presence candidate.

The geometry adapter converts same-frame hem, waist and floor coordinate intervals into a conservative normalized interval. It requires matching frame, camera configuration, reference, presentation mode and calibration evidence. Missing or inconsistent evidence produces an unavailable result. The calibration validator checks structure; it cannot verify physical measurements. No body/hem detector or physical calibration was created by this integration.

The requested modes remain worn, hanging, mannequin and held. Hanging and held outputs must use a calibrated standard body reference and be labelled estimates. A segmentation bounding box alone cannot provide this reference.

## Remaining acceptance work

- Expand independently grouped, rights-documented negatives and improve detection without sacrificing valid-skirt coverage. The current small presence candidate is not a release improvement.
- Expand full-view fabric training with defensible source labels and sufficient unseen garments per class; evaluate automatic same-frame crops before enabling the fabric switch for inference.
- Implement and evaluate same-frame geometry extraction, bind a verified camera configuration, and collect measured calibration profiles for each supported presentation.
- Obtain garments for representative camera-domain evaluation, then verify installation, timing, sustained operation and display behavior on the actual Raspberry Pi.

No new dependencies were installed during this recovery. Desktop export and synthetic contract checks do not establish Pi compatibility or live-camera accuracy.

## Integration checks

Root reran **223 Python tests** and **14 mocked camera scenarios**. The new research-v4 bundle passed its independent 14-file inventory verifier before and after an actual private HTTP run; three saved-frame predictions exactly matched the selected baseline path. The temporary server stopped afterward and no camera was activated. See [test log](../records/validation/2026-10-12-integration-tests.log), [HTTP results](../records/validation/2026-10-12-live-http-bundle.json) and [bundle instructions](OFFLINE_RELEASE.md).
