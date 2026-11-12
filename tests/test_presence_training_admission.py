import copy
import json
from pathlib import Path
import unittest
from tools.training.train_presence import validate

ROOT = Path(__file__).resolve().parents[1]

class PresenceTrainingAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads((ROOT / 'records/experiments/20261011-presence-v1/inputs.json').read_text())

    def test_executed_inputs_pass_explicit_admission(self):
        validate(self.rows)

    def test_invalid_negative_admission_fails_closed(self):
        for field, value in [('training_eligibility', {'approved': False}),
                             ('grouping_review_pending', True),
                             ('label_evidence', {'original_inspected': False}),
                             ('label', None)]:
            with self.subTest(field=field):
                rows = copy.deepcopy(self.rows)
                negative = next(r for r in rows if r['presence_target'] == 0)
                negative[field] = value
                with self.assertRaisesRegex(ValueError, 'explicit reviewed training admission'):
                    validate(rows)

    def test_protected_partition_and_group_leakage_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['source_partition'] = 'val2020'
        with self.assertRaisesRegex(ValueError, 'Protected source partition'):
            validate(rows)
        rows = copy.deepcopy(self.rows)
        train = next(r for r in rows if r['split'] == 'development_train')
        validation = next(r for r in rows if r['split'] == 'development_validation')
        validation['group_hash'] = train['group_hash']
        with self.assertRaisesRegex(ValueError, 'Cross-split group'):
            validate(rows)

if __name__ == '__main__':
    unittest.main()
