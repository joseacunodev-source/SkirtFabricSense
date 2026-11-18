"""Synthetic Pi installation contracts; every subprocess is mocked, no installs."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import pi_install as installer


class PiInstallTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.kit = self.root / 'input-kit'
        (self.kit / 'config').mkdir(parents=True)
        (self.kit / 'tools').mkdir()
        (self.kit / 'tools/collect_environment.py').write_text('# synthetic, never executed', encoding='utf-8')
        self.profile = {'target': {'python': '3.13', 'os_codename': 'trixie', 'min_glibc': '2.28'},
                        'runtime': {'distribution': 'synthetic-runtime', 'version': 'fixture'}}
        (self.kit / 'config/profile.json').write_text(json.dumps(self.profile), encoding='utf-8')
        self.destination = self.home / 'new-release'
        self.records = self.root / 'evidence'
        self.observed = {'system': 'Linux', 'machine': 'aarch64', 'pointer_bits': 64,
                         'python': [3, 13], 'libc': ['glibc', '2.41'],
                         'board': 'Raspberry Pi 4 Model B Rev 1.5',
                         'os_codename': 'trixie', 'effective_uid': 1000}
        self.station_hash = hashlib.sha256(b'synthetic station identity').hexdigest()
        self.verified = {'status': 'passed', 'station_inventory_sha256': self.station_hash,
                         'wheel_packages':[{'name':'synthetic-runtime','version':'fixture'},
                                           {'name':'Pillow','version':'synthetic'},
                                           {'name':'numpy','version':'synthetic'}],
                         'pi_verified': False}
        self.probe_report = {'status': 'passed', 'pi_verified': False, 'full_live_acceptance': False,
                             'station_inventory_sha256': self.station_hash,
                             'parity': {'status': 'passed'},
                             'worker': {'models': {name: {} for name in
                                 ('pleating', 'localizer', 'presence', 'fabric')}}}

    def plan(self, observation=None, **kwargs):
        with patch.object(installer.Path, 'home', return_value=self.home), \
             patch.object(installer, 'verify_kit', return_value=self.verified):
            return installer.plan(self.kit, self.destination, self.records,
                                  self.observed if observation is None else observation, **kwargs)

    def install(self, fail_pip=False, fail_snapshot=False, probe_report=None, exception_on_pip=False):
        commands = []
        def execute(command, **kwargs):
            commands.append(command)
            self.assertTrue(kwargs['capture_output'])
            self.assertEqual(kwargs['env']['PYTHONDONTWRITEBYTECODE'], '1')
            if '-m' in command and 'venv' in command:
                target = Path(command[-1]) / 'bin/python'
                target.parent.mkdir(parents=True)
                target.write_text('synthetic interpreter; never executed', encoding='utf-8')
            if '-m' in command and 'pip' in command and 'install' in command:
                if exception_on_pip: raise OSError('synthetic executable failure')
                if fail_pip: return subprocess.CompletedProcess(command, 1, '', 'synthetic wheel failure')
            if '-c' in command:
                return subprocess.CompletedProcess(command, 0, '{"synthetic-runtime":"fixture","Pillow":"synthetic","numpy":"synthetic"}', '')
            if '--output' in command:
                output = Path(command[command.index('--output') + 1])
                if any(str(value).endswith('collect_environment.py') for value in command):
                    if fail_snapshot: return subprocess.CompletedProcess(command, 1, '', 'synthetic collector failure')
                    output.write_text('{"environment":"synthetic"}', encoding='utf-8')
                else:
                    output.write_text(json.dumps(self.probe_report if probe_report is None else probe_report),
                                      encoding='utf-8')
            return subprocess.CompletedProcess(command, 0, 'synthetic command passed', '')
        with patch.object(installer.Path, 'home', return_value=self.home), \
             patch.object(installer, 'observe', return_value=self.observed), \
             patch.object(installer, 'verify_kit', return_value=self.verified), \
             patch.object(installer.subprocess, 'run', side_effect=execute):
            report = installer.install(self.kit, self.destination, self.records)
        return report, commands

    def test_plan_is_read_only_and_keeps_physical_acceptance_open(self):
        before = {path.relative_to(self.root).as_posix(): path.read_bytes()
                  for path in self.root.rglob('*') if path.is_file()}
        with patch.object(installer.subprocess, 'run') as command:
            result = self.plan(fabric_research=True)
        command.assert_not_called()
        after = {path.relative_to(self.root).as_posix(): path.read_bytes()
                 for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(result['status'], 'planned_not_installed')
        self.assertTrue(result['fabric_research'])
        self.assertFalse(result['pi_verified'])
        self.assertFalse(result['full_live_acceptance'])
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.records.exists())

    def test_wrong_platform_os_python_board_root_and_libc_block_plan(self):
        mismatches = [('system', 'Windows'), ('machine', 'x86_64'), ('pointer_bits', 32),
                      ('python', [3, 11]), ('board', 'Raspberry Pi 5 Model B'),
                      ('board', ''), ('os_codename', 'bookworm'), ('effective_uid', 0),
                      ('libc', ['glibc', '2.27']), ('libc', ['musl', '1.2']), ('libc', [])]
        for key, value in mismatches:
            with self.subTest(key=key, value=value):
                result = self.plan(dict(self.observed, **{key: value}))
                self.assertEqual(result['status'], 'blocked')
                self.assertTrue(result['blockers'])
                self.assertFalse(result['pi_verified'])

    def test_install_refuses_wrong_target_before_any_mutation(self):
        observation = dict(self.observed, machine='x86_64')
        with patch.object(installer.Path, 'home', return_value=self.home), \
             patch.object(installer, 'observe', return_value=observation), \
             patch.object(installer, 'verify_kit', return_value=self.verified), \
             patch.object(installer.subprocess, 'run') as command:
            with self.assertRaisesRegex(ValueError, 'ARM'):
                installer.install(self.kit, self.destination, self.records)
        command.assert_not_called()
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.records.exists())

    def test_locations_protect_existing_source_and_records(self):
        with patch.object(installer.Path, 'home', return_value=self.home):
            self.destination.mkdir()
            with self.assertRaisesRegex(ValueError, 'existing releases'):
                installer.locations(self.kit, self.destination, self.records)
            with self.assertRaisesRegex(ValueError, 'home'):
                installer.locations(self.kit, self.root / 'outside-home', self.records)
            with self.assertRaisesRegex(ValueError, 'records outside'):
                installer.locations(self.kit, self.home / 'other', self.kit / 'records')
            with self.assertRaisesRegex(ValueError, 'records outside'):
                installer.locations(self.kit, self.home / 'other', self.home / 'other/evidence')
            nested_kit = self.home / 'input'
            nested_kit.mkdir()
            with self.assertRaisesRegex(ValueError, 'separate'):
                installer.locations(nested_kit, nested_kit / 'release', self.records)
            with self.assertRaisesRegex(ValueError, 'Control characters'):
                installer.locations(self.kit, self.home / 'bad\nExecStart=other', self.records)

    def test_symlink_input_and_records_are_rejected(self):
        link = self.root / 'kit-link'
        try: link.symlink_to(self.kit, target_is_directory=True)
        except OSError: self.skipTest('Symlink creation is unavailable on this host')
        with patch.object(installer.Path, 'home', return_value=self.home):
            with self.assertRaisesRegex(ValueError, 'Symlinks'):
                installer.locations(link, self.destination, self.records)
            with self.assertRaisesRegex(ValueError, 'Symlinks'):
                installer.locations(self.kit, self.destination, link)

    def test_success_uses_offline_hash_pins_and_does_not_activate_service(self):
        result, commands = self.install()
        self.assertEqual(result['status'], 'installed_model_checks_passed_physical_acceptance_open')
        for key in ('pi_verified', 'full_live_acceptance', 'service_enabled', 'camera_permission_granted'):
            self.assertFalse(result[key])
        wheel_command = next(command for command in commands if 'pip' in command and 'install' in command)
        for argument in ('--no-index', '--only-binary=:all:', '--require-hashes'):
            self.assertIn(argument, wheel_command)
        self.assertFalse(any('systemctl' in command or 'sudo' in command or 'apt' in command for command in commands))
        run = Path(result['records_directory'])
        ledger = [json.loads(row) for row in (self.records / 'installations.jsonl').read_text().splitlines()]
        self.assertTrue(ledger)
        self.assertTrue(all(row['status'] == 'succeeded' for row in ledger))
        self.assertTrue((run / 'environment.json').is_file())
        self.assertTrue((run / 'installed-versions.json').is_file())
        self.assertTrue((run / 'installation-result.json').is_file())
        self.assertTrue((run / 'skirtfabric.service').is_file())
        self.assertFalse((self.home / '.config/systemd/user/skirtfabric.service').exists())

    def test_wheel_failure_is_logged_and_failed_release_is_preserved(self):
        for index, exception in enumerate((False, True)):
            with self.subTest(exception=exception):
                self.destination = self.home / f'failure-{index}'
                self.records = self.root / f'failure-records-{index}'
                result, _ = self.install(fail_pip=True, exception_on_pip=exception)
                self.assertEqual(result['status'], 'failed')
                self.assertTrue(self.destination.is_dir())
                self.assertTrue((self.destination / 'kit/config/profile.json').is_file())
                ledger = [json.loads(row) for row in (self.records / 'installations.jsonl').read_text().splitlines()]
                failure = next(row for row in ledger if row['action'] == 'install-wheels')
                self.assertEqual(failure['status'], 'failed')
                self.assertNotEqual(failure['exit_code'], 0)
                self.assertTrue(Path(failure['verification_log']).is_file())
                self.assertTrue((Path(result['records_directory']) / 'environment.json').is_file())
                self.assertFalse((Path(result['records_directory']) / 'skirtfabric.service').exists())

    def test_environment_failure_remains_failure_after_best_effort_snapshot(self):
        result, _ = self.install(fail_snapshot=True)
        self.assertEqual(result['status'], 'failed')
        self.assertIn('environment-snapshot', result['error'])
        self.assertTrue((Path(result['records_directory']) / 'installation-result.json').is_file())

    def test_probe_requires_parity_station_all_roles_and_research_flags(self):
        variants = []
        for key, value in [('pi_verified', True), ('full_live_acceptance', True),
                           ('station_inventory_sha256', '0' * 64), ('status', 'failed')]:
            item = copy.deepcopy(self.probe_report); item[key] = value; variants.append(item)
        absent_parity = copy.deepcopy(self.probe_report); absent_parity['parity'] = {'status': 'not_requested'}; variants.append(absent_parity)
        missing_role = copy.deepcopy(self.probe_report); del missing_role['worker']['models']['fabric']; variants.append(missing_role)
        variants.append([])
        for field in ('parity','worker'):
            item = copy.deepcopy(self.probe_report); item[field] = None; variants.append(item)
        item = copy.deepcopy(self.probe_report); item['worker']['models'] = None; variants.append(item)
        for index, item in enumerate(variants):
            with self.subTest(index=index):
                self.destination = self.home / f'bad-probe-{index}'
                self.records = self.root / f'bad-probe-records-{index}'
                result, _ = self.install(probe_report=item)
                self.assertEqual(result['status'], 'failed')
                self.assertFalse((Path(result['records_directory']) / 'skirtfabric.service').exists())

    def test_observed_versions_must_match_the_verified_wheels(self):
        self.verified['wheel_packages'][0]['version'] = 'different-fixture'
        result, _ = self.install()
        self.assertEqual(result['status'], 'failed')
        self.assertIn('versions differ', result['error'])
        self.assertFalse((Path(result['records_directory']) / 'skirtfabric.service').exists())

    def test_startup_files_quote_literals_and_remain_inactive(self):
        run = self.root / 'startup % special'
        run.mkdir()
        destination = self.home / 'release $USER % quoted'
        with patch.object(installer.subprocess, 'run') as command:
            files = installer.startup_files(destination, run, fabric_research=True)
        command.assert_not_called()
        self.assertEqual(set(files), {'skirtfabric.service', 'start-skirtfabric-kiosk.sh', 'skirtfabric.desktop'})
        unit = (run / 'skirtfabric.service').read_text()
        self.assertIn('$$USER', unit)
        self.assertIn('%%', unit)
        self.assertNotIn('After=default.target', unit)
        self.assertIn('WantedBy=default.target', unit)
        self.assertIn('NoNewPrivileges=true', unit)
        self.assertIn('RestartSec=5', unit)
        self.assertIn('--fabric-research', unit)
        self.assertNotIn('User=root', unit)
        kiosk = (run / 'start-skirtfabric-kiosk.sh').read_text()
        self.assertIn('http://127.0.0.1:8766/', kiosk)
        self.assertIn('WAYLAND_DISPLAY', kiosk)
        for bypass in ('--no-sandbox', '--disable-web-security', '--use-fake-ui-for-media-stream',
                       '--use-fake-device-for-media-stream', 'systemctl enable', 'sudo '):
            self.assertNotIn(bypass, unit + kiosk)
        desktop = (run / 'skirtfabric.desktop').read_text()
        self.assertIn('Exec="', desktop)
        self.assertIn('%%', desktop)
        self.assertIn('Terminal=false', desktop)


if __name__ == '__main__':
    unittest.main()
