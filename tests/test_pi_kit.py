"""Exercise offline-kit boundaries with fake wheels and models; no runtime installation."""
import copy
import json
from pathlib import Path
import stat
import unittest
import warnings
import zipfile

from tools import pi_kit as kit


class PiKitTests(unittest.TestCase):
    def setUp(self):
        # Reuse the real station-format fixture without importing its TestCase into this module.
        from tests.test_station_package import StationPackageTests
        station_fixture = StationPackageTests('test_invalid_ports_rejected')
        station_fixture.setUp()
        self.addCleanup(station_fixture.doCleanups)
        station_fixture.create()
        self.root = station_fixture.root
        self.station = station_fixture.output
        self.inputs = self.root / 'inputs'
        self.inputs.mkdir()
        self.wheels = self.root / 'wheelhouse'
        self.wheels.mkdir()
        self.output = self.root / 'kit-output'
        for name in kit.TOOLS:
            path = self.root / 'tools' / name
            path.parent.mkdir(exist_ok=True)
            path.write_text('# fixture ' + name, encoding='utf-8')
        self.profile = self.inputs / 'profile.json'
        self.write_json(self.profile, {'schema_version': 1, 'pi_verified': False, 'candidate_only': True,
            'target': {'board': 'Raspberry Pi 4', 'system': 'Linux', 'machine': 'aarch64',
                       'python': '3.13', 'abi': 'cp313', 'os_codename': 'trixie', 'min_glibc': '2.28'},
            'runtime': {'distribution': 'ai-edge-litert', 'version': '2.3.0',
                        'module': 'ai_edge_litert.interpreter'}})
        self.guide = self.inputs / 'guide.md'
        self.guide.write_text('Research installation fixture; Pi acceptance remains open.', encoding='utf-8')
        self.lock = self.inputs / 'candidate.lock.txt'
        self.write_wheel('ai-edge-litert', '2.3.0', 'cp313-cp313-manylinux_2_27_aarch64')
        self.write_wheel('numpy', '2.3.5', 'cp313-cp313-manylinux_2_27_aarch64')
        self.write_wheel('Pillow', '13.0.0', 'cp313-cp313-manylinux_2_28_aarch64')
        self.write_lock()
        self.reference = self.inputs / 'reference.json'
        config = json.loads((self.station / 'station.json').read_text())
        identities = {'pleating': kit.digest(self.station / 'application/model.tflite')}
        identities.update({name: record['sha256'] for name, record in config['models'].items()})
        tensor = {'shape': [1, 1], 'dtype': 'float32', 'sha256': 'a' * 64}
        models = {role: {'model_sha256': sha, 'input': copy.deepcopy(tensor),
                         'output': dict(tensor, values=[0.25])} for role, sha in identities.items()}
        self.write_json(self.reference, {'schema_version': 1, 'kind': 'pi_model_probe', 'status': 'passed',
            'pi_verified': False, 'full_live_acceptance': False,
            'station_inventory_sha256': kit.digest(self.station / 'station-inventory.json'),
            'worker': {'status': 'passed', 'fixture': {'id': 'rgb_mod256_v1', 'seed': 42}, 'models': models}})

    @staticmethod
    def write_json(path, record):
        path.write_text(json.dumps(record), encoding='utf-8')

    def write_wheel(self, name, version, tag, extra=None, metadata_name=None):
        filename = name.replace('-', '_') + '-' + version + '-' + tag + '.whl'
        path = self.wheels / filename
        info = name.replace('-', '_') + '-' + version + '.dist-info/'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr(info + 'METADATA', 'Metadata-Version: 2.1\nName: ' + (metadata_name or name)
                             + '\nVersion: ' + version + '\n')
            archive.writestr(info + 'WHEEL', 'Wheel-Version: 1.0\nTag: ' + tag + '\n')
            archive.writestr(name.replace('-', '_') + '/__init__.py', '# synthetic wheel')
            if extra:
                for member, body in extra:
                    # ZipInfo construction normalizes Windows separators; assign
                    # afterward to exercise an actually unsafe stored member.
                    entry = zipfile.ZipInfo('placeholder')
                    entry.filename = member
                    archive.writestr(entry, body)
        return path

    def write_lock(self):
        lines = []
        for path in sorted(self.wheels.glob('*.whl')):
            with zipfile.ZipFile(path) as archive:
                name = next(n for n in archive.namelist() if n.endswith('.dist-info/METADATA'))
                fields = dict(line.split(': ', 1) for line in archive.read(name).decode().splitlines() if ': ' in line)
            lines.append(fields['Name'] + '==' + fields['Version'] + ' --hash=sha256:' + kit.digest(path))
        self.lock.write_text('# Synthetic candidates\n' + '\n'.join(lines) + '\n', encoding='utf-8')

    def build(self, output=None):
        return kit.build(self.station, self.wheels, self.lock, self.reference,
                         self.profile, self.guide, output or self.output, self.root)

    def rehash(self):
        inventory = json.loads((self.output / 'inventory.json').read_text())
        for row in inventory['files']:
            path = self.output / row['path']
            row.update(bytes=path.stat().st_size, sha256=kit.digest(path))
        self.write_json(self.output / 'inventory.json', inventory)

    def test_build_verifies_and_relocates_without_mutating_station(self):
        before = kit.digest(self.station / 'station-inventory.json')
        result = self.build()
        self.assertEqual(result['status'], 'passed')
        self.assertFalse(result['pi_verified'])
        self.assertFalse(result['runtime_verified'])
        self.assertFalse(result['full_live_acceptance'])
        self.assertEqual(len(result['wheel_packages']), 3)
        self.assertEqual(before, kit.digest(self.station / 'station-inventory.json'))
        moved = self.root / 'relocated kit'
        self.output.rename(moved)
        self.assertEqual(kit.verify_kit(moved)['status'], 'passed')

    def test_existing_output_and_nested_inputs_are_preserved(self):
        self.build()
        before = kit.digest(self.output / 'inventory.json')
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            self.build()
        self.assertEqual(before, kit.digest(self.output / 'inventory.json'))
        for folder in (self.station, self.wheels, self.inputs, self.root / 'tools'):
            with self.subTest(folder=folder):
                with self.assertRaisesRegex(ValueError, 'immutable'):
                    self.build(folder / 'nested-kit')
                self.assertFalse((folder / 'nested-kit').exists())

    def test_tampered_payload_and_unlisted_entries_fail(self):
        self.build()
        guide = self.output / 'INSTALL_PI4.md'
        old = guide.read_bytes()
        guide.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'changed'):
            kit.verify_kit(self.output)
        guide.write_bytes(old)
        extra = self.output / 'unlisted.txt'
        extra.write_text('not inventoried')
        with self.assertRaisesRegex(ValueError, 'membership'):
            kit.verify_kit(self.output)
        extra.unlink()
        (self.output / 'empty-unlisted').mkdir()
        with self.assertRaisesRegex(ValueError, 'directory'):
            kit.verify_kit(self.output)

    def test_inventory_rejects_traversal_duplicates_and_invalid_sizes(self):
        self.build()
        path = self.output / 'inventory.json'
        original = json.loads(path.read_text())
        for value in ('../outside', '/absolute', 'tools\\windows.py', 'C:/outside'):
            altered = copy.deepcopy(original)
            altered['files'][0]['path'] = value
            self.write_json(path, altered)
            with self.assertRaises(ValueError):
                kit.verify_kit(self.output)
        duplicate = copy.deepcopy(original)
        duplicate['files'].append(dict(duplicate['files'][0], path=duplicate['files'][0]['path'].upper()))
        self.write_json(path, duplicate)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            kit.verify_kit(self.output)
        for value in (-1, True, '3'):
            altered = copy.deepcopy(original); altered['files'][0]['bytes'] = value
            self.write_json(path, altered)
            with self.assertRaisesRegex(ValueError, 'byte'):
                kit.verify_kit(self.output)

    def test_semantic_profile_and_pi_claim_checks_survive_rehash(self):
        self.build()
        path = self.output / 'config/profile.json'
        original = json.loads(path.read_text())
        for section, key, value in [('target', 'board', 'Raspberry Pi 5'), ('target', 'abi', 'cp312'),
                                    ('target', 'machine', 'x86_64'), ('runtime', 'version', '999')]:
            modified = copy.deepcopy(original); modified[section][key] = value
            self.write_json(path, modified); self.rehash()
            with self.assertRaises(ValueError):
                kit.verify_kit(self.output)
        self.write_json(path, original); self.rehash()
        manifest = self.output / 'kit.json'
        config = json.loads(manifest.read_text()); config['pi_verified'] = True
        self.write_json(manifest, config); self.rehash()
        with self.assertRaisesRegex(ValueError, 'metadata'):
            kit.verify_kit(self.output)

    def test_reference_identity_completion_and_finite_tensor_checks(self):
        original = json.loads(self.reference.read_text())
        variants = []
        for key, value in [('status', 'failed'), ('pi_verified', True), ('station_inventory_sha256', '0' * 64)]:
            modified = copy.deepcopy(original); modified[key] = value; variants.append(modified)
        modified = copy.deepcopy(original); del modified['worker']['models']['fabric']; variants.append(modified)
        modified = copy.deepcopy(original); modified['worker'] = []; variants.append(modified)
        modified = copy.deepcopy(original); modified['worker']['models']['pleating']['model_sha256'] = '0' * 64; variants.append(modified)
        for values in ([float('nan')], [True], [], [0.1, 0.2]):
            modified = copy.deepcopy(original); modified['worker']['models']['presence']['output']['values'] = values
            variants.append(modified)
        for modified in variants:
            self.write_json(self.reference, modified)
            with self.assertRaises(ValueError):
                self.build()
            self.assertFalse(self.output.exists())

    def test_lock_is_complete_exact_hashed_and_not_duplicated(self):
        original = self.lock.read_text()
        for modified in (original.replace('--hash=sha256:', '--hash=md5:'),
                         original + original.splitlines()[-1] + '\n',
                         '\n'.join(original.splitlines()[:-1]),
                         original.replace('ai-edge-litert==2.3.0', 'ai-edge-litert>=2.3.0'),
                         original.replace(kit.digest(next(self.wheels.glob('numpy-*.whl'))), '0' * 64)):
            self.lock.write_text(modified)
            with self.assertRaises(ValueError):
                self.build()
            self.assertFalse(self.output.exists())

    def test_incompatible_wheel_abi_architecture_and_identity_fail(self):
        target = json.loads(self.profile.read_text())['target']
        for tag in ('cp312-cp312-manylinux_2_27_aarch64', 'cp313-cp313-manylinux_2_27_x86_64',
                    'cp313-cp313-manylinux_2_34_aarch64'):
            path = self.write_wheel('different', '1.0', tag)
            with self.assertRaisesRegex(ValueError, 'ARM64'):
                kit.wheel_info(path, target)
        path = self.write_wheel('different', '1.0', 'py3-none-any', metadata_name='other-name')
        with self.assertRaisesRegex(ValueError, 'identities'):
            kit.wheel_info(path, target)

    def test_pure_python_and_stable_abi_tags_are_supported_candidates(self):
        target = json.loads(self.profile.read_text())['target']
        for tag in ('py3-none-any', 'cp311-abi3-manylinux_2_27_aarch64'):
            path = self.write_wheel('dependency', '1.0', tag)
            self.assertEqual(kit.wheel_info(path, target)['name'], 'dependency')

    def test_unsafe_or_duplicate_wheel_members_are_rejected_without_extraction(self):
        target = json.loads(self.profile.read_text())['target']
        for name in ('../outside', '/absolute', 'unsafe\\file.py'):
            path = self.write_wheel('dependency', '1.0', 'py3-none-any', [(name, 'never extracted')])
            with self.assertRaises(ValueError):
                kit.wheel_info(path, target)
        path = self.write_wheel('dependency', '1.0', 'py3-none-any')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(path, 'a') as archive:
                archive.writestr('dependency/__init__.py', 'duplicate')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            kit.wheel_info(path, target)
        path = self.write_wheel('dependency', '1.0', 'py3-none-any')
        member = zipfile.ZipInfo('dependency/link'); member.create_system = 3
        member.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(path, 'a') as archive:
            archive.writestr(member, '../outside')
        with self.assertRaisesRegex(ValueError, 'link'):
            kit.wheel_info(path, target)

    def test_missing_sources_and_bad_station_fail_before_output(self):
        (self.root / 'tools/pi_install.py').unlink()
        with self.assertRaises(OSError):
            self.build()
        self.assertFalse(self.output.exists())
        (self.station / 'models/presence/model.tflite').write_bytes(b'tampered')
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.output.exists())

    def test_symlink_inputs_and_output_parents_are_rejected(self):
        link = self.root / 'guide-link.md'
        try:
            link.symlink_to(self.guide)
        except OSError:
            self.skipTest('Symlink creation unavailable')
        with self.assertRaisesRegex(ValueError, 'Link'):
            kit.build(self.station, self.wheels, self.lock, self.reference,
                      self.profile, link, self.output, self.root)
        folder = self.root / 'output-link'
        folder.symlink_to(self.inputs, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Link'):
            self.build(folder / 'kit')


if __name__ == '__main__':
    unittest.main()
