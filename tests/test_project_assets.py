"""Exercise private asset transfer using small local files; no network or models."""
import copy
import hashlib
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

from tools import project_assets as assets


class ProjectAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='skirt-assets-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base/'source'
        self.source.mkdir()
        self.content = {'artifacts/model.tflite': b'model fixture\0' * 100,
                        'data/external/source/image.jpg': b'image fixture',
                        'records/acquisitions/source/raw.json': b'{"source": "fixture"}'}
        for name, body in self.content.items():
            path = self.source/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        self.manifest = {'schema_version': 1, 'data_kind': 'git_excluded_project_assets',
                         'file_count': len(self.content),
                         'total_bytes': sum(map(len, self.content.values())),
                         'files': [{'path': name, 'bytes': len(body),
                                    'sha256': hashlib.sha256(body).hexdigest()}
                                   for name, body in sorted(self.content.items())]}
        self.archive = self.base/'assets.zip'
        self.destination = self.base/'destination'

    def write_zip(self, entries=None):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.archive, 'w') as archive:
                for name, body in entries if entries is not None else self.content.items():
                    archive.writestr(name, body)

    def test_inventory_requires_git_ignored_and_permitted_paths(self):
        if not shutil.which('git'):
            self.skipTest('Git unavailable')
        subprocess.run(['git', 'init', '-q', str(self.source)], check=True)
        (self.source/'.gitignore').write_text(
            'artifacts/\ndata/external/\nrecords/acquisitions/\ndata/candidates/\ndocs/references/*.jpg\n', encoding='utf-8')
        extra = {'artifacts/.env': b'not transferable', 'artifacts/__pycache__/code.pyc': b'cache',
                 'artifacts/backup.zip': b'archive', 'records/camera/frame.jpg': b'not ignored',
                 'records/acquisitions/source/credentials.json': b'not transferable',
                 'data/candidates/review.jpg': b'candidate', 'docs/references/guide.jpg': b'guide'}
        for name, body in extra.items():
            target = self.source/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
        actual = assets.inventory(self.source)
        self.assertEqual({r['path'] for r in actual['files']},
                         set(self.content) | {'data/candidates/review.jpg', 'docs/references/guide.jpg'})
        self.assertEqual(assets.verify(self.source, actual)['status'], 'passed')

    def test_pack_restore_and_matching_files_are_preserved(self):
        result = assets.pack(self.source, self.manifest, self.archive)
        self.assertEqual(result['status'], 'packed')
        restored = assets.restore(self.archive, self.manifest, self.destination)
        self.assertEqual(restored['files_copied'], len(self.content))
        self.assertEqual(restored['verification']['status'], 'passed')
        again = assets.restore(self.archive, self.manifest, self.destination)
        self.assertEqual(again['files_copied'], 0)
        self.assertEqual(again['files_already_matched'], len(self.content))
        for name, body in self.content.items():
            self.assertEqual((self.destination/name).read_bytes(), body)

    def test_only_required_dtd_source_archive_is_inventoried_and_transferred(self):
        if not shutil.which('git'):
            self.skipTest('Git unavailable')
        subprocess.run(['git', 'init', '-q', str(self.source)], check=True)
        (self.source/'.gitignore').write_text('data/external/\n', encoding='utf-8')
        allowed = 'data/external/dtd/dtd-r1.0.1-labels.tar.gz'
        self.assertEqual(assets.SOURCE_ARCHIVE_ALLOWLIST, {allowed})
        archives = {allowed: b'synthetic annotations archive',
                    'data/external/dtd/other-labels.tar.gz': b'other source archive',
                    'data/external/dtd/dtd-r1.0.1-labels.tar.gz.zip': b'wrapped source',
                    'artifacts/transfer-backup.zip': b'generated archive',
                    'records/acquisitions/backup.tar': b'backup'}
        for name, body in archives.items():
            target = self.source/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
            self.assertEqual(assets.permitted(name), name == allowed)
        inventory = assets.inventory(self.source)
        self.assertEqual({r['path'] for r in inventory['files']},
                         {allowed, 'data/external/source/image.jpg'})
        assets.pack(self.source, inventory, self.archive)
        restored = assets.restore(self.archive, inventory, self.destination)
        self.assertEqual(restored['verification']['status'], 'passed')
        self.assertEqual((self.destination/allowed).read_bytes(), archives[allowed])
        self.assertFalse((self.destination/'artifacts/transfer-backup.zip').exists())

    def test_verify_reports_missing_and_mismatched(self):
        (self.source/'artifacts/model.tflite').write_bytes(b'changed')
        (self.source/'data/external/source/image.jpg').unlink()
        result = assets.verify(self.source, self.manifest)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['missing'], ['data/external/source/image.jpg'])
        self.assertEqual(result['mismatched'], ['artifacts/model.tflite'])

    def test_pack_refuses_existing_archive(self):
        self.archive.write_bytes(b'preserve')
        with self.assertRaises(FileExistsError):
            assets.pack(self.source, self.manifest, self.archive)
        self.assertEqual(self.archive.read_bytes(), b'preserve')

    def test_pack_refuses_invalid_source_and_removes_new_failed_archive(self):
        (self.source/'artifacts/model.tflite').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'verification'):
            assets.pack(self.source, self.manifest, self.archive)
        self.assertFalse(self.archive.exists())
        with patch.object(assets, 'verify', return_value={'status': 'passed'}):
            with self.assertRaisesRegex(ValueError, 'changed during packing'):
                assets.pack(self.source, self.manifest, self.archive)
        self.assertFalse(self.archive.exists())

    def test_restore_existing_mismatch_prevents_any_new_file(self):
        self.write_zip()
        mismatch = self.destination/'data/external/source/image.jpg'
        mismatch.parent.mkdir(parents=True)
        mismatch.write_bytes(b'preserve')
        with self.assertRaisesRegex(ValueError, 'Existing destination differs'):
            assets.restore(self.archive, self.manifest, self.destination)
        self.assertEqual(mismatch.read_bytes(), b'preserve')
        self.assertFalse((self.destination/'artifacts/model.tflite').exists())

    def test_restore_rejects_wrong_hash_before_writing_destination(self):
        modified = dict(self.content)
        modified['records/acquisitions/source/raw.json'] = b'X' * len(modified['records/acquisitions/source/raw.json'])
        self.write_zip(modified.items())
        with self.assertRaisesRegex(ValueError, 'SHA256 differs'):
            assets.restore(self.archive, self.manifest, self.destination)
        self.assertFalse(any(self.destination.rglob('*')))

    def test_restore_rejects_unsafe_extra_duplicate_and_size_entries(self):
        variants = [list(self.content.items()) + [(name, b'bad')]
                    for name in ('../outside', '/absolute', 'artifacts\\windows.bin',
                                 'artifacts/extra.bin', 'ARTIFACTS/model.tflite', 'artifacts/model.tflite')]
        variants.append([(name, body + b'growth') for name, body in self.content.items()])
        for entries in variants:
            with self.subTest(entries=[name for name, _ in entries]):
                self.write_zip(entries)
                with self.assertRaises(ValueError):
                    assets.restore(self.archive, self.manifest, self.destination)
                self.assertFalse(any(self.destination.rglob('*')))
        self.assertFalse((self.base/'outside').exists())

    def test_restore_rejects_zip_symlink(self):
        with zipfile.ZipFile(self.archive, 'w') as archive:
            for name, body in self.content.items():
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, body)
        with self.assertRaisesRegex(ValueError, 'links/non-files'):
            assets.restore(self.archive, self.manifest, self.destination)

    def test_manifest_rejects_duplicate_case_and_unsafe_paths(self):
        for name in ('../escape', 'README.md', 'artifacts/.env', 'artifacts/CON.txt',
                     'artifacts/file.', 'artifacts/file\x00', 'artifacts/backup.zip'):
            with self.subTest(path=name):
                manifest = copy.deepcopy(self.manifest)
                manifest['files'][0]['path'] = name
                with self.assertRaises(ValueError):
                    assets.manifest_rows(manifest)
        manifest = copy.deepcopy(self.manifest)
        manifest['files'][1]['path'] = 'ARTIFACTS/model.tflite'
        with self.assertRaises(ValueError):
            assets.manifest_rows(manifest)

    def test_manifest_rejects_totals_and_types(self):
        for key, value in (('bytes', -1), ('bytes', True), ('sha256', 'bad')):
            manifest = copy.deepcopy(self.manifest)
            manifest['files'][0][key] = value
            with self.assertRaises(ValueError):
                assets.manifest_rows(manifest)
        manifest = copy.deepcopy(self.manifest)
        manifest['total_bytes'] += 1
        with self.assertRaisesRegex(ValueError, 'totals'):
            assets.manifest_rows(manifest)

    def test_source_and_destination_symlinks_are_rejected(self):
        target = self.source/'artifacts/model.tflite'
        target.unlink()
        external = self.base/'external.bin'
        external.write_bytes(self.content['artifacts/model.tflite'])
        try:
            target.symlink_to(external)
        except OSError:
            self.skipTest('Creating symlinks is unavailable on this host')
        with self.assertRaisesRegex(ValueError, 'Symlinks/junctions'):
            assets.verify(self.source, self.manifest)
        self.write_zip()
        self.destination.mkdir()
        (self.destination/'artifacts').symlink_to(self.source/'artifacts', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlinks/junctions'):
            assets.restore(self.archive, self.manifest, self.destination)


if __name__ == '__main__':
    unittest.main()
