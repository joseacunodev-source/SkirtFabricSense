import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from tools.datasets.audit_textilenet_metadata import audit, identities, read_rows


class TextileNetMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, rows):
        path = self.root / name
        path.write_text(json.dumps(rows), encoding="utf-8")
        return path

    def test_duplicate_and_multi_label_evidence_does_not_admit(self):
        url = "https://contestimg.wish.com/api/webimage/58bfea307e5ff95c1752def8-large"
        path = self.write("train.json", [["1_imaterial.jpeg", "denim", url],
                                          ["2_imaterial.jpeg", "chiffon", url],
                                          ["3.jpeg", "denim", "https://example.org/3"]])
        result = audit(path)
        groups = result["train_summary"]["identity_groups"]
        self.assertEqual(groups["exact_url"]["distinct"], 2)
        self.assertEqual(groups["exact_url"]["excess_rows"], 1)
        self.assertEqual(groups["exact_url"]["groups_with_multiple_source_labels"], 1)
        self.assertEqual(result["train_summary"]["source_label_counts"], {"chiffon": 1, "denim": 2})
        self.assertEqual(result["training_admissions"], 0)
        self.assertFalse(result["physical_garment_identity_verified"])
        self.assertFalse(result["instance_material_association_verified"])
        self.assertFalse(result["protected_overlap_checked"])
        self.assertEqual(result["train_input"]["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_protected_identity_check_omits_label_distribution(self):
        train = self.write("train.json", [["1_imaterial.jpeg", "denim", "https://example.org/a?x=1"]])
        held = self.write("test.json", [["1_imaterial.jpeg", "SECRET_TEST_LABEL", "https://example.org/a?x=2"]])
        result = audit(train, [held])
        shared = result["protected_inputs"][0]["train_shared_identity_groups"]
        self.assertEqual(shared["filename"], 1)
        self.assertEqual(shared["host_and_path"], 1)
        self.assertEqual(shared["exact_url"], 0)
        self.assertTrue(result["protected_overlap_checked"])
        self.assertNotIn("SECRET_TEST_LABEL", json.dumps(result))
        self.assertNotIn("source_label_counts", result["protected_inputs"][0]["summary"])

    def test_wish_token_is_identity_lead_not_filename_or_query(self):
        a = identities(["1_imaterial.jpeg", "a", "https://contestimg.wish.com/api/webimage/58bfea307e5ff95c1752def8-large"])
        b = identities(["2_imaterial.jpeg", "b", "http://contestimg.wish.com/api/webimage/58bfea307e5ff95c1752def8-small?x=1"])
        self.assertEqual(a["wish_webimage_token"], b["wish_webimage_token"])
        self.assertNotEqual(a["exact_url"], b["exact_url"])
        self.assertNotEqual(a["filename"], b["filename"])

    def test_rejects_malformed_rows(self):
        bad = [{}, [["a", "denim"]], [["a", "denim", 4]], [["../a", "denim", "https://example.org/a"]],
               [["a", "", "https://example.org/a"]], [["a", "denim", "file:///a"]],
               [["a", "denim", "https://user:secret@example.org/a"]],
               [["a", "denim", "https://example.org:bad/a"]],
               [["a", "denim\n", "https://example.org/a"]]]
        for index, rows in enumerate(bad):
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    read_rows(self.write(f"bad{index}.json", rows))

    def test_declared_bounds_are_enforced(self):
        path = self.write("train.json", [["a", "denim", "https://example.org/a"]] * 2)
        with self.assertRaises(ValueError):
            read_rows(path, max_bytes=2)
        with self.assertRaises(ValueError):
            read_rows(path, max_rows=1)

    def test_api_bounds_are_positive_non_boolean_integers(self):
        path = self.write("train.json", [])
        for key in ("max_bytes", "max_rows"):
            for value in (0, -1, True, False, 1.5, "20", None):
                with self.subTest(key=key, value=value):
                    with self.assertRaisesRegex(ValueError, "positive integers"):
                        read_rows(path, **{key: value})

    def test_growth_after_stat_cannot_trigger_unbounded_read(self):
        class RecordingStream(io.BytesIO):
            def read(self, size=-1):
                self.requested_size = size
                return super().read(size)
        stream = RecordingStream(b"x" * 100)
        with patch.object(Path, "stat", return_value=SimpleNamespace(st_size=1)), \
                patch.object(Path, "open", return_value=stream):
            with self.assertRaisesRegex(ValueError, "grew beyond"):
                read_rows("growing.json", max_bytes=8)
        self.assertEqual(stream.requested_size, 9)


if __name__ == "__main__":
    unittest.main()
