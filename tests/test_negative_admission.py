import hashlib
import json
from pathlib import Path
import unittest
from tools.datasets.prepare_negative_pilot import ROOT, prepare, assign_splits, ALLOWED

class NegativeAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[json.loads(x) for x in (ROOT/'data/labels/negative-reviewed-v1.jsonl').read_text().splitlines()]
        cls.report=json.loads((ROOT/'data/labels/negative-reviewed-v1.report.json').read_text())
        cls.admitted=[r for r in cls.rows if r['training_eligibility']['approved']]
    def test_complete_review_and_hash(self):
        self.assertEqual(len(self.rows),90)
        self.assertEqual(len({r['sample_id'] for r in self.rows}),90)
        self.assertEqual(hashlib.sha256((ROOT/self.report['manifest']).read_bytes()).hexdigest(),self.report['manifest_sha256'])
    def test_conservative_admission(self):
        self.assertEqual(len(self.admitted),12)
        for r in self.admitted:
            self.assertIn(r['source_license']['name'],ALLOWED)
            self.assertTrue(r['label_evidence']['original_inspected'])
            self.assertFalse(r['label_evidence']['independent_human_review'])
            self.assertEqual(r['label'],'no_skirt')
            self.assertEqual(r['source_partition'],'train2020')
    def test_quarantine_never_gets_label_or_split(self):
        for r in self.rows:
            if not r['training_eligibility']['approved']:
                self.assertIsNone(r['split'])
                self.assertIsNone(r['label'])
                self.assertTrue(r['label_evidence']['quarantine_reasons'])
        matched=next(r for r in self.rows if r['source_item_id']=='1632')
        self.assertIn('cross-pool',str(matched['label_evidence']))
    def test_group_split_integrity(self):
        groups={}
        for r in self.admitted:
            self.assertEqual(groups.setdefault(r['group_id'],r['split']),r['split'])
        val=[r for r in self.admitted if r['split']=='development_validation']
        self.assertEqual(len(val),3)
        self.assertEqual({r['sampling_bucket'] for r in val},{'pants','shorts','dress'})
    def test_deterministic_rebuild(self):
        positives=[json.loads(x) for x in (ROOT/'data/labels/skirt-baseline-v1.jsonl').read_text().splitlines()]
        self.assertEqual(prepare(ROOT/'data/manifests/negative-candidates-v1.jsonl',positive=positives),self.rows)
    def test_source_group_collision_quarantined(self):
        r=self.admitted[0]
        rows=prepare(ROOT/'data/manifests/negative-candidates-v1.jsonl',positive=[r])
        result=next(x for x in rows if x['sample_id']==r['sample_id'])
        self.assertFalse(result['training_eligibility']['approved'])
        self.assertIsNone(result['split'])
    def test_split_independent_of_input_order(self):
        self.assertEqual(assign_splits(self.admitted),assign_splits(list(reversed(self.admitted))))
    def test_mixed_category_group_rejected(self):
        with self.assertRaises(ValueError):
            assign_splits([{'group_id':'same','sampling_bucket':'pants'},{'group_id':'same','sampling_bucket':'dress'}])
if __name__=='__main__':unittest.main()
