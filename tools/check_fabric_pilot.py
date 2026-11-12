"""Reopen archived fabric smoke models and independently verify desktop parity.

This checks a research artifact only. It provides no app or Pi integration.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.training.train_fabric_pilot import validate


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    import numpy as np
    import tensorflow as tf
    from PIL import Image, ImageOps
    tf.config.set_visible_devices([], 'GPU')
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(2)
    run_dir = ROOT / 'records/experiments/20261011-fabric-smoke-v1'
    model_dir = ROOT / 'artifacts/models/fabric-smoke-v1'
    run = json.loads((run_dir / 'run.json').read_text())
    if run['status'] != 'completed':
        raise ValueError('Incomplete archived run')
    for name, expected in [('inputs.jsonl', run['dataset_manifest_sha256']),
                           ('splits.json', run['split_manifest_sha256']),
                           ('training_source.py', run['source_revision_or_hash_manifest']['training']),
                           ('preparation_source.py', run['source_revision_or_hash_manifest']['preparation'])]:
        if sha(run_dir / name) != expected:
            raise ValueError('Archived source or data changed: ' + name)
    if sha(model_dir / 'model.tflite') != run['export']['sha256']:
        raise ValueError('Export hash mismatch')
    rows = [json.loads(line) for line in (run_dir / 'inputs.jsonl').read_text().splitlines()]
    validate(rows, json.loads((run_dir / 'splits.json').read_text()))
    model = tf.keras.models.load_model(model_dir / 'model.keras', compile=False)
    interpreter = tf.lite.Interpreter(model_path=str(model_dir / 'model.tflite'), num_threads=2)
    interpreter.allocate_tensors()
    input_info = interpreter.get_input_details()[0]
    output_info = interpreter.get_output_details()[0]
    if input_info['shape'].tolist() != [1, 224, 224, 3] or input_info['dtype'] != np.float32:
        raise ValueError('Unexpected input contract')
    if output_info['shape'].tolist() != [1, 4] or output_info['dtype'] != np.float32:
        raise ValueError('Unexpected output contract')
    archived = {r['sample_id']: r for r in json.loads((run_dir / 'validation-predictions.json').read_text())}
    predictions = []
    for row in rows:
        if row['split'] != 'development_validation':
            continue
        path = ROOT / row['original_path']
        if sha(path) != row['sha256']:
            raise ValueError('Changed original')
        with Image.open(path) as image:
            crop = image.convert('RGB').crop(row['roi_xyxy'])
            image = ImageOps.pad(crop, (224, 224), method=Image.Resampling.BILINEAR, color=(128, 128, 128))
            x = np.asarray(image, dtype=np.float32)[None]
        keras = model(x, training=False).numpy()[0]
        interpreter.set_tensor(input_info['index'], x)
        interpreter.invoke()
        lite = interpreter.get_tensor(output_info['index'])[0]
        previous = np.asarray(archived[row['sample_id']]['scores'])
        predictions.append({'sample_id': row['sample_id'], 'label': row['label'],
            'keras_scores': keras.tolist(), 'tflite_scores': lite.tolist(),
            'maximum_absolute_error': float(np.abs(keras - lite).max()),
            'archived_prediction_maximum_absolute_error': float(np.abs(keras - previous).max()),
            'class_agreement': bool(keras.argmax() == lite.argmax()),
            'prediction': run['classes'][int(lite.argmax())]})
    passed = (len(predictions) == 5 and all(p['maximum_absolute_error'] <= .001
        and p['archived_prediction_maximum_absolute_error'] <= .001 and p['class_agreement'] for p in predictions))
    record = {'status': 'passed' if passed else 'failed', 'date': '2026-10-12',
        'verification_source_sha256': sha(__file__), 'device': 'WSL desktop CPU; GPU disabled',
        'tensorflow_version': tf.__version__, 'numpy_version': np.__version__,
        'model_sha256': sha(model_dir / 'model.tflite'),
        'tolerance': .001, 'predictions': predictions, 'pi_verified': False,
        'live_approved': False, 'limitations': 'Five development images; smoke verification only.'}
    args.output.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': record['status'], 'images': len(predictions),
        'maximum_absolute_error': max(p['maximum_absolute_error'] for p in predictions)}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
