import copy
import unittest
from tools.datasets.prepare_negative_extension import prepare


class ExtensionTests(unittest.TestCase):
    def fixture(self):
        rows=[{'sample_id':str(i),'sha256':str(i),'group_id':'g'+str(i),'sampling_bucket':'pants',
               'source_partition':'train2020','source_license':{'name':'Attribution License',
                'url':'https://creativecommons.org/licenses/by/2.0/'}} for i in range(4)]
        reviews=[{'sample_id':r['sample_id'],'sha256':r['sha256'],'original_inspected':True,
                  'approve_no_skirt':True,'observation':'Visible separate trouser legs','related_sample_ids':[]} for r in rows]
        return rows,reviews

    def test_preserve_old_and_quarantine_known_links(self):
        rows,reviews=self.fixture();old=[{'sample_id':'old','split':'development_validation'}]
        result=prepare(rows,reviews,copy.deepcopy(old),{'0'})
        self.assertEqual(result[0],old[0]);self.assertIsNone(result[1]['split'])
        self.assertFalse(result[1]['training_eligibility']['approved'])
        self.assertEqual({r['split'] for r in result[2:]},{'development_train','development_validation'})

    def test_incomplete_or_changed_reviews_rejected(self):
        rows,reviews=self.fixture()
        with self.assertRaises(ValueError):prepare(rows,reviews[:-1],[],set())
        reviews[0]['sha256']='changed'
        with self.assertRaises(ValueError):prepare(rows,reviews,[],set())

    def test_related_or_unreviewed_not_admitted(self):
        rows,reviews=self.fixture();reviews[0]['related_sample_ids']=['other']
        self.assertFalse(prepare(rows,reviews,[],set())[0]['training_eligibility']['approved'])
        reviews[0]['original_inspected']=False
        with self.assertRaises(ValueError):prepare(rows,reviews,[],set())

    def test_protected_and_rights(self):
        rows,reviews=self.fixture();rows[0]['source_license']['url']='mismatch'
        self.assertFalse(prepare(rows,reviews,[],set())[0]['training_eligibility']['approved'])
        rows[0]['source_partition']='val2020'
        with self.assertRaises(ValueError):prepare(rows,reviews,[],set())
