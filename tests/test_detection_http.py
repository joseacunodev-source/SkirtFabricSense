import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tools.check_detection_http import (
    check_prediction, validate_comparison, verify_identities,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    models = {'presence':'a'*64,'masks':{'v1':'b'*64,'v2':'c'*64},'pleating':'d'*64}
    region = {'status':'provisional','roi':[10,20,30,40],'model_sha256':models['masks']['v2']}
    case = {'sample_id':'example-1','presence_target':1,
            'presence':{'accepted':True,'score':.8,'threshold':.5,'model_sha256':models['presence']},
            'paths':{name:{'accepted':True,'pleating_prediction':'pleated'}
                     for name in ('v1','v2','v1_plus_presence','v2_plus_presence')}}
    case['paths']['v2']['localization'] = region
    comparison = {'status':'completed','primary_candidate':'v2_plus_presence','baseline':'v1',
                  'fixed_presence_threshold':.5,'fixed_mask_threshold':.5,'models':models,'results':[case]}
    result = {'style':{'status':'provisional','label':'pleated'},
              'fabric':{'status':'disabled'},'length':{'status':'unavailable'},
              'metadata':{'presence':copy.deepcopy(case['presence']),
                          'localization':copy.deepcopy(region),'pleating_model_sha256':models['pleating']}}
    return comparison, case, result


class DetectionHttpTests(unittest.TestCase):
    def test_completed_fixture_and_output(self):
        comparison,case,result = fixture()
        self.assertIs(validate_comparison(comparison),comparison)
        self.assertTrue(check_prediction(result,case,comparison['models']))

    def test_all_three_model_identities_required(self):
        comparison,_,_ = fixture()
        presence = {'status':'completed','export':{'sha256':'a'*64}}
        localizer = {'status':'completed','export':{'sha256':'c'*64}}
        verify_identities(comparison,presence,localizer,'d'*64)
        for target in ('presence','localizer','pleating'):
            p,l,model = copy.deepcopy(presence),copy.deepcopy(localizer),'d'*64
            if target=='presence':p['export']['sha256']='e'*64
            elif target=='localizer':l['export']['sha256']='e'*64
            else:model='e'*64
            with self.assertRaisesRegex(ValueError,'identity mismatch'):
                verify_identities(comparison,p,l,model)

    def test_comparison_missing_identity_and_incomplete_paths_rejected(self):
        for mutate in (
            lambda c:c['models'].pop('pleating'),
            lambda c:c['results'][0]['paths'].pop('v2_plus_presence'),
            lambda c:c.update(status='started'),
            lambda c:c['results'][0]['presence'].update(score=float('nan')),
            lambda c:c['results'][0]['paths']['v2']['localization'].update(model_sha256='f'*64),
        ):
            comparison,_,_ = fixture()
            mutate(comparison)
            with self.assertRaises(ValueError):validate_comparison(comparison)

    def test_http_model_roi_decision_and_score_mismatches_rejected(self):
        for mutate in (
            lambda r:r['metadata']['presence'].update(model_sha256='f'*64),
            lambda r:r['metadata']['localization'].update(model_sha256='f'*64),
            lambda r:r['metadata'].update(pleating_model_sha256='f'*64),
            lambda r:r['metadata']['localization'].update(roi=[11,20,30,40]),
            lambda r:r['metadata']['presence'].update(score=float('nan')),
            lambda r:r['metadata']['presence'].update(score=.6),
            lambda r:r['style'].update(label='non_pleated'),
            lambda r:r['style'].update(status='unavailable'),
            lambda r:r['fabric'].update(status='provisional'),
        ):
            comparison,case,result = fixture()
            mutate(result)
            with self.assertRaises(ValueError):check_prediction(result,case,comparison['models'])

    def test_gated_negative_does_not_require_localization(self):
        comparison,case,result = fixture()
        case['presence'].update(accepted=False,score=.1)
        case['paths']['v2_plus_presence'].update(accepted=False,pleating_prediction=None)
        result['style'].update(status='unavailable',label=None)
        result['metadata']={'presence':copy.deepcopy(case['presence'])}
        self.assertFalse(check_prediction(result,case,comparison['models']))

    def test_checks_survive_python_optimized_mode(self):
        comparison,case,result = fixture()
        result['metadata']['localization']['roi']=[0,0,1,1]
        payload = json.dumps([result,case,comparison['models']])
        program = (
            'import json,sys; from tools.check_detection_http import check_prediction\n'
            'result,case,models=json.loads(sys.stdin.read())\n'
            'try: check_prediction(result,case,models)\n'
            'except ValueError: sys.exit(0)\n'
            'sys.exit(7)\n'
        )
        completed = subprocess.run([sys.executable,'-O','-c',program],input=payload,
                                   text=True,cwd=ROOT,capture_output=True,timeout=15)
        self.assertEqual(completed.returncode,0,completed.stderr)


if __name__=='__main__':unittest.main()
