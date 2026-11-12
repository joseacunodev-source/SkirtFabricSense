import json
from pathlib import Path
import tempfile
import unittest

from tools.build_release import build, digest, source_file, MODEL, CONTRACT, RECORD


class ReleaseBuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative, content in [(MODEL, b"fake model"), (CONTRACT, b"{}")]:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.record = {"release_id": "skirt-finetune-v1", "model_files_and_sha256": [
            {"path": MODEL, "sha256": digest(self.root / MODEL)}],
            "contract": {"path": CONTRACT, "sha256": digest(self.root / CONTRACT)}}
        (self.root / RECORD).parent.mkdir(parents=True)
        self.write_record()
        self.out = self.root / "release"

    def write_record(self):
        (self.root / RECORD).write_text(json.dumps(self.record), encoding="utf-8")

    def test_manifest_and_inventory(self):
        metadata = build(self.root, self.out)
        manifest = json.loads((self.out / "manifest.json").read_text())
        self.assertEqual(set(manifest), {"schema_version", "bundle_id", "model", "contract", "files", "status", "pi_verified"})
        self.assertFalse(manifest["pi_verified"])
        self.assertEqual(len(manifest["files"]), 2)
        self.assertEqual(len(metadata["files"]), 2)
        for item in metadata["files"]:
            self.assertEqual(digest(self.out / item["path"]), item["sha256"])

    def test_tamper_rejected_before_output(self):
        (self.root / MODEL).write_bytes(b"modified")
        with self.assertRaises(ValueError):
            build(self.root, self.out)
        self.assertFalse(self.out.exists())

    def test_missing_contract(self):
        (self.root / CONTRACT).unlink()
        with self.assertRaises(ValueError):
            build(self.root, self.out)
        self.assertFalse(self.out.exists())

    def test_no_overwrite(self):
        build(self.root, self.out)
        with self.assertRaises(FileExistsError):
            build(self.root, self.out)

    def test_traversal_and_absolute_paths(self):
        for bad in ["../outside", "/etc/passwd", "C:/secret", "a\\b"]:
            with self.assertRaises(ValueError):
                source_file(self.root, bad)
        self.record["contract"]["path"] = "../outside"
        self.write_record()
        with self.assertRaises(ValueError):
            build(self.root, self.out)

    def test_app_inventory_is_separate(self):
        static = self.root / "app/static"
        static.mkdir(parents=True)
        (static / "index.html").write_text("local")
        (self.root / "app/server.py").write_text("pass")
        metadata = build(self.root, self.out, include_app=True)
        self.assertEqual(len(metadata["files"]), 4)
        self.assertEqual(len(json.loads((self.out / "manifest.json").read_text())["files"]), 2)

    def test_symlink_source(self):
        path = self.root / MODEL
        real = self.root / "real-model"
        path.rename(real)
        try:
            path.symlink_to(real)
        except OSError:
            self.skipTest("OS does not permit unprivileged symlinks")
        with self.assertRaises(ValueError):
            build(self.root, self.out)


if __name__ == "__main__":
    unittest.main()
