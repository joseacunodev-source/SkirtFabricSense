"""Loopback research application with browser camera and saved-image inputs."""
import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import threading
import time
import uuid
from urllib.parse import urlparse, parse_qs

MAX_BODY=16*1024*1024


def make_handler(root, predictor, review_store, pipeline=None):
    inference_lock=threading.Lock()
    job_lock=threading.Lock()
    current_job={}
    class Handler(BaseHTTPRequestHandler):
        def reject_before_body(self, status, message):
            # Consume only a bounded, unambiguously framed body before closing.
            # Closing a Windows socket with unread input can reset the connection
            # before the client receives the rejection. Never decode rejected data.
            lengths=self.headers.get_all('Content-Length',[])
            try:size=int(lengths[0]) if len(lengths)==1 else -1
            except ValueError:size=-1
            if not self.headers.get('Transfer-Encoding') and 0<size<=MAX_BODY:
                timeout=self.connection.gettimeout()
                deadline=time.monotonic()+2
                try:
                    while size:
                        remaining=deadline-time.monotonic()
                        if remaining<=0:break
                        self.connection.settimeout(remaining)
                        chunk=self.rfile.read1(min(size,65536))
                        if not chunk:break
                        size-=len(chunk)
                except (OSError,TimeoutError):
                    pass
                finally:self.connection.settimeout(timeout)
            self.close_connection=True
            return self.send(status,{'error':message})

        def send(self, status, data, content_type='application/json'):
            body=json.dumps(data,allow_nan=False).encode() if content_type=='application/json' else data
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url=urlparse(self.path)
            try:
                if url.path in ['/', '/review', '/analysis']:
                    name={'/':'index.html','/review':'review.html','/analysis':'analysis.html'}[url.path]
                    self.send(200,(root/'app/static'/name).read_bytes(),'text/html; charset=utf-8')
                elif url.path=='/api/status':
                    self.send(200,{'status':'ready','mode':'camera_research',
                        'camera_enabled':False,'camera_capture':'browser_opt_in',
                        'server_camera_capture':False,'automatic_results':'experimental_or_unavailable'})
                elif url.path=='/api/jobs':
                    if pipeline is None:return self.send(503,{'error':'Worker unavailable'})
                    with job_lock:
                        if parse_qs(url.query).get('id',[''])[0]!=current_job.get('id'):
                            return self.send(409,{'error':'Job superseded or unknown'})
                        state=pipeline.snapshot()
                        result=state['result']
                        if result and result['frame_id']==current_job['frame_id']:
                            response={'state':'complete','result':result['prediction']}
                        elif current_job.get('cancelled'):
                            response={'state':'cancelled'}
                        elif current_job['frame_id'] in (state['active_frame_id'],state['pending_frame_id']):
                            response={'state':'pending'}
                        else:response={'state':'unavailable','reason':state['reason']}
                    self.send(200,response)
                elif url.path=='/api/review':
                    if review_store is None:return self.send(503,{'error':'Label review requires the original project dataset; analysis remains available.'})
                    self.send(200,review_store.queue())
                elif url.path=='/api/review/image':
                    if review_store is None:return self.send(503,{'error':'Label review dataset unavailable'})
                    path=review_store.image_path(parse_qs(url.query).get('id',[''])[0])
                    self.send(200,path.read_bytes(),'image/jpeg')
                else:self.send(404,{'error':'Not found'})
            except (ValueError, KeyError, FileNotFoundError) as exc:
                self.send(400,{'error':str(exc)})

        def do_POST(self):
            # Prevent another website from sending browser-origin mutations to localhost.
            origin=self.headers.get('Origin')
            if origin and origin not in [f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']:
                return self.reject_before_body(403,'Cross-origin request refused')
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                return self.reject_before_body(415,'Use application/json')
            try:
                size=int(self.headers.get('Content-Length','0'))
                if size<1 or size>MAX_BODY:return self.send(413,{'error':'Request size unsupported'})
                payload=json.loads(self.rfile.read(size))
                if not isinstance(payload,dict):raise ValueError('Expected JSON object')
                if self.path=='/api/review':
                    if review_store is None:return self.send(503,{'error':'Label review dataset unavailable'})
                    return self.send(200,review_store.save(payload))
                if self.path=='/api/jobs/cancel':
                    if pipeline is None:return self.send(503,{'error':'Worker unavailable'})
                    with job_lock:
                        if payload.get('id')==current_job.get('id') and current_job:
                            pipeline.invalidate('selection_changed')
                            current_job['cancelled']=True
                    return self.send(200,{'status':'invalidated_if_current'})
                if self.path not in ('/api/analyze','/api/jobs','/api/live'):return self.send(404,{'error':'Not found'})
                if self.path=='/api/analyze' and pipeline is not None:
                    return self.send(410,{'error':'Use POST /api/jobs and poll GET /api/jobs?id=...'})
                from PIL import Image, ImageOps
                raw=base64.b64decode(payload['image_base64'],validate=True)
                with Image.open(io.BytesIO(raw)) as opened:
                    if opened.width*opened.height>20_000_000:raise ValueError('Image exceeds 20 megapixels')
                    image=ImageOps.exif_transpose(opened).convert('RGB')
                live=self.path=='/api/live'
                if live:
                    if type(payload.get('fabric_enabled')) is not bool:raise ValueError('Fabric setting must be boolean')
                    if payload.get('presentation') not in ('worn','hanging','mannequin','held'):raise ValueError('Unsupported presentation')
                elif type(payload.get('full_skirt_confirmed')) is not bool:raise ValueError('Framing confirmation must be boolean')
                roi=payload.get('roi')
                if roi is not None and (not isinstance(roi,list) or len(roi)!=4 or any(type(n) is not int for n in roi)):
                    raise ValueError('ROI must contain four integer coordinates')
                if self.path in ('/api/jobs','/api/live'):
                    if pipeline is None:return self.send(503,{'error':'Worker unavailable'})
                    with job_lock:
                        options={'fabric_enabled':payload['fabric_enabled'],'presentation':payload['presentation'],
                                 'source_frame_id':uuid.uuid4().hex,'camera_config_id':None} if live else roi
                        submitted=pipeline.submit(image,roi=options,valid=True,
                            full_skirt_confirmed=False if live else payload['full_skirt_confirmed'],scene_changed=True)
                        if not submitted['accepted']:raise ValueError('Frame not accepted')
                        current_job.clear()
                        current_job.update(id=uuid.uuid4().hex,frame_id=submitted['frame_id'])
                        response=dict(current_job)
                    return self.send(202,response)
                if not inference_lock.acquire(blocking=False):return self.send(409,{'error':'Inference busy; retry shortly'})
                try:
                    result=predictor.predict(image,tuple(roi) if roi else None,payload['full_skirt_confirmed'])
                finally:inference_lock.release()
                self.send(200,result)
            except Exception as exc:
                self.send(400,{'error':str(exc)})

        def log_message(self, format, *args):
            print('%s %s'%(self.address_string(),format%args),flush=True)
    return Handler


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--port',type=int,default=8765)
    p.add_argument('--experimental-localizer',type=Path,help='Opt-in research run directory; empty-scene rejection is unverified')
    p.add_argument('--no-review',action='store_true',help='Skip loading the original label-review dataset for camera sessions')
    p.add_argument('--experimental-presence',type=Path,help='Optional exported development presence gate; requires localizer')
    p.add_argument('--experimental-pose',type=Path,help='Optional MoveNet candidate model directory; does not enable calibrated length')
    p.add_argument('--experimental-fabric',type=Path,help='Opt-in four-class appearance smoke; unapproved for demonstration claims')
    p.add_argument('--calibration-profile',type=Path,help='Validate/load a reference profile; a geometry provider is still required')
    a=p.parse_args()
    if a.experimental_presence and not a.experimental_localizer:p.error('Presence gate requires --experimental-localizer')
    if a.experimental_fabric and not a.experimental_localizer:p.error('Fabric smoke requires --experimental-localizer')
    from app.inference import SkirtPredictor
    from app.review import ReviewStore
    from app.pipeline import ImagePipeline
    from app.localization import AutomaticPredictor, SkirtLocalizer
    from app.presence import PresenceGate
    from app.pose import PoseCandidates
    from app.fabric import FabricSmokePredictor
    from app.geometry import validate_profile
    profile=json.loads(a.calibration_profile.read_text()) if a.calibration_profile else None
    if profile is not None and validate_profile(profile):p.error('Invalid calibration profile: '+', '.join(validate_profile(profile)))
    predictor=SkirtPredictor(a.bundle)
    review_store=ReviewStore(a.root) if not a.no_review and (a.root/'data/manifests/skirt_candidates.jsonl').exists() else None
    automatic=AutomaticPredictor(predictor,SkirtLocalizer(a.experimental_localizer) if a.experimental_localizer else None,
        presence=PresenceGate(a.experimental_presence) if a.experimental_presence else None,calibration_profile=profile,
        pose=PoseCandidates(a.experimental_pose) if a.experimental_pose else None,
        fabric=FabricSmokePredictor(a.experimental_fabric) if a.experimental_fabric else None)
    pipeline=ImagePipeline(automatic,max_frame_age=30,max_result_age=30)
    server=ThreadingHTTPServer(('127.0.0.1',a.port),make_handler(a.root,predictor,review_store,pipeline))
    print(f'SkirtFabricSense camera workspace: http://127.0.0.1:{a.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        server.server_close()
        if not pipeline.close(5):print('Inference worker still busy at shutdown',flush=True)


if __name__=='__main__':main()
