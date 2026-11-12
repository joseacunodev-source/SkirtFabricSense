# Independent development-release verification

`tools/verify_release.py` checks a completed bundle without importing the application, loading TensorFlow/LiteRT, installing packages, or changing any files. It is separate from the builder so that acceptance also examines copied bytes and the complete destination inventory.

```text
python tools/verify_release.py artifacts/releases/skirt-finetune-v1-desktop-async-v2 --require-app
python -m unittest discover -s tests -p test_release_verifier.py -v
```

The verifier exits zero only on acceptance and prints JSON. Failure exits one and includes a reason. Run it after building and again before launching a copied bundle. Use a fresh bundle destination after source changes; verification of an older bundle does not mean it includes the latest application code.

Checks include:

- Schema, development-only status, matching bundle identity, model/contract paths and explicit `pi_verified: false`.
- Exact payload inventory, sizes and SHA-256 hashes, plus agreement between manifest and inventory model hashes.
- Missing and extra files or directories, duplicate/case-colliding paths, duplicate JSON keys, traversal and nonportable path forms.
- Symlinks and Windows reparse points throughout the tree and its ancestors, without following links while scanning.
- Required baseline application files whenever an app is present (or `--require-app` is supplied); pipeline/controller files must appear together.
- The current pleating input/output declaration, label order, preprocessing, inside-model normalization and score semantics.

The baseline application minimum is `inference.py`, `review.py`, `server.py`, `static/index.html` and `static/review.html` under `app/`. This supports the archived synchronous application as well as the async bundle. It is not an analysis of Python imports or proof that a future application has included every new dependency. New application architectures need corresponding acceptance rules and integration tests.

## Evidence — October 9, 2026

Executed using existing Windows Python 3.11.9; no installations or environment changes were made. All **13 tests passed**, including an actual filesystem symlink rejection. Tests cover corruption of unchanged byte length, missing/extra payload, unexpected empty directory, unsafe paths, duplicate entries/JSON keys, cross-metadata disagreement, a rehashed incompatible contract, missing app files, incomplete async pair and false Pi verification claims.

The existing `artifacts/releases/skirt-finetune-v1-desktop-async-v2` passed with **9 payload files**, application included:

| Checked metadata | SHA-256 |
|---|---|
| manifest.json | `98ada650d7dff4cb297377a8f2d3ccb2c102807c298247beb68ca3a47868d437` |
| inventory.json | `ef4ad27288105322c06279ca59c335494266324eed1e0cd19613988e3a3eb278` |

## Limits of acceptance

Hashes detect disagreement against included metadata, not a malicious party replacing both metadata and payload. This is not publisher authentication or signature verification. File contents can also change after verification; run against a stable local bundle and preserve it during launch.

Contract validation examines JSON declarations, not actual model tensor operators. A model with a compatible declaration still needs the existing runtime loading/parity checks. The verifier does not execute camera capture, import every application dependency, prove software correctness, verify licensing, or establish Raspberry Pi compatibility, accuracy, latency or recovery behavior. Its report explicitly leaves runtime verification, publisher authentication and Pi verification false.

See [bundle construction](OFFLINE_RELEASE.md) and [Pi deployment gates](RASPBERRY_PI_DEPLOYMENT.md).
