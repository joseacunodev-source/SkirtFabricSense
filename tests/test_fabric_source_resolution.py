import unittest
from tools.datasets.fabric_source_resolution import analyze_table


class SourceTableTests(unittest.TestCase):
    def data(self, ids=('A0001', 'B0002')):
        return ('ID (AXXXX);Product type (#);Care Label Present (0,1);Readable label (0,1);Fibre 1 Layer 1;Area\n'
                + f'{ids[0]};9;1;1;cotton;A\n'
                + f'{ids[1]};5;1;1;polyester;B\n').encode()

    def test_skirt_count_is_metadata_only(self):
        result, skirts = analyze_table(self.data())
        self.assertEqual(result['skirt_metadata_rows'], 1)
        self.assertEqual(result['training_admissions'], 0)
        self.assertFalse(result['image_item_join_verified'])
        self.assertEqual(skirts[0]['ID (AXXXX)'], 'A0001')

    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError):
            analyze_table(self.data(('A0001', 'A0001')))

    def test_missing_columns_rejected(self):
        with self.assertRaises(ValueError):
            analyze_table(b'ID;type\n1;9\n')

    def test_no_composition_inferred_from_absent_label(self):
        result, _ = analyze_table(self.data().replace(b';9;1;1;', b';9;0;0;'))
        self.assertEqual(result['skirts_with_present_readable_label_and_first_fibre'], 0)
        self.assertFalse(result['appearance_label_conversion_performed'])
