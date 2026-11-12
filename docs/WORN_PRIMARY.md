# Worn skirts as the primary workflow

October22: the current research launch is [station-v2](STATION_PACKAGE.md), with category-aware gate/localizer and explicit research fabric opt-in. Worn-first scope is unchanged. Validated wearer references, observed geometry and physical acceptance remain missing. Use [the current handoff](AGENT_HANDOFF.md) and [task board](TASK_BOARD.md); older checklists below are dated.

Updated October 16, 2026. The user explicitly retained hanging, held and mannequin presentations as secondary options.

October 19 status: presentation review, the 265/66 worn subset and the expanded negative freeze are complete. The optional v4 presence/localizer-v2 chain improves relative development results, but worn-domain fabric labels, observed wearer references, measured calibration and real-garment/Pi acceptance remain open. The [active task board](TASK_BOARD.md) supersedes the older checklist below. [Evidence](OCT19_RECOVERY.md).

## Implemented

The camera page explicitly selects Worn by a person and groups the other modes as secondary. Framing guidance changes with the selected mode. Worn guidance requests the entire skirt and waist-to-feet/floor reference in one frame; the face is not required. Changing mode still invalidates old results. Fabric retains its independent switch. No model, frozen split, calibration profile or archived release bundle was changed.

Verification: `node tests/camera_ui_lifecycle.cjs` passed all 14 mocked camera/live-loop scenarios, including worn framing guidance and switching to the secondary reference guidance. These checks do not measure physical framing, recognition accuracy or Pi behavior. No dependency installation or camera activation occurred. The source app has this update; the immutable research-v5 bundle retains its earlier UI.

## Current implementation checklist — October 17

The [task board](TASK_BOARD.md) is authoritative for current priorities; implementation/verification notes above describe the October16 UI change.

- [x] Complete presentation review and freeze the 265/66 worn development subset.
- [x] Implement optional body-keypoint candidates, conservative hem extraction and measured-calibration preparation.
- [x] Connect and evaluate research-only fabric appearance; preserve the toggle and attribute independence.
- [ ] Improve usable detection/rejection after source/label review (S01–S03).
- [ ] Expand evidence-backed fabric groups, train and validate an accepted candidate (S04–S05).
- [ ] Validate actual wearer/waist/floor references and hem extraction (S06).
- [ ] Measure physical calibration and test unseen garments (P01–P04).
- [ ] Verify the real Pi station and supervised demonstration (P05–P07).
- [ ] Verify secondary presentations separately (M01).

Research prototypes do not establish accepted automatic length or fabric performance. [Completed work and limits](OCT17_NEXT_MILESTONE.md).

## Unchanged boundaries

One camera, one full-skirt frame; no sequential close-up. Hanging/held use a calibrated standard-body estimate, not the holder's anatomy. Mannequin mode uses its verified reference. This priority change does not establish automatic hemline extraction, production fabric recognition, public readiness or an increase in measured project completion.
