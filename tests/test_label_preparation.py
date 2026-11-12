import copy
import unittest
from tools.datasets.prepare_labels import prepare, source_label


class LabelPreparationTests(unittest.TestCase):
    def setUp(self):
        self.row = {'sample_id': 'a', 'source_partition': 'train2020', 'sha256': 'hash',
                    'source_labels': {'attributes': [{'name': 'pleat'}]}}
        self.split = {'assignments': [{'sample_id': 'a', 'split': 'development_train', 'group_hash': 'g'}]}

    def test_missing_pleat_is_unknown(self):
        self.row['source_labels']['attributes'] = []
        self.assertIsNone(source_label(self.row)[0])

    def test_conflicting_annotations_are_unknown(self):
        self.row['source_labels']['attributes'].append({'name': 'no special manufacturing technique'})
        self.assertIsNone(source_label(self.row)[0])

    def test_explicit_negative_is_source_only(self):
        self.row['source_labels']['attributes'] = [{'name': 'no special manufacturing technique'}]
        self.assertEqual(source_label(self.row)[0], 'source_no_special_manufacturing')

    def test_protected_source_rejected(self):
        self.row['source_partition'] = 'val2020'
        with self.assertRaises(ValueError):
            prepare([self.row], self.split, [])

    def test_group_leakage_rejected(self):
        other = dict(self.row, sample_id='b')
        self.split['assignments'].append({'sample_id': 'b', 'split': 'development_validation', 'group_hash': 'g'})
        with self.assertRaises(ValueError):
            prepare([self.row, other], self.split, [])

    def test_bad_review_hash_rejected(self):
        with self.assertRaises(ValueError):
            prepare([self.row], self.split, [{'sample_id': 'a', 'image_sha256': 'wrong'}])

    def test_review_exclusion_and_input_preservation(self):
        original = copy.deepcopy(self.row)
        review = {'sample_id': 'a', 'image_sha256': 'hash', 'appearance_label': 'unknown',
                  'full_skirt_view': False, 'exclude_auxiliary': True}
        queue, auxiliary, appearance = prepare([self.row], self.split, [review])
        self.assertEqual((len(queue), len(auxiliary), len(appearance)), (1, 0, 0))
        self.assertEqual(self.row, original)


if __name__ == '__main__':
    unittest.main()
