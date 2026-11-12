"""Meaningful leakage and admission regression checks; uses existing Pillow only."""
import copy
import json
from pathlib import Path
import random
import tempfile
import unittest

from PIL import Image
from tools.datasets import audit_candidates as audit
from tools.datasets import prepare_splits as splits


class DatasetPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def record(self, name, seed=1, partition="train"):
        generator = random.Random(seed)
        image = Image.frombytes("RGB", (32, 32), generator.randbytes(32 * 32 * 3))
        path = self.root / f"{name}.png"
        image.save(path)
        return {"sample_id": name, "source_id": "fixture", "source_partition": partition,
                "original_path": path.name, "sha256": audit.sha256(path),
                "width": 32, "height": 32, "group_id": f"listing:{name}",
                "garment_id": None, "terms_reference": "fixture-permission",
                "project_labels": {"test_task": {"value": str(seed % 2), "status": "approved", "evidence": "fixture"}},
                "training_eligibility": {"test_task": {"approved": True, "reason": "fixture"}}}

    def test_corruption_and_dimension_mismatch_rejected(self):
        record = self.record("a")
        record["height"] = 31
        self.assertEqual(audit.audit([record], self.root)["counts"]["integrity_errors"], 1)
        record["height"] = 32
        (self.root / "a.png").write_bytes(b"broken")
        report = audit.audit([record], self.root)
        self.assertEqual(report["counts"]["integrity_errors"], 1)
        with self.assertRaisesRegex(ValueError, "Integrity"):
            splits.prepare([record], report, "test_task")

    def test_decode_rejects_valid_hash_of_nonimage(self):
        record = self.record("a")
        path = self.root / "a.png"
        path.write_bytes(b"not an image")
        record["sha256"] = audit.sha256(path)
        self.assertEqual(audit.audit([record], self.root)["counts"]["decoded_images"], 0)

    def test_path_escape_and_duplicate_ids_rejected(self):
        record = self.record("a")
        record["original_path"] = "../outside.png"
        self.assertIn("escapes", audit.audit([record], self.root)["images"][0]["error"])
        manifest = self.root / "samples.jsonl"
        manifest.write_text(json.dumps(record) + "\n" + json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            audit.load_records([manifest])

    def test_exact_duplicate_of_holdout_never_enters_training(self):
        train = self.record("train", seed=2)
        holdout = self.record("holdout", seed=2, partition="val2020")
        report = audit.audit([train, holdout], self.root)
        result = splits.prepare([train, holdout], report, "test_task")
        self.assertEqual(result["counts"]["admitted_records"], 0)
        self.assertEqual(report["counts"]["unique_file_hashes"], 1)
        self.assertEqual(report["counts"]["verified_physical_garment_ids"], 0)

    def test_source_labels_do_not_become_project_labels(self):
        record = self.record("a")
        record["source_labels"] = {"fabric": "satin"}
        record["project_labels"] = {}
        result = splits.prepare([record], audit.audit([record], self.root), "test_task")
        self.assertEqual(result["counts"]["admitted_records"], 0)

    def test_task_approval_does_not_transfer_and_missing_terms_rejected(self):
        record = self.record("a")
        report = audit.audit([record], self.root)
        self.assertEqual(splits.prepare([record], report, "fabric")["counts"]["admitted_records"], 0)
        del record["terms_reference"]
        self.assertEqual(splits.prepare([record], report, "test_task")["counts"]["admitted_records"], 0)

    def test_parents_and_transitive_groups_stay_together(self):
        records = [self.record(str(i), seed=i) for i in range(3)]
        records[1]["parent_sample_id"] = "0"
        records[2]["group_id"] = records[1]["group_id"]
        report = audit.audit(records, self.root, near_distance=0)
        result = splits.prepare(records, report, "test_task")
        self.assertEqual(len({r["group_hash"] for r in result["assignments"]}), 1)
        self.assertEqual(len({r["split"] for r in result["assignments"]}), 1)
        self.assertEqual(report["counts"]["original_records"], 2)

    def test_missing_parent_fails_instead_of_leaking(self):
        record = self.record("a")
        record["parent_sample_id"] = "absent"
        with self.assertRaisesRegex(ValueError, "Missing parent"):
            splits.prepare([record], audit.audit([record], self.root), "test_task")

    def test_near_duplicate_connected_to_holdout_is_excluded(self):
        records = [self.record(str(i), seed=i, partition="test" if i == 2 else "train") for i in range(3)]
        report = audit.audit(records, self.root, near_distance=0)
        report["near_duplicate_candidates"] = [{"sample_ids": ["0", "1"], "distance": 1},
                                                {"sample_ids": ["1", "2"], "distance": 1}]
        self.assertEqual(splits.prepare(records, report, "test_task")["counts"]["admitted_records"], 0)

    def test_unknown_partition_excluded_and_input_order_deterministic(self):
        records = [self.record(str(i), seed=i) for i in range(20)]
        records[0]["source_partition"] = "unresolved"
        report = audit.audit(records, self.root)
        first = splits.prepare(records, report, "test_task")
        second = splits.prepare(list(reversed(records)), report, "test_task")
        self.assertEqual(first["assignments"], second["assignments"])
        self.assertNotIn("0", {r["sample_id"] for r in first["assignments"]})
        self.assertEqual(len(first["counts"]["partitions"]), 2)

    def test_report_does_not_overwrite_existing_evidence(self):
        path = self.root / "result.json"
        audit.write_json(path, {"result": 1})
        with self.assertRaises(FileExistsError):
            audit.write_json(path, {"result": 2})
        self.assertEqual(json.loads(path.read_text())["result"], 1)


if __name__ == "__main__":
    unittest.main()
