import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
from PIL import Image
from app.pose import PREPROCESSING, PoseCandidates, prepare, decode
from app.localization import AutomaticPredictor


class PoseTests(unittest.TestCase):
    def test_aspect_fit_and_inverse_coordinates(self):
        tensor, mapping = prepare(Image.new('RGB', (400, 200), 'red'))
        self.assertEqual(tensor.shape, (1, 192, 192, 3))
        self.assertEqual(tensor.dtype, np.uint8)
        self.assertEqual(mapping['pad_left_top'], [0, 48])
        self.assertEqual(int(tensor[0, 0].max()), 0)
        output = np.full((1, 1, 17, 3), .5, dtype=np.float32)
        points = decode(output, mapping)
        self.assertAlmostEqual(points[0]['x'], 200)
        self.assertAlmostEqual(points[0]['y'], 100)
        self.assertFalse(any(p['observed'] for p in points))

    def test_model_zero_coordinate_is_inside_square_source(self):
        _, mapping = prepare(Image.new("RGB", (192, 192)))
        point = decode(np.zeros((1, 1, 17, 3), dtype=np.float32), mapping)[0]
        self.assertEqual((point["x"], point["y"]), (0, 0))
        self.assertTrue(point["inside_source"])

    def test_padding_candidates_not_observed_or_clamped(self):
        _, mapping = prepare(Image.new('RGB', (400, 200)))
        output = np.zeros((1, 1, 17, 3), dtype=np.float32)
        self.assertFalse(decode(output, mapping)[0]['inside_source'])
        self.assertLess(decode(output, mapping)[0]['y'], 0)

    def test_invalid_model_outputs(self):
        _, mapping = prepare(Image.new('RGB', (400, 200)))
        for value in (np.zeros((17, 3)), np.full((1, 1, 17, 3), np.nan),
                      np.full((1, 1, 17, 3), 1.1)):
            with self.assertRaises(ValueError):
                decode(value, mapping)

    def test_pose_failure_and_secondary_mode_do_not_enable_length(self):
        class Pose:
            def detect(self, *args):
                raise RuntimeError('synthetic failure')
        predictor = AutomaticPredictor(None, pose=Pose())
        result = predictor.predict(Image.new('RGB', (100, 100)),
                                   {'presentation': 'worn', 'fabric_enabled': False, 'source_frame_id': 'frame'})
        self.assertEqual(result['metadata']['wearer_pose']['reason'], 'pose_provider_failed')
        self.assertEqual(result['length']['status'], 'unavailable')
        result = predictor.predict(Image.new('RGB', (100, 100)),
                                   {'presentation': 'held', 'fabric_enabled': False})
        self.assertNotIn('wearer_pose', result['metadata'])


class PoseLoaderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.model_bytes = b'synthetic model: interpreter is mocked, not a real export'
        (self.root / 'model.tflite').write_bytes(self.model_bytes)
        self.contract = {
            'model_id': 'movenet-lightning-f16-v4',
            'preprocessing': PREPROCESSING,
            'sha256': hashlib.sha256(self.model_bytes).hexdigest(),
        }
        self.write_contract()

    def write_contract(self):
        (self.root / 'contract.json').write_text(json.dumps(self.contract), encoding='utf-8')

    def fake_runtime(self, inputs=None, outputs=None):
        interpreter = MagicMock()
        interpreter.get_input_details.return_value = inputs if inputs is not None else [
            {'shape': np.array([1, 192, 192, 3]), 'dtype': np.uint8, 'index': 7}]
        interpreter.get_output_details.return_value = outputs if outputs is not None else [
            {'shape': np.array([1, 1, 17, 3]), 'dtype': np.float32, 'index': 11}]
        interpreter.get_tensor.return_value = np.full((1, 1, 17, 3), .5, dtype=np.float32)
        factory = MagicMock(return_value=interpreter)
        return factory, interpreter

    def test_changed_model_bytes_rejected_before_runtime_load(self):
        (self.root / 'model.tflite').write_bytes(self.model_bytes + b'tampered')
        with patch('app.pose._load_runtime') as load:
            with self.assertRaisesRegex(ValueError, 'model contract mismatch'):
                PoseCandidates(self.root)
        load.assert_not_called()

    def test_mismatched_contract_fields_rejected_before_runtime_load(self):
        for field, value in [('sha256', '0' * 64), ('preprocessing', 'RGB stretched192'),
                             ('model_id', 'different-pose-model')]:
            with self.subTest(field=field):
                original = self.contract[field]
                self.contract[field] = value
                self.write_contract()
                with patch('app.pose._load_runtime') as load:
                    with self.assertRaisesRegex(ValueError, 'model contract mismatch'):
                        PoseCandidates(self.root)
                load.assert_not_called()
                self.contract[field] = original

    def test_wrong_tensor_counts_rejected_without_indexing_empty_lists(self):
        input_detail = {'shape': [1, 192, 192, 3], 'dtype': np.uint8, 'index': 7}
        output_detail = {'shape': [1, 1, 17, 3], 'dtype': np.float32, 'index': 11}
        for inputs, outputs in [([], [output_detail]), ([input_detail], []),
                                ([input_detail] * 2, [output_detail]),
                                ([input_detail], [output_detail] * 2)]:
            with self.subTest(input_count=len(inputs), output_count=len(outputs)):
                factory, interpreter = self.fake_runtime(inputs, outputs)
                with patch('app.pose._load_runtime', return_value=(factory, 'mock')):
                    with self.assertRaisesRegex(ValueError, 'tensor contract mismatch'):
                        PoseCandidates(self.root)
                interpreter.invoke.assert_not_called()

    def test_wrong_tensor_shapes_and_dtypes_rejected(self):
        cases = [
            ('input', 'shape', [1, 256, 256, 3]),
            ('input', 'shape', [192, 192, 3]),
            ('input', 'dtype', np.float32),
            ('output', 'shape', [1, 17, 3]),
            ('output', 'shape', [1, 1, 18, 3]),
            ('output', 'dtype', np.float16),
        ]
        for tensor, key, value in cases:
            with self.subTest(tensor=tensor, field=key, value=value):
                inputs = [{'shape': [1, 192, 192, 3], 'dtype': np.uint8, 'index': 7}]
                outputs = [{'shape': [1, 1, 17, 3], 'dtype': np.float32, 'index': 11}]
                (inputs if tensor == 'input' else outputs)[0][key] = value
                factory, interpreter = self.fake_runtime(inputs, outputs)
                with patch('app.pose._load_runtime', return_value=(factory, 'mock')):
                    with self.assertRaisesRegex(ValueError, 'tensor contract mismatch'):
                        PoseCandidates(self.root)
                interpreter.invoke.assert_not_called()

    def test_invalid_frame_identity_rejected_before_inference(self):
        factory, interpreter = self.fake_runtime()
        with patch('app.pose._load_runtime', return_value=(factory, 'mock')):
            model = PoseCandidates(self.root)
        for frame_id in (None, '', '  ', 1, False, ['frame']):
            with self.subTest(frame_id=frame_id):
                with self.assertRaisesRegex(ValueError, 'Source frame identity required'):
                    model.detect(Image.new('RGB', (300, 200)), frame_id)
        interpreter.set_tensor.assert_not_called()
        interpreter.invoke.assert_not_called()

    def test_valid_detection_preserves_identity_mapping_and_unverified_status(self):
        factory, interpreter = self.fake_runtime()
        with patch('app.pose._load_runtime', return_value=(factory, 'mock')):
            model = PoseCandidates(self.root)
        result = model.detect(Image.new('RGB', (400, 200)), 'source-frame-123')
        self.assertEqual(result['frame_id'], 'source-frame-123')
        self.assertEqual(result['model_sha256'], self.contract['sha256'])
        self.assertEqual(result['preprocessing']['source_size'], [400, 200])
        self.assertEqual(result['preprocessing']['pad_left_top'], [0, 48])
        self.assertEqual(result['status'], 'provisional_landmark_candidates')
        self.assertFalse(result['geometry_eligible'])
        self.assertEqual(len(result['landmarks']), 17)
        self.assertFalse(any(point['observed'] for point in result['landmarks']))
        index, values = interpreter.set_tensor.call_args.args
        self.assertEqual(index, 7)
        self.assertEqual(values.shape, (1, 192, 192, 3))
        self.assertEqual(values.dtype, np.uint8)
        interpreter.invoke.assert_called_once_with()
        interpreter.get_tensor.assert_called_once_with(11)


if __name__ == '__main__':
    unittest.main()
