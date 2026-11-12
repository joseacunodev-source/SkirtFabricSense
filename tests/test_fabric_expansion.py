import json
import unittest
from tools.datasets.expand_fabric_v2 import select, JOIN, OLD

class FabricExpansionTests(unittest.TestCase):
    def test_real_partition_excludes_all_prior_and_protected_groups(self):
        rows = list(map(json.loads, JOIN.read_text().splitlines()))
        old = list(map(json.loads, OLD.read_text().splitlines()))
        selected, assessment = select(rows, old)
        self.assertEqual(len(selected), 30)
        self.assertEqual(assessment['remaining_eligible_groups_by_source_label'], {'cotton':106})
        self.assertEqual(len({r['official_item_id'] for r in selected}), 30)
        forbidden = {r['official_item_id'] for r in old} | {r['official_item_id'] for r in rows if r['official_split'] != 'train'}
        self.assertFalse(forbidden & {r['official_item_id'] for r in selected})
        self.assertTrue(all(r['official_split'] == 'train' for r in selected))

    def test_conflicts_and_cross_partition_groups_are_excluded(self):
        def row(item, code, split='train', view='front'):
            return dict(official_item_id=item, lower_fabric_source_code=code, official_split=split, filename=f'WOMEN-Skirts-id_00000001-{item}_{view}.jpg')
        rows = [row('conflict',0), row('conflict',1), row('leak',0), row('leak',0,'query'), row('good',0), row('good',0,view='full')]
        chosen, assessment = select(rows, [])
        self.assertEqual([r['filename'] for r in chosen], ['WOMEN-Skirts-id_00000001-good_full.jpg'])
        self.assertIn('conflict',assessment['conflicting_or_unsupported_groups'])

    def test_limits(self):
        for limit in (0,61):
            with self.assertRaises(ValueError): select([], [], limit)

    def test_unsafe_filename_rejected(self):
        row = dict(official_item_id='id_00000001', lower_fabric_source_code=1,
                   official_split='train', filename='../escape.jpg')
        with self.assertRaises(ValueError): select([row], [])

if __name__ == '__main__': unittest.main()
