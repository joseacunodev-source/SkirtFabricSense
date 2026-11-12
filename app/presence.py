"""Optional experimental binary presence gate; no physical-frame validity claim."""
import hashlib
import json
from pathlib import Path
import threading
import numpy as np
from PIL import Image
from app.inference import _load_runtime

class PresenceGate:
    def __init__(self, root):
        root=Path(root);record=json.loads((root/'run.json').read_text());model=root/'model.tflite'
        if record.get('status')!='completed' or hashlib.sha256(model.read_bytes()).hexdigest()!=record['export']['sha256']:
            raise ValueError('Incomplete or changed presence model')
        if record.get('preprocessing')!='Full RGB resize224 Pillow bilinear; float32 0..255; normalization inside model' or record.get('threshold')!=.5:
            raise ValueError('Unsupported presence preprocessing or threshold')
        runtime,self.runtime=_load_runtime();self.interpreter=runtime(model_path=str(model),num_threads=2);self.interpreter.allocate_tensors()
        inputs=self.interpreter.get_input_details();outputs=self.interpreter.get_output_details()
        if len(inputs)!=1 or len(outputs)!=1:raise ValueError('Presence tensor count mismatch')
        self.input=inputs[0];self.output=outputs[0]
        if (list(self.input['shape'])!=[1,224,224,3] or list(self.output['shape'])!=[1,1]
                or self.input['dtype']!=np.float32 or self.output['dtype']!=np.float32):
            raise ValueError('Presence tensor contract mismatch')
        self.sha256=record['export']['sha256'];self.lock=threading.Lock()

    def check(self,image):
        values=np.asarray(image.convert('RGB').resize((224,224),Image.Resampling.BILINEAR),dtype=np.float32)[None]
        with self.lock:
            self.interpreter.set_tensor(self.input['index'],values);self.interpreter.invoke()
            score=float(self.interpreter.get_tensor(self.output['index'])[0,0])
        if not np.isfinite(score) or not 0<=score<=1:raise ValueError('Invalid presence probability')
        return {'accepted':score>=.5,'score':score,'threshold':.5,'model_sha256':self.sha256,
                'reason':'experimental_presence_score_not_calibrated_or_full_view_validation'}
