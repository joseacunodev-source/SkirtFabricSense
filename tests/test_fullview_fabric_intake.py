"""Protect the real metadata boundary before any fabric image reaches training."""
import json
import unittest
from tools.datasets.acquire_fullview_fabric import candidates, DownloadForm, JOIN

class FullviewIntakeTests(unittest.TestCase):
    def test_selection_preserves_original_train_and_one_source_item(self):
        mapping = {r['filename']:r for r in map(json.loads, JOIN.read_text().splitlines())}
        selected = candidates(10)
        self.assertTrue(selected)
        self.assertEqual(len(selected), len({r[3] for r in selected}))
        for name, item, code, official_item in selected:
            self.assertEqual(mapping[name]['official_split'], 'train')
            self.assertEqual(mapping[name]['official_item_id'], official_item)
            self.assertEqual(mapping[name]['lower_fabric_source_code'], code)
            self.assertNotEqual(code, 7)
            self.assertFalse(mapping[name]['training_admitted'])

    def test_bounded_selection_does_not_add_test_only_classes(self):
        selected = candidates(1)
        self.assertEqual({r[2] for r in selected}, {0,1,2,5})
        self.assertEqual(len(selected), 4)

    def test_confirmation_fields_only_come_from_named_form(self):
        form = DownloadForm()
        form.feed('<input name="unrelated" value="bad"><form id="download-form" action="https://drive.usercontent.google.com/download"><input name="id" value="public"><input name="confirm" value="yes"></form><input name="outside" value="bad">')
        self.assertEqual(form.fields, {'id':'public', 'confirm':'yes'})
        self.assertEqual(form.action, 'https://drive.usercontent.google.com/download')

if __name__ == '__main__': unittest.main()
