# Compact camera interface

Implemented source reviewed November 11, 2026. At an 800 × 480 landscape browser viewport, the camera preview, Start/Stop controls, camera selector, presentation selector, camera-mode selector, four attribute values and fabric switch are visible together without scrolling. The long hemline reference and framing instructions use keyboard-accessible native disclosures. Opening guidance can extend the page and require scrolling; closing it restores the compact view.

The cream and burgundy interface, worn-primary default, four presentation modes, nine hemline categories and independent unavailable states remain in place. The compact camera preview is 205 CSS pixels high. Start, Stop, the three selectors and the fabric-switch label each have at least 44 CSS pixels of height in this viewport. These dimensions are browser measurements, not physical screen or touch measurements.

## What changed

The camera action row uses a compact grid, placing camera selection beside Start and Stop instead of pushing actions onto another row. Presentation and requested camera mode have their own rows below the preview. Result cards use less vertical padding while retaining their labels, values and reasons. Extended reference content is available under **Hemline reference**, and **Framing and setup guidance** opens below the two main panels.

The live inference JavaScript and capture/expiry schedule were not changed by this layout work. Camera access still requires the operator to choose Start camera. Controls that change the scene or configuration keep their existing invalidation behavior. Reduced-motion settings, synchronous result clearing, the fabric switch and explicitly uncalibrated score display remain covered by the lifecycle checks.

## Verified evidence

- The existing Node fixture passed 18 camera/live-loop scenarios, 21 score cases, six motion cases and seven camera-mode/safety cases: **52 mocked cases**.
- The actual HTML passed **six Edge browser layout scenarios**: compact camera-off, settings changed, synthetic attribute text, disclosures closed again, desktop camera-off and a 390-pixel portrait view. The compact scenarios check that essential controls and values remain inside 800 × 480, with no horizontal overflow. The portrait check allows vertical scrolling.
- Keyboard opening/closing of both native disclosures passed. All nine hemline labels and all four presentation options remain present.
- The browser check made zero camera requests and stopped its owned local HTTP server. Its temporary synthetic result text is layout-test input only, not model or camera evidence.
- Independent source-hash review matched the earlier saved browser result: `40618a91db6b19cd918d70ad10056cd79aaa9c0b44b869d60f2bc60c53c68f3f`.

[Independent browser report](../records/validation/2026-11-11-compact-layout/independent-review/browser.json), [800 × 480 screenshot](../records/validation/2026-11-11-compact-layout/independent-review/camera-off-800x480.png), [desktop screenshot](../records/validation/2026-11-11-compact-layout/independent-review/camera-off-desktop.png), and [source-bound review record](../records/validation/2026-11-11-compact-layout/independent-review/review.json).

Both screenshots show the actual camera-off interface. They contain no generated garment image or fabricated classification. The prior source-level report and screenshots remain preserved in the parent evidence directory.

## Reproduce

Use the existing bundled Node runtime from the project root. No packages were installed.

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' tests/camera_ui_lifecycle.cjs
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' tests/compact_layout_browser.cjs records/validation/NEW-COMPACT-LAYOUT-CHECK
```

The browser check refuses to overwrite an existing report; choose a fresh output directory. It serves the current source HTML on an owned ephemeral loopback port, opens existing Microsoft Edge through Playwright, and closes its browser/server after completion.

## Remaining acceptance

The source change needs a new immutable app/station package and its usual inventory/HTTP verification; it does not alter an existing frozen station in place. Follow the centrally selected version in [the station guide](STATION_PACKAGE.md) rather than assuming that editing `app/static/index.html` changed an old package.

Actual Waveshare display readability, resistive-touch accuracy, browser scaling, full-skirt preview detail and simultaneous live inference remain untested. Test the final OS display setup and all essential actions on the physical Pi station before demonstration acceptance. Software layout verification does not establish model accuracy, measured length or Raspberry Pi performance.
