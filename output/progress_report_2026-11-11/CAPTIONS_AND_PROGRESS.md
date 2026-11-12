# Progress report evidence — November 11, 2026

These images document the actual desktop research prototype and literal existing source code. The UI was captured in Microsoft Edge from the selected station-v8/research-v13 application. The camera was left off. Code images are browser-rendered source excerpts with original line numbers, rather than screenshots of an IDE. No generative image tool was used.

## Suggested figures and captions

1. **01_current_camera_ui_desktop.png** — Desktop interface of the SkirtFabricSense research prototype, showing the camera controls, presentation selection, fabric toggle and separate attribute-status panels. The camera is off and no prediction is displayed.
2. **02_current_camera_ui_800x480.png** — Initial browser viewport of the interface at 800 × 480 pixels, matching the selected display resolution. Additional controls and reference information extend below the viewport and require scrolling. This capture does not establish physical LCD readability or touch operation.
3. **03_code_training.png** — Implemented transfer-learning code for the MobileNetV2 pleating model, including frozen input/split checks, fine-tuning controls and a GPU execution check. The screenshot documents the implementation; no training was started for this capture.
4. **04_code_frame_freshness.png** — Implemented handling of completed inference work. Results are rejected after disconnection, scene-generation changes or expiry, helping prevent an old classification from reappearing.
5. **05_code_hemline_rules.png** — Implemented hemline-rule logic that requires eight calibrated boundaries, checks the hem uncertainty interval and returns an uncertain result at a category boundary. Real wearer-reference detection and measured calibration remain unfinished.

For a short report, use Figures 1, 3 and 4. Add Figure 5 when discussing the length-estimation work. Figure 2 is useful for documenting the display adaptation and the remaining layout verification. Keep the captions with the images; do not describe a camera-off screenshot as a live classification test.

## Progress paragraph to adapt

The current software prototype provides a camera-first interface with controls for camera selection, capture mode and garment presentation. Separate result panels have been implemented for pleating, hemline length and optional fabric appearance. The training code uses MobileNetV2 transfer learning and records model and dataset identities. The processing controller includes checks that discard stale results after disconnection, a scene change or excessive frame age. Hemline classification rules and uncertainty handling have also been implemented. Current validation is based on development images and software checks. Independent label confirmation, reliable fabric recognition, validated wearer geometry, measured calibration and testing with the actual camera and Raspberry Pi remain in progress.

## How to insert the images

Use the original PNG files, preserve their aspect ratio and place a caption below each figure. Put the wider code images on a landscape page or in an appendix so the text stays legible. Retain the editable HTML excerpts if a larger rendering is needed. Do not enlarge the 800 × 480 capture and describe it as a physical-screen photograph.

## Evidence limits

The application and model files were not modified for presentation. No camera was accessed, no classification result was invented and no model was trained. These screenshots establish interface and code implementation progress only. The capture record contains the served-page/source hashes and the browser viewport sizes.

The initial project-wide records check found pre-existing malformed JSON response files in the interrupted November 4 background-acquisition folder. That finding is saved in records/validation/2026-11-11-progress-screenshots-initial.json. It does not establish a failed screenshot capture, but it prevents claiming the entire project record audit passed. Those acquisition files were preserved for later recovery.
