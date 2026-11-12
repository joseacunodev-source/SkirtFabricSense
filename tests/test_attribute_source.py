import copy
import json
from pathlib import Path
import tempfile
import unittest
from tools.datasets.inspect_attribute_source import analyze, parse_dictionary, summarize, join_partitions, OUT


class AttributeSourceTests(unittest.TestCase):
    def setUp(self):
        self.args = [['img/Named_Skirt/img_00001.jpg'], [1], [[1, 0]],
                     [['Skirt', '2']], [['denim', '5'], ['pleated', '1']]]

    def test_dictionary_count(self):
        self.assertEqual(parse_dictionary('1\nname type\nSkirt 2\n'), [['Skirt', '2']])
        with self.assertRaises(ValueError):
            parse_dictionary('2\nname type\nSkirt 2\n')

    def test_dictionary_duplicates(self):
        with self.assertRaises(ValueError):
            parse_dictionary('2\nname type\nSkirt 2\nSkirt 2\n')

    def test_counts_and_no_admission(self):
        report, rows = summarize(*self.args)
        self.assertEqual(report['fabric_counts']['denim']['image_references'], 1)
        self.assertFalse(rows[0]['training_eligible'])
        self.assertEqual(rows[0]['source_partition'], 'Anno_fine/train')

    def test_unequal_rows(self):
        self.args[1] = []
        with self.assertRaises(ValueError): summarize(*self.args)

    def test_reject_bad_categories_attributes_and_paths(self):
        for index, bad in [(0, ['../bad.jpg']), (1, [0]), (1, [2]), (2, [[-1, 0]]), (2, [[1]])]:
            args = copy.deepcopy(self.args)
            args[index] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError): summarize(*args)

    def test_duplicate_path(self):
        for index in range(3): self.args[index] *= 2
        with self.assertRaises(ValueError): summarize(*self.args)

    def test_multi_attribute_kept(self):
        self.args[4][1] = ['chiffon', '5']
        self.args[2][0][1] = 1
        report, rows = summarize(*self.args)
        self.assertEqual(report['fabric_label_cardinality'], {2: 1})
        self.assertEqual(rows[0]['source_fabric_attributes'], ['denim', 'chiffon'])

    def test_tamper_fails_before_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target/'report.json').write_text(json.dumps({'observations': []}))
            (target/'list_attr_cloth.txt').write_text('tamper')
            with self.assertRaisesRegex(ValueError, 'hash/size mismatch'): analyze(target)

    def test_saved_metadata_counts(self):
        # Temporary output avoids rewriting dated research records during tests.
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            for name in ['report.json', 'list_attr_cloth.txt', 'list_category_cloth.txt', 'train.txt', 'train_cate.txt', 'train_attr.txt']:
                (target/name).write_bytes((OUT/name).read_bytes())
            result = analyze(target)
            self.assertEqual((result['training_rows'], result['skirt_image_references']), (14000, 680))
            self.assertEqual(result['fabric_counts']['chiffon']['image_references'], 74)
            self.assertEqual(result['fabric_counts']['knit']['image_references'], 37)
            self.assertFalse(result['test_labels_accessed'])

    def test_partition_join_excludes_original_holdouts_and_shared_folders(self):
        _, rows = summarize(*self.args)
        text = '2\nimage_name evaluation_status\nimg/Named_Skirt/img_00001.jpg train\nimg/Named_Skirt/img_00002.jpg test\n'
        joined, total = join_partitions(text, rows)
        self.assertEqual(total, 2)
        self.assertFalse(joined[0]['acquisition_eligible'])
        self.assertEqual(joined[0]['folder_original_partitions'], ['test', 'train'])
        self.assertFalse(joined[0]['physical_garment_identity_verified'])

    def test_partition_train_only_group_eligible_but_not_admitted(self):
        _, rows = summarize(*self.args)
        joined, _ = join_partitions('1\nimage_name evaluation_status\nimg/Named_Skirt/img_00001.jpg train\n', rows)
        self.assertTrue(joined[0]['acquisition_eligible'])
        self.assertFalse(joined[0]['training_eligible'])

    def test_partition_invalid_and_missing(self):
        _, rows = summarize(*self.args)
        for text in ['0\nheader\n', '1\nheader\nimg/Named_Skirt/img_00001.jpg unknown\n',
                     '2\nheader\nimg/Named_Skirt/img_00001.jpg train\nimg/Named_Skirt/img_00001.jpg test\n']:
            with self.subTest(text=text), self.assertRaises(ValueError): join_partitions(text, rows)


if __name__ == '__main__': unittest.main()
