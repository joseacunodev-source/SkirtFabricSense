import copy
import unittest
import tempfile
from pathlib import Path
from tools.datasets.audit_worn_readiness import audit, write_report, verify_contact_reviews
import hashlib


class WornAuditTests(unittest.TestCase):
    def test_existing_report_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            write_report(path, {"original": True})
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                write_report(path, {"replacement": True})
            self.assertEqual(path.read_bytes(), original)

    def setUp(self):
        self.row = dict(sample_id="a", sha256="hash", original_path="a.jpg", split="development_train",
                        group_hash="g", label="pleated", label_evidence={"evidence": "Worn skirt with feet visible"})
        self.assignment = dict(sample_id="a", split="development_train", group_hash="g")
        self.review = dict(sample_id="a", image_sha256="hash", presentation="worn",
                           review_method="original_image_visual_inspection", reviewer="agent", evidence="Visible wearer",
                           waistband_visible=True, hem_visible=True, feet_and_support_surface_visible=True)

    def test_notes_do_not_invent_presentation(self):
        result = audit([self.row], [self.assignment])
        self.assertEqual(result["unknown_presentation"], 1)

    def test_sheet_review_is_not_original_inspection(self):
        review = dict(self.review, review_method='contact_sheet_visual_inspection',
                      inspection_sheet='sheet.jpg', sheet_position=1, sheet_sha256='a'*64)
        result = audit([self.row], [self.assignment], [review])
        self.assertEqual(result['reviewed_originals'], 0)
        self.assertEqual(result['reviewed_via_sheet'], 1)
        self.assertEqual(result['reviewed_samples'], 1)
        del review['sheet_sha256']
        with self.assertRaises(ValueError):
            audit([self.row], [self.assignment], [review])

    def test_sheet_bytes_and_position_are_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'sheet.jpg').write_bytes(b'actual sheet')
            sha = hashlib.sha256(b'actual sheet').hexdigest()
            entry = dict(self.row, inspection_sheet='sheet.jpg', sheet_position=1, sheet_sha256=sha)
            review = dict(self.review, original_path='a.jpg', review_method='contact_sheet_visual_inspection',
                          inspection_sheet='sheet.jpg', sheet_position=1, sheet_sha256=sha)
            verify_contact_reviews([review], [entry], root)
            with self.assertRaises(ValueError):
                verify_contact_reviews([dict(review, sheet_position=2)], [entry], root)
            (root/'sheet.jpg').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                verify_contact_reviews([review], [entry], root)

    def test_overlay_preserves_source_and_never_admits(self):
        before = copy.deepcopy(self.row)
        result = audit([self.row], [self.assignment], [self.review])
        self.assertEqual(result["reviewed_originals"], 1)
        self.assertEqual(result["calibrated_geometry_examples"], 0)
        self.assertFalse(result["rows"][0]["new_training_admission"])
        self.assertEqual(self.row, before)

    def test_audit_date_is_explicit_and_validated(self):
        self.assertEqual(audit([self.row], [self.assignment], audit_date="2026-10-17")["date_asia_manila"], "2026-10-17")
        with self.assertRaises(ValueError):
            audit([self.row], [self.assignment], audit_date="2026-99-99")

    def test_blank_or_nontext_review_evidence_rejected(self):
        for key in ("reviewer", "evidence"):
            for value in ("   ", "", 1, ["note"], None):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    audit([self.row], [self.assignment], [dict(self.review, **{key: value})])

    def test_bad_review_hash(self):
        self.review["image_sha256"] = "changed"
        with self.assertRaises(ValueError):
            audit([self.row], [self.assignment], [self.review])

    def test_duplicate_or_foreign_review_rejected(self):
        with self.assertRaises(ValueError):
            audit([self.row], [self.assignment], [self.review, self.review])
        self.review["sample_id"] = "foreign"
        with self.assertRaises(ValueError):
            audit([self.row], [self.assignment], [self.review])

    def test_split_change_rejected(self):
        self.assignment["split"] = "development_validation"
        with self.assertRaises(ValueError):
            audit([self.row], [self.assignment])

    def test_group_leakage_rejected(self):
        other = dict(self.row, sample_id="b", split="development_validation")
        with self.assertRaises(ValueError):
            audit([self.row, other], [self.assignment, dict(self.assignment, sample_id="b", split="development_validation")])

    def test_review_method_and_visibility_required(self):
        for key, value in [("review_method", "filename_guess"), ("feet_and_support_surface_visible", "yes"), ("presentation", "person")]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                audit([self.row], [self.assignment], [dict(self.review, **{key: value})])


if __name__ == "__main__":
    unittest.main()
