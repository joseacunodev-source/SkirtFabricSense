import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.verify_release import APP_REQUIRED, verify


class ReleaseVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'bundle'
        self.root.mkdir()
        source = Path(__file__).resolve().parents[1] / 'artifacts/models/skirt-finetune-v1/contract.json'
        (self.root / 'contract.json').write_bytes(source.read_bytes())
        (self.root / 'model.tflite').write_bytes(b'fake model; no runtime claim')
        self.manifest = dict(schema_version=1, bundle_id='skirt-finetune-v1',
                             status='development_only', pi_verified=False,
                             model='model.tflite', contract='contract.json')
        self.inventory = dict(schema_version=1, bundle_id='skirt-finetune-v1',
                              status='development_only', pi_verified=False, dependencies_included=False)
        self.rehash()

    def write_metadata(self):
        for name, value in [('manifest', self.manifest), ('inventory', self.inventory)]:
            (self.root / (name + '.json')).write_text(json.dumps(value), encoding='utf-8')

    def rehash(self):
        files = []
        for path in sorted(self.root.rglob('*')):
            if path.is_file() and path.name not in ('manifest.json', 'inventory.json'):
                data = path.read_bytes()
                files.append(dict(path=path.relative_to(self.root).as_posix(),
                                  sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
        self.inventory['files'] = files
        self.manifest['files'] = [{k: entry[k] for k in ('path', 'sha256')}
                                  for entry in files if entry['path'] in ('model.tflite', 'contract.json')]
        self.write_metadata()

    def test_valid_model_only(self):
        self.assertEqual(verify(self.root)['payload_files'], 2)
        self.assertFalse(verify(self.root)['runtime_verified'])

    def test_application_required_and_complete(self):
        with self.assertRaisesRegex(ValueError, 'application'):
            verify(self.root, True)
        for name in APP_REQUIRED:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture', encoding='utf-8')
        self.rehash()
        self.assertTrue(verify(self.root, True)['application_included'])
        (self.root / 'app/pipeline.py').write_text('fixture')
        self.rehash()
        with self.assertRaisesRegex(ValueError, 'async'):
            verify(self.root)

    def test_corrupt_same_size(self):
        path = self.root / 'model.tflite'
        path.write_bytes(b'X' * path.stat().st_size)
        with self.assertRaisesRegex(ValueError, 'hash'):
            verify(self.root)

    def test_missing_file(self):
        (self.root / 'model.tflite').unlink()
        with self.assertRaisesRegex(ValueError, 'inventory'):
            verify(self.root)

    def test_extra_file(self):
        (self.root / 'secret.txt').write_text('unexpected')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            verify(self.root)

    def test_extra_empty_directory(self):
        (self.root / 'unexpected').mkdir()
        with self.assertRaisesRegex(ValueError, 'directories'):
            verify(self.root)

    def test_unsafe_inventory_paths(self):
        for name in ('../outside', '/absolute', 'C:/absolute', 'app\\x', './model.tflite', 'app//x', 'app/x.'):
            with self.subTest(path=name):
                self.inventory['files'][0]['path'] = name
                self.write_metadata()
                with self.assertRaises(ValueError):
                    verify(self.root)

    def test_duplicate_entry(self):
        self.inventory['files'].append(dict(self.inventory['files'][0]))
        self.write_metadata()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            verify(self.root)

    def test_disagreeing_manifest(self):
        self.manifest['files'][0]['sha256'] = '0' * 64
        self.write_metadata()
        with self.assertRaisesRegex(ValueError, 'disagreement'):
            verify(self.root)

    def test_contract_change_even_when_rehashed(self):
        path = self.root / 'contract.json'
        contract = json.loads(path.read_text())
        contract['output']['labels'].reverse()
        path.write_text(json.dumps(contract))
        self.rehash()
        with self.assertRaisesRegex(ValueError, 'contract'):
            verify(self.root)

    def test_duplicate_json_key(self):
        path = self.root / 'manifest.json'
        path.write_text(path.read_text().replace('{', '{"schema_version": 1,', 1))
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON'):
            verify(self.root)

    def test_cannot_claim_pi_verified(self):
        self.manifest['pi_verified'] = True
        self.write_metadata()
        with self.assertRaisesRegex(ValueError, 'metadata'):
            verify(self.root)

    def test_symlink_file_rejected(self):
        target = self.root / 'model.tflite'
        outside = self.root.parent / 'outside.tflite'
        target.replace(outside)
        try:
            target.symlink_to(outside)
        except OSError as exc:
            self.skipTest('Host does not permit symlink creation: ' + str(exc))
        with self.assertRaisesRegex(ValueError, 'Link'):
            verify(self.root)


if __name__ == '__main__':
    unittest.main()
