"""Verify isolated-runtime failure and parity handling with synthetic local fixtures."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import pi_probe as probe


class PiProbeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.station = self.root / 'station'
        (self.station / 'application').mkdir(parents=True)
        (self.station / 'application/manifest.json').write_text('{"model":"model.tflite"}', encoding='utf-8')
        (self.station / 'station-inventory.json').write_text('{}', encoding='utf-8')
        self.paths = {'pleating': self.station / 'application/model.tflite',
                      **{role: self.station / 'models' / role / 'model.tflite' for role in probe.ROLES[1:]}}
        for role, path in self.paths.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('synthetic ' + role).encode())
        self.hashes = {role: probe.sha(path) for role, path in self.paths.items()}
        self.output = self.root / 'result.json'
        self.result = self.worker_result()

    def worker_result(self):
        models = {}
        for role in probe.ROLES:
            count = 1
            for n in probe.OUTPUT_SHAPES[role]: count *= n
            values = [.25] * count
            models[role] = {'model_sha256': self.hashes[role],
                'input': {'shape': probe.INPUT_SHAPE, 'dtype': 'float32',
                          'sha256': hashlib.sha256(probe.fixture_bytes()).hexdigest()},
                'output': {'shape': probe.OUTPUT_SHAPES[role], 'dtype': 'float32',
                           'values': values, 'sha256': hashlib.sha256(struct.pack('<' + 'f' * count, *values)).hexdigest()},
                'timings': {'warmup_iterations': 1, 'warmup_ms': 2., 'load_allocate_ms': 3.,
                            'iterations': 3, 'invoke_ms': [1., 2., 3.], 'p50_ms': 2., 'p95_ms': 2.9}}
        return {'status': 'passed', 'fixture': dict(probe.FIXTURE), 'runtime': 'fixture_runtime',
                'threads': 2, 'models': models}

    def run_mocked(self, data=None, code=0, exception=None, reference=None):
        completed = subprocess.CompletedProcess(['synthetic'], code,
            json.dumps(self.result if data is None else data), 'synthetic runtime log')
        with patch.object(probe, 'verify_station', return_value={'status': 'passed'}), \
             patch.object(probe, 'observations', return_value={'system': 'synthetic'}), \
             patch.object(probe.subprocess, 'run', side_effect=exception, return_value=completed) as command:
            report = probe.run_probe(self.station, self.output, reference=reference)
        return report, command

    def reference(self, worker=None):
        return {'schema_version': 1, 'kind': 'pi_model_probe', 'status': 'passed',
                'pi_verified': False, 'full_live_acceptance': False,
                'station_inventory_sha256': probe.sha(self.station / 'station-inventory.json'),
                'worker': self.result if worker is None else worker}

    def test_success_stays_research_only_and_isolates_cpu_worker(self):
        result, command = self.run_mocked()
        self.assertEqual(result['status'], 'passed')
        self.assertFalse(result['pi_verified'])
        self.assertFalse(result['full_live_acceptance'])
        self.assertEqual(result['parity']['status'], 'not_requested')
        argv = command.call_args.args[0]
        self.assertIn('--worker', argv)
        self.assertEqual(command.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], '-1')
        self.assertEqual(command.call_args.kwargs['env']['PYTHONDONTWRITEBYTECODE'], '1')
        self.assertEqual(probe.strict_json(self.output.read_text())['worker'], self.result)

    def test_timeout_and_signal_create_failed_evidence(self):
        for code, exception in [(0, subprocess.TimeoutExpired(['worker'], 120)), (-4, None), (1, None)]:
            with self.subTest(code=code, exception=exception):
                self.output = self.root / ('failure-' + str(code) + '.json')
                result, _ = self.run_mocked(code=code, exception=exception)
                self.assertEqual(result['status'], 'failed')
                self.assertFalse(result['pi_verified'])
                if exception: self.assertTrue(result['worker_timed_out'])
                if code == -4: self.assertEqual(result['worker_signal'], 4)

    def test_malformed_worker_stdout_is_saved_as_failure(self):
        completed = subprocess.CompletedProcess(['worker'], 0, 'runtime printed noise', '')
        with patch.object(probe, 'verify_station', return_value={}), \
             patch.object(probe, 'observations', return_value={}), \
             patch.object(probe.subprocess, 'run', return_value=completed):
            result = probe.run_probe(self.station, self.output)
        self.assertEqual(result['status'], 'failed')
        self.assertIn('noise', result['worker_stdout_tail'])

    def test_wrong_models_shapes_dtypes_and_finite_values_fail_closed(self):
        cases = []
        missing = copy.deepcopy(self.result); del missing['models']['fabric']; cases.append(missing)
        shape = copy.deepcopy(self.result); shape['models']['presence']['output']['shape'] = [1, 2]; cases.append(shape)
        dtype = copy.deepcopy(self.result); dtype['models']['presence']['input']['dtype'] = 'int8'; cases.append(dtype)
        nonfinite = copy.deepcopy(self.result); nonfinite['models']['presence']['output']['values'] = [float('nan')]; cases.append(nonfinite)
        boolean = copy.deepcopy(self.result); boolean['models']['presence']['output']['values'] = [True]; cases.append(boolean)
        changed = copy.deepcopy(self.result); changed['models']['pleating']['model_sha256'] = '0' * 64; cases.append(changed)
        timing = copy.deepcopy(self.result); timing['models']['presence']['timings'] = []; cases.append(timing)
        for index, value in enumerate(cases):
            with self.subTest(index=index):
                self.output = self.root / f'bad-result-{index}.json'
                result, _ = self.run_mocked(data=value)
                self.assertEqual(result['status'], 'failed')

    def test_reference_parity_passes_then_rejects_changed_output(self):
        reference = self.root / 'reference.json'
        reference.write_text(json.dumps(self.reference()), encoding='utf-8')
        result, _ = self.run_mocked(reference=reference)
        self.assertEqual(result['parity']['status'], 'passed')
        self.assertEqual(result['parity']['models']['localizer']['elements_compared'], 3136)
        self.output = self.root / 'changed-parity.json'
        other = copy.deepcopy(self.result)
        other['models']['presence']['output']['values'] = [.5]
        other['models']['presence']['output']['sha256'] = hashlib.sha256(struct.pack('<f', .5)).hexdigest()
        result, _ = self.run_mocked(data=other, reference=reference)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['parity']['status'], 'failed')

    def test_reference_missing_role_identity_and_nan_are_rejected(self):
        variants = []
        wrong = self.reference(); wrong['station_inventory_sha256'] = '0' * 64; variants.append(wrong)
        missing = copy.deepcopy(self.reference()); del missing['worker']['models']['localizer']; variants.append(missing)
        nonfinite = copy.deepcopy(self.reference()); nonfinite['other'] = float('inf'); variants.append(nonfinite)
        for index, value in enumerate(variants):
            reference = self.root / f'reference-{index}.json'
            reference.write_text(json.dumps(value), encoding='utf-8')
            self.output = self.root / f'reference-failure-{index}.json'
            result, _ = self.run_mocked(reference=reference)
            self.assertEqual(result['status'], 'failed')

    def test_invalid_station_does_not_spawn_runtime(self):
        with patch.object(probe, 'verify_station', side_effect=ValueError('changed station')), \
             patch.object(probe, 'observations', return_value={}), \
             patch.object(probe.subprocess, 'run') as command:
            result = probe.run_probe(self.station, self.output)
        self.assertEqual(result['status'], 'failed')
        command.assert_not_called()

    def test_output_paths_and_existing_reports_are_preserved(self):
        with self.assertRaisesRegex(ValueError, 'immutable'):
            probe.run_probe(self.station, self.station / 'result.json')
        self.output.write_bytes(b'preserve')
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            probe.run_probe(self.station, self.output)
        self.assertEqual(self.output.read_bytes(), b'preserve')

    def test_iteration_and_timeout_parameters_rejected_before_work(self):
        for arguments in [{'iterations': 0}, {'iterations': True}, {'iterations': 1001},
                          {'timeout': float('nan')}, {'timeout': 0}, {'timeout': 3601}]:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                probe.run_probe(self.station, self.output, **arguments)
        self.assertFalse(self.output.exists())

    def test_fixture_bytes_are_platform_independent_raw_float_rgb(self):
        data = probe.fixture_bytes()
        self.assertEqual(len(data), 1 * 224 * 224 * 3 * 4)
        self.assertEqual(struct.unpack('<4f', data[:16]), (42., 79., 116., 153.))
        # The integer color pattern repeats exactly588 times; compare an
        # independently packed little-endian block, not native array bytes.
        expected = struct.pack('<256f', *((i * 37 + 42) % 256 for i in range(256))) * 588
        self.assertEqual(data, expected)
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         '8191895d8f4d01fa398c76fd6f5e2b857272c03e41053ddeec982da609f86d91')


if __name__ == '__main__':
    unittest.main()
