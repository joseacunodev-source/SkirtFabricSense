import unittest
from tools.check_detection_candidate import compare, metrics


class DetectionComparisonTests(unittest.TestCase):
    def test_tradeoff_is_not_declared_improvement(self):
        baseline = {'positive_accepted':41,'correct_pleating':33,'negative_rejected':25}
        candidate = {'positive_accepted':40,'correct_pleating':33,'negative_rejected':45}
        self.assertFalse(all(compare(candidate, baseline).values()))
        candidate['positive_accepted'] = 42
        self.assertTrue(all(compare(candidate, baseline).values()))

    def test_coverage_and_rejection_have_separate_denominators(self):
        rows = [{'presence_target':1, 'expected_pleating':'pleated',
                 'paths':{'x':{'accepted':True,'pleating_prediction':'pleated'}}},
                {'presence_target':1, 'expected_pleating':'pleated',
                 'paths':{'x':{'accepted':False,'pleating_prediction':None}}},
                {'presence_target':0, 'expected_pleating':None,
                 'paths':{'x':{'accepted':False,'pleating_prediction':None}}}]
        result = metrics(rows,'x')
        self.assertEqual(result['positive_coverage'],.5)
        self.assertEqual(result['accepted_pleating_accuracy'],1)
        self.assertEqual(result['negative_rejection'],1)


if __name__ == '__main__':
    unittest.main()
