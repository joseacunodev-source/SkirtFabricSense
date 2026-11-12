"""Frozen cache identity and fixed-threshold chain checkpoint selection regressions."""
import copy
import inspect
import json
from pathlib import Path
import tempfile
import unittest

from tools.training import train_presence_finetune as candidate


class JointSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rows = [dict(sample_id=name, split='development_validation', presence_target=target,
                          label='pleated' if target else 'no_skirt')
                     for name, target in [('p1', 1), ('p2', 1), ('p3', 1), ('n1', 0), ('n2', 0)]]
        self.rows.append(dict(sample_id='train', split='development_train', presence_target=1, label='pleated'))
        self.inputs = self.root/'inputs.json'
        candidate.save(self.inputs, self.rows)
        hashes = {}
        for name in ('v1', 'v2'):
            directory = self.root/f'artifacts/models/skirt-localizer-{name}'
            directory.mkdir(parents=True)
            model = directory/'model.tflite'
            model.write_bytes(('synthetic model '+name).encode())
            hashes[name] = candidate.sha(model)
            candidate.save(directory/'run.json', {'status': 'completed', 'export': {'sha256': hashes[name]}})
        pleating = self.root/'artifacts/releases/skirt-finetune-v1-desktop-research-v7'
        pleating.mkdir(parents=True)
        (pleating/'model.tflite').write_bytes(b'synthetic pleating model')
        candidate.save(pleating/'manifest.json', {'files': [{'path': 'model.tflite', 'sha256': candidate.sha(pleating/'model.tflite')}]})
        self.cache = dict(status='completed', inputs_sha256=candidate.sha(self.inputs),
                          source_sha256='a'*64, fixed_presence_threshold=.5, fixed_mask_threshold=.5,
                          models={'masks': hashes, 'presence': 'untrusted historical probability model'}, results=[])
        for row in self.rows[:-1]:
            item = dict(sample_id=row['sample_id'], presence_target=row['presence_target'],
                        expected_pleating='pleated' if row['presence_target'] else None,
                        presence={'score': 0}, paths={})
            for name in ('v1', 'v2'):
                accepted = name == 'v2' or row['sample_id'] in ('p1', 'p2', 'n1')
                prediction = 'non_pleated' if name == 'v1' and row['sample_id'] == 'p2' else 'pleated'
                item['paths'][name] = dict(accepted=accepted,
                    pleating_prediction=prediction if accepted else None,
                    localization={'model_sha256': hashes[name], 'status': 'provisional' if accepted else 'unavailable'})
                item['paths'][name+'_plus_presence'] = {'accepted': False, 'pleating_prediction': None}
            self.cache['results'].append(item)
        self.path = self.root/'cache.json'

    def load(self, cache=None):
        candidate.save(self.path, self.cache if cache is None else cache)
        return candidate.load_joint_cache(self.root, self.path, self.inputs, self.rows)

    def test_default_keeps_minimum_balanced_bce_and_optional_argument(self):
        self.assertIsNone(inspect.signature(candidate.run).parameters['joint_comparison_cache'].default)
        self.assertLess(candidate.selection_rank(.2), candidate.selection_rank(.3))
        self.assertEqual(candidate.selection_rank(.2), (.2,))
        self.assertEqual(candidate.phases(), [('head', 3, .001), ('finetune', 5, .00001)])

    def test_cache_order_is_reconciled_to_current_validation(self):
        self.cache['results'].reverse()
        rows, provenance = self.load()
        self.assertEqual([r['sample_id'] for r in rows], ['p1', 'p2', 'p3', 'n1', 'n2'])
        self.assertEqual(provenance['sha256'], candidate.sha(self.path))
        self.assertEqual(provenance['comparison_source_sha256'], 'a'*64)
        self.assertEqual(provenance['validation_images'], 5)

    def test_changed_input_bytes_rejected(self):
        self.inputs.write_text(self.inputs.read_text()+'\n')
        with self.assertRaisesRegex(ValueError, 'inputs hash'):
            self.load()

    def test_explicit_pleating_identity_is_verified_and_recorded(self):
        model = self.root/'artifacts/releases/skirt-finetune-v1-desktop-research-v7/model.tflite'
        self.cache['models']['pleating'] = candidate.sha(model)
        _, provenance = self.load()
        self.assertIn('Explicit cache', provenance['pleating_lineage']['basis'])

    def test_wrong_explicit_pleating_identity_is_rejected(self):
        for value in ('0'*64,None):
            with self.subTest(value=value):
                self.cache['models']['pleating'] = value
                with self.assertRaisesRegex(ValueError, 'explicit pleating'):
                    self.load()

    def test_duplicate_missing_extra_and_train_identity_rejected(self):
        for variant in ('duplicate', 'missing', 'extra', 'train'):
            with self.subTest(variant=variant):
                cache = copy.deepcopy(self.cache)
                if variant == 'duplicate': cache['results'][-1] = copy.deepcopy(cache['results'][0])
                if variant == 'missing': cache['results'].pop()
                if variant == 'extra': cache['results'].append(copy.deepcopy(cache['results'][0]))
                if variant == 'train': cache['results'][0]['sample_id'] = 'train'
                with self.assertRaisesRegex(ValueError, 'membership|identity'):
                    self.load(cache)

    def test_changed_target_or_expected_pleating_rejected(self):
        for field, value in [('presence_target', 0), ('presence_target', True),
                             ('expected_pleating', 'non_pleated')]:
            with self.subTest(field=field, value=value):
                cache = copy.deepcopy(self.cache)
                cache['results'][0][field] = value
                with self.assertRaisesRegex(ValueError, 'target or expected'):
                    self.load(cache)

    def test_model_bytes_cached_hash_export_hash_and_row_hash_rejected(self):
        for variant in ('bytes', 'cached', 'export', 'row'):
            with self.subTest(variant=variant):
                cache = copy.deepcopy(self.cache)
                model = self.root/'artifacts/models/skirt-localizer-v1/model.tflite'
                original = model.read_bytes()
                run_path = model.parent/'run.json'
                original_run = run_path.read_text()
                try:
                    if variant == 'bytes': model.write_bytes(b'changed')
                    if variant == 'cached': cache['models']['masks']['v1'] = '0'*64
                    if variant == 'export': candidate.save(run_path, {'status': 'completed', 'export': {'sha256': '0'*64}})
                    if variant == 'row': cache['results'][0]['paths']['v1']['localization']['model_sha256'] = '0'*64
                    with self.assertRaisesRegex(ValueError, 'model|export'):
                        self.load(cache)
                finally:
                    model.write_bytes(original)
                    run_path.write_text(original_run)

    def test_old_presence_predictions_and_gated_paths_are_ignored(self):
        first, _ = self.load()
        self.cache['metrics'] = {'v2_plus_presence': {'positive_accepted': 999}}
        for item in self.cache['results']:
            item['presence'] = {'score': 'corrupt old score', 'accepted': True}
            item['paths']['v2_plus_presence'] = {'accepted': True, 'pleating_prediction': 'wrong'}
        second, _ = self.load()
        self.assertEqual(first, second)
        result = candidate.joint_metrics(second, [1, 1, 0, 0, 0])
        self.assertEqual(result['v2_plus_presence']['positive_accepted'], 2)
        self.assertTrue(result['eligible'])

    def test_eligibility_requires_all_three_counts_and_strict_rejection_gain(self):
        rows, _ = self.load()
        eligible = candidate.joint_metrics(rows, [.5, .5, .49, .49, .49])
        self.assertTrue(eligible['eligible'])
        self.assertEqual(eligible['v1'], dict(positive_count=3, positive_accepted=2,
                                            correct_pleating=1, negative_count=2, negative_rejected=1))
        coverage_failure = candidate.joint_metrics(rows, [.5, .49, .49, .49, .49])
        self.assertFalse(coverage_failure['eligible'])
        self.assertFalse(coverage_failure['development_criteria']['accepted_skirts_preserved'])
        rejection_tie = candidate.joint_metrics(rows, [.5, .5, .5, .49, .5])
        self.assertFalse(rejection_tie['eligible'])
        self.assertFalse(rejection_tie['development_criteria']['negative_rejection_improved'])
        wrong_rows = copy.deepcopy(rows)
        for row in wrong_rows: row['paths']['v2']['pleating_prediction'] = 'non_pleated'
        correct_failure = candidate.joint_metrics(wrong_rows, [1, 1, 1, 0, 0])
        self.assertFalse(correct_failure['development_criteria']['correct_pleating_preserved'])

    def test_eligible_rank_precedes_loss_and_uses_count_priority(self):
        def rank(rejected=5, correct=4, accepted=6, loss=.8, eligible=True):
            return candidate.selection_rank(loss, {'eligible': eligible,
                'v2_plus_presence': dict(negative_rejected=rejected, correct_pleating=correct, positive_accepted=accepted)})
        self.assertLess(rank(loss=9), rank(loss=.01, eligible=False))
        self.assertLess(rank(rejected=6, correct=1, accepted=1), rank())
        self.assertLess(rank(correct=5, accepted=5), rank())
        self.assertLess(rank(accepted=7), rank())
        self.assertLess(rank(loss=.7), rank())
        self.assertEqual(rank(), rank())

    def test_no_eligible_epoch_falls_back_to_minimum_bce(self):
        first = {'eligible': False, 'v2_plus_presence': dict(negative_rejected=8, correct_pleating=1, positive_accepted=1)}
        second = {'eligible': False, 'v2_plus_presence': dict(negative_rejected=1, correct_pleating=3, positive_accepted=4)}
        self.assertLess(candidate.selection_rank(.1, first), candidate.selection_rank(.2, second))

    def test_invalid_mask_contract_threshold_or_probability_rejected(self):
        for variant in ('threshold', 'accepted', 'prediction', 'source', 'status', 'status_inconsistent'):
            with self.subTest(variant=variant):
                cache = copy.deepcopy(self.cache)
                if variant == 'threshold': cache['fixed_mask_threshold'] = .4
                if variant == 'accepted': cache['results'][0]['paths']['v1']['accepted'] = 1
                if variant == 'prediction': cache['results'][0]['paths']['v1']['pleating_prediction'] = None
                if variant == 'source': cache['source_sha256'] = 'missing'
                if variant == 'status': cache['results'][0]['paths']['v1']['localization']['status'] = 'unknown'
                if variant == 'status_inconsistent': cache['results'][0]['paths']['v1']['localization']['status'] = 'unavailable'
                with self.assertRaises(ValueError): self.load(cache)
        rows, _ = self.load()
        for probabilities in ([1], [1, 1, 1, 1, float('nan')], [1, 1, 1, 1, -1]):
            with self.assertRaises(ValueError): candidate.joint_metrics(rows, probabilities)

    def test_historical_pleating_bundle_hash_checked_and_lineage_recorded(self):
        _, provenance = self.load()
        path = self.root/provenance['pleating_lineage']['path']
        self.assertEqual(provenance['pleating_lineage']['sha256'], candidate.sha(path))
        path.write_bytes(b'changed pleating')
        with self.assertRaisesRegex(ValueError, 'pleating bundle model hash'):
            self.load()


if __name__ == '__main__': unittest.main()
