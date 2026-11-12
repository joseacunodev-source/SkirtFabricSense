import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.training import train_presence_finetune as candidate


class Layer:
    def __init__(self,name):
        self.name=name; self.trainable=True; self.weights=[1]


class BatchNorm(Layer):
    pass


class Base:
    def __init__(self):
        self.trainable=True
        self.layers=[Layer('early'),BatchNorm('early_BN'),Layer('block_13_expand'),
                     BatchNorm('block_13_expand_BN'),Layer('block_14_project')]


class PresenceFineTuneTests(unittest.TestCase):
    def test_prespecified_schedule_and_balance(self):
        self.assertEqual(candidate.phases(), [('head',3,.001),('finetune',5,.00001)])
        self.assertEqual(candidate.balanced_weights([1,1,1,0]),{0:2.,1:2/3})
        with self.assertRaises(ValueError): candidate.balanced_weights([1,1])

    def test_head_freezes_every_backbone_layer(self):
        base=Base()
        self.assertEqual(candidate.configure_backbone(base,'head',BatchNorm),[])
        self.assertFalse(base.trainable)
        self.assertTrue(all(not l.trainable for l in base.layers))

    def test_finetune_boundary_keeps_every_batchnorm_frozen(self):
        base=Base()
        names=candidate.configure_backbone(base,'finetune',BatchNorm)
        self.assertEqual(names,['block_13_expand','block_14_project'])
        self.assertFalse(base.layers[0].trainable)
        self.assertTrue(all(not l.trainable for l in base.layers if isinstance(l,BatchNorm)))
        self.assertTrue(base.trainable)

    def test_missing_boundary_and_bad_phase_fail(self):
        base=Base(); base.layers=base.layers[:2]
        with self.assertRaises(ValueError): candidate.configure_backbone(base,'finetune',BatchNorm)
        with self.assertRaises(ValueError): candidate.configure_backbone(Base(),'bogus',BatchNorm)

    def test_path_escape_and_missing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'root'; root.mkdir()
            outside=Path(temp)/'outside'; outside.write_text('x')
            with self.assertRaises(ValueError): candidate.safe_path(root,'../outside')
            with self.assertRaises(ValueError): candidate.safe_path(root,'missing')

    def test_current_manifest_admission_and_original_counts(self):
        rows,_=candidate.prepare_rows(candidate.ROOT,'data/labels/negative-reviewed-v2.jsonl')
        positives=[r for r in rows if r['presence_target']==1]
        self.assertEqual(len(positives),331)
        self.assertEqual(sum(r['split']=='development_validation' for r in positives),66)
        self.assertEqual(sum(r['presence_target']==0 for r in rows),75)

    def test_approved_negative_without_review_fails(self):
        source=candidate.ROOT/'data/labels/negative-reviewed-v2.jsonl'
        negatives=[json.loads(s) for s in source.read_text().splitlines()]
        row=next(r for r in negatives if r.get('training_eligibility',{}).get('approved'))
        row['label_evidence']['original_inspected']=False
        with tempfile.TemporaryDirectory(dir=candidate.ROOT) as temp:
            path=Path(temp)/'negative.jsonl'
            path.write_text('\n'.join(json.dumps(r) for r in negatives))
            with self.assertRaisesRegex(ValueError,'admission'):
                candidate.prepare_rows(candidate.ROOT,path)

    def test_worn_review_hash_mismatch_fails(self):
        real_read=Path.read_text
        def read(path,*args,**kwargs):
            text=real_read(path,*args,**kwargs)
            if path.name=='worn-pleating-development-v1.jsonl':
                rows=[json.loads(s) for s in text.splitlines()]
                rows[0]['presentation_review']['image_sha256']='0'*64
                return '\n'.join(json.dumps(r) for r in rows)
            return text
        with patch.object(Path,'read_text',read):
            with self.assertRaisesRegex(ValueError,'hash-bound worn'):
                candidate.prepare_rows(candidate.ROOT,'data/labels/negative-reviewed-v2.jsonl')


if __name__=='__main__': unittest.main()
