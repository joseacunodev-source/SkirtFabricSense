import json
from pathlib import Path
import tempfile
import unittest

from tools.build_release import build as build_app, MODEL, CONTRACT, RECORD
from tools.station_package import build, digest, launch_command, verify_station
from tools.verify_release import APP_REQUIRED


class StationPackageTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        actual = Path(__file__).resolve().parents[1]
        for relative, content in ((MODEL,b'fixture, not a valid runtime model'),
                                  (CONTRACT,(actual/CONTRACT).read_bytes())):
            target = self.root/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(content)
        record = self.root/RECORD
        record.parent.mkdir(parents=True)
        record.write_text(json.dumps({'release_id':'skirt-finetune-v1',
            'model_files_and_sha256':[{'path':MODEL,'sha256':digest(self.root/MODEL)}],
            'contract':{'path':CONTRACT,'sha256':digest(self.root/CONTRACT)}}),encoding='utf-8')
        for name in APP_REQUIRED:
            path = self.root/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text('fixture',encoding='utf-8')
        build_app(self.root,self.root/'artifacts/releases/skirt-finetune-v1-desktop-research-v7',True)
        for name in ('skirt-localizer-v2','skirt-presence-v4','fabric-smoke-v1'):
            path = self.root/'artifacts/models'/name
            path.mkdir(parents=True)
            (path/'model.tflite').write_bytes(b'model fixture')
            (path/'run.json').write_text(json.dumps({'status':'completed',
                'export':{'sha256':digest(path/'model.tflite')}}),encoding='utf-8')
        self.presence = self.root/'artifacts/models/skirt-presence-v4'
        self.output = self.root/'station'

    def create(self):
        return build(self.root,self.output,self.presence)

    def rehash_config(self):
        inventory = json.loads((self.output/'station-inventory.json').read_text())
        entry = next(x for x in inventory['files'] if x['path']=='station.json')
        entry.update(sha256=digest(self.output/'station.json'),bytes=(self.output/'station.json').stat().st_size)
        (self.output/'station-inventory.json').write_text(json.dumps(inventory),encoding='utf-8')

    def test_relocated_package_has_internal_launch_paths_and_fabric_opt_in(self):
        result = self.create()
        self.assertFalse(result['pi_verified'])
        relocated = self.root/'relocated station'
        self.assertTrue(self.output.resolve().is_relative_to(self.root.resolve()))
        self.assertTrue(relocated.resolve().is_relative_to(self.root.resolve()))
        self.output.rename(relocated)
        default = launch_command(relocated)
        self.assertNotIn('--experimental-fabric',default)
        self.assertNotIn(str(self.output),str(default))
        self.assertIn(str(relocated/'models/presence'),default)
        self.assertIn('--no-review',default)
        self.assertEqual(default[default.index('--root')+1],str(relocated/'application'))
        self.assertIn('--experimental-fabric',launch_command(relocated,fabric_research=True))

    def test_tampered_model_refused_before_launch(self):
        self.create()
        (self.output/'models/presence/model.tflite').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'changed'):
            launch_command(self.output)

    def test_uninventoried_file_or_empty_directory_rejected(self):
        self.create()
        extra = self.output/'unlisted.txt'
        extra.write_text('unexpected')
        with self.assertRaisesRegex(ValueError,'membership'):
            verify_station(self.output)
        extra.unlink()
        (self.output/'unlisted').mkdir()
        with self.assertRaisesRegex(ValueError,'directories'):
            verify_station(self.output)

    def test_config_traversal_rejected_even_after_inventory_rehash(self):
        self.create()
        config = json.loads((self.output/'station.json').read_text())
        config['models']['presence']['directory'] = '../outside'
        (self.output/'station.json').write_text(json.dumps(config),encoding='utf-8')
        self.rehash_config()
        with self.assertRaisesRegex(ValueError,'directory'):
            verify_station(self.output)

    def test_pi_or_length_claim_rejected(self):
        self.create()
        config = json.loads((self.output/'station.json').read_text())
        config['pi_verified'] = True
        (self.output/'station.json').write_text(json.dumps(config),encoding='utf-8')
        self.rehash_config()
        with self.assertRaisesRegex(ValueError,'metadata'):
            verify_station(self.output)

    def test_bad_source_fails_before_output_and_existing_output_is_preserved(self):
        model = self.presence/'model.tflite'
        old = model.read_bytes()
        model.write_bytes(b'corrupted')
        with self.assertRaisesRegex(ValueError,'hash'):
            self.create()
        self.assertFalse(self.output.exists())
        model.write_bytes(old)
        self.create()
        with self.assertRaisesRegex(ValueError,'overwrite'):
            self.create()

    def test_invalid_ports_rejected(self):
        for port in (False,0,65536,'8766'):
            with self.assertRaisesRegex(ValueError,'Port'):
                launch_command(self.output,port)

    def test_output_inside_immutable_inputs_is_refused(self):
        bundle = self.root/'artifacts/releases/skirt-finetune-v1-desktop-research-v7'
        before = digest(bundle/'inventory.json')
        for source in (bundle,self.presence,self.root/'artifacts/models/skirt-localizer-v2'):
            output = source/'nested station'
            with self.assertRaisesRegex(ValueError,'immutable input'):
                build(self.root,output,self.presence)
            self.assertFalse(output.exists())
        self.assertEqual(before,digest(bundle/'inventory.json'))

    def test_explicit_application_copies_new_ui_and_preserves_prior_bundle(self):
        old = self.root/'artifacts/releases/skirt-finetune-v1-desktop-research-v7'
        old_hash = digest(old/'inventory.json')
        ui = self.root/'app/static/index.html'
        ui.write_text('new camera startup fixture',encoding='utf-8')
        new = self.root/'artifacts/releases/new-app'
        build_app(self.root,new,True)
        result = build(self.root,self.output,self.presence,new.relative_to(self.root))
        self.assertEqual(result['status'],'passed')
        self.assertEqual((self.output/'application/app/static/index.html').read_bytes(),ui.read_bytes())
        self.assertEqual(old_hash,digest(old/'inventory.json'))
        with self.assertRaisesRegex(ValueError,'immutable input'):
            build(self.root,new/'nested station',self.presence,new)

    def test_explicit_application_is_verified_before_output(self):
        new = self.root/'artifacts/releases/no-app'
        build_app(self.root,new,False)
        with self.assertRaises(ValueError):
            build(self.root,self.output,self.presence,new)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
