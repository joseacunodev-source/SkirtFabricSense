import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "tools/datasets/acquire_seed.py"
SPEC = importlib.util.spec_from_file_location("acquire_seed", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class AcquisitionIntegrityTests(unittest.TestCase):
    def test_corruption_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sample").write_bytes(b"original")
            manifest = {"artifacts": [{"path": "sample", "sha256": module.digest(b"original"),
                                       "size_bytes": 8, "kind": "image"}]}
            self.assertEqual(module.verify_manifest(manifest, root)["images"], 1)
            (root / "sample").write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                module.verify_manifest(manifest, root)

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "escapes"):
                module.verify_manifest({"artifacts": [{"path": "../outside"}]}, Path(temp))

    def test_verify_only_never_networks_or_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"artifacts": []}))
            before = manifest.read_bytes()
            with patch.object(module, "ROOT", root), patch.object(module, "MANIFEST", manifest), \
                 patch.object(module, "request", side_effect=AssertionError("Network forbidden")), \
                 patch.object(module, "atomic_write", side_effect=AssertionError("Writes forbidden")), \
                 patch("sys.argv", ["acquire_seed", "--verify-only"]):
                module.main()
            self.assertEqual(before, manifest.read_bytes())

    def test_failed_replace_preserves_original(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            path.write_bytes(b"original")
            with patch.object(module.os, "replace", side_effect=OSError("simulated failure")):
                with self.assertRaises(OSError):
                    module.atomic_write(path, b"replacement")
            self.assertEqual(path.read_bytes(), b"original")
            self.assertEqual(list(Path(temp).iterdir()), [path])


if __name__ == "__main__":
    unittest.main()
