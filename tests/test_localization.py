"""Synthetic localization contracts; no camera or learned accuracy claims."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image
from app.localization import AutomaticPredictor, SkirtLocalizer, decode_mask, LOCALIZER_PREPROCESSING
from app.pipeline import ImagePipeline


class MaskTests(unittest.TestCase):
    def mask(self):
        mask = np.zeros((56, 56), dtype=np.float32)
        mask[10:30, 7:21] = .9
        return mask

    def test_source_coordinates_preserve_non_square_frame(self):
        result = decode_mask(self.mask(), 1120, 560)
        self.assertEqual(result['roi'], [140, 100, 420, 300])
        self.assertEqual(result['mask_pixels'], 280)
        self.assertEqual(result['status'], 'provisional')
        self.assertIn('not_verified', result['reason'])

    def test_outward_rounding_covers_small_source(self):
        self.assertEqual(decode_mask(self.mask(), 57, 113)['roi'], [7, 20, 22, 61])

    def test_empty_and_small_components_abstain(self):
        mask = np.zeros((56, 56))
        mask[10:12, 10:14] = 1
        self.assertEqual(decode_mask(mask, 560, 560)['reason'], 'no_supported_skirt_region')

    def test_tiny_noise_does_not_create_second_region(self):
        mask = self.mask()
        mask[40, 40] = 1
        self.assertEqual(decode_mask(mask, 560, 560)['status'], 'provisional')

    def test_multiple_and_diagonally_touching_regions_abstain(self):
        mask = np.zeros((56, 56))
        mask[10:13, 10:13] = 1
        mask[13:16, 13:16] = 1
        self.assertEqual(decode_mask(mask, 560, 560)['reason'], 'multiple_regions')

    def test_each_frame_edge_is_rejected(self):
        for region in [(slice(0, 3), slice(20, 23)), (slice(53, 56), slice(20, 23)),
                       (slice(20, 23), slice(0, 3)), (slice(20, 23), slice(53, 56))]:
            with self.subTest(region=region):
                mask = np.zeros((56, 56))
                mask[region] = 1
                self.assertEqual(decode_mask(mask, 560, 560)['reason'], 'region_touches_frame_edge')

    def test_invalid_values_shape_dimensions_and_settings_rejected(self):
        for value in [np.nan, np.inf, -.1, 1.1]:
            mask = self.mask()
            mask[0, 0] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode_mask(mask, 560, 560)
        for mask, width, height, kwargs in [
                (np.zeros((55, 56)), 560, 560, {}), (self.mask(), 0, 560, {}),
                (self.mask(), True, 560, {}), (self.mask(), 560, 2.5, {}),
                (self.mask(), 560, 560, {'threshold': 1}),
                (self.mask(), 560, 560, {'min_pixels': True})]:
            with self.subTest(width=width, kwargs=kwargs), self.assertRaises(ValueError):
                decode_mask(mask, width, height, **kwargs)


class AutomaticTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new('RGB', (560, 560))
        self.pleating = Mock()
        self.pleating.predict.return_value = {
            'style': {'status': 'provisional', 'label': 'pleated', 'score': .75},
            'metadata': {'model_sha256': 'test-only', 'roi_xyxy': [70, 100, 210, 300]}}

    def test_manual_delegate_preserves_confirmation(self):
        wrapper = AutomaticPredictor(self.pleating)
        result = wrapper.predict(self.image, (1, 2, 30, 40), False)
        self.pleating.predict.assert_called_once_with(self.image, (1, 2, 30, 40), False)
        self.assertIs(result, self.pleating.predict.return_value)

    def test_missing_localizer_abstains_and_honors_fabric_toggle_all_modes(self):
        wrapper = AutomaticPredictor(self.pleating)
        for presentation in ('worn', 'hanging', 'mannequin', 'held'):
            for enabled in (True, False):
                result = wrapper.predict(self.image, {'presentation': presentation, 'fabric_enabled': enabled})
                self.assertEqual(result['style']['status'], 'unavailable')
                self.assertEqual(result['length']['status'], 'unavailable')
                self.assertEqual(result['fabric']['status'], 'unavailable' if enabled else 'disabled')
                self.assertEqual(result['metadata']['presentation'], presentation)
                self.assertFalse(result['metadata']['pi_verified'])
        self.pleating.predict.assert_not_called()

    def test_localizer_rejection_does_not_call_classifier(self):
        localizer = Mock()
        localizer.locate.return_value = {'status': 'unavailable', 'roi': None, 'reason': 'multiple_regions'}
        result = AutomaticPredictor(self.pleating, localizer).predict(
            self.image, {'presentation': 'held', 'fabric_enabled': False})
        self.assertEqual(result['style']['reason'], 'multiple_regions')
        self.assertEqual(result['fabric']['status'], 'disabled')
        self.pleating.predict.assert_not_called()

    def test_provisional_path_preserves_roi_and_experimental_limitations(self):
        localizer = Mock()
        localizer.locate.return_value = {'status': 'provisional', 'roi': [70, 100, 210, 300]}
        result = AutomaticPredictor(self.pleating, localizer).predict(
            self.image, {'presentation': 'hanging', 'fabric_enabled': True})
        self.pleating.predict.assert_called_once_with(self.image, (70, 100, 210, 300), True)
        self.assertEqual(result['style']['label'], 'pleated')
        self.assertIn('unverified', result['style']['reason'])
        self.assertEqual(result['metadata']['roi_xyxy'], [70, 100, 210, 300])
        self.assertTrue(result['metadata']['experimental'])
        self.assertEqual(result['length']['status'], 'unavailable')
        self.assertEqual(result['fabric']['status'], 'unavailable')

    def test_pipeline_owns_live_options_before_worker_uses_them(self):
        import threading
        entered, release = threading.Event(), threading.Event()
        calls = []
        class Predictor:
            def predict(self, image, options, confirmed):
                entered.set()
                release.wait(2)
                calls.append((options, confirmed))
                return {'synthetic': True}
        pipeline = ImagePipeline(Predictor(), max_frame_age=30, max_result_age=30)
        try:
            options = {'fabric_enabled': False, 'presentation': 'held', 'nested': {'value': 1}}
            pipeline.submit(self.image, roi=options, valid=True, full_skirt_confirmed=False)
            self.assertTrue(entered.wait(2))
            options['fabric_enabled'] = True
            options['nested']['value'] = 2
            release.set()
            self.assertTrue(pipeline.wait_idle(2))
            self.assertEqual(calls, [({'fabric_enabled': False, 'presentation': 'held', 'nested': {'value': 1}}, False)])
        finally:
            release.set()
            self.assertTrue(pipeline.close(2))


class LocalizerLoadTests(unittest.TestCase):
    def make_record(self, root):
        (root / 'model.tflite').write_bytes(b'synthetic model')
        digest = hashlib.sha256(b'synthetic model').hexdigest()
        (root / 'run.json').write_text(json.dumps({'status': 'completed', 'export': {'sha256': digest},
            'preprocessing': LOCALIZER_PREPROCESSING, 'threshold': .5}))
        return digest

    def interpreter(self):
        runtime = Mock()
        runtime.get_input_details.return_value = [{'shape': [1, 224, 224, 3], 'dtype': np.float32, 'index': 0}]
        runtime.get_output_details.return_value = [{'shape': [1, 56, 56, 1], 'dtype': np.float32, 'index': 1}]
        mask = np.zeros((1, 56, 56, 1), dtype=np.float32)
        mask[0, 10:30, 7:21, 0] = .9
        runtime.get_tensor.return_value = mask
        return runtime

    def test_tensor_shape_and_dtype_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_record(root)
            for side, field, value in [('input', 'dtype', np.uint8), ('output', 'dtype', np.uint8),
                                        ('input', 'shape', [1, 256, 256, 3]),
                                        ('output', 'shape', [1, 56, 56, 2])]:
                runtime = self.interpreter()
                getattr(runtime, 'get_' + side + '_details').return_value[0][field] = value
                with self.subTest(side=side, field=field), patch('app.localization._load_runtime', return_value=(Mock(return_value=runtime), 'fake')):
                    with self.assertRaisesRegex(ValueError, 'tensor contract'):
                        SkirtLocalizer(root)

    def test_empty_or_extra_tensors_rejected_before_indexing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_record(root)
            for side in ('input', 'output'):
                for count in (0, 2):
                    runtime = self.interpreter()
                    details = getattr(runtime, 'get_' + side + '_details')
                    details.return_value = details.return_value * count
                    with self.subTest(side=side, count=count), patch(
                            'app.localization._load_runtime', return_value=(Mock(return_value=runtime), 'fake')):
                        with self.assertRaisesRegex(ValueError, 'tensor contract'):
                            SkirtLocalizer(root)
                    runtime.invoke.assert_not_called()

    def test_changed_or_missing_preprocessing_and_threshold_never_load_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for field, value in [('preprocessing', None), ('preprocessing', 'RGB letterbox224'),
                                 ('threshold', None), ('threshold', .7), ('threshold', '0.5'),
                                 ('threshold', True)]:
                self.make_record(root)
                record = json.loads((root / 'run.json').read_text())
                if value is None:
                    del record[field]
                else:
                    record[field] = value
                (root / 'run.json').write_text(json.dumps(record))
                with self.subTest(field=field, value=value), patch('app.localization._load_runtime') as runtime:
                    with self.assertRaisesRegex(ValueError, 'preprocessing or threshold contract'):
                        SkirtLocalizer(root)
                    runtime.assert_not_called()

    def test_raw_rgb_preprocessing_and_output_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            digest = self.make_record(root)
            runtime = self.interpreter()
            with patch('app.localization._load_runtime', return_value=(Mock(return_value=runtime), 'fake')):
                localizer = SkirtLocalizer(root)
                result = localizer.locate(Image.new('L', (1120, 560), 200))
            tensor_index, tensor = runtime.set_tensor.call_args.args
            self.assertEqual(tensor_index, 0)
            self.assertEqual(tensor.shape, (1, 224, 224, 3))
            self.assertEqual(tensor.dtype, np.float32)
            np.testing.assert_array_equal(tensor, np.full(tensor.shape, 200, dtype=np.float32))
            runtime.invoke.assert_called_once()
            self.assertEqual(result['roi'], [140, 100, 420, 300])
            self.assertEqual(result['model_sha256'], digest)

    def test_incomplete_or_tampered_model_never_loads_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'model.tflite').write_bytes(b'synthetic model')
            digest = hashlib.sha256(b'synthetic model').hexdigest()
            for status, model_hash in [('running', digest), ('completed', '0' * 64)]:
                (root / 'run.json').write_text(json.dumps({'status': status, 'export': {'sha256': model_hash}}))
                with patch('app.localization._load_runtime') as runtime, self.assertRaises(ValueError):
                    SkirtLocalizer(root)
                runtime.assert_not_called()


if __name__ == '__main__':
    unittest.main()
