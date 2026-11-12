import unittest
from tools.datasets.merge_presentation_reviews import merge


class PresentationMergeTests(unittest.TestCase):
    def test_overrides_require_same_original_and_unique_identity(self):
        sheet = dict(sample_id='one', original_path='one.jpg', image_sha256='sha',
                     review_method='contact_sheet_visual_inspection', presentation='unknown')
        original = dict(sheet, review_method='original_image_visual_inspection', presentation='worn')
        self.assertEqual(merge([], [sheet], [original]), [original])
        for override in (dict(original, image_sha256='changed'), dict(original, sample_id='foreign'), sheet):
            with self.assertRaises(ValueError):
                merge([], [sheet], [override])
        with self.assertRaises(ValueError):
            merge([], [sheet], [original, original])
        with self.assertRaises(ValueError):
            merge([sheet], [sheet], [])


if __name__ == '__main__':
    unittest.main()
