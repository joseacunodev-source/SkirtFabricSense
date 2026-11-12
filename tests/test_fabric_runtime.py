"""Fabric smoke contract checks with synthetic tensors, not accuracy evidence."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image
from app.fabric import FabricSmokePredictor, LABELS, PREPROCESSING, prepare_fabric_image


class FabricRuntimeTests(unittest.TestCase):
    def fixture(self, root):
        payload = b'synthetic fabric artifact'
        digest = hashlib.sha256(payload).hexdigest()
        (root/'model.tflite').write_bytes(payload)
        record = dict(status='completed', classes=LABELS, input_preprocessing=PREPROCESSING,
                      run_id='20261011-fabric-smoke-v1',
                      export=dict(sha256=digest, live_approved=False, pi_verified=False))
        (root/'run.json').write_text(json.dumps(record))
        runtime = Mock()
        runtime.get_input_details.return_value = [dict(shape=[1,224,224,3], dtype=np.float32, index=0)]
        runtime.get_output_details.return_value = [dict(shape=[1,4], dtype=np.float32, index=1)]
        runtime.get_tensor.return_value = np.array([[.1,.6,.2,.1]], dtype=np.float32)
        return record, runtime, digest

    def test_original_crop_before_resize_no_expansion(self):
        image = Image.new('RGB', (1000,800), 'red')
        image.paste((0,255,0), (400,300,600,500))
        prepared = prepare_fabric_image(image, [400,300,600,500])
        self.assertEqual(prepared.size, (224,224))
        self.assertTrue((np.asarray(prepared) == [0,255,0]).all())
        padded = prepare_fabric_image(Image.new('L',(10,20),200), [0,0,10,20])
        self.assertEqual(padded.getpixel((0,0)), (128,128,128))

    def test_invalid_rois(self):
        image = Image.new('RGB',(100,80))
        for roi in [None,[1,2,3],[-1,0,10,10],[0,0,101,80],[5,5,5,10],
                    [0.,0,10,10],[False,0,10,10],[0,0,float('nan'),10]]:
            with self.subTest(roi=roi), self.assertRaises(ValueError):
                prepare_fabric_image(image,roi)

    def test_artifact_contract_rejected_before_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for key,value in [('status','started'),('classes',list(reversed(LABELS))),
                              ('input_preprocessing','other'),('run_id','other'),
                              ('export',dict(sha256='bad',live_approved=False,pi_verified=False))]:
                record,runtime,digest=self.fixture(root);record[key]=value
                (root/'run.json').write_text(json.dumps(record))
                with patch('app.fabric.MODEL_SHA256',digest), patch('app.fabric._load_runtime') as loader:
                    with self.assertRaises(ValueError):FabricSmokePredictor(root)
                    loader.assert_not_called()
            record,runtime,digest=self.fixture(root)
            (root/'model.tflite').write_bytes(b'changed')
            with patch('app.fabric.MODEL_SHA256',digest), self.assertRaises(ValueError):
                FabricSmokePredictor(root)

    def test_tensor_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for side,value in [('input',[]),('output',[]),
                ('input',[dict(shape=[1,224,224,3],dtype=np.uint8,index=0)]),
                ('output',[dict(shape=[1,2],dtype=np.float32,index=1)]),
                ('output',[dict(shape=[1,4],dtype=np.float32,index=1)]*2)]:
                record,runtime,digest=self.fixture(root)
                getattr(runtime,'get_'+side+'_details').return_value=value
                with patch('app.fabric.MODEL_SHA256',digest), patch('app.fabric._load_runtime',return_value=(Mock(return_value=runtime),'fake')):
                    with self.assertRaises(ValueError):FabricSmokePredictor(root)

    def test_output_validity_and_research_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);record,runtime,digest=self.fixture(root)
            with patch('app.fabric.MODEL_SHA256',digest), patch('app.fabric._load_runtime',return_value=(Mock(return_value=runtime),'fake')):
                predictor=FabricSmokePredictor(root)
            image=Image.new('RGB',(640,480),200)
            result=predictor.predict(image,[10,20,300,400])
            self.assertEqual(result['label'],LABELS[1])
            self.assertEqual(result['status'],'research_only')
            self.assertFalse(result['composition_verified']);self.assertFalse(result['live_approved'])
            self.assertFalse(result['pi_verified'])
            self.assertEqual(result['roi_xyxy'],[10,20,300,400])
            tensor=runtime.set_tensor.call_args.args[1]
            self.assertEqual(tensor.shape,(1,224,224,3));self.assertEqual(tensor.dtype,np.float32)
            for values in [[[float('nan'),0,0,1]],[[float('inf'),0,0,0]],
                           [[-.1,.6,.3,.2]],[[1.1,0,0,0]],[[.1,.1,.1,.1]],[[.5,.5]]]:
                runtime.get_tensor.return_value=np.array(values,dtype=np.float32)
                with self.subTest(values=values),self.assertRaises(ValueError):
                    predictor.predict(image,[10,20,300,400])


if __name__=='__main__':unittest.main()
