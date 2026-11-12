"""Synthetic model-contract and optional-gate tests, not accuracy evidence."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image
from app.presence import PresenceGate
from app.localization import AutomaticPredictor
from tests.test_geometry import fixture


class PresenceTests(unittest.TestCase):
    def runtime(self):
        runtime=Mock()
        runtime.get_input_details.return_value=[dict(shape=[1,224,224,3],dtype=np.float32,index=0)]
        runtime.get_output_details.return_value=[dict(shape=[1,1],dtype=np.float32,index=1)]
        runtime.get_tensor.return_value=np.array([[.5]],dtype=np.float32)
        return runtime

    def record(self,root):
        (root/'model.tflite').write_bytes(b'synthetic')
        record=dict(status='completed',export=dict(sha256=hashlib.sha256(b'synthetic').hexdigest()),
                    preprocessing='Full RGB resize224 Pillow bilinear; float32 0..255; normalization inside model',threshold=.5)
        (root/'run.json').write_text(json.dumps(record))
        return record

    def test_scores_preprocessing_and_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); record=self.record(root); runtime=self.runtime()
            with patch('app.presence._load_runtime',return_value=(Mock(return_value=runtime),'fake')):
                gate=PresenceGate(root)
                for score,accepted in [(0,False),(.49,False),(.5,True),(1,True)]:
                    runtime.get_tensor.return_value=np.array([[score]],dtype=np.float32)
                    result=gate.check(Image.new('L',(640,480),200))
                    self.assertEqual(result['accepted'],accepted)
                    self.assertEqual(result['model_sha256'],record['export']['sha256'])
                tensor=runtime.set_tensor.call_args.args[1]
                self.assertEqual(tensor.shape,(1,224,224,3))
                self.assertEqual(tensor.dtype,np.float32)
                self.assertTrue((tensor==200).all())
                for bad in [float('nan'),float('inf'),-.1,1.1]:
                    runtime.get_tensor.return_value=np.array([[bad]],dtype=np.float32)
                    with self.assertRaises(ValueError):gate.check(Image.new('RGB',(10,10)))

    def test_artifact_and_preprocessing_contract_before_runtime_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for key,value in [('status','started'),('threshold',.7),('preprocessing','other'),
                              ('export',{'sha256':'changed'})]:
                record=self.record(root);record[key]=value
                (root/'run.json').write_text(json.dumps(record))
                with patch('app.presence._load_runtime') as loader:
                    with self.assertRaises(ValueError):PresenceGate(root)
                    loader.assert_not_called()

    def test_tensor_count_shape_dtype(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.record(root)
            for side,value in [('input',[]),('output',[]),
                ('input',[dict(shape=[1,224,224,3],dtype=np.uint8,index=0)]),
                ('output',[dict(shape=[1,2],dtype=np.float32,index=1)])]:
                runtime=self.runtime();getattr(runtime,'get_'+side+'_details').return_value=value
                with patch('app.presence._load_runtime',return_value=(Mock(return_value=runtime),'fake')):
                    with self.assertRaises(ValueError):PresenceGate(root)


class OptionalIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.image=Image.new('RGB',(640,480))
        self.localizer=Mock();self.localizer.locate.return_value=dict(status='provisional',roi=[10,20,300,400])
        self.pleating=Mock();self.pleating.predict.return_value=dict(style=dict(status='provisional',label='pleated'),
            metadata=dict(model_sha256='synthetic',roi_xyxy=[10,20,300,400]))
        self.options=dict(presentation='worn',fabric_enabled=False,source_frame_id='frame-1',camera_config_id='test-camera')

    def test_presence_rejection_short_circuits_downstream(self):
        presence=Mock();presence.check.return_value=dict(accepted=False,score=.1)
        provider=Mock()
        result=AutomaticPredictor(self.pleating,self.localizer,presence,provider,fixture()['profile']).predict(self.image,self.options)
        self.assertEqual(result['style']['status'],'unavailable')
        self.assertEqual(result['length']['status'],'unavailable')
        self.localizer.locate.assert_not_called();self.pleating.predict.assert_not_called();provider.assert_not_called()

    def test_valid_same_frame_evidence_and_default_gate_disabled(self):
        provider=Mock(return_value=fixture()['evidence'])
        wrapper=AutomaticPredictor(self.pleating,self.localizer,geometry_provider=provider,calibration_profile=fixture()['profile'])
        self.assertIsNone(wrapper.presence)
        result=wrapper.predict(self.image,self.options)
        self.assertEqual(result['length']['label'],'below_knee')
        self.assertEqual(result['length']['frame_id'],'frame-1')
        provider.assert_called_once_with(self.image,self.localizer.locate.return_value,self.options)

    def test_missing_or_stale_geometry_cannot_invent_length(self):
        for evidence in [None,{**fixture()['evidence'],'frame_id':'old'}]:
            result=AutomaticPredictor(self.pleating,self.localizer,geometry_provider=Mock(return_value=evidence),
                calibration_profile=fixture()['profile']).predict(self.image,self.options)
            self.assertEqual(result['length']['status'],'unavailable')
            self.assertEqual(result['style']['label'],'pleated')

    def test_geometry_failure_preserves_independent_pleating(self):
        result=AutomaticPredictor(self.pleating,self.localizer,geometry_provider=Mock(side_effect=RuntimeError('extractor')),
            calibration_profile=fixture()['profile']).predict(self.image,self.options)
        self.assertEqual(result['length']['reason'],'geometry_provider_failed')
        self.assertEqual(result['style']['label'],'pleated')
