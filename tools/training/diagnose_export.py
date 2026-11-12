"""Read-only investigation of the first smoke export; not an accuracy experiment."""
import numpy as np
import tensorflow as tf
path = '/home/skirttrain/skirt-fabric-sense/runs/gpu-smoke-001'
example = np.ones((1, 32, 32, 3), dtype=np.float32)
model = tf.saved_model.load(path+'/saved_model')
print('SavedModel', model.signatures['serving_default'](tf.constant(example)))
for resolver in [tf.lite.experimental.OpResolverType.AUTO, tf.lite.experimental.OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES]:
    interpreter = tf.lite.Interpreter(model_path=path+'/smoke.tflite', experimental_op_resolver_type=resolver)
    interpreter.allocate_tensors()
    interpreter.set_tensor(interpreter.get_input_details()[0]['index'], example)
    interpreter.invoke()
    print(resolver, interpreter.get_tensor(interpreter.get_output_details()[0]['index']))
    for item in interpreter.get_tensor_details():
        if item['name'].startswith('arith.constant'):
            value=interpreter.get_tensor(item['index'])
            print(item['name'],value.shape,np.isfinite(value).all(),value.min(),value.max())
