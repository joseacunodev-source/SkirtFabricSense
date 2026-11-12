# Hardware and capture plan

November 4: user selected Waveshare 14447 (800 × 480, HDMI video and USB resistive touch). Station-v7/research-v12 contains the compact landscape UI, verified with 45 mocked cases and 12 saved-image HTTP jobs. Station-v6 is rollback. Physical screen, touch, camera and Pi performance remain unverified. [Waveshare 14447 layout](LCD_14447_LAYOUT.md).

Current recommendation: **Pi 5 8GB, official 27W supply, compatible active cooling, 64GB microSD and one autofocus USB webcam**. C920s is the economical candidate; Brio 4K is the higher-detail comparison if affordable. See [November 4 purchase/project review](PURCHASE_REVIEW_NOV04.md) for sources, limits and setup order. Purchase is planned, not confirmed.

Planning baseline: **1 October 2026, Asia/Manila**; reviewed **2 October 2026**. Status: **proposed; no Raspberry Pi hardware has been purchased or tested for this project**. This file is an engineering record for the implementation, not a capstone manuscript chapter.

## Fixed requirements

- Use one physical camera and one full-skirt view for skirt style, length, and fabric prediction.
- Native-resolution software crops from that same frame are allowed. A second camera, separate close-up capture, or moving the skirt nearer for fabric recognition is outside the agreed workflow.
- Show continuous live preview and automatic results. Training runs on the laptop; final inference must run offline on the selected Raspberry Pi.
- Optimize capture detail before spending on inference acceleration. A faster computer cannot recover texture that the camera did not capture.

The user last confirmed no webcam on October 23 and plans to buy one as of November 4; older webcam access is historical. Its model, negotiated resolution, focus distance, exposure controls, and suitability still need measurement. The previously discussed RTX 3060 laptop is the training host; use the project environment inventory for verified laptop specifications.

## Bill of materials

Prices and vendors are deliberately unfilled until local quotes and exact SKUs are checked. Quantities below are planning quantities, not a purchase order.

| Item | Quantity | Status / priority | Selection rule |
|---|---:|---|---|
| Raspberry Pi 5, 4GB or 8GB | 1 | Proposed, required for deployment | 4GB is a starting candidate for small CPU models; choose 8GB for additional application memory if the quote is acceptable. Extra RAM does not guarantee faster inference. |
| Official Raspberry Pi 27W USB-C supply | 1 | Proposed, required | Budget for the Pi and connected peripherals; test voltage stability under camera/display/inference load. |
| Active cooling and compatible ventilated case | 1 set | Proposed, required | Confirm case/cooler fit and camera-cable clearance. Preserve airflow in the final enclosure. |
| Reliable microSD, proposed 64GB | 1 | Proposed, required | Capacity is a starting estimate for OS, releases, and bounded logs; measure actual usage. Full training dataset stays on the laptop. |
| Backup microSD or recovery image destination | 1 | Proposed, required for recovery | Store a tested recovery image and installation manifest. A second card makes demonstration recovery easier. |
| Previously used fixed-focus webcam | 0 confirmed available | Historical; no current availability | Test before assuming it is unusable; record actual decoded frame size and focus quality. |
| Final camera: autofocus USB UVC or Camera Module 3 standard | 1 total | Proposed, required; choose one | Select using the full-skirt image-quality test below. USB supports laptop collection and Pi deployment using the same camera. CSI requires the Pi for capture. |
| CSI Standard-Mini camera cable | 1 if CSI selected | Conditional required | Camera Module 3 has a 15-pin connector; Pi 5 uses the 22-pin mini connector. Verify length and routing. |
| Waveshare 5inch HDMI LCD (G), SKU 14447 | 1 | User selected; not physically verified | Check readable result sizes, touch calibration, resolution/orientation, power, and Pi 5 compatibility. External monitor can serve development. |
| Display/data/power cables | As selected | Conditional required | HDMI display requires suitable micro-HDMI cable and often USB for touch; DSI requires the exact Pi 5 cable and supported driver. |
| Rigid camera support and skirt fixture | 1 set | Proposed, required | Repeatable camera height, distance, angle, and waistband placement; avoid handheld capture as the default deployment geometry. |
| Plain matte background | 1 | Proposed, required | Contrast with light and dark garments without strong reflections or distracting patterns. |
| Diffuse continuous lighting and supports | 1 set | Proposed, required | Cover the full skirt evenly; avoid visible flicker, glare, and deep fold shadows. Record arrangement and settings. |
| Ruler/reference target and focus target | 1 set | Proposed, required | Calibrate in the garment plane and verify detail at full-skirt distance. Keep visible reference outside the fabric region used by the model. |
| Enclosure and strain relief | 1 set | Proposed, after geometry stabilizes | Fix accessible connectors, airflow, camera alignment, and service access. |
| USB SSD or external laptop drive | 1 | Optional, based on storage measurements | Useful for dataset/checkpoint storage; unnecessary for a small Pi inference bundle unless logs demand it. |
| Accelerator / AI HAT / AI Camera | 0 baseline | Deferred | Only consider after measured CPU latency misses the target. Each introduces another model-conversion and compatibility path. |

Official Pi 5 specifications support the board/power/cooling shortlist; they do not establish this application's frame rate. [Raspberry Pi 5 product page](https://www.raspberrypi.com/products/raspberry-pi-5/). Cable selection follows the official camera installation guide. [Camera installation](https://www.raspberrypi.com/documentation/accessories/camera.html).

## Camera selection and acceptance

An autofocus USB UVC camera is the practical first comparison because it can be used unchanged for laptop data collection and Pi deployment. Do not choose a retail model until its actual modes and Linux focus controls are verified. Advertising terms such as “4K” are insufficient if the useful mode is heavily compressed or interpolated.

Camera Module 3 standard is the official CSI candidate: a 4608 x 2592 sensor with autofocus and a visible-light IR filter in its standard variant. The wide version has a larger field of view; choose it only if the available room requires it. The standard field of view is the first candidate to keep more pixels on the garment. Its maximum sensor resolution is not a promise of that resolution at a requested streaming frame rate. [Camera Module 3 specifications](https://www.raspberrypi.com/products/camera-module-3/).

At the **same final full-skirt distance**, collect the following before committing to final camera settings:

1. Entire waistband, hem, and side boundaries visible on the largest planned skirt; record safety margins and physical mounting dimensions.
2. Actual sensor/output mode, pixel format, decoded dimensions, frame rate, exposure/gain, white balance, focus behavior, and any crop/binning. Save an original frame as evidence.
3. Detail samples from the center, edges, dark folds, shiny surfaces, and patterned fabric. Judge native pixels before resizing. Reject persistent blur or compression artifacts that erase the needed cues.
4. Focus acquisition and stability when a garment changes. Where supported, focus automatically, then lock for the settled garment; record the control values and unlock/reset rule.
5. Measured preview and inference latency with that mode. Compare higher-detail/slower modes against lower-detail/faster modes on unseen specimens.
6. Repeat across separate sessions and lighting conditions expected in the demonstration. Count failed captures and uncertain fabric results.

The candidate passes only when the pilot shows usable fabric information and repeatable skirt boundaries. Super-resolution, digital zoom, or sharpening must not be counted as evidence of newly observed fabric structure. Fabric identification from a full view remains a feasibility risk even with a sharper camera.

## Length reference and geometry

The user has selected worn skirts as the primary workflow. Hanging, held and mannequin presentations remain secondary with separate reference conditions.

- **Secondary mounted mode:** fix the waistband position, camera, and approximate garment plane; define length classes using a documented reference measured in that setup. Measure actual garment length separately for ground truth. Perspective calibration is a projected-length estimate when draping moves the fabric out of plane; quantify that error before displaying centimeters.
- **Primary worn mode:** a knee-relative label requires a visible/known body reference and a definition for obscured knees. A full-skirt crop alone does not provide a wearer's anatomical scale.
- Recalibrate after changes to camera position, optical/digital zoom, output crop, resolution mapping, or the fixture. Do not use an average population height as a substitute for calibration.

Save camera parameters, an annotated setup photograph, reference dimensions, calibration ID, and measured repeatability with each accepted station configuration.

## Purchase sequence

1. Obtain one suitable USB webcam and test it on the laptop at full-skirt/wearer framing; measure available room geometry and collect garment evidence.
2. Obtain a shortlist quote for one final camera, Pi 5, power, cooling, storage, mounts, and lighting. Confirm exact camera controls and return/demo options before purchase.
3. Bring up the Pi and camera early enough to run the first exported model; do not postpone compatibility testing until the final week.
4. Choose display/enclosure once camera geometry and application memory/performance are measured.

For each purchased part, record SKU, hardware revision where available, supplier, purchase date, actual cost, driver/firmware requirements, and test outcome in the project hardware inventory when created. Keep receipts and device serial numbers in private purchase records rather than publishing them in shared reports. Current purchase total: **not established**.
