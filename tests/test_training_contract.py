import copy
import unittest
from tools.training.train_skirt_baseline import validate_rows


class TrainingContractTests(unittest.TestCase):
    def setUp(self):
        self.rows=[]
        self.assignments={}
        for split,n in [('development_train',10),('development_validation',5)]:
            for label in ['pleated','non_pleated']:
                for i in range(n):
                    sid=f'{split}-{label}-{i}'
                    r=dict(sample_id=sid,source_partition='train2020',split=split,group_hash=sid,label=label,sha256='h',
                           label_evidence=dict(full_skirt_view=True,appearance_label=label,evidence='visual review',image_sha256='h'))
                    self.rows.append(r)
                    self.assignments[sid]=dict(split=split,group_hash=sid)

    def test_balanced_pilot_passes(self):
        self.assertEqual(validate_rows(self.rows,self.assignments)['development_validation']['pleated'],5)

    def test_single_class_validation_rejected(self):
        rows=[r for r in self.rows if not (r['split']=='development_validation' and r['label']=='pleated')]
        with self.assertRaises(ValueError): validate_rows(rows,self.assignments)

    def test_heldout_rejected(self):
        self.rows[0]['source_partition']='val2020'
        with self.assertRaises(ValueError): validate_rows(self.rows,self.assignments)

    def test_framing_rejected(self):
        self.rows[0]['label_evidence']['full_skirt_view']=False
        with self.assertRaises(ValueError): validate_rows(self.rows,self.assignments)

    def test_malformed_boolean_rejected(self):
        self.rows[0]['label_evidence']['full_skirt_view']='false'
        with self.assertRaises(ValueError): validate_rows(self.rows,self.assignments)

    def test_exclusion_rejected(self):
        self.rows[0]['label_evidence']['exclude_auxiliary']=True
        with self.assertRaises(ValueError): validate_rows(self.rows,self.assignments)

    def test_review_conflict_rejected(self):
        self.rows[0]['label_evidence']['review_conflict']=True
        with self.assertRaises(ValueError): validate_rows(self.rows,self.assignments)

    def test_changed_assignment_rejected(self):
        self.rows[0]['split']='development_validation'
        with self.assertRaises(ValueError): validate_rows(self.rows,self.assignments)

    def test_duplicate_rejected(self):
        self.rows.append(copy.deepcopy(self.rows[0]))
        with self.assertRaises(ValueError): validate_rows(self.rows,self.assignments)


if __name__=='__main__': unittest.main()
