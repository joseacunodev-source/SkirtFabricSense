"""Independent actual-Keras checks; no dataset fitting or package changes."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.training import train_presence_finetune as candidate


class AdmissionReviewRegressionTests(unittest.TestCase):
    def reject_negative_mutation(self, mutate):
        source = candidate.ROOT / 'data/labels/negative-reviewed-v2.jsonl'
        rows = [json.loads(line) for line in source.read_text().splitlines()]
        row = next(row for row in rows if row.get('training_eligibility', {}).get('approved') is True)
        mutate(row)
        original_read = Path.read_text
        def read(path, *args, **kwargs):
            if path.resolve() == source.resolve():
                return '\n'.join(json.dumps(row) for row in rows)
            return original_read(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read):
            with self.assertRaisesRegex(ValueError, 'Negative review hash or source identity'):
                candidate.prepare_rows(candidate.ROOT, source)

    def test_stale_review_hash_is_rejected(self):
        self.reject_negative_mutation(lambda row: row['label_evidence'].update(image_sha256='0' * 64))

    def test_conflicting_second_hash_is_rejected(self):
        self.reject_negative_mutation(lambda row: row['label_evidence'].update(sha256='0' * 64))

    def test_missing_review_hash_is_rejected(self):
        def mutate(row):
            row['label_evidence'].pop('image_sha256', None)
            row['label_evidence'].pop('sha256', None)
        self.reject_negative_mutation(mutate)

    def test_wrong_review_identity_is_rejected(self):
        self.reject_negative_mutation(lambda row: row['label_evidence'].update(sample_id='another-source'))

    def test_frozen_positive_and_assignment_bytes_are_pinned(self):
        files = ('worn-pleating-development-v1.jsonl', 'source-skirt-development-splits.json')
        for changed in files:
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                directory = root / 'data/manifests'
                directory.mkdir(parents=True)
                for name in files:
                    content = (candidate.ROOT / 'data/manifests' / name).read_bytes()
                    (directory / name).write_bytes(content + (b'\n' if name == changed else b''))
                negative = root / 'negatives.jsonl'
                negative.write_text('')
                with self.assertRaisesRegex(ValueError, 'Frozen positive manifest or source assignments changed'):
                    candidate.prepare_rows(root, negative)


@unittest.skipUnless(importlib.util.find_spec('tensorflow'), 'TensorFlow not installed in this interpreter')
class ActualKerasPresenceReview(unittest.TestCase):
    def test_actual_cached_weights_and_phase_variables(self):
        import tensorflow as tf
        provenance = json.loads((candidate.ROOT / 'records/acquisitions/2026-10-04-mobilenetv2-weights.json').read_text())
        weights = Path(provenance['path'])
        if os.name == 'nt':
            self.skipTest('Recorded pretrained path belongs to the WSL training environment')
        self.assertTrue(weights.is_file(), 'Training cache is missing; never automatically download')
        self.assertEqual(hashlib.sha256(weights.read_bytes()).hexdigest(), provenance['sha256'])
        base = tf.keras.applications.MobileNetV2(include_top=False, weights=str(weights),
                                                input_shape=(224, 224, 3), pooling='avg')
        candidate.configure_backbone(base, 'head', tf.keras.layers.BatchNormalization)
        self.assertFalse(base.trainable_variables)
        names = candidate.configure_backbone(base, 'finetune', tf.keras.layers.BatchNormalization)
        self.assertTrue(base.trainable_variables)
        self.assertIn('block_13_expand', names)
        boundary = next(i for i, layer in enumerate(base.layers) if layer.name == 'block_13_expand')
        expected = []
        for index, layer in enumerate(base.layers):
            if index < boundary or isinstance(layer, tf.keras.layers.BatchNormalization):
                self.assertFalse(layer.trainable_variables, layer.name)
            else:
                expected.extend(layer.trainable_variables)
        self.assertEqual({id(v) for v in base.trainable_variables}, {id(v) for v in expected})
        self.assertFalse(any(layer.trainable for layer in base.layers
                             if isinstance(layer, tf.keras.layers.BatchNormalization)))
        tf.keras.backend.clear_session()


if __name__ == '__main__':
    unittest.main()
