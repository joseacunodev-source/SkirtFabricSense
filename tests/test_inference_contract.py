import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image
from app.inference import SkirtPredictor, prepare_image, PREPROCESSING


class FakeInterpreter:
    input_shape = [1, 224, 224, 3]
    scores = [[.3, .7]]

    def __init__(self, **kwargs):
        self.invocations = 0

    def allocate_tensors(self):
        pass

    def get_input_details(self):
        return [dict(shape=self.input_shape, dtype=np.float32, index=0)]

    def get_output_details(self):
        return [dict(shape=[1, 2], dtype=np.float32, index=1)]

    def set_tensor(self, index, values):
        self.values = values

    def invoke(self):
        self.invocations += 1

    def get_tensor(self, index):
        return np.array(self.scores, dtype=np.float32)


class InferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.contract = dict(input=dict(shape=[1, 224, 224, 3], dtype='float32', color='RGB', range=[0, 255]),
                             output=dict(shape=[1, 2], dtype='float32', labels=['non_pleated', 'pleated'],
                                         semantics='uncalibrated softmax scores'),
                             preprocessing=PREPROCESSING, normalization='Inside model only')
        (self.root/'model.tflite').write_bytes(b'fake interpreter test fixture, not a real model')
        self.write_bundle()
        self.patcher = patch('app.inference._load_runtime', return_value=(FakeInterpreter, 'test-double'))
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def write_bundle(self):
        (self.root/'contract.json').write_text(json.dumps(self.contract))
        self.manifest = dict(schema_version=1, bundle_id='test-bundle', model='model.tflite',
                             contract='contract.json', files=[dict(path=name,
                             sha256=hashlib.sha256((self.root/name).read_bytes()).hexdigest())
                             for name in ['model.tflite', 'contract.json']])
        (self.root/'manifest.json').write_text(json.dumps(self.manifest))

    def test_unconfirmed_never_invokes(self):
        predictor = SkirtPredictor(self.root)
        for confirmed in [False, 'true', 1]:
            result = predictor.predict(Image.new('RGB', (100, 200)), full_skirt_confirmed=confirmed)
            self.assertEqual(result['style']['status'], 'unavailable')
        self.assertEqual(predictor.interpreter.invocations, 0)

    def test_confirmed_provisional_rgb_and_no_external_normalization(self):
        predictor = SkirtPredictor(self.root)
        result = predictor.predict(Image.new('RGB', (224, 224), (255, 0, 0)), full_skirt_confirmed=True)
        self.assertEqual(result['style']['label'], 'pleated')
        self.assertEqual(result['style']['status'], 'provisional')
        self.assertEqual(result['fabric']['status'], 'unavailable')
        self.assertEqual(result['length']['status'], 'unavailable')
        np.testing.assert_array_equal(predictor.interpreter.values[0, 0, 0], [255, 0, 0])
        self.assertEqual(predictor.interpreter.values.dtype, np.float32)
        json.dumps(result, allow_nan=False)

    def test_roi_padding_and_source_coordinates(self):
        image, box = prepare_image(Image.new('RGB', (200, 400), (255, 0, 0)), (50, 100, 150, 300))
        self.assertEqual(box, (45, 90, 155, 310))
        self.assertEqual(image.size, (224, 224))
        self.assertEqual(image.getpixel((0, 0)), (128, 128, 128))
        self.assertEqual(image.getpixel((112, 112)), (255, 0, 0))

    def test_roi_clips_to_source_before_expansion(self):
        _, box = prepare_image(Image.new('RGB', (100, 100)), (-20, -30, 50, 50))
        self.assertEqual(box, (0, 0, 53, 53))

    def test_invalid_roi_rejected(self):
        for roi in [(30, 30, 20, 20), (100, 0, 120, 10), (0, 0, float('nan'), 10), (True, 0, 2, 3)]:
            with self.subTest(roi=roi), self.assertRaises(ValueError):
                prepare_image(Image.new('RGB', (100, 100)), roi)

    def test_corrupt_model_rejected_before_runtime(self):
        (self.root/'model.tflite').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            SkirtPredictor(self.root)

    def test_contract_label_swap_rejected(self):
        self.contract['output']['labels'].reverse()
        self.write_bundle()
        with self.assertRaisesRegex(ValueError, 'output contract'):
            SkirtPredictor(self.root)

    def test_external_normalization_contract_rejected(self):
        self.contract['normalization'] = 'outside'
        self.write_bundle()
        with self.assertRaises(ValueError):
            SkirtPredictor(self.root)

    def test_actual_tensor_shape_rejected(self):
        with patch.object(FakeInterpreter, 'input_shape', [1, 128, 128, 3]):
            with self.assertRaisesRegex(ValueError, 'tensor differs'):
                SkirtPredictor(self.root)

    def test_unsafe_path_rejected(self):
        self.manifest['files'][0]['path'] = '../outside'
        (self.root/'manifest.json').write_text(json.dumps(self.manifest))
        with self.assertRaises(ValueError):
            SkirtPredictor(self.root)

    def test_required_hash_and_duplicate_rejected(self):
        for entries in [self.manifest['files'][1:], self.manifest['files'] * 2]:
            manifest = copy.deepcopy(self.manifest)
            manifest['files'] = entries
            (self.root/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                SkirtPredictor(self.root)

    def test_nonfinite_scores_rejected(self):
        for scores in [[[float('nan'), .2]], [[.8, .8]], [[-.1, 1.1]]]:
            with patch.object(FakeInterpreter, 'scores', scores):
                predictor = SkirtPredictor(self.root)
                with self.assertRaises(ValueError):
                    predictor.predict(Image.new('RGB', (20, 20)), full_skirt_confirmed=True)


if __name__ == '__main__':
    unittest.main()
