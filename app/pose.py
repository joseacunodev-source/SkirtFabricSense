"""Optional MoveNet landmark candidates; never calibrated anatomical evidence."""
import hashlib
import json
from pathlib import Path
import threading

import numpy as np
from PIL import Image
from app.inference import _load_runtime

NAMES = ('nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
         'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
         'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
         'left_knee', 'right_knee', 'left_ankle', 'right_ankle')
PREPROCESSING = 'RGB Pillow bilinear aspect-fit192 black pad centered; uint8 0..255; inverse recorded resize/pad'


def prepare(image):
    width, height = image.size
    if min(width, height) < 2:
        raise ValueError('Pose source dimensions must be at least two pixels')
    scale = min(192 / width, 192 / height)
    resized = [max(1, round(width * scale)), max(1, round(height * scale))]
    left, top = (192 - resized[0]) // 2, (192 - resized[1]) // 2
    canvas = Image.new('RGB', (192, 192), (0, 0, 0))
    canvas.paste(image.convert('RGB').resize(tuple(resized), Image.Resampling.BILINEAR), (left, top))
    return np.asarray(canvas, dtype=np.uint8)[None], {
        'source_size': [width, height], 'resized_size': resized, 'pad_left_top': [left, top]}


def decode(values, mapping):
    values = np.asarray(values)
    if values.shape != (1, 1, 17, 3) or not np.isfinite(values).all():
        raise ValueError('Invalid pose tensor')
    if (values < 0).any() or (values > 1).any():
        raise ValueError('Pose coordinates/scores outside normalized range')
    width, height = mapping['source_size']
    rw, rh = mapping['resized_size']
    left, top = mapping['pad_left_top']
    result = []
    for name, (y, x, score) in zip(NAMES, values[0, 0]):
        # Invert model normalized image coordinates through actual rounded resize.
        px = (float(x) * 192 - left) * width / rw
        py = (float(y) * 192 - top) * height / rh
        result.append({'name': name, 'x': px, 'y': py, 'score': float(score),
                       'inside_source': 0 <= px < width and 0 <= py < height,
                       'observed': False})
    return result


class PoseCandidates:
    def __init__(self, root):
        root = Path(root)
        record = json.loads((root / 'contract.json').read_text(encoding='utf-8'))
        model = root / 'model.tflite'
        if (record.get('preprocessing') != PREPROCESSING or record.get('model_id') != 'movenet-lightning-f16-v4'
                or hashlib.sha256(model.read_bytes()).hexdigest() != record.get('sha256')):
            raise ValueError('Pose model contract mismatch')
        runtime, self.runtime = _load_runtime()
        self.interpreter = runtime(model_path=str(model), num_threads=2)
        self.interpreter.allocate_tensors()
        inputs, outputs = self.interpreter.get_input_details(), self.interpreter.get_output_details()
        if (len(inputs) != 1 or len(outputs) != 1
                or list(inputs[0]['shape']) != [1, 192, 192, 3] or inputs[0]['dtype'] != np.uint8
                or list(outputs[0]['shape']) != [1, 1, 17, 3] or outputs[0]['dtype'] != np.float32):
            raise ValueError('Pose tensor contract mismatch')
        self.input, self.output = inputs[0], outputs[0]
        self.sha256 = record['sha256']
        self.lock = threading.Lock()

    def detect(self, image, frame_id):
        if not isinstance(frame_id, str) or not frame_id.strip():
            raise ValueError('Source frame identity required')
        values, mapping = prepare(image)
        with self.lock:
            self.interpreter.set_tensor(self.input['index'], values)
            self.interpreter.invoke()
            output = self.interpreter.get_tensor(self.output['index']).copy()
        return {'status': 'provisional_landmark_candidates', 'frame_id': frame_id,
                'model_sha256': self.sha256, 'preprocessing': mapping,
                'landmarks': decode(output, mapping), 'geometry_eligible': False,
                'reason': 'Single-pose candidates; visibility, wearer association, waist and floor contact unverified.'}
