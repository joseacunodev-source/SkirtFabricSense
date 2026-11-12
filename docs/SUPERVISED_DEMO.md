# Supervised capstone demonstration target

October22: station-v2 is selected for desktop research after independent model and HTTP review. It still falsely accepts10/52 development negatives; fabric, calibrated length and physical/Pi acceptance remain unfinished. The supervised demonstration is not accepted. [Current evidence](OCT22_INTEGRATION.md), [task board](TASK_BOARD.md).

October 19: the presence follow-up passes a relative development comparison and saved-frame app checks. It still falsely accepts 13/52 development negatives; fabric, calibrated length and physical/Pi acceptance remain unfinished. The supervised demonstration is not accepted. Use the [current task board](TASK_BOARD.md) and [latest evidence](OCT19_RECOVERY.md).

User clarification, October 14, 2026: the requested 85% refers to **project completion**, and public use means a **supervised capstone demonstration**. It does not set an 85% model accuracy claim. The one-camera requirement, four presentation modes, fabric toggle and nine hemline classes remain in scope.

The demonstrator should explain which outputs are experimental and which are unavailable, keep the full skirt visible, and use only supported/calibrated placements. A supervisor does not make unsupported fabric or length results valid. Keep unavailable outputs explicit rather than filling them with guesses.

## Demonstration acceptance

| Check | Current evidence | Still required |
|---|---|---|
| Start/stop preview and automatically process current frames | Desktop integration, mocked lifecycle tests and earlier physical preview connection | Rehearsal using the actual demonstration camera and lighting |
| Pleating and localization | Exported development models and paired source-image evaluations | Reliable performance on unseen demonstration garments, including non-skirts |
| Fabric toggle | Toggle and optional research appearance path verified through saved-frame HTTP | Defensible labels, sufficient groups and an accepted model beyond the tiny automatic-crop pilot |
| Nine hemline labels | Conservative geometry/hem adapters, optional pose candidates and measured-calibration builder | Geometry extraction, measured reference and all supported-mode checks |
| Scene change, disconnection and stale outputs | Controller and UI tests | Physical removal/replacement/disconnection rehearsal |
| Offline Pi operation | Documented deployment plan and desktop export | Actual ARM64 installation, inference, camera/display operation and measured runtime |
| Reproducible demo | Versioned bundle and data/run records | Freeze the accepted model/profile/configuration, rehearse and preserve rollback |

## Current sequence toward demonstration acceptance — October 17

- [x] Complete negative and presentation review; freeze grouped development inputs.
- [x] Train/export detection candidates and perform paired comparisons; retain failed candidates without promotion.
- [x] Verify research-v7 default and optional fabric/pose paths with saved images.
- [ ] Improve detection and fabric performance sufficiently for an accepted candidate (S01–S05).
- [ ] Validate wearer references and measured hemline calibration (S06/P02).
- [ ] Evaluate the actual camera and unseen demonstration garments (P01/P03/P04).
- [ ] Install and test the actual Pi station, then freeze/rehearse the accepted release (S07/P05–P07).
- [ ] Verify secondary presentation modes separately (M01).

Task IDs and dependencies are maintained in the [active task board](TASK_BOARD.md). Worn skirts are the primary demonstration workflow; secondary options remain in scope.

The current completion estimate is not automatically raised to 85% because this target was requested. Only accepted work closes a milestone. Missing physical evidence remains open until the actual camera setup, garments and Pi are available.
