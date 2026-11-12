# Offline development bundle

October22: use [portable station-v2](STATION_PACKAGE.md) for the selected desktop research configuration. It packages the verified research-v7 app with its presence/localization/fabric files; station-v1 remains rollback. Both actual desktop HTTP checks pass. Dependencies and physical calibration are not bundled, and Pi execution remains unverified. Older bundle history below is preserved.

## Research-v7 desktop bundle — October 17

17 payload files include optional pose/fabric adapters and the unchanged pleating model. Separate optional models and installed runtime are required. Inventory SHA-256 `0128196438e5b3fb61ba2bab224b351b3de9e9b1e6eb50a171711804bc231eb5`. Default and research saved-frame HTTP/inventory checks passed; neither establishes camera accuracy or Pi compatibility. [Evidence](OCT17_NEXT_MILESTONE.md).

## Research-v6 desktop bundle — integrated October 17

`artifacts/releases/skirt-finetune-v1-desktop-research-v6` contains 15 verified payload files, including the worn-first UI and conservative geometry helper. Inventory SHA-256: `3ae08c98f4cf6b00dab61cf7d6e0085dd4cd9447c38877a78c127c3c10346950`. Three saved-frame HTTP outputs matched the reference, with inventory checks before/after the private server stopped. [Evidence](../records/validation/2026-10-16-live-http-bundle.json). No pose detector, live fabric model, calibration or dependencies are supplied. This is desktop research packaging, not Pi or supervised-demo acceptance.

October 15: the new `artifacts/releases/skirt-finetune-v1-desktop-research-v5` retains the selected pleating model and adds strict localizer preprocessing, threshold and tensor-count checks. All 14 payload hashes passed verification before and after an actual private HTTP run; three saved-frame results matched the previous selected path exactly. [HTTP evidence](../records/validation/2026-10-15-live-http-bundle.json). Inventory SHA-256: `67abdcbd001d043eac9b750c969817a69001ce6fde0affcd3232a1c67de29a15`. Experimental localization models remain separate. No camera, fabric, length or Pi accuracy is inferred.

October 12: `artifacts/releases/skirt-finetune-v1-desktop-research-v4` contains 14 verified payload files with the unchanged selected pleating model. Optional presence and localization artifacts are separate; fabric smoke is not included. Inventory SHA-256: `3166d41acd954a2197afc9d510edc2e73425368184371fca2161dbbf34e5eee5`. Three saved development frames matched previous results through its actual HTTP server; integrity passed again after shutdown. [HTTP evidence](../records/validation/2026-10-12-live-http-bundle.json). This is laptop/WSL verification, not Pi installation or webcam accuracy. Reproduce with `tools/check_bundle_http.py --bundle PATH --output NEW_JSON_PATH` using the documented training interpreter; it starts and stops a private loopback server without accessing a camera.

The standard-library builder packages the existing pleating model and its unchanged preprocessing contract for local development. It verifies both files against the recorded fine-tuned release before copying. It does not install anything, download assets, include training data, or establish Raspberry Pi compatibility.

```text
python tools/build_release.py --output artifacts/releases/skirt-finetune-v1-desktop --include-app
```

The destination must not exist. Preserve previous bundles; use a new destination after application changes. Sources and destination ancestors must not be symlinks or Windows reparse points. Path traversal, unexpected source paths, missing source files and checksum changes fail the build. A failed copy leaves an incomplete directory without a completed manifest; do not use it.

`manifest.json` is the model loader contract: schema version 1, bundle ID `skirt-finetune-v1`, local `model.tflite` and `contract.json` paths, their SHA-256 checksums, status `development_only`, and `pi_verified: false`. `inventory.json` separately records every copied payload file, its size/hash, the builder hash and original release-record hash. The optional application payload consists of `app/*.py` and flat `app/static/*` files present at build time. Application changes require rebuilding into a new directory. Checksums detect accidental alteration; they are not cryptographic signatures establishing publisher trust.

No dependency wheels, camera drivers, operating-system image or installer are included. Running offline still requires a separately installed compatible runtime and application dependencies. Review image/pretrained-weight redistribution rights before distributing model bundles publicly. No training photos are packaged.

## Real Raspberry Pi gates still pending

1. Record the actual ARM64 OS, Python ABI, glibc and camera configuration.
2. Resolve, install and log a compatible inference runtime and application dependencies; create a separate tested edge lock and environment snapshot.
3. Verify bundle checksums before loading; check tensor shape, dtype, ordered labels and normalization against the bundled contract.
4. Compare reference inputs against laptop outputs and measure latency/memory on the device.
5. Test camera failure, stale-result clearing, offline operation, sustained temperature/load, restart and recovery.
6. Retain the old bundle for rollback and record a real deployment acceptance report before changing any Pi verification status.

See [Raspberry Pi deployment](RASPBERRY_PI_DEPLOYMENT.md) for the full acceptance plan and [fine-tuning evidence](FINETUNING_RESULTS.md) for model limitations. Fabric recognition, length calibration and automatic garment localization are not supplied by this model bundle.
# October 10 development bundle

`artifacts/releases/skirt-finetune-v1-desktop-live-v3` contains 12 checksummed payload files for the current camera application and pleating model. The independent verifier passed; the actual bundled server matched three archived automatic-path outputs over HTTP using the separately supplied localizer. [Integration evidence](../records/validation/2026-10-10-integration-summary.json), [HTTP evidence](../records/validation/2026-10-10-live-http-bundle.json), [launch instructions](LIVE_AUTOMATIC_PILOT.md).

The optional localizer is under `artifacts/models/skirt-localizer-v1`, not embedded in this bundle. Use `python -B -m app.server` when running inside an immutable release directory so bytecode caches do not add unlisted files. Dependencies are not included; this is neither a clean-machine installer nor a verified Pi release. Earlier bundles remain preserved.
