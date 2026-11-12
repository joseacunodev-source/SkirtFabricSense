"""Synthetic offline editor/intake checks; no production observations."""
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from tools.geometry_annotation import build_editor, load_source, validate_draft


class GeometryAnnotationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.photo = self.root/'source.jpg'
        Image.new('RGB',(120,240),(220,225,230)).save(self.photo)
        self.row = dict(sample_id='synthetic-sample',garment_group_id='synthetic-group',
                        split='development_validation',original_path='source.jpg',
                        image_sha256=hashlib.sha256(self.photo.read_bytes()).hexdigest())
        self.inventory = self.root/'inventory.json'
        self.write_inventory([self.row])

    def tearDown(self):
        self.temp.cleanup()

    def write_inventory(self, rows):
        self.inventory.write_text(json.dumps(rows),encoding='utf-8')

    def draft(self):
        binding,image=load_source(self.inventory,self.row['sample_id'],self.root)
        image.close()
        return dict(schema_version=1,data_kind='pending_source_geometry_observation',
                    review_status='pending_independent_reconciliation',reviewed=False,evaluator_approved=False,
                    binding=binding,reviewer={'display_name':'Synthetic test agent','actor_kind':'agent'},
                    review_date=date.today().isoformat(),original_viewed=True,
                    observations={'waist_y':{'visibility':'visible','interval':[25,30]},
                                  'hem_y':{'visibility':'visible','interval':[130,135]},
                                  'floor_y':{'visibility':'uncertain','interval':None}},
                    notes='Synthetic test observations only; no real person.')

    def test_pending_unknown_reference_remains_valid_without_approval(self):
        result=validate_draft(self.draft(),self.inventory,self.root)
        self.assertEqual(result['status'],'valid_pending_draft')
        self.assertFalse(result['evaluator_approved'])

    def test_build_full_original_and_refuse_overwrite(self):
        output=self.root/'editor.html'
        build_editor(self.inventory,self.row['sample_id'],self.root,output)
        html=output.read_text(encoding='utf-8')
        self.assertIn('data:image/png;base64,',html)
        self.assertIn(self.row['image_sha256'],html)
        self.assertNotIn('/*GEOMETRY_DOCUMENT*/null',html)
        before=output.read_bytes()
        with self.assertRaises(FileExistsError):
            build_editor(self.inventory,self.row['sample_id'],self.root,output)
        self.assertEqual(before,output.read_bytes())

    def test_original_hash_changed(self):
        draft=self.draft()
        self.photo.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'SHA256'):
            validate_draft(draft,self.inventory,self.root)

    def test_inventory_hash_changes_even_without_membership_change(self):
        draft=self.draft()
        self.inventory.write_text(json.dumps([self.row],indent=2),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'binding differs'):
            validate_draft(draft,self.inventory,self.root)

    def test_protected_and_training_sources_excluded(self):
        for split in ['development_train','test','external_holdout_sanity']:
            self.write_inventory([dict(self.row,split=split)])
            with self.assertRaisesRegex(ValueError,'development_validation'):
                load_source(self.inventory,self.row['sample_id'],self.root)

    def test_cross_split_group_or_hash_fails_before_image_open(self):
        for change in [dict(sample_id='second',split='development_train'),
                       dict(sample_id='second',garment_group_id='other',split='development_train')]:
            self.write_inventory([self.row,dict(self.row,**change)])
            with self.assertRaises(ValueError):
                load_source(self.inventory,self.row['sample_id'],self.root)

    def test_path_traversal_rejected(self):
        self.write_inventory([dict(self.row,original_path='../source.jpg')])
        with self.assertRaises(ValueError):
            load_source(self.inventory,self.row['sample_id'],self.root)

    def test_exif_dimensions_are_source_coordinate_dimensions(self):
        exif=Image.Exif();exif[274]=6
        Image.new('RGB',(100,60)).save(self.photo,exif=exif)
        self.row['image_sha256']=hashlib.sha256(self.photo.read_bytes()).hexdigest()
        self.write_inventory([self.row])
        binding,image=load_source(self.inventory,self.row['sample_id'],self.root)
        self.assertEqual(binding['frame_size'],[60,100]);image.close()

    def test_visible_interval_bounds_order_and_finiteness(self):
        for interval in [[-1,5],[0,240],[50,40],[0,float('nan')],[True,5],['1',5],[]]:
            draft=self.draft();draft['observations']['hem_y']['interval']=interval
            with self.subTest(interval=interval),self.assertRaises(ValueError):
                validate_draft(draft,self.inventory,self.root)

    def test_hidden_or_unknown_does_not_accept_inferred_interval(self):
        for visibility in ['hidden','uncertain']:
            draft=self.draft();draft['observations']['hem_y']['visibility']=visibility
            with self.assertRaisesRegex(ValueError,'invented'):
                validate_draft(draft,self.inventory,self.root)

    def test_cannot_declare_approval_or_extra_camera_identity(self):
        for field,value in [('reviewed',True),('evaluator_approved',True),
                            ('review_status','approved'),('camera_config_id','guessed')]:
            draft=self.draft();draft[field]=value
            with self.assertRaises(ValueError):validate_draft(draft,self.inventory,self.root)

    def test_required_review_evidence_and_attestation(self):
        for field,value in [('notes',' '),('original_viewed',False),('review_date','2026-99-99')]:
            draft=self.draft();draft[field]=value
            with self.assertRaises(ValueError):validate_draft(draft,self.inventory,self.root)
        draft=self.draft();draft['reviewer']['actor_kind']='expert_verified'
        with self.assertRaises(ValueError):validate_draft(draft,self.inventory,self.root)

    def test_unexpected_identity_or_coordinates_rejected(self):
        for field,value in [('frame_size',[240,120]),('coordinate_convention','resized_pixels'),
                            ('garment_group_id','renamed')]:
            draft=self.draft();draft['binding'][field]=value
            with self.assertRaises(ValueError):validate_draft(draft,self.inventory,self.root)

    def test_html_metadata_cannot_close_script(self):
        self.row['sample_id']='</script><script>alert(1)</script>'
        self.write_inventory([self.row]);output=self.root/'editor.html'
        build_editor(self.inventory,self.row['sample_id'],self.root,output)
        self.assertNotIn(self.row['sample_id'],output.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
