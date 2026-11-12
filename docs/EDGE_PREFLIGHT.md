# Read-only edge preflight

Implemented October17,2026. Run `python tools/edge_preflight.py --bundle PATH_TO_BUNDLE --output NEW_REPORT.json` with the interpreter intended for deployment. The tool installs nothing, activates no camera and preserves existing reports.

It records OS, architecture, pointer width, Python, libc, board-model text and installed application/runtime distribution versions. It verifies the bundle inventory separately and reports missing prerequisites. A platform/distribution pass is preliminary: runtime imports, operator invocation, reference parity, camera/display/calibration and sustained offline operation remain required. `pi_verified` always remains false in this preflight.

Three synthetic tests passed. The actual Windows desktop check correctly failed the target gate because it is Windows AMD64 with no observed Pi identity or inference distribution in that tooling interpreter. Its17-file research-v7 bundle verification passed. [Actual desktop report](../records/validation/2026-10-17-edge-preflight-desktop.json). This is evidence that the wrong platform is rejected, not a Pi test.

Once a Pi is available, use the chosen edge environment to run this tool, the [environment collector](../tools/collect_environment.py), bundle verification and actual model checks. Log each package operation in the installation ledger and freeze an edge-specific lock only after success. No universal package installer or tested ARM64 lock is claimed by this addition.
