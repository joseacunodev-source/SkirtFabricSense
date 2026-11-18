"""Isolate a four-model CPU invocation/parity probe; never install or activate a camera.

Synthetic inputs exercise exported operators. Timings are invocation-only and do
not establish camera FPS, prediction accuracy, calibrated length or Pi acceptance.
"""
from __future__ import annotations

import argparse
from array import array
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time

if __package__:
    from .station_package import verify_station
else:
    from station_package import verify_station

ROLES = ('pleating', 'localizer', 'presence', 'fabric')
INPUT_SHAPE = [1, 224, 224, 3]
OUTPUT_SHAPES = {'pleating': [1, 2], 'localizer': [1, 56, 56, 1],
                 'presence': [1, 1], 'fabric': [1, 4]}
FIXTURE = {'id': 'rgb_mod256_v1', 'seed': 42,
           'algorithm': '(uint32_arange * 37 + 42) % 256; reshape1x224x224x3; rawRGBfloat32'}
ATOL = RTOL = 1e-3


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


@lru_cache(maxsize=1)
def fixture_bytes():
    values = array('f', ((i * 37 + FIXTURE['seed']) % 256 for i in range(math.prod(INPUT_SHAPE))))
    require(values.itemsize == 4, 'Synthetic fixture requires four-byte float storage')
    if sys.byteorder != 'little':
        values.byteswap()
    return values.tobytes()


def strict_json(body):
    def constant(value):
        raise ValueError('Nonfinite JSON constant rejected: ' + value)
    return json.loads(body, parse_constant=constant)


def finite_tree(value):
    if isinstance(value, dict):
        for child in value.values():
            finite_tree(child)
    elif isinstance(value, list):
        for child in value:
            finite_tree(child)
    elif type(value) is float:
        require(math.isfinite(value), 'Nonfinite numeric report value')


def paths_for(station):
    manifest = strict_json((station / 'application/manifest.json').read_text(encoding='utf-8'))
    require(manifest.get('model') == 'model.tflite', 'Unexpected pleating model path')
    return {'pleating': station / 'application' / manifest['model'],
            **{role: station / 'models' / role / 'model.tflite' for role in ROLES[1:]}}


def percentile(values, fraction):
    ordered = sorted(values)
    rank = (len(ordered) - 1) * fraction
    lower, upper = math.floor(rank), math.ceil(rank)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def worker(station, iterations):
    """Only this subprocess imports numerical/runtime packages."""
    verify_station(station)
    sys.path.insert(0, str(station / 'application'))
    import numpy as np
    from app.inference import _load_runtime
    interpreter_class, runtime = _load_runtime()
    models = {}
    values = np.frombuffer(fixture_bytes(), dtype='<f4').astype(np.float32, copy=True).reshape(INPUT_SHAPE)
    for role, model in paths_for(station).items():
        start = time.perf_counter()
        interpreter = interpreter_class(model_path=str(model), num_threads=2)
        interpreter.allocate_tensors()
        load_ms = (time.perf_counter() - start) * 1000
        inputs, outputs = interpreter.get_input_details(), interpreter.get_output_details()
        require(len(inputs) == len(outputs) == 1, role + ': exactly one input/output required')
        incoming, outgoing = inputs[0], outputs[0]
        require(list(incoming['shape']) == INPUT_SHAPE and incoming['dtype'] == np.float32,
                role + ': unsupported input shape/dtype')
        require(list(outgoing['shape']) == OUTPUT_SHAPES[role] and outgoing['dtype'] == np.float32,
                role + ': unsupported output shape/dtype')
        interpreter.set_tensor(incoming['index'], values)
        start = time.perf_counter(); interpreter.invoke()
        warmup_ms = (time.perf_counter() - start) * 1000
        timings = []
        for _ in range(iterations):
            interpreter.set_tensor(incoming['index'], values)
            start = time.perf_counter(); interpreter.invoke()
            timings.append((time.perf_counter() - start) * 1000)
        result = interpreter.get_tensor(outgoing['index'])
        require(list(result.shape) == OUTPUT_SHAPES[role] and result.dtype == np.float32,
                role + ': output changed shape/dtype')
        require(np.isfinite(result).all() and (result >= 0).all() and (result <= 1).all(),
                role + ': output must contain finite probabilities in [0,1]')
        output_bytes = result.astype('<f4', copy=False).tobytes(order='C')
        models[role] = {'model_sha256': sha(model),
            'input': {'shape': INPUT_SHAPE, 'dtype': 'float32',
                      'sha256': hashlib.sha256(fixture_bytes()).hexdigest()},
            'output': {'shape': OUTPUT_SHAPES[role], 'dtype': 'float32',
                       'sha256': hashlib.sha256(output_bytes).hexdigest(),
                       'values': result.reshape(-1).tolist()},
            'timings': {'warmup_iterations': 1, 'warmup_ms': warmup_ms,
                        'load_allocate_ms': load_ms, 'iterations': iterations,
                        'invoke_ms': timings, 'p50_ms': percentile(timings, .5),
                        'p95_ms': percentile(timings, .95)}}
        del interpreter
    return {'status': 'passed', 'fixture': FIXTURE, 'runtime': runtime, 'threads': 2,
            'models': models, 'timing_scope': 'CPU model invocation only; preprocessing/capture/UI excluded'}


def validate_worker(value, model_hashes, iterations=None):
    require(isinstance(value, dict) and value.get('status') == 'passed', 'Worker did not pass')
    finite_tree(value)
    require(value.get('fixture') == FIXTURE, 'Synthetic fixture contract mismatch')
    require(isinstance(value.get('runtime'), str) and value['runtime'], 'Missing runtime identity')
    require(value.get('threads') == 2, 'Unexpected thread contract')
    models = value.get('models')
    require(isinstance(models, dict) and set(models) == set(ROLES), 'Missing or extra model roles')
    for role in ROLES:
        record = models[role]
        require(isinstance(record, dict) and record.get('model_sha256') == model_hashes[role],
                role + ': model identity mismatch')
        require(record.get('input') == {'shape': INPUT_SHAPE, 'dtype': 'float32',
                'sha256': hashlib.sha256(fixture_bytes()).hexdigest()}, role + ': input identity mismatch')
        output = record.get('output', {})
        require(isinstance(output, dict) and output.get('shape') == OUTPUT_SHAPES[role]
                and output.get('dtype') == 'float32', role + ': output shape/dtype mismatch')
        values = output.get('values')
        require(isinstance(values, list) and len(values) == math.prod(OUTPUT_SHAPES[role])
                and all(type(x) in (int, float) and math.isfinite(x) and 0 <= x <= 1 for x in values),
                role + ': invalid finite output probabilities')
        digest = hashlib.sha256(struct.pack('<' + 'f' * len(values), *values)).hexdigest()
        require(output.get('sha256') == digest, role + ': output digest mismatch')
        timing = record.get('timings', {})
        require(isinstance(timing, dict), role + ': invalid timing record')
        count = timing.get('iterations')
        require(type(count) is int and 1 <= count <= 1000
                and (iterations is None or iterations == count), role + ': invalid iteration count')
        times = timing.get('invoke_ms')
        require(isinstance(times, list) and len(times) == count
                and all(type(t) in (int, float) and math.isfinite(t) and t >= 0 for t in times),
                role + ': invalid timing samples')
        for name in ('warmup_ms', 'load_allocate_ms', 'p50_ms', 'p95_ms'):
            number = timing.get(name)
            require(type(number) in (int, float) and math.isfinite(number) and number >= 0,
                    role + ': invalid ' + name)
        require(timing.get('warmup_iterations') == 1, role + ': warmup contract mismatch')
    return value


def compare_reference(current, reference, inventory_hash, model_hashes):
    finite_tree(reference)
    require(isinstance(reference, dict) and reference.get('schema_version') == 1
            and reference.get('kind') == 'pi_model_probe' and reference.get('status') == 'passed'
            and reference.get('pi_verified') is False and reference.get('full_live_acceptance') is False,
            'Reference must be a passed research-only probe report')
    require(reference.get('station_inventory_sha256') == inventory_hash, 'Reference station identity mismatch')
    expected = validate_worker(reference.get('worker'), model_hashes)
    comparisons = {}
    for role in ROLES:
        actual = current['models'][role]['output']['values']
        wanted = expected['models'][role]['output']['values']
        errors = [abs(a - b) for a, b in zip(actual, wanted)]
        passed = all(delta <= ATOL + RTOL * abs(b) for delta, b in zip(errors, wanted))
        comparisons[role] = {'passed': passed, 'maximum_absolute_error': max(errors),
                             'elements_compared': len(errors)}
    return {'status': 'passed' if all(r['passed'] for r in comparisons.values()) else 'failed',
            'atol': ATOL, 'rtol': RTOL, 'models': comparisons}


def observations():
    board = Path('/sys/firmware/devicetree/base/model')
    thermal = Path('/sys/class/thermal/thermal_zone0/temp')
    temperature = None
    if thermal.is_file():
        try:
            temperature = float(thermal.read_text().strip()) / 1000
            if not math.isfinite(temperature): temperature = None
        except (OSError, ValueError): pass
    versions = {}
    for name in ('numpy', 'Pillow', 'ai-edge-litert', 'tflite-runtime', 'tensorflow'):
        try: versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: versions[name] = None
    board_text = ''
    if board.is_file():
        try: board_text = board.read_text(errors='replace').rstrip('\0\n')
        except OSError: pass
    return {'system': platform.system(), 'machine': platform.machine(),
            'pointer_bits': struct.calcsize('P') * 8, 'python': platform.python_version(),
            'libc': list(platform.libc_ver()), 'packages': versions,
            'board_model': board_text,
            'temperature_celsius': temperature}


def run_probe(station, output, reference=None, iterations=3, timeout=120):
    station, output = Path(station).absolute(), Path(output).resolve()
    require(not output.is_relative_to(station.resolve()), 'Probe output must be outside the immutable station')
    require(not output.exists(), 'Refusing to overwrite probe output')
    require(type(iterations) is int and 1 <= iterations <= 1000, 'Iterations must be1..1000')
    require(type(timeout) in (int, float) and math.isfinite(timeout) and 0 < timeout <= 3600,
            'Timeout must be positive and at most3600 seconds')
    report = {'schema_version': 1, 'kind': 'pi_model_probe', 'status': 'failed',
              'recorded_at': datetime.now(timezone.utc).isoformat(), 'observations': observations(),
              'pi_verified': False, 'full_live_acceptance': False,
              'parity': {'status': 'not_requested'},
              'limits': 'Synthetic CPU operator/parity probe, not accuracy, camera FPS, calibrated geometry, '
                        'live application, sustained thermal performance or Pi acceptance.'}
    try:
        report['station_verification'] = verify_station(station)
        report['station_inventory_sha256'] = sha(station / 'station-inventory.json')
        hashes = {role: sha(path) for role, path in paths_for(station).items()}
        expected = strict_json(Path(reference).read_text(encoding='utf-8')) if reference else None
        command = [sys.executable, '-B', str(Path(__file__).resolve()), '--worker',
                   '--station', str(station), '--iterations', str(iterations)]
        report['worker_command'] = command
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='-1', PYTHONDONTWRITEBYTECODE='1'))
        report['worker_exit_code'] = result.returncode
        report['worker_stderr_tail'] = result.stderr[-12000:]
        if result.returncode != 0:
            report['worker_stdout_tail'] = result.stdout[-4000:]
        if result.returncode < 0:
            report['worker_signal'] = -result.returncode
        require(result.returncode == 0, 'Runtime worker failed with exit code ' + str(result.returncode))
        try:
            data = validate_worker(strict_json(result.stdout), hashes, iterations)
        except ValueError:
            report['worker_stdout_tail'] = result.stdout[-4000:]
            raise
        report['worker'] = data
        if expected is not None:
            report['parity'] = compare_reference(data, expected, report['station_inventory_sha256'], hashes)
            report['reference_sha256'] = sha(reference)
            require(report['parity']['status'] == 'passed', 'Reference numerical parity failed')
        require(sha(station / 'station-inventory.json') == report['station_inventory_sha256'],
                'Station inventory changed during probe')
        verify_station(station)
        report['status'] = 'passed'
    except subprocess.TimeoutExpired:
        report['error'] = 'Runtime worker timed out'
        report['worker_timed_out'] = True
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        report['error'] = str(exc)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False); stream.write('\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--station', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--iterations', type=int, default=3)
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        try:
            require(1 <= args.iterations <= 1000, 'Invalid worker iterations')
            value = worker(args.station.resolve(), args.iterations)
            print(json.dumps(value, allow_nan=False)); return 0
        except Exception as exc:
            print(json.dumps({'status': 'failed', 'error': str(exc)}, allow_nan=False)); return 1
    if args.output is None:
        parser.error('--output is required outside worker mode')
    try:
        report = run_probe(args.station, args.output, args.reference, args.iterations, args.timeout)
    except (OSError, ValueError) as exc:
        parser.exit(1, json.dumps({'status': 'failed', 'error': str(exc)}) + '\n')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ('worker', 'worker_stderr_tail', 'worker_stdout_tail')}, indent=2, allow_nan=False))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
