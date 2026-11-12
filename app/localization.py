"""Experimental full-frame mask localization. Not a calibrated presence detector."""
import hashlib,json,threading
from pathlib import Path
import numpy as np
from PIL import Image
from app.inference import _load_runtime

LOCALIZER_PREPROCESSING = 'RGB full source resized bilinear224; source all-skirt polygon masks nearest56; model normalization inside'


def decode_mask(mask,width,height,threshold=.5,min_pixels=9):
    mask=np.asarray(mask)
    if mask.shape!=(56,56) or not np.isfinite(mask).all() or (mask<0).any() or (mask>1).any():
        raise ValueError('Expected finite 56x56 probabilities in [0,1]')
    if type(width) is not int or type(height) is not int or width<1 or height<1:
        raise ValueError('Positive source dimensions required')
    if not 0<threshold<1 or type(min_pixels) is not int or min_pixels<1:
        raise ValueError('Invalid decoder configuration')
    pixels=mask>=threshold;visited=np.zeros_like(pixels);components=[]
    for y,x in zip(*np.where(pixels)):
        if visited[y,x]:continue
        stack=[(int(y),int(x))];visited[y,x]=True;component=[]
        while stack:
            cy,cx=stack.pop();component.append((cy,cx))
            for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
                ny,nx=cy+dy,cx+dx
                if 0<=ny<56 and 0<=nx<56 and pixels[ny,nx] and not visited[ny,nx]:
                    visited[ny,nx]=True;stack.append((ny,nx))
        if len(component)>=min_pixels:components.append(component)
    if len(components)!=1:
        return {'status':'unavailable','roi':None,'reason':'no_supported_skirt_region' if not components else 'multiple_regions'}
    ys,xs=zip(*components[0]);x0,x1=min(xs),max(xs)+1;y0,y1=min(ys),max(ys)+1
    if x0==0 or y0==0 or x1==56 or y1==56:
        return {'status':'unavailable','roi':None,'reason':'region_touches_frame_edge'}
    roi=[int(x0*width/56),int(y0*height/56),int(np.ceil(x1*width/56)),int(np.ceil(y1*height/56))]
    return {'status':'provisional','roi':roi,'reason':'experimental_mask_not_verified_presence_or_full_view',
            'mask_pixels':len(components[0]),'threshold':threshold}


class SkirtLocalizer:
    def __init__(self,run_dir):
        root=Path(run_dir);record=json.loads((root/'run.json').read_text())
        model=root/'model.tflite'
        if record.get('status')!='completed' or hashlib.sha256(model.read_bytes()).hexdigest()!=record['export']['sha256']:
            raise ValueError('Incomplete or changed localization model')
        if (record.get('preprocessing')!=LOCALIZER_PREPROCESSING
                or type(record.get('threshold')) not in (int,float)
                or record['threshold']!=.5):
            raise ValueError('Localizer preprocessing or threshold contract mismatch')
        cls,self.runtime=_load_runtime();self.interpreter=cls(model_path=str(model),num_threads=2);self.interpreter.allocate_tensors()
        inputs=self.interpreter.get_input_details();outputs=self.interpreter.get_output_details()
        if len(inputs)!=1 or len(outputs)!=1:
            raise ValueError('Localizer tensor contract mismatch: expected one input and one output')
        self.input=inputs[0];self.output=outputs[0]
        if list(self.input['shape'])!=[1,224,224,3] or list(self.output['shape'])!=[1,56,56,1] or self.input['dtype']!=np.float32 or self.output['dtype']!=np.float32:
            raise ValueError('Localizer tensor contract mismatch')
        self.sha256=record['export']['sha256'];self.lock=threading.Lock()

    def locate(self,image):
        values=np.asarray(image.convert('RGB').resize((224,224),Image.Resampling.BILINEAR),dtype=np.float32)[None]
        with self.lock:
            self.interpreter.set_tensor(self.input['index'],values);self.interpreter.invoke()
            mask=self.interpreter.get_tensor(self.output['index'])[0,:,:,0].copy()
        return {**decode_mask(mask,image.width,image.height),'model_sha256':self.sha256}


class AutomaticPredictor:
    """Manual analysis and experimental automatic localization share one worker."""
    def __init__(self,pleating,localizer=None,presence=None,geometry_provider=None,calibration_profile=None,pose=None,fabric=None):
        self.pleating=pleating;self.localizer=localizer;self.presence=presence
        self.geometry_provider=geometry_provider;self.calibration_profile=calibration_profile
        self.pose=pose
        self.fabric=fabric

    def predict(self,image,roi=None,full_skirt_confirmed=False):
        options=roi if isinstance(roi,dict) else None
        if options is None:return self.pleating.predict(image,roi,full_skirt_confirmed)
        result={'style':{'status':'unavailable','label':None,'score':None,'reason':'Automatic localizer is not enabled.'},
                'fabric':{'status':'unavailable','reason':'No verified fabric model is installed.'} if options['fabric_enabled'] else {'status':'disabled','reason':'Fabric recognition is off.'},
                'length':{'status':'unavailable','reason':'Calibrated body reference and hem geometry are required.'},
                'metadata':{'presentation':options['presentation'],'automatic':True,'experimental':True,'pi_verified':False}}
        if self.pose is not None and options['presentation']=='worn':
            try:
                result['metadata']['wearer_pose']=self.pose.detect(image,options.get('source_frame_id'))
            except Exception:
                result['metadata']['wearer_pose']={'status':'unavailable','reason':'pose_provider_failed','geometry_eligible':False}
        if self.localizer is None:return result
        if self.presence is not None:
            check=self.presence.check(image);result['metadata']['presence']=check
            if not check['accepted']:
                result['style']['reason']='Skirt presence not supported by the experimental gate.'
                return result
        region=self.localizer.locate(image);result['metadata']['localization']=region
        if region['status']!='provisional':result['style']['reason']=region['reason'];return result
        predicted=self.pleating.predict(image,tuple(region['roi']),True)
        result['style']={**predicted['style'],'reason':'Experimental automatic ROI; full-skirt validity and empty-scene rejection are unverified.'}
        result['metadata']['pleating_model_sha256']=predicted['metadata']['model_sha256']
        result['metadata']['roi_xyxy']=predicted['metadata']['roi_xyxy']
        if self.fabric is not None and options['fabric_enabled']:
            try:
                result['fabric']=self.fabric.predict(image,tuple(region['roi']))
                result['fabric']['source_frame_id']=options.get('source_frame_id')
            except Exception:
                result['fabric']={'status':'unavailable','reason':'experimental_fabric_provider_failed'}
        if self.calibration_profile is not None:
            from app.geometry import estimate_hemline
            # Only an independently implemented provider may supply quality and
            # reference evidence. A mask box alone never manufactures landmarks.
            try:
                evidence=self.geometry_provider(image,region,options) if self.geometry_provider else None
            except Exception:
                # Geometry is independent of pleating. An extractor failure must
                # abstain for length without discarding an otherwise usable ROI.
                result['length']={'status':'unavailable','label':None,'score':None,
                                  'reason':'geometry_provider_failed'}
                return result
            result['length']=estimate_hemline(frame_id=options.get('source_frame_id'),
                camera_config_id=options.get('camera_config_id'),frame_size=image.size,
                mode=options['presentation'],evidence=evidence,profile=self.calibration_profile)
        return result
