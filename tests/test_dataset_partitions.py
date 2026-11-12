"""Adversarial checks of existing split metadata; no model or image loading."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.audit_dataset_partitions import audit_partitions, load_rows


def row(name, split="development_train", **extra):
    return dict(sample_id=name, split=split, source_partition="train2020", **extra)


def codes(report):
    return {issue["code"] for issue in report["issues"]}


class DatasetPartitionTests(unittest.TestCase):
    def test_disjoint_development_passes_without_claiming_final_test(self):
        report = audit_partitions([row("a", group_id="one"), row("b", "development_validation", group_id="two")])
        self.assertEqual(report["status"], "passed_metadata_checks")
        self.assertEqual(report["unique_sample_counts_by_role"], {"model_validation": 1, "training": 1})
        self.assertEqual(report["final_test_readiness"], "not_established_by_metadata_audit")

    def test_transitive_parent_and_session_cross_split(self):
        assignments = [row("a", parent_sample_id="b"), row("c", "locked_test", session_id="session")]
        catalog = [row("b", session_id="session")]
        report = audit_partitions(assignments, catalog)
        self.assertIn("connected_component_crosses_partitions", codes(report))
        self.assertEqual(report["assigned_connected_components"], 1)

    def test_protected_original_joined_by_file_hash_alias(self):
        report = audit_partitions([row("crop", image_sha256="a" * 64)], [
            {"sample_id": "seed", "sha256": "a" * 64, "original_split": "val2020"}])
        self.assertIn("development_component_contains_protected_or_unknown_source", codes(report))

    def test_locked_catalog_split_never_silently_becomes_development(self):
        report = audit_partitions([row("a", group_id="item")], [row("b", "locked_test", group_id="item")])
        self.assertIn("development_component_contains_protected_or_unknown_source", codes(report))

    def test_missing_parent_fails(self):
        self.assertIn("missing_parent_record", codes(audit_partitions([row("a", parent_sample_id="absent")])))

    def test_unknown_source_fails_development(self):
        report = audit_partitions([{"sample_id": "a", "split": "development_train"}])
        self.assertIn("development_component_missing_source_partition", codes(report))

    def test_conflicting_catalog_provenance_not_overwritten(self):
        report = audit_partitions([row("a", sha256="a" * 64)], [
            {"sample_id": "a", "source_partition": "test", "sha256": "b" * 64}])
        self.assertIn("conflicting_source_partitions", codes(report))
        self.assertIn("conflicting_sample_file_hashes", codes(report))

    def test_source_partition_cannot_hide_protected_original_split(self):
        report = audit_partitions([row("a", original_split="val2020")])
        self.assertIn("conflicting_source_partitions", codes(report))
        self.assertIn("development_component_contains_protected_or_unknown_source", codes(report))

    def test_assignment_split_alias_conflict_fails(self):
        report = audit_partitions([row("a", project_split="locked_test")])
        self.assertIn("conflicting_split_aliases", codes(report))
        self.assertIn("development_component_contains_protected_or_unknown_source", codes(report))

    def test_frozen_catalog_assignment_drift_fails(self):
        report = audit_partitions([row("a")], [row("a", "development_validation")])
        self.assertIn("conflicting_project_partition_declarations", codes(report))
        self.assertIn("connected_component_crosses_partitions", codes(report))

    def test_connected_catalog_development_partition_drift_fails(self):
        report = audit_partitions([row("a", group_id="garment")], [row("b", "development_validation", group_id="garment")])
        self.assertIn("connected_component_crosses_partitions", codes(report))

    def test_model_validation_aliases_are_consistent(self):
        for split, project_split in (("validation", "development_validation"), ("val", "model_validation")):
            report = audit_partitions([row("a", split, project_split=project_split)])
            self.assertEqual(report["status"], "passed_metadata_checks")
        report = audit_partitions([{"sample_id": "a", "project_split": "validation", "source_partition": "train2020"}])
        self.assertEqual(report["status"], "passed_metadata_checks")

    def test_non_assignment_catalog_status_not_treated_as_partition(self):
        report = audit_partitions([row("a")], [row("a", "candidate_pending_review")])
        self.assertEqual(report["status"], "passed_metadata_checks")

    def test_source_item_ids_are_namespaced(self):
        report = audit_partitions([row("a", source_id="first", source_item_id="1"),
                                   row("b", "development_validation", source_id="second", source_item_id="1")])
        self.assertEqual(report["status"], "passed_metadata_checks")

    def test_duplicate_assignments_not_counted_as_new_samples(self):
        report = audit_partitions([row("a"), row("a")])
        self.assertIn("duplicate_assignment_sample_id", codes(report))
        self.assertEqual(report["unique_assigned_samples"], 1)
        self.assertEqual(report["assignment_rows"], 2)

    def test_unknown_split_and_empty_input_fail(self):
        self.assertIn("unknown_assignment_split", codes(audit_partitions([row("a", "testing_maybe")])) )
        self.assertEqual(audit_partitions([])["status"], "failed")

    def test_bad_hash_or_identity_fails(self):
        report = audit_partitions([row("a", group_id=["not", "an", "id"], sha256="broken")])
        self.assertIn("invalid_hash", codes(report))
        self.assertIn("invalid_identity_value", codes(report))

    def test_current_json_and_jsonl_containers(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name, content in (("array.json", [row("a")]), ("object.json", {"samples": [row("a")]}),
                                  ("split.json", {"assignments": [row("a")]})):
                path = folder / name
                path.write_text(json.dumps(content), encoding="utf-8")
                self.assertEqual(load_rows(path)[0]["sample_id"], "a")
            path = folder / "rows.jsonl"
            path.write_text(json.dumps(row("a")) + "\n\n", encoding="utf-8")
            self.assertEqual(load_rows(path), [row("a")])

    def test_cli_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source, output = folder / "in.json", folder / "out.json"
            source.write_text(json.dumps([row("a")]), encoding="utf-8")
            script = Path(__file__).resolve().parents[1] / "tools/audit_dataset_partitions.py"
            args = [sys.executable, "-B", str(script), "--manifest", str(source), "--output", str(output)]
            first = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            before = output.read_bytes()
            second = subprocess.run(args, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(output.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
