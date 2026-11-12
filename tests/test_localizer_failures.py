import unittest
from tools.analyze_localizer_failures import summarize


class FailureAuditTests(unittest.TestCase):
    def fixture(self):
        row = {'sample_id': 'one', 'positive': False}
        for model in ('v1', 'v2', 'v3'):
            row[model] = {'accepted': True, 'region': {'reason': 'provisional'}}
        source = {'sample_id': 'one', 'split': 'development_validation', 'label': 'no_skirt',
                  'sampling_bucket': 'dress', 'original_path': 'one.jpg', 'sha256': 'hash', 'group_id': 'group'}
        return row, source

    def test_persistent_failures_and_buckets(self):
        row, source = self.fixture()
        result = summarize({'results': [row]}, [source])
        self.assertEqual(result['negative_buckets']['dress']['v3_false_accepts'], 1)
        self.assertEqual(result['all_models_false_accept'][0]['group_id'], 'group')
        row['v3']['accepted'] = False
        row['v3']['region']['reason'] = 'multiple_regions'
        result = summarize({'results': [row]}, [source])
        self.assertEqual(result['all_models_false_accept'], [])
        self.assertEqual(result['rejection_reasons_all_99_inputs']['v3'], {'multiple_regions': 1})

    def test_duplicate_and_wrong_split_fail(self):
        row, source = self.fixture()
        with self.assertRaises(ValueError):
            summarize({'results': [row, row]}, [source])
        with self.assertRaises(ValueError):
            summarize({'results': [row]}, [source, source])
        source['split'] = 'development_train'
        with self.assertRaises(ValueError):
            summarize({'results': [row]}, [source])


if __name__ == '__main__':
    unittest.main()
