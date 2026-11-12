# Purchase and project review — November 4, 2026

The project is ready to enter hardware development, not ready for a full-feature public demonstration. The user plans to buy a Pi and webcam; purchase and possession are not yet confirmed. Worn skirts remain primary, with hanging/held/mannequin secondary. Preserve one live full-skirt frame, nine hemline labels, independent pleating and the optional fabric switch.

## Recommended first purchase

| Part | Recommendation | Reason / condition |
|---|---|---|
| Board | Raspberry Pi 5, **8GB** | Engineering recommendation for browser plus several CPU models and development headroom. 4GB is a budget alternative requiring memory measurement. More RAM does not make the same model intrinsically faster; 16GB and AI accelerators are not justified yet. |
| Power | Official Raspberry Pi **27W USB-C supply**, suitable local plug | Official guidance recommends this for Pi 5; a recognized 5V/5A supply enables the larger shared USB power budget. Include webcam/display consumption in testing. |
| Cooling | Official Active Cooler and a case explicitly compatible with it | Sustained inference needs thermal testing. Avoid buying incompatible or redundant case-fan assemblies. |
| Storage | Reputable **64GB microSD**, card reader and spare/recovery medium | Proposed capacity for OS, application and bounded logs; keep training datasets on the laptop. SSD can wait. |
| Camera, economical | **Logitech C920s Pro HD**, exact SKU verified | Published autofocus and 1080p/30. Suitable first candidate for framing/pleating experiments; no assurance of sufficient full-view fabric detail. |
| Camera, higher-detail candidate | **Logitech Brio 4K Business/Pro**, exact 4K model verified | Published autofocus, 4K/30 and 1080p/60. Preferred comparison if affordable because texture is a project risk. Use suitable USB 3 cable/port; actual Linux modes, controls and full-frame latency still require testing. Do not confuse other Brio models with this model. |
| Capture setup | Rigid camera mount, diffuse lighting, matte background, tape measure/reference target | These affect full-skirt detail and geometric repeatability. Leave budget for them and actual garments. |
| Display | Use an available HDMI monitor initially; buy final LCD after testing | Include micro-HDMI-to-HDMI cable. A laptop HDMI socket is usually an output, not a Pi display input. Touch/display power and cable requirements depend on the exact LCD. |

Choose one camera, not both. Buy from a seller with a useful return/testing policy and verify the exact model, original resolution, mounting options and included USB cable. Local quotes and stock have not been checked; no price or order is asserted. Basic UVC video does not establish support for every proprietary control on Linux. Do not depend on Logi Tune, face tracking, digital zoom or background effects for the Pi workflow.

Primary manufacturer sources checked November 4: [Pi 5 specifications](https://www.raspberrypi.com/products/raspberry-pi-5/), [Pi power documentation](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/computers/raspberry-pi/power-supplies.adoc), [Active Cooler](https://www.raspberrypi.com/products/active-cooler/), [C920s](https://www.logitech.com/en-us/shop/p/c920s-pro-hd-webcam.960-001257), [Brio 4K](https://www.logitech.com/en-us/business/shop/p/brio-4k-hdr-webcam.960-001105), [Logitech UVC/USB guidance](https://support.logi.com/hc/en-us/articles/360060226873-Capture-requirements). These support advertised specifications, not project-specific compatibility or measured performance.

## Actual software findings

- Station-v6/research-v11 remains selected; its 28 station payload files and 17 application payload files verify. It contains no dependency installer or tested ARM64 lock. V5 remains rollback.
- Saved source-domain development results remain 44/66 skirts accepted, 38/66 correct pleating, and 42/52 negatives rejected. This leaves 22 unavailable skirts and 10 false accepts. The [paired analysis](DETECTION_UNCERTAINTY_OCT23.md) reveals three gained and three lost correct skirt results versus v4, not identical per-image behavior. No new inference or accuracy gain is claimed here.
- Fabric remains a 17-group appearance smoke, with five validation examples and no accepted production model. The [blind evidence queue](FABRIC_EVIDENCE_REVIEW.md) has zero submissions. Better optics cannot establish fibre composition from appearance alone.
- Length adapters and calibration tooling exist, but accepted wearer-reference detection, observed geometry and measured calibration are missing. The device will not automatically produce reliable nine-class length merely after installation.
- The live UI calls getUserMedia with a device ID or video:true; it does **not** request 1080p/4K. It captures the negotiated video dimensions into its canvas. Add a mode selector, negotiated-mode reporting and safe resolution-change invalidation before comparing cameras; preserve the single-frame pipeline and payload limits.
- Runtime loading expects an Interpreter API from ai_edge_litert.interpreter, tflite_runtime.interpreter or TensorFlow. A CompiledModel-only installation is not a drop-in replacement. Validate all selected exported operators and preprocessing on ARM64 before locking versions.
- The October 22 checkpoint had four stale document hashes from unfinished October 23 integration. The original checkpoint is archived before reconciliation. No training/preview process matched the scoped WSL check on November 4.
- COCO intake attempts acquired zero images: TLS hostname failure, then HTTP 404. Failed sources and executed code are retained. Commons tool code exists but no acquisition record exists; it must not be represented as a completed download. Collection remains 1,932 registered originals.

The focused review reran **73 tests, all passed**, covering fabric review, saved-prediction analysis, COCO intake and continuation references. The prior intake fixes now reject mismatched creator accounts and return failure status for a failed acquisition. This is targeted software evidence, not a rerun of every application test or a hardware benchmark. No packages were installed and no model weights changed.

## Bring-up order after purchase

1. **Laptop camera acceptance:** record exact SKU/USB ID, actual resolution/frame rate, autofocus and focus-lock behavior, lighting and original frames. Frame waistband through feet/floor for worn-reference work, with safe margins. Keep automatic cropping/zoom off. Compare 1080p and higher modes at the same full-body distance; do not move closer for fabric.
2. **Collect garments:** identify actual garments and evidence for their labels, separate development and unseen test garments before predictions, and include dresses/trousers/empty scenes. Repeated frames are not independent garments. Record consent for wearable captures.
3. **Pi platform:** choose a named supported 64-bit Raspberry Pi OS Desktop image, record its checksum and Python/glibc versions, then resolve a matching ARM64 runtime. Historical runtime wheel tables are candidates, not installation instructions. Preserve system Python. Record every install and collect the Pi environment snapshot separately from WSL.
4. **Saved-frame parity:** verify the station inventory, run edge preflight, import the actual Interpreter, invoke all selected models and compare the same permitted development frames with laptop results. Resolve any ABI/operator failures before camera integration.
5. **Live integration:** use the Pi-local browser at localhost with the USB camera connected to the Pi. A remote laptop browser captures its own camera and is a different topology. Check permission, resolution, focus, stale clearing, camera disconnect and reconnect.
6. **Geometry and model improvements:** annotate actual wearer/hem evidence, measure and validate calibration, confirm fabric vocabulary/labels, retrain justified candidates on the laptop and export/parity-check before release. Hanging/held estimates require their own standard-body calibration.
7. **Acceptance:** benchmark full pipeline latency/coverage, memory and thermal behavior for a 60-minute session, cold reboot, offline operation and rollback. Verify the chosen LCD at its actual resolution. Freeze the accepted installation and recovery record only after these pass.

Next software priority is capture-mode selection and reporting, followed by usable review/collection flows. No completed training run should be restarted just because hardware is ordered. No overall completion percentage or finish date is inferred from this purchase review.
