import importlib.util
import io
from pathlib import Path
import unittest
from PIL import Image

PATH = Path(__file__).resolve().parents[1] / 'tools/datasets/expand_negatives_v2.py'
spec = importlib.util.spec_from_file_location('negative_v2', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class NegativeExpansionTests(unittest.TestCase):
    def test_license_name_url_pair_required(self):
        for name, url in mod.LICENSE_URLS.items():
            self.assertTrue(mod.permitted_license({'name': name, 'url': url}))
        self.assertFalse(mod.permitted_license({'name': 'Attribution License', 'url': 'https://creativecommons.org/licenses/by-nd/2.0/'}))
        self.assertFalse(mod.permitted_license({'name': 'Attribution License', 'url': 'https://creativecommons.org.evil/licenses/by/2.0/'}))
        self.assertFalse(mod.permitted_license({}))

    def test_flickr_variants_and_page_share_key(self):
        key = 'flickr-photo-36501437664'
        for url in ['https://live.staticflickr.com/2/36501437664_abc123_b.jpg', 'https://www.flickr.com/photos/gotovan/36501437664/']:
            self.assertEqual(mod.source_key(url), key)

    def test_dimension_mismatch_rejected(self):
        image = io.BytesIO()
        Image.new('RGB', (10, 12)).save(image, format='PNG')
        self.assertEqual(mod.validate_image(image.getvalue(), {'width': 10, 'height': 12}), (10, 12))
        with self.assertRaisesRegex(ValueError, 'Dimensions'):
            mod.validate_image(image.getvalue(), {'width': 12, 'height': 10})

    def test_selection_retains_exclusions_and_no_skirts(self):
        data = {'categories': [{'id': 6,'name': 'pants'}, {'id': 7,'name': 'shorts'}, {'id': 8,'name': 'skirt'}, {'id': 10,'name': 'dress'}],
                'licenses': [{'id': 0,'name': 'Attribution License','url': mod.LICENSE_URLS['Attribution License']}], 'images': [], 'annotations': []}
        for i, category in enumerate([6, 7, 10, 6, 8], 1):
            data['images'].append({'id': i, 'license': 0, 'width': 100, 'height': 100, 'original_url': f'https://live.staticflickr.com/2/{i}_abc123.jpg'})
            data['annotations'].append({'image_id': i, 'category_id': category, 'bbox': [10, 10, 60, 60]})
        exclusions = {'flickr-photo-4'}
        rows = mod.select(data, {'2'}, exclusions)
        self.assertEqual({row[0]['id'] for row in rows}, {1, 3})
        self.assertEqual(exclusions, {'flickr-photo-4'})

if __name__ == '__main__':
    unittest.main()
