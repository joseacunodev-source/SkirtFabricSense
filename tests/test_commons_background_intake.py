import copy
import unittest

from tools.datasets import acquire_commons_backgrounds as intake


def selected():
    return {'pageid': 10, 'title': 'File:Empty room.jpg', 'candidate_category': 'Category:Empty rooms'}


def page():
    return {'pageid': 10, 'title': 'File:Empty room.jpg', 'ns': 6,
            'revisions': [{'revid': 54321}],
            'imageinfo': [{'url': 'https://upload.wikimedia.org/wikipedia/commons/a/ab/Empty_room.jpg',
                           'mime': 'image/jpeg', 'mediatype': 'BITMAP', 'size': 512, 'width': 640, 'height': 480,
                           'sha1': 'a' * 40, 'timestamp': '2020-01-01T00:00:00Z', 'user': 'Uploader',
                           'extmetadata': {'Artist': {'value': '<a href="https://commons.wikimedia.org/wiki/User:Photographer">Actual Creator</a>'},
                                           'LicenseUrl': {'value': 'https://creativecommons.org/licenses/by-sa/4.0'},
                                           'LicenseShortName': {'value': 'CC BY-SA 4.0'},
                                           'Credit': {'value': 'Own work'}, 'ObjectName': {'value': 'Empty room'}}}]}


class CommonsIntakeTests(unittest.TestCase):
    def test_per_file_attribution_identity_and_revision(self):
        evidence = intake.photo_evidence(page(), selected())
        self.assertEqual(evidence['author'], 'Actual Creator')
        self.assertNotEqual(evidence['author'], evidence['source_uploader'])
        self.assertEqual(evidence['source_revision'], 54321)
        self.assertEqual(evidence['license_url'], 'https://creativecommons.org/licenses/by-sa/4.0/')
        self.assertEqual(evidence['modifications'], 'None; original source JPEG bytes retained')

    def test_thumbnail_rejected_even_with_valid_license(self):
        value = page()
        value['imageinfo'][0]['url'] = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Empty_room.jpg/640px-Empty_room.jpg'
        with self.assertRaisesRegex(ValueError, 'thumbnail'):
            intake.photo_evidence(value, selected())

    def test_oversized_original_not_replaced_with_thumbnail(self):
        value = page()
        value['imageinfo'][0]['size'] = intake.PHOTO_CAP + 1
        value['imageinfo'][0]['thumburl'] = 'https://upload.wikimedia.org/wikipedia/commons/thumb/small.jpg'
        with self.assertRaisesRegex(ValueError, '2MiB cap'):
            intake.photo_evidence(value, selected())

    def test_missing_or_unknown_author_excluded(self):
        for author in ('', 'unknown', 'Anonymous', '<span>Unknown author</span>'):
            value = page()
            value['imageinfo'][0]['extmetadata']['Artist']['value'] = author
            with self.subTest(author=author), self.assertRaisesRegex(ValueError, 'attribution'):
                intake.photo_evidence(value, selected())

    def test_nonpermissive_or_unsupported_license_excluded(self):
        for licence in ('https://creativecommons.org/licenses/by-nc/4.0/', 'https://creativecommons.org/licenses/by-nd/2.0/',
                        'https://creativecommons.org/publicdomain/zero/1.0/', 'https://example.test/license'):
            value = page()
            value['imageinfo'][0]['extmetadata']['LicenseUrl']['value'] = licence
            with self.subTest(license=licence), self.assertRaisesRegex(ValueError, 'per-file'):
                intake.photo_evidence(value, selected())

    def test_license_name_url_conflict_excluded(self):
        value = page()
        value['imageinfo'][0]['extmetadata']['LicenseShortName']['value'] = 'CC BY-NC 4.0'
        with self.assertRaisesRegex(ValueError, 'conflict'):
            intake.photo_evidence(value, selected())

    def test_changed_photo_revision_or_identity_not_silently_accepted(self):
        for key, value in [('pageid', 11), ('title', 'File:Other.jpg'), ('ns', 0), ('revisions', [])]:
            source = page()
            source[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                intake.photo_evidence(source, selected())

    def test_restrictions_not_silently_ignored(self):
        value = page()
        value['imageinfo'][0]['extmetadata']['Restrictions'] = {'value': 'personality rights'}
        with self.assertRaisesRegex(ValueError, 'restrictions'):
            intake.photo_evidence(value, selected())

    def test_original_host_and_type_restricted(self):
        for key, value in [('mime', 'image/png'), ('mediatype', 'DRAWING'), ('url', 'https://example.test/photo.jpg'), ('sha1', 'bad')]:
            source = page()
            source['imageinfo'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                intake.photo_evidence(source, selected())

    def test_category_selection_deterministic_bounded_and_provisional(self):
        rows = [{'pageid': 11, 'title': 'File:Zebra vase.jpg', 'ns': 6},
                {'pageid': 10, 'title': 'File:Empty room.jpg', 'ns': 6},
                {'pageid': 12, 'title': 'File:A woman wearing skirt.jpg', 'ns': 6},
                {'pageid': 13, 'title': 'File:Model.svg', 'ns': 6}]
        result = intake.category_rows({'query': {'categorymembers': rows}}, 'Category:Empty rooms')
        self.assertEqual([row['pageid'] for row in result], [10, 11])
        self.assertFalse(any('labels' in row for row in result))
        with self.assertRaisesRegex(ValueError, 'bound'):
            intake.category_rows({'query': {'categorymembers': rows * 3}}, 'Category:Empty rooms')

    def test_api_errors_and_duplicates_stop(self):
        with self.assertRaisesRegex(ValueError, 'API error'):
            intake.category_rows({'error': {'code': 'denied'}}, 'Category:Empty rooms')
        row = {'pageid': 10, 'title': 'File:Empty room.jpg', 'ns': 6}
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            intake.category_rows({'query': {'categorymembers': [row, copy.deepcopy(row)]}}, 'Category:Empty rooms')

    def test_source_partition_does_not_invent_train_membership(self):
        url = intake.api_url(list='categorymembers', cmtitle='Category:Empty rooms', cmlimit='8')
        self.assertTrue(url.startswith('https://commons.wikimedia.org/w/api.php?'))
        self.assertNotIn('train', url)
        self.assertNotIn('validation', url)


if __name__ == '__main__':
    unittest.main()
