"""Synthetic paired-prediction tests; no images, models or hardware used."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import report_detection_uncertainty as report


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def fixture():
    rows = []
    labels = ['pleated', 'no_skirt', 'pleated', 'pleated', 'non_pleated', 'non_pleated', 'no_skirt', 'no_skirt']
    for i, label in enumerate(labels):
        group = 'shared-positive' if i in (2, 3) else 'group-'+str(i)
        rows.append(dict(sample_id='sample-'+str(i), sha256=digest('image'+str(i)),
            original_path='images/'+str(i)+'.jpg', source_partition='train2020',
            split='development_train' if i < 2 else 'development_validation',
            presence_target=int(label != 'no_skirt'), label=label,
            group_id=group, group_hash=digest(group), grouping_review_pending=False,
            training_eligibility=dict(approved=True), label_evidence=dict(original_inspected=True),
            sampling_bucket='dress' if label == 'no_skirt' else None))
    inputs_digest = digest(json.dumps(rows))
    models = dict(masks=dict(v2=digest('mask')), pleating=digest('pleating'), presence=digest('gate'))
    predictions = ['pleated', 'non_pleated', 'non_pleated', 'pleated', 'pleated', 'pleated']
    def comparison(gates):
        results = []
        for row, gate, prediction in zip(rows[2:], gates, predictions):
            mask = dict(accepted=True, pleating_prediction=prediction,
                localization=dict(status='provisional', threshold=.5, model_sha256=models['masks']['v2']))
            results.append(dict(sample_id=row['sample_id'], presence_target=row['presence_target'],
                expected_pleating=row['label'] if row['presence_target'] else None,
                presence=dict(accepted=gate, score=.8 if gate else .2, threshold=.5, model_sha256=models['presence']),
                paths=dict(v2=mask, v2_plus_presence=dict(accepted=gate, pleating_prediction=prediction if gate else None))))
        result = dict(status='completed', inputs_sha256=inputs_digest, split_hash=report.split_hash(rows),
            fixed_presence_threshold=.5, fixed_mask_threshold=.5, models=copy.deepcopy(models), results=results)
        recompute(result, rows)
        return result
    return rows, comparison([True, False, True, True, True, False]), comparison([True, True, True, False, False, False]), inputs_digest


def recompute(value, rows):
    validation = [r for r in rows if r['split'] == 'development_validation']
    value['metrics'] = {report.PATH:report.raw_metrics(validation, {r['sample_id']:r for r in value['results']})}


class DetectionUncertaintyTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.baseline, self.candidate, self.input_hash = fixture()

    def run_report(self, **kwargs):
        return report.evaluate(self.rows, self.baseline, self.candidate,
            inputs_digest=self.input_hash, resamples=100, **kwargs)

    def test_counts_include_abstentions_and_class_confusions(self):
        result = self.run_report()
        raw = result['raw_image_metrics']['candidate']
        self.assertEqual((raw['positive_count'], raw['positive_accepted'], raw['correct_pleating']), (4, 3, 2))
        self.assertEqual(raw['confusion_matrix']['non_pleated'], dict(pleated=0, non_pleated=1, unavailable=1))
        self.assertEqual(raw['per_pleating_class']['non_pleated']['end_to_end_correctness'], .5)
        self.assertEqual(raw['per_pleating_class']['non_pleated']['accepted_accuracy'], 1)
        self.assertEqual(raw['negative_rejected'], 2)
        self.assertEqual(result['paired_transitions']['negative_states'], {'falsely_accepted -> rejected':1, 'rejected -> rejected':1})

    def test_equal_group_weights_keep_multiple_images_together(self):
        result = self.run_report()
        values = result['equal_source_group_bootstrap']['metrics']['skirt_coverage']
        self.assertAlmostEqual(values['baseline']['estimate'], 5/6)
        self.assertAlmostEqual(values['candidate']['estimate'], 2/3)
        self.assertAlmostEqual(values['candidate_minus_baseline']['estimate'], -1/6)
        self.assertEqual(result['inventory']['validation_source_groups'], 5)
        self.assertEqual(result['inventory']['validation_group_size_histogram'], {'2':1, '1':4})

    def test_bootstrap_is_deterministic_and_paired_identity_is_zero(self):
        self.assertEqual(self.run_report(), self.run_report())
        self.candidate = copy.deepcopy(self.baseline)
        metrics = self.run_report()['equal_source_group_bootstrap']['metrics']
        for value in metrics.values():
            delta = value['candidate_minus_baseline']
            self.assertEqual(delta['estimate'], 0)
            self.assertEqual(delta['percentile_95_interval'], [0, 0])
        self.assertEqual(self.run_report()['paired_transitions']['changed_results'], [])

    def test_zero_accepted_selective_accuracy_is_null_not_zero(self):
        for value in (self.baseline, self.candidate):
            for item in value['results']:
                item['presence'].update(accepted=False, score=.2)
                item['paths'][report.PATH] = dict(accepted=False, pleating_prediction=None)
            recompute(value, self.rows)
        metrics = self.run_report()['equal_source_group_bootstrap']['metrics']
        for value in metrics['accepted_pleating_accuracy'].values():
            self.assertIsNone(value['estimate'])
            self.assertIsNone(value['percentile_95_interval'])
            self.assertEqual(value['undefined_resamples'], 100)
        self.assertEqual(metrics['end_to_end_pleating_correctness']['candidate']['estimate'], 0)

    def test_missing_validation_member_fails(self):
        self.candidate['results'].pop()
        with self.assertRaisesRegex(ValueError, 'membership'):
            self.run_report()

    def test_duplicate_validation_member_fails(self):
        self.candidate['results'][-1] = self.candidate['results'][0]
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.run_report()

    def test_extra_or_training_member_fails(self):
        self.candidate['results'][-1]['sample_id'] = self.rows[0]['sample_id']
        with self.assertRaisesRegex(ValueError, 'unexpected'):
            self.run_report()

    def test_changed_truth_fails(self):
        self.candidate['results'][0]['expected_pleating'] = 'non_pleated'
        with self.assertRaisesRegex(ValueError, 'truth'):
            self.run_report()

    def test_bool_target_is_not_integer_truth(self):
        self.candidate['results'][0]['presence_target'] = True
        with self.assertRaisesRegex(ValueError, 'truth'):
            self.run_report()

    def test_cross_split_group_fails(self):
        self.rows[2]['group_hash'] = self.rows[0]['group_hash']
        self.rows[2]['group_id'] = self.rows[0]['group_id']
        with self.assertRaisesRegex(ValueError, 'crosses'):
            self.run_report()

    def test_inconsistent_group_alias_fails(self):
        self.rows[2]['group_id'] = self.rows[0]['group_id']
        with self.assertRaisesRegex(ValueError, 'aliases'):
            self.run_report()

    def test_mixed_target_group_not_split_into_strata(self):
        self.rows[-1]['group_hash'] = self.rows[2]['group_hash']
        self.rows[-1]['group_id'] = self.rows[2]['group_id']
        with self.assertRaisesRegex(ValueError, 'Mixed-target'):
            self.run_report()

    def test_protected_partition_fails(self):
        self.rows[-1]['source_partition'] = 'test2020'
        with self.assertRaisesRegex(ValueError, 'Protected'):
            self.run_report()

    def test_input_or_split_hash_mutation_fails(self):
        for field in ('inputs_sha256', 'split_hash'):
            with self.subTest(field=field):
                before = self.candidate[field]
                self.candidate[field] = digest('mutated')
                with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                    self.run_report()
                self.candidate[field] = before

    def test_changed_fixed_threshold_fails(self):
        self.candidate['fixed_presence_threshold'] = .6
        with self.assertRaisesRegex(ValueError, 'thresholds changed'):
            self.run_report()

    def test_nonfinite_score_and_score_acceptance_mismatch_fail(self):
        for score in (float('nan'), float('inf'), -.2, 1.1, .2):
            with self.subTest(score=score):
                self.candidate['results'][0]['presence']['score'] = score
                with self.assertRaisesRegex(ValueError, 'Presence score'):
                    self.run_report()

    def test_rejection_cannot_keep_prediction(self):
        self.candidate['results'][-1]['paths'][report.PATH]['pleating_prediction'] = 'pleated'
        with self.assertRaisesRegex(ValueError, 'acceptance/prediction'):
            self.run_report()

    def test_gated_path_must_match_mask_and_presence(self):
        self.candidate['results'][-1]['paths'][report.PATH] = dict(accepted=True, pleating_prediction='pleated')
        with self.assertRaisesRegex(ValueError, 'fixed saved'):
            self.run_report()

    def test_shared_model_and_saved_mask_predictions_must_match(self):
        self.candidate['models']['pleating'] = digest('other')
        with self.assertRaisesRegex(ValueError, 'identities differ'):
            self.run_report()
        self.candidate['models']['pleating'] = self.baseline['models']['pleating']
        self.candidate['results'][0]['paths']['v2']['localization']['roi'] = [1,2,3,4]
        with self.assertRaisesRegex(ValueError, 'results differ'):
            self.run_report()

    def test_archived_aggregate_counts_are_recomputed(self):
        self.candidate['metrics'][report.PATH]['negative_rejected'] = 0
        with self.assertRaisesRegex(ValueError, 'aggregate count'):
            self.run_report()

    def test_validation_size_is_a_protocol_check(self):
        with self.assertRaisesRegex(ValueError, 'size differs'):
            self.run_report(expected_validation_count=118)

    def test_duplicate_original_image_fails(self):
        self.rows[-1]['sha256'] = self.rows[0]['sha256']
        with self.assertRaisesRegex(ValueError, 'Duplicate source image'):
            self.run_report()

    def test_invalid_resampling_parameters_fail(self):
        validation = report.validate_inputs(self.rows)
        predictions = {r['sample_id']:r for r in self.baseline['results']}
        for count in (0, True, -1, 100001):
            with self.subTest(count=count), self.assertRaises(ValueError):
                report.paired_bootstrap(validation, predictions, predictions, resamples=count)

    def test_actual_input_bytes_must_match_completed_run_hash(self):
        # Build only the earlier-loading files: integrity must fail before any
        # source manifest/model access, proving this is not a syntax-only check.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            files = {report.DEFAULT_INPUTS:self.rows}
            files.update({report.DEFAULT_REPORTS['baseline']:self.baseline,
                          report.DEFAULT_REPORTS['candidate']:self.candidate})
            for path in report.DEFAULT_RUNS.values():
                files[path] = dict(status='completed', frozen_inputs_sha256=self.input_hash,
                    split_hash=report.split_hash(self.rows), threshold=.5,
                    export=dict(sha256=self.baseline['models']['presence']))
            for path, value in files.items():
                target = root/path
                target.parent.mkdir(parents=True, exist_ok=True)
                # Different serialization changes the actual file hash.
                target.write_text(json.dumps(value, indent=2), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'archived run/input/split/export'):
                report.evaluate_files(root, resamples=10)

    def test_archived_truth_and_groups_must_match_frozen_source_rows(self):
        positives = [{k:v for k,v in r.items() if k != 'presence_target'} for r in self.rows if r['presence_target']]
        negatives = [{k:v for k,v in r.items() if k != 'presence_target'} for r in self.rows if not r['presence_target']]
        assignments = [{k:r[k] for k in ('sample_id','group_hash','split')} for r in positives]
        report.validate_manifest_bindings(self.rows, positives, negatives, assignments)
        for field, mutation in (('label','non_pleated'), ('group_hash',digest('invented')), ('split','development_validation')):
            with self.subTest(field=field):
                rows = copy.deepcopy(self.rows)
                rows[0][field] = mutation
                with self.assertRaisesRegex(ValueError, 'frozen manifests'):
                    report.validate_manifest_bindings(rows, positives, negatives, assignments)

    def test_original_source_split_assignment_cannot_be_rewritten(self):
        positives = [{k:v for k,v in r.items() if k != 'presence_target'} for r in self.rows if r['presence_target']]
        negatives = [{k:v for k,v in r.items() if k != 'presence_target'} for r in self.rows if not r['presence_target']]
        assignments = [{k:r[k] for k in ('sample_id','group_hash','split')} for r in positives]
        assignments[0]['split'] = 'development_validation'
        with self.assertRaisesRegex(ValueError, 'original grouped split'):
            report.validate_manifest_bindings(self.rows, positives, negatives, assignments)


if __name__ == '__main__':
    unittest.main()
