"""Fail-closed GPU training and float TFLite parity smoke test (synthetic data)."""
import argparse
import hashlib
import json
import platform
import time
import traceback
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = {'status': 'started', 'seed': 42, 'data': 'synthetic stateless normal, 4x32x32x3',
              'dataset_manifest': None, 'split_hash': None,
              'purpose': 'infrastructure only; no project accuracy or Pi verification',
              'python': platform.python_version(),
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    try:
        import numpy as np
        import tensorflow as tf
        report['versions'] = {'tensorflow': tf.__version__, 'numpy': np.__version__}
        gpus = tf.config.list_physical_devices('GPU')
        report['gpu_devices'] = [str(g) for g in gpus]
        if not gpus:
            raise RuntimeError('No TensorFlow GPU found; CPU fallback is forbidden')
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        tf.config.set_soft_device_placement(False)
        tf.keras.utils.set_random_seed(42)
        with tf.device('/GPU:0'):
            x = tf.random.stateless_normal([4, 32, 32, 3], seed=[42, 1])
            y = tf.constant([0, 1, 0, 1])
            model = tf.keras.Sequential([
                tf.keras.Input(shape=(32, 32, 3)),
                tf.keras.layers.Conv2D(4, 3, activation='relu'),
                tf.keras.layers.GlobalAveragePooling2D(),
                tf.keras.layers.Dense(2)])
            model(x)
            before = [v.numpy().copy() for v in model.trainable_variables]
            optimizer = tf.keras.optimizers.SGD(learning_rate=0.01)
            started = time.perf_counter()
            with tf.GradientTape() as tape:
                prediction = model(x, training=True)
                loss = tf.reduce_mean(tf.keras.losses.sparse_categorical_crossentropy(y, prediction, from_logits=True))
            gradients = tape.gradient(loss, model.trainable_variables)
            if any(g is None or not np.isfinite(g.numpy()).all() for g in gradients):
                raise RuntimeError('Missing or nonfinite gradient')
            norm = float(tf.linalg.global_norm(gradients).numpy())
            if norm <= 0:
                raise RuntimeError('Zero gradient')
            optimizer.apply_gradients(zip(gradients, model.trainable_variables))
            after = [v.numpy() for v in model.trainable_variables]
            report.update(loss=float(loss.numpy()), gradient_norm=norm,
                          elapsed_training_step_seconds=time.perf_counter() - started,
                          tensor_device=x.device, prediction_device=prediction.device,
                          weights_changed=any(not np.array_equal(a, b) for a, b in zip(before, after)),
                          optimizer={'name': 'SGD', 'learning_rate': 0.01, 'steps': 1})
            if 'GPU:0' not in prediction.device or not report['weights_changed'] or not np.isfinite(report['loss']):
                raise RuntimeError('GPU training verification failed')
            example = x[:1].numpy()
            expected = model(example, training=False).numpy()
        # Export with a fixed batch-one signature and built-in operators only.
        signature = tf.function(lambda value: model(value, training=False),
                                input_signature=[tf.TensorSpec([1, 32, 32, 3], tf.float32)])
        with tf.device('/CPU:0'):
            saved = args.output / 'saved_model'
            model.export(str(saved), format='tf_saved_model',
                         input_signature=[tf.TensorSpec([1, 32, 32, 3], tf.float32)])
            converter = tf.lite.TFLiteConverter.from_saved_model(str(saved))
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
            blob = converter.convert()
            (args.output / 'smoke.tflite').write_bytes(blob)
            interpreter = tf.lite.Interpreter(model_content=blob, num_threads=1)
            interpreter.allocate_tensors()
            interpreter.set_tensor(interpreter.get_input_details()[0]['index'], example)
            interpreter.invoke()
            actual = interpreter.get_tensor(interpreter.get_output_details()[0]['index'])
        finite_outputs = bool(np.isfinite(actual).all() and np.isfinite(expected).all())
        report['export'] = {'sha256': hashlib.sha256(blob).hexdigest(), 'bytes': len(blob),
                            'finite_outputs': finite_outputs,
                            'maximum_absolute_error': float(np.max(np.abs(actual - expected))) if finite_outputs else None,
                            'atol': 1e-5, 'rtol': 1e-4, 'hardware': 'desktop CPU, not Raspberry Pi'}
        if not finite_outputs:
            raise RuntimeError('Nonfinite export output')
        np.testing.assert_allclose(actual, expected, atol=1e-5, rtol=1e-4)
        report['status'] = 'passed'
    except Exception as exc:
        report.update(status='failed', error=str(exc), traceback=traceback.format_exc())
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
