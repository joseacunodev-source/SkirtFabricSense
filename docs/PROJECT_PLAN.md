# Project plan

Updated task priorities: October22, 2026. Use the [active task board](TASK_BOARD.md) and [agent handoff](AGENT_HANDOFF.md) for current work and dependencies. The calendar below is the original October1 planning baseline, not current completion evidence. [Latest implementation evidence](OCT22_INTEGRATION.md).

## Outcome

A single-camera, local Raspberry Pi application continuously displays the full skirt and estimates supported skirt attributes, operational length, and visual fabric category. It rejects unusable frames, displays uncertainty, and records reproducible measurements for engineering evaluation. The user controls the main capstone document independently.

The useful research question is whether native-resolution information in a full-skirt frame supports generalizable fabric predictions under a defined capture setup. This is not established by the literature, available GPU, or a polished UI. Treat it as the first feasibility gate.

## Agreed inputs

- One camera; full skirt stays visible; automatic classification without a separate close-up.
- Laptop: ASUS TUF Dash F15, i5-11300H (4 cores/8 threads), RTX 3060 Laptop GPU (6 GB), about 16 GB RAM, Windows 11. Initial disk free approximately 104 GB; snapshots supersede transient figures.
- Existing webcam available; focus/detail suitability unverified.
- Raspberry Pi, LCD, lighting, mount, and enclosure not yet owned. Flexible hardware budget; no specific ceiling agreed.
- Approximately one to two months. Plan for eight weeks with week-four prototype.
- User authorizes project documentation, skills, public dataset acquisition, and delegated engineering tasks.

## Scope decisions and remaining inputs

These do not stop documentation, data discovery, capture experiments, or compatibility research. They do block final dataset labels and claims.

1. Fabric targets: operational appearance classes, separate fabric/fiber attributes, or adviser-required original labels with explicit rules. Never silently decide cotton versus satin precedence.
2. Confirmed style/length scope: independent pleated/non-pleated plus nine hemline categories. Worn skirts are primary; hanging, held and mannequin remain secondary. The earlier short/long proposal is superseded.
3. Length boundary: document physical reference, units, waistband anchor, borderline band, and whether output describes a fixture or a wearer. No unsupported population-average knee inference.
4. Camera and board purchase: pilot image quality, runtime compatibility, budget ceiling, available workspace, and actual component dimensions inform selection.

## Original calendar and gates — historical planning targets

| Window | Work | Required evidence to advance |
|---|---|---|
| Oct 1-7 | Resolve ontology; camera pilot; environment setup plan; acquire permitted datasets | Label guide, reproducible capture geometry, audited source manifest |
| Oct 8-14 | Train full-frame and patch fabric baselines; skirt baseline; export proof | Group-held-out pilot results, conversion report, limitations by class |
| Oct 15-21 | Expand deployment-matched samples; test first Pi runtime; optimize inputs | On-device inference evidence and error analysis; target stack pinned only after success |
| Oct 22-28 | Integrate live preview, inference scheduling, uncertainty, record export | Complete offline prototype, no stale results after garment changes |
| Oct 29-Nov 4 | Address highest-impact errors and app recovery | Validation-selected candidate; measured memory/latency; quality gates |
| Nov 5-11 | Freeze configuration and conduct final evaluation | Locked test report including rejected samples, confidence intervals, device benchmarks |
| Nov 12-18 | Final hardware assembly, clean setup rehearsal, documentation | Installation from release bundle on clean media; enclosure and cooling checks |
| Nov 19-25 | Contingency, reliability checks, demo rehearsal | Repeatable demonstration and complete evidence bundle |

Dates are scheduling targets, not a promise of ML accuracy. If a gate fails, record it and narrow claims or improve samples/optics within the single-view constraint. Do not switch secretly to another capture workflow. Use the week-eight buffer for actual faults, not speculative features.

## Work packages

| ID | Owner role | Deliverable | Dependencies |
|---|---|---|---|
| WP01 | Integration/documentation | Requirements, decisions, architecture, logs, skill workflow | User constraints |
| WP02 | Data engineering | Source registry, annotation guide, deduplication, frozen splits | Ontology and terms review |
| WP03 | ML | Baselines, experiments, calibrated predictions, model release | Pilot data, training environment |
| WP04 | Edge/hardware | BOM, capture station, runtime, repeatable installation | Camera evidence, early exported model |
| WP05 | Application | Live pipeline, UI, state management, exports | Stable inference contract |
| WP06 | Verification | Held-out evaluation, robustness, thermal and recovery tests | Locked candidate and physical Pi |

Agents can research WP02-WP04 in parallel. Acquisition, label changes, shared manifests, package changes, and final integration need a single owner to avoid inconsistent state. No standing autonomous background agent is implied by this plan.

## Original implementation sequence — historical baseline

1. Review recorded open decisions and create annotation rules before final labels.
2. Create an isolated training environment, verify GPU detection, then record exact resolved versions. This environment/GPU/export setup is now completed and recorded in [GPU setup](GPU_SETUP.md); the original setup step is closed.
3. Capture test charts and full skirts using existing webcam. Preserve raw frames and geometry; inspect native patches rather than enlarged previews.
4. Acquire the chosen camera early if the existing device fails detail tests; collect final data with deployment optics.
5. Create specimen IDs and split them before augmentation. Audit permission, duplicates, labels, and leakage in external data.
6. Train lightweight baselines and export at once. Evaluate on unseen physical garments before expanding model complexity.
7. Bring up Pi as early as hardware arrives; lock its runtime only after import, model, camera, and UI checks.
8. Implement full live integration after the basic ML and deployment path are demonstrated.

## Deliberate exclusions from the initial release

Cloud-dependent inference, online inventory integration, automatic retraining in the kiosk, physical fiber-composition measurement, arbitrary camera geometry, multiple simultaneous garments, and claims about unseen textile classes. These exclusions bound engineering effort; retain raw observations needed to reconsider them later.
