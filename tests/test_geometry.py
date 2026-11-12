import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from app.geometry import estimate_hemline, validate_profile
from app.hemline import LABELS


def fixture():
    # Synthetic numbers exercise mechanics only, never production calibration.
    profile = dict(schema_version=1, profile_id='synthetic', reference_id='synthetic-body',
        camera_config_id='test-camera', calibration_evidence='synthetic-test-only',
        coordinate='waist_to_floor', labels=list(LABELS), supported_modes=['worn','held','hanging','mannequin'],
        frame_size=[640,480], boundaries=[.1,.2,.3,.4,.5,.6,.7,.8], projection='upright_rectified_vertical')
    evidence = dict(frame_id='frame-1', camera_config_id='test-camera', frame_size=[640,480],
        mode='worn', reference_id='synthetic-body', reference_kind='observed_body_landmarks',
        hem_y=[235,245], waist_y=[100,100], floor_y=[400,400],
        quality={key:True for key in ('full_skirt_visible','single_garment','reference_associated',
        'projection_valid','hem_visible','waist_reference_valid','floor_reference_valid')})
    return dict(frame_id='frame-1', camera_config_id='test-camera', frame_size=[640,480], mode='worn',
                profile=profile, evidence=evidence)


class GeometryTests(unittest.TestCase):
    def test_valid_worn(self):
        result=estimate_hemline(**fixture())
        self.assertEqual(result['label'],'below_knee')
        self.assertEqual(result['status'],'estimate')
        self.assertIsNone(result['score'])
        self.assertEqual(result['frame_id'],'frame-1')

    def test_nonworn_reference(self):
        for mode in ('hanging','held','mannequin'):
            args=fixture(); args['mode']=args['evidence']['mode']=mode
            args['evidence']['reference_kind']='calibrated_standard_body'
            self.assertEqual(estimate_hemline(**args)['status'],'estimate')

    def test_worn_cannot_use_standard_body(self):
        args=fixture(); args['evidence']['reference_kind']='calibrated_standard_body'
        self.assertEqual(estimate_hemline(**args)['reason'],'unsupported_reference_evidence')

    def test_missing_evidence(self):
        for key in ('profile','evidence'):
            args=fixture(); args[key]=None
            self.assertEqual(estimate_hemline(**args)['status'],'unavailable')

    def test_stale_and_mismatched(self):
        for key,value in [('frame_id','old'),('camera_config_id','other'),('frame_size',[320,240]),
                          ('reference_id','other'),('mode','held')]:
            args=fixture(); args['evidence'][key]=value
            self.assertEqual(estimate_hemline(**args)['status'],'unavailable')

    def test_changed_camera(self):
        for key,value in [('camera_config_id','changed'),('frame_size',[1280,720])]:
            args=fixture(); args[key]=value
            self.assertEqual(estimate_hemline(**args)['reason'],'camera_configuration_mismatch')

    def test_each_quality_gate(self):
        for key in fixture()['evidence']['quality']:
            args=fixture(); args['evidence']['quality'][key]=False
            self.assertEqual(estimate_hemline(**args)['reason'],'geometry_quality_not_established')

    def test_uncertainty_propagates(self):
        args=fixture(); args['evidence']['waist_y']=[80,120]; args['evidence']['floor_y']=[380,420]
        self.assertEqual(estimate_hemline(**args)['status'],'uncertain')

    def test_invalid_intervals(self):
        for interval in ([300,200],[-1,200],[200,480],[float('nan'),200],[True,200],None):
            args=fixture(); args['evidence']['hem_y']=interval
            self.assertEqual(estimate_hemline(**args)['reason'],'invalid_pixel_geometry')

    def test_order_and_outside(self):
        args=fixture(); args['evidence']['floor_y']=[90,100]
        self.assertEqual(estimate_hemline(**args)['reason'],'ambiguous_reference_order')
        args=fixture(); args['evidence']['hem_y']=[50,60]
        self.assertEqual(estimate_hemline(**args)['reason'],'hem_outside_calibrated_range')

    def test_malformed_profiles(self):
        for key,value in [('supported_modes',[{}]),('boundaries',[.1]*8),('projection','tilted'),
                          ('frame_size',[True,480]),('calibration_evidence','')]:
            args=fixture(); args['profile'][key]=value
            self.assertTrue(validate_profile(args['profile']))
            self.assertEqual(estimate_hemline(**args)['reason'],'invalid_calibration_profile')

    def test_cli_valid_and_invalid(self):
        script=Path(__file__).resolve().parents[1]/'tools'/'validate_calibration.py'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'synthetic.json'
            for profile,code in [(fixture()['profile'],0),({},1)]:
                path.write_text(json.dumps(profile),encoding='utf-8')
                result=subprocess.run([sys.executable,str(script),str(path)],capture_output=True,text=True)
                self.assertEqual(result.returncode,code,result.stderr)
                self.assertFalse(json.loads(result.stdout)['physical_calibration_verified'])


if __name__=='__main__':unittest.main()
