"""Local pleating inference for explicit, user-confirmed skirt regions.

This module does not detect skirts or establish fabric, length, or calibrated
confidence. Loading a bundle verifies its contents before loading a runtime.
"""
import hashlib
import importlib
import json
import math
from pathlib import Path, PurePosixPath
import threading

from PIL import Image, ImageOps


PREPROCESSING = ('Source annotated bbox plus 5% each side; RGB Pillow bilinear '
                 'letterbox224; padding128; model Rescaling(1/127.5,offset=-1) exactly once')
LABELS = ['non_pleated', 'pleated']


def prepare_image(image, roi=None):
    """Return padded RGB PIL input and actual source crop, without normalization."""
    if not isinstance(image, Image.Image) or image.width < 1 or image.height < 1:
        raise ValueError('A nonempty PIL image is required')
    if roi is None:
        roi = (0, 0, image.width, image.height)
    if (len(roi) != 4 or any(isinstance(v, bool) or not isinstance(v, (int, float))
                            or not math.isfinite(v) for v in roi)):
        raise ValueError('ROI must contain four finite pixel coordinates')
    x0, y0, x1, y1 = roi
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(image.width, x1), min(image.height, y1)
    if x1 <= x0 or y1 <= y0:
        raise ValueError('ROI does not contain a positive image region')
    width, height = x1-x0, y1-y0
    box = (max(0, math.floor(x0-width*.05)), max(0, math.floor(y0-height*.05)),
           min(image.width, math.ceil(x1+width*.05)), min(image.height, math.ceil(y1+height*.05)))
    crop = image.convert('RGB').crop(box)
    return ImageOps.pad(crop, (224, 224), method=Image.Resampling.BILINEAR,
                        color=(128, 128, 128)), box


def _load_runtime():
    failures = []
    for module, name in [('ai_edge_litert.interpreter', 'ai_edge_litert'),
                         ('tflite_runtime.interpreter', 'tflite_runtime'),
                         ('tensorflow', 'tensorflow.lite')]:
        try:
            loaded = importlib.import_module(module)
        except ImportError as exc:
            failures.append(f'{name}: {exc}')
            continue
        interpreter = loaded.lite.Interpreter if module == 'tensorflow' else loaded.Interpreter
        return interpreter, name
    raise RuntimeError('No usable LiteRT interpreter is installed. ' + '; '.join(failures))


def _bundle_file(root, relative):
    if not isinstance(relative, str) or '\\' in relative or ':' in relative:
        raise ValueError('Invalid bundle path')
    parts = PurePosixPath(relative)
    if parts.is_absolute() or '..' in parts.parts or not parts.parts:
        raise ValueError('Bundle path escapes its directory')
    result = (root / relative).resolve()
    if not result.is_relative_to(root) or not result.is_file():
        raise ValueError('Missing or unsafe bundle file: ' + relative)
    return result


class SkirtPredictor:
    def __init__(self, bundle_dir: Path):
        root = Path(bundle_dir).resolve()
        manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        if manifest.get('schema_version') != 1 or not isinstance(manifest.get('bundle_id'), str):
            raise ValueError('Unsupported bundle manifest')
        hashes = {}
        for item in manifest.get('files', []):
            relative = item['path']
            if relative in hashes:
                raise ValueError('Duplicate bundle path')
            actual = hashlib.sha256(_bundle_file(root, relative).read_bytes()).hexdigest()
            if actual != item['sha256']:
                raise ValueError('Bundle SHA256 mismatch: ' + relative)
            hashes[relative] = actual
        for required in ['contract', 'model']:
            if manifest.get(required) not in hashes:
                raise ValueError('Unhashed required bundle file: ' + required)
        contract = json.loads(_bundle_file(root, manifest['contract']).read_text(encoding='utf-8'))
        expected_input = dict(shape=[1, 224, 224, 3], dtype='float32', color='RGB', range=[0, 255])
        if contract.get('input') != expected_input:
            raise ValueError('Unsupported model input contract')
        output = contract.get('output', {})
        if (output.get('shape') != [1, 2] or output.get('dtype') != 'float32'
                or output.get('labels') != LABELS or output.get('semantics') != 'uncalibrated softmax scores'
                or contract.get('normalization') != 'Inside model only'
                or contract.get('preprocessing') != PREPROCESSING):
            raise ValueError('Unsupported preprocessing or output contract')
        import numpy as np
        interpreter_class, self.runtime = _load_runtime()
        self.interpreter = interpreter_class(model_path=str(_bundle_file(root, manifest['model'])), num_threads=2)
        self.interpreter.allocate_tensors()
        inputs, outputs = self.interpreter.get_input_details(), self.interpreter.get_output_details()
        if len(inputs) != 1 or len(outputs) != 1:
            raise ValueError('Model must have exactly one input and output')
        for tensor, shape in [(inputs[0], [1, 224, 224, 3]), (outputs[0], [1, 2])]:
            if list(tensor['shape']) != shape or tensor['dtype'] != np.float32:
                raise ValueError('Actual model tensor differs from declared contract')
        self.input_index, self.output_index = inputs[0]['index'], outputs[0]['index']
        self.model_id, self.model_sha256 = manifest['bundle_id'], hashes[manifest['model']]
        self.contract_sha256 = hashes[manifest['contract']]
        self._lock = threading.Lock()

    def predict(self, image: Image.Image, roi=None, full_skirt_confirmed=False):
        prepared, box = prepare_image(image, roi)
        result = dict(
            style=dict(status='unavailable', label=None, score=None,
                       reason='Confirm a complete skirt view; automatic skirt detection is not implemented.'),
            fabric=dict(status='unavailable', reason='No verified fabric model is installed.'),
            length=dict(status='unavailable', reason='Calibrated length measurement is not implemented.'),
            metadata=dict(roi_xyxy=list(box), input_width=image.width, input_height=image.height,
                          model_input_width=224, model_input_height=224, runtime=self.runtime,
                          model_id=self.model_id, model_sha256=self.model_sha256,
                          contract_sha256=self.contract_sha256, full_skirt_confirmed=full_skirt_confirmed is True,
                          roi_source='user_region' if roi is not None else 'full_image',
                          score_semantics='uncalibrated softmax score', pi_verified=False))
        if full_skirt_confirmed is not True:
            return result
        import numpy as np
        values = np.asarray(prepared, dtype=np.float32)[None, ...]
        with self._lock:
            self.interpreter.set_tensor(self.input_index, values)
            self.interpreter.invoke()
            scores = np.array(self.interpreter.get_tensor(self.output_index), copy=True)
        if (scores.shape != (1, 2) or not np.isfinite(scores).all()
                or (scores < 0).any() or (scores > 1).any()
                or not np.isclose(scores.sum(), 1, atol=1e-4)):
            raise ValueError('Model returned invalid softmax scores')
        index = int(scores[0].argmax())
        result['style'] = dict(status='provisional', label=LABELS[index], score=float(scores[0, index]),
                               reason='Agent-labelled web-image pilot; score is uncalibrated and input validity is user-confirmed.')
        return result
