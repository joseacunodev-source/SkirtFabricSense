import copy
import json
import unittest
from pathlib import Path
from tools.datasets.prepare_fabric_pilot import prepare
from tools.training.train_fabric_pilot import validate

ROOT=Path(__file__).resolve().parents[1]

class FabricPilotTests(unittest.TestCase):
    def setUp(self):
        self.source=[json.loads(x) for x in (ROOT/'data/manifests/fullview-fabric-candidates-v1.jsonl').read_text().splitlines()]
        self.rows,self.review=prepare(self.source)
        self.splits={'assignments':[{'sample_id':r['sample_id'],'group_id':r['group_id'],'split':r['split']} for r in self.rows]}
    def test_frozen_smoke_counts(self):
        self.assertEqual(len(self.rows),17)
        self.assertEqual(sum(r['split']=='development_validation' for r in self.rows),5)
        self.assertEqual(len(self.review),25)
        validate(self.rows,self.splits)
    def test_order_independent(self):
        other,_=prepare(self.source[::-1])
        self.assertEqual({r['sample_id']:r['split'] for r in self.rows},{r['sample_id']:r['split'] for r in other})
    def test_query_partition_rejected(self):
        self.source[0]['source_partition']='query'
        with self.assertRaises(ValueError):prepare(self.source)
    def test_repeated_source_group_rejected(self):
        self.source[1]['group_id']=self.source[0]['group_id']
        with self.assertRaises(ValueError):prepare(self.source)
    def test_source_not_mutated(self):
        self.assertTrue(all(r['training_admitted'] is False for r in self.source))
    def test_split_tampering_rejected(self):
        self.splits['assignments'][0]['split']='development_train' if self.rows[0]['split']=='development_validation' else 'development_validation'
        with self.assertRaises(ValueError):validate(self.rows,self.splits)
    def test_cross_split_group_rejected(self):
        a=next(r for r in self.rows if r['split']=='development_train');b=next(r for r in self.rows if r['split']=='development_validation')
        b['group_id']=a['group_id']
        with self.assertRaises(ValueError):validate(self.rows,self.splits)
    def test_unadmitted_rejected(self):
        self.rows[0]['training_admitted']=False
        with self.assertRaises(ValueError):validate(self.rows,self.splits)
    def test_unknown_source_label_rejected(self):
        self.source[0]['source_lower_fabric_label']='polyester'
        with self.assertRaises(ValueError):prepare(self.source)
    def test_duplicate_split_assignment_rejected(self):
        self.splits['assignments'].append(copy.deepcopy(self.splits['assignments'][0]))
        with self.assertRaises(ValueError):validate(self.rows,self.splits)

if __name__=='__main__':unittest.main()
