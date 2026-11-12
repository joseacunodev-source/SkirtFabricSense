import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('negative_intake', Path(__file__).resolve().parents[1] / 'tools/datasets/acquire_negatives.py')
intake = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(intake)


class NegativeIntakeTests(unittest.TestCase):
    def data(self):
        return {'categories': [{'id': i, 'name': n} for i, n in [(6, 'pants'), (7, 'shorts'), (8, 'skirt'), (10, 'dress')]],
                'images': [{'id': i} for i in range(1, 8)],
                'annotations': [{'image_id': i, 'category_id': c} for i, c in [(1, 6), (2, 7), (3, 10), (4, 6), (4, 8), (5, 6), (5, 10), (6, 8)]]}

    def test_reject_skirt_and_unannotated(self):
        rows = intake.select_candidates(self.data(), set())
        self.assertEqual({r[0]['id'] for r in rows}, {1, 2, 3, 5})

    def test_existing_ids_excluded(self):
        self.assertNotIn(1, [r[0]['id'] for r in intake.select_candidates(self.data(), {'1'})])

    def test_repeatable_and_balanced_order(self):
        a = intake.select_candidates(self.data(), set())
        self.assertEqual(a, intake.select_candidates(self.data(), set()))
        self.assertEqual([r[2] for r in a[:3]], list(intake.BUCKETS))

    def test_overlap_one_candidate(self):
        rows = [r for r in intake.select_candidates(self.data(), set()) if r[0]['id'] == 5]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], 'pants')

    def test_taxonomy_mismatch_rejected(self):
        d = self.data()
        d['categories'][2]['name'] = 'other'
        with self.assertRaises(ValueError):
            intake.select_candidates(d, set())

    def test_unsafe_paths(self):
        for path in ('../x.jpg', 'nested/x.jpg', 'nested\\x.jpg', ''):
            with self.assertRaises(ValueError):
                intake.safe_filename(path)
        self.assertEqual(intake.safe_filename('abc.jpg'), 'abc.jpg')

    def test_manifest_path_escape(self):
        with self.assertRaises(ValueError):
            intake.verify_record({'original_path': 'README.md'})


if __name__ == '__main__':
    unittest.main()
