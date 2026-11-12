"""Synthetic provenance fixtures; tests are not submitted garment observations."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools.datasets import fabric_evidence_review as review


class FabricEvidenceReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rows = []
        for i, split in enumerate(("development_train", "development_validation")):
            relative = review.SOURCE_DIR + f"/synthetic-{i}.jpg"
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            # Minimum SOF header for parser tests, explicitly not a real photo.
            body = b"\xff\xd8\xff\xc0" + struct.pack(">H", 8) + b"\x08" + struct.pack(">HH", 8 + i, 10) + b"\x01\xff\xd9"
            path.write_bytes(body)
            self.rows.append({"sample_id": f"fixture-{i}", "source_id": "deepfashion-multimodal",
                              "source_partition": "train", "split": split, "group_id": f"group-{i}",
                              "admission_scope": "internal_pipeline_smoke_only", "training_admitted": True,
                              "composition_verified": False, "independent_human_review": False,
                              "physical_garment_verified": False, "label": "private_source_cotton_appearance",
                              "original_path": relative, "sha256": review.sha(path), "size_bytes": len(body),
                              "width": 10, "height": 8 + i, "terms_reference": review.TERMS})
        terms = self.root / review.TERMS
        terms.parent.mkdir(parents=True, exist_ok=True)
        terms.write_text("Synthetic terms fixture; no photo licence asserted.", encoding="utf-8")
        self.freeze()
        self.directory = self.root / "records/review/synthetic"

    def freeze(self, assignments=None):
        manifest = self.root / review.MANIFEST
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("".join(json.dumps(r) + "\n" for r in self.rows), encoding="utf-8")
        assignments = assignments if assignments is not None else [
            {k: r[k] for k in ("sample_id", "group_id", "split")} for r in self.rows]
        (self.root / review.SPLITS).write_text(json.dumps({"assignments": assignments}), encoding="utf-8")
        self.pins = {p: review.sha(self.root / p) for p in (review.MANIFEST, review.SPLITS, review.TERMS)}

    def build(self):
        return review.build(self.root, self.directory, self.pins)

    def payload(self):
        queue = json.loads((self.directory / review.QUEUE).read_text(encoding="utf-8"))
        row = queue["records"][0]
        return {"review_id": row["review_id"], "queue_sha256": review.sha(self.directory / review.QUEUE),
                "image_sha256": row["image"]["sha256"],
                "reviewer": {"display_name": "Synthetic actor", "actor_kind": "agent"},
                "original_viewed": True,
                "observations": {"appearance_status": "unknown", "appearance_descriptors": [],
                                 "material_to_skirt_association": "uncertain", "presentation": "unknown",
                                 "full_skirt_visibility": "uncertain", "texture_detail": "insufficient",
                                 "notes": "Synthetic test payload, never an actual image observation."},
                "composition_evidence": {"status": "not_observed", "unverified_claim": None},
                "source_evidence_references": []}

    def append(self, payload):
        return review.append(self.root, self.directory, payload, self.pins)

    def verify(self):
        return review.verify(self.root, self.directory, self.pins)

    def test_blind_queue_excludes_labels_scores_splits_and_groups(self):
        result = self.build()
        self.assertEqual(result["observations_submitted"], 0)
        queue = json.loads((self.directory / review.QUEUE).read_text(encoding="utf-8"))
        self.assertEqual(set(queue["records"][0]), {"review_id", "image"})
        serialized = json.dumps(queue)
        for hidden in ("private_source", "cotton", "development_train", "group-0", "model_score"):
            self.assertNotIn(hidden, serialized)
        bindings = json.loads((self.directory / review.BINDINGS).read_text(encoding="utf-8"))
        self.assertEqual(bindings["records"][0]["original_source_record"], self.rows[0])
        self.assertEqual(self.verify()["pending_samples"], 2)

    def test_build_refuses_existing_directory(self):
        self.build()
        with self.assertRaises(FileExistsError):
            self.build()

    def test_build_confined_to_review_records(self):
        with self.assertRaises(ValueError):
            review.build(self.root, self.root / "data/output", self.pins)

    def test_frozen_input_hash_tamper(self):
        for path in (review.MANIFEST, review.SPLITS, review.TERMS):
            with self.subTest(path=path):
                target = self.root / path
                original = target.read_bytes()
                target.write_bytes(original + b" ")
                with self.assertRaisesRegex(ValueError, "Frozen input hash"):
                    review.load_inputs(self.root, self.pins)
                target.write_bytes(original)

    def test_protected_source_partitions_rejected(self):
        for value in ("query", "gallery", "test", "val2020"):
            with self.subTest(partition=value):
                self.rows[0]["source_partition"] = value
                self.freeze()
                with self.assertRaisesRegex(ValueError, "Protected"):
                    review.load_inputs(self.root, self.pins)

    def test_protected_project_split_rejected(self):
        self.rows[0]["split"] = "test"
        self.freeze()
        with self.assertRaises(ValueError):
            self.build()

    def test_group_overlap_rejected_even_with_matching_assignments(self):
        self.rows[1]["group_id"] = self.rows[0]["group_id"]
        self.freeze()
        with self.assertRaisesRegex(ValueError, "overlaps"):
            self.build()

    def test_assignment_duplicate_missing_extra_or_changed_rejected(self):
        valid = [{k: r[k] for k in ("sample_id", "group_id", "split")} for r in self.rows]
        changed = copy.deepcopy(valid)
        changed[0]["group_id"] = "new-group"
        for assignments in (valid + [valid[0]], valid[1:], valid + [dict(valid[0], sample_id="extra")], changed):
            with self.subTest(assignments=assignments):
                self.freeze(assignments)
                with self.assertRaises(ValueError):
                    self.build()

    def test_image_hash_and_size_tamper_rejected(self):
        image = self.root / self.rows[0]["original_path"]
        image.write_bytes(image.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "hash/size"):
            self.build()

    def test_image_dimensions_and_unsafe_path_rejected(self):
        for key, value in (("width", 99), ("original_path", "../outside.jpg")):
            original = self.rows[0][key]
            self.rows[0][key] = value
            self.freeze()
            with self.assertRaises(ValueError):
                self.build()
            self.rows[0][key] = original

    def test_source_truth_promotion_rejected(self):
        for field in ("composition_verified", "independent_human_review", "physical_garment_verified"):
            self.rows[0][field] = True
            self.freeze()
            with self.assertRaises(ValueError):
                self.build()
            self.rows[0][field] = False

    def test_append_chains_without_approving_or_overwriting(self):
        self.build()
        first = self.append(self.payload())
        first_bytes = (self.directory / review.EVENTS).read_bytes()
        second_payload = self.payload()
        second_payload["reviewer"] = {"display_name": "Self reported human", "actor_kind": "human"}
        second = self.append(second_payload)
        self.assertTrue((self.directory / review.EVENTS).read_bytes().startswith(first_bytes))
        events = [json.loads(x) for x in (self.directory / review.EVENTS).read_text().splitlines()]
        self.assertEqual(events[1]["previous_event_sha256"], first["event_sha256"])
        result = self.verify()
        self.assertEqual(result["event_chain_head_sha256"], second["event_sha256"])
        self.assertEqual(result["observations_submitted"], 2)
        self.assertEqual(result["samples_with_submitted_observations"], 1)
        self.assertFalse(result["independent_human_truth_established"])
        self.assertFalse(result["training_approved"])

    def test_no_observation_or_admission_can_be_added_to_queue(self):
        self.build()
        queue_path = self.directory / review.QUEUE
        queue = json.loads(queue_path.read_text())
        queue["records"][0]["label"] = "cotton"
        queue_path.write_text(json.dumps(queue))
        with self.assertRaisesRegex(ValueError, "package changed"):
            self.verify()

    def test_private_binding_tamper_rejected(self):
        self.build()
        path = self.directory / review.BINDINGS
        value = json.loads(path.read_text())
        value["records"][0]["original_source_record"]["split"] = "development_validation"
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            self.verify()

    def test_payload_unknown_fields_or_truth_claims_rejected(self):
        self.build()
        for key in ("training_approved", "composition_verified", "independent_human_review", "model_score"):
            payload = self.payload()
            payload[key] = True
            with self.assertRaises(ValueError):
                self.append(payload)
        self.assertEqual(self.verify()["observations_submitted"], 0)

    def test_wrong_queue_image_or_review_binding_rejected(self):
        self.build()
        for key, value in (("review_id", "missing"), ("queue_sha256", "0" * 64), ("image_sha256", "0" * 64)):
            payload = self.payload()
            payload[key] = value
            with self.assertRaises(ValueError):
                self.append(payload)

    def test_original_viewing_attestation_required(self):
        self.build()
        for value in (False, "true", 1):
            payload = self.payload()
            payload["original_viewed"] = value
            with self.assertRaises(ValueError):
                self.append(payload)

    def test_appearance_unknown_mixed_and_association(self):
        self.build()
        payload = self.payload()
        payload["observations"].update(appearance_status="mixed_appearance",
                                       appearance_descriptors=["sheer sections", "dense opaque sections"],
                                       material_to_skirt_association="clear")
        self.append(payload)
        for field, value in (("material_to_skirt_association", "uncertain"), ("appearance_status", "unknown"),
                             ("appearance_descriptors", []), ("appearance_descriptors", ["same", "same"])):
            invalid = copy.deepcopy(payload)
            invalid["observations"][field] = value
            with self.assertRaises(ValueError):
                self.append(invalid)

    def test_visual_composition_claim_rejected(self):
        self.build()
        payload = self.payload()
        payload["composition_evidence"] = {"status": "verified", "unverified_claim": "100% cotton"}
        with self.assertRaisesRegex(ValueError, "cannot verify"):
            self.append(payload)

    def test_unverified_document_claim_needs_hashed_skirt_reference(self):
        self.build()
        payload = self.payload()
        payload["composition_evidence"] = {"status": "unverified_document_claim", "unverified_claim": "Tag claims a blend"}
        with self.assertRaises(ValueError):
            self.append(payload)
        doc = self.root / "records/review/synthetic-supplier.txt"
        doc.write_text("Synthetic claim, no actual garment.", encoding="utf-8")
        ref = {"path": doc.relative_to(self.root).as_posix(), "sha256": review.sha(doc),
               "kind": "supplier_document", "item_association": "claimed_skirt"}
        payload["source_evidence_references"] = [ref]
        self.append(payload)
        self.assertFalse(self.verify()["composition_verified"])
        doc.write_text("Changed source", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.verify()

    def test_reference_escape_and_duplicate_rejected(self):
        self.build()
        payload = self.payload()
        ref = {"path": review.TERMS, "sha256": self.pins[review.TERMS], "kind": "terms", "item_association": "unresolved"}
        for refs in ([dict(ref, path="../outside.txt")], [ref, ref], [dict(ref, sha256="0" * 64)]):
            payload["source_evidence_references"] = refs
            with self.assertRaises(ValueError):
                self.append(payload)

    def test_hash_chain_tamper_reorder_and_tail_rejected(self):
        self.build()
        self.append(self.payload())
        self.append(self.payload())
        path = self.directory / review.EVENTS
        original = path.read_bytes()
        rows = original.splitlines(keepends=True)
        for tampered in (rows[1] + rows[0], original[:-1], original.replace(b"Synthetic actor", b"Changed actor")):
            path.write_bytes(tampered)
            with self.assertRaises(ValueError):
                self.verify()
        path.write_bytes(original)
        self.assertEqual(self.verify()["observations_submitted"], 2)

    def test_rehashed_event_cannot_claim_approval(self):
        self.build()
        self.append(self.payload())
        path = self.directory / review.EVENTS
        original = json.loads(path.read_text())
        for field in ("training_approved", "composition_verified"):
            event = copy.deepcopy(original)
            event[field] = True
            event["event_sha256"] = review.object_sha({k: v for k, v in event.items() if k != "event_sha256"})
            path.write_bytes(review.canonical(event) + b"\n")
            with self.assertRaises(ValueError):
                self.verify()

    def test_concurrent_writer_lock_is_not_bypassed(self):
        self.build()
        lock = self.directory / ".append.lock"
        lock.touch()
        with self.assertRaises(FileExistsError):
            self.append(self.payload())
        self.assertTrue(lock.exists())
        self.assertEqual(self.verify()["observations_submitted"], 0)

    def test_post_build_original_or_input_tamper_blocks_append(self):
        self.build()
        image = self.root / self.rows[0]["original_path"]
        image.write_bytes(image.read_bytes() + b"corrupt")
        with self.assertRaises(ValueError):
            self.append(self.payload())
        self.assertEqual((self.directory / review.EVENTS).read_bytes(), b"")

    def test_append_refuses_outside_directory_before_creating_lock(self):
        outside = self.root / "data/outside"
        outside.mkdir(parents=True)
        with self.assertRaises(ValueError):
            review.append(self.root, outside, {})
        self.assertEqual(list(outside.iterdir()), [])

    def test_missing_event_log_does_not_reset_history(self):
        self.build()
        (self.directory / review.EVENTS).unlink()
        with self.assertRaises(ValueError):
            self.verify()

    def test_blank_event_row_and_duplicate_event_identity_rejected(self):
        self.build()
        self.append(self.payload())
        path = self.directory / review.EVENTS
        original = path.read_bytes()
        for mutated in (original + b"\n", original + original):
            path.write_bytes(mutated)
            with self.assertRaises(ValueError):
                self.verify()

    def test_rehashed_events_reject_bool_schema_and_non_utc_time(self):
        self.build()
        self.append(self.payload())
        path = self.directory / review.EVENTS
        original = json.loads(path.read_text())
        for field, value in (("schema_version", True), ("recorded_at_utc", "2026-10-23T12:00:00"),
                             ("recorded_at_utc", "2026-10-23T12:00:00+08:00")):
            event = copy.deepcopy(original)
            event[field] = value
            event["event_sha256"] = review.object_sha({k: v for k, v in event.items() if k != "event_sha256"})
            path.write_bytes(review.canonical(event) + b"\n")
            with self.assertRaises(ValueError):
                self.verify()

    def test_descriptor_and_reviewer_text_must_be_bounded(self):
        self.build()
        for mutation in ("control", "long_name", "many_descriptors", "unknown_actor"):
            payload = self.payload()
            if mutation == "control":
                payload["observations"]["notes"] = "control\x00"
            elif mutation == "long_name":
                payload["reviewer"]["display_name"] = "a" * 101
            elif mutation == "many_descriptors":
                payload["observations"]["appearance_descriptors"] = [str(i) for i in range(9)]
            else:
                payload["reviewer"]["actor_kind"] = "verified_human"
            with self.assertRaises(ValueError):
                self.append(payload)


if __name__ == "__main__":
    unittest.main()
