"""Strict adapter for the archived four-class fabric appearance smoke only.

No live approval, calibrated confidence, composition or Pi support is implied.
"""
import hashlib
import json
from pathlib import Path
import threading

import numpy as np
from PIL import Image, ImageOps
from app.inference import _load_runtime

LABELS = ['source_cotton_appearance', 'source_denim_appearance',
          'source_leather_appearance', 'source_chiffon_appearance']
MODEL_SHA256 = '81f144a1c7cd4910989374a1a86c85e955fb4f65cd81ef88c26e7cbcf1158bfd'
PREPROCESSING = ('Manual reviewed source-pixel skirt ROI; RGB; PIL bilinear '
                 'aspect-preserving pad224 gray128; float32 0..255; model normalization inside')


def prepare_fabric_image(image, roi):
    """Crop the original frame before resize, exactly as smoke training did."""
    if not isinstance(image, Image.Image) or image.width < 1 or image.height < 1:
        raise ValueError('Nonempty original PIL image required')
    if (not isinstance(roi, (list, tuple)) or len(roi) != 4
            or any(type(value) is not int for value in roi)):
        raise ValueError('ROI must contain four integer source-pixel coordinates')
    x0, y0, x1, y1 = roi
    if not (0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height):
        raise ValueError('ROI must lie within the original frame')
    crop = image.convert('RGB').crop(tuple(roi))
    return ImageOps.pad(crop, (224, 224), method=Image.Resampling.BILINEAR,
                        color=(128, 128, 128))


class FabricSmokePredictor:
    """Explicit research adapter; the default live application does not use it."""
    def __init__(self, model_dir):
        root = Path(model_dir)
        record_bytes = (root / 'run.json').read_bytes()
        record = json.loads(record_bytes)
        model = root / 'model.tflite'
        actual_hash = hashlib.sha256(model.read_bytes()).hexdigest()
        if (record.get('status') != 'completed' or record.get('classes') != LABELS
                or record.get('input_preprocessing') != PREPROCESSING
                or record.get('run_id') != '20261011-fabric-smoke-v1'
                or record.get('export', {}).get('sha256') != MODEL_SHA256
                or actual_hash != MODEL_SHA256
                or record.get('export', {}).get('live_approved') is not False
                or record.get('export', {}).get('pi_verified') is not False):
            raise ValueError('Fabric smoke artifact or preprocessing contract mismatch')
        cls, self.runtime = _load_runtime()
        self.interpreter = cls(model_path=str(model), num_threads=2)
        self.interpreter.allocate_tensors()
        inputs = self.interpreter.get_input_details()
        outputs = self.interpreter.get_output_details()
        if len(inputs) != 1 or len(outputs) != 1:
            raise ValueError('Fabric model requires exactly one input and output')
        for tensor, shape in [(inputs[0], [1, 224, 224, 3]), (outputs[0], [1, 4])]:
            if list(tensor['shape']) != shape or tensor['dtype'] != np.float32:
                raise ValueError('Fabric model tensor contract mismatch')
        self.input_index, self.output_index = inputs[0]['index'], outputs[0]['index']
        self.model_sha256 = actual_hash
        self.run_sha256 = hashlib.sha256(record_bytes).hexdigest()
        self._lock = threading.Lock()

    def predict(self, original_image, roi):
        prepared = prepare_fabric_image(original_image, roi)
        values = np.asarray(prepared, dtype=np.float32)[None]
        with self._lock:
            self.interpreter.set_tensor(self.input_index, values)
            self.interpreter.invoke()
            scores = np.array(self.interpreter.get_tensor(self.output_index), copy=True)
        if (scores.shape != (1, 4) or not np.isfinite(scores).all()
                or (scores < 0).any() or (scores > 1).any()
                or not np.isclose(scores.sum(), 1, atol=1e-4, rtol=0)):
            raise ValueError('Fabric model returned invalid softmax scores')
        winner = int(scores[0].argmax())
        return dict(status='research_only', label=LABELS[winner], score=float(scores[0, winner]),
                    scores=scores[0].tolist(), labels=list(LABELS),
                    reason='Source appearance smoke only; not verified fiber composition.',
                    score_semantics='uncalibrated softmax score', composition_verified=False,
                    live_approved=False, pi_verified=False, runtime=self.runtime,
                    model_sha256=self.model_sha256, run_sha256=self.run_sha256,
                    roi_xyxy=list(roi), source_frame_size=list(original_image.size),
                    preprocessing='Original source-pixel ROI before bilinear pad224 gray128; no ROI expansion')
