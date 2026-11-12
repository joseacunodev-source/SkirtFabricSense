"""Frozen-split full-frame skirt mask pilot; no camera or protected-test use."""
import argparse,hashlib,json,shutil,subprocess,sys,time,traceback
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.training.train_skirt_baseline import validate_rows

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')

def run(out,report,epochs,negative_manifest=None):
 import numpy as np
 from PIL import Image,ImageDraw
 manifest=ROOT/'data/labels/skirt-baseline-v1.jsonl'
 splits=ROOT/'data/manifests/source-skirt-development-splits.json'
 annotations=ROOT/'data/external/fashionpedia_train/instances_attributes_train2020.json'
 rows=[json.loads(x) for x in manifest.read_text().splitlines()]
 assignments={r['sample_id']:r for r in json.loads(splits.read_text())['assignments']}
 validate_rows(rows,assignments)
 report.update(manifest_sha256=sha(manifest),split_sha256=sha(splits),annotations_sha256=sha(annotations))
 if negative_manifest is not None:
  from tools.training.train_presence import validate
  negatives=[json.loads(line) for line in negative_manifest.read_text().splitlines() if line.strip()]
  negatives=[r for r in negatives if r.get('training_eligibility',{}).get('approved') is True]
  validate([{**r,'presence_target':1} for r in rows]+[{**r,'presence_target':0} for r in negatives])
  rows+=negatives
  report['negative_manifest']={'path':str(negative_manifest),'sha256':sha(negative_manifest)}
 selected_ids={int(r['source_item_id']) for r in rows}
 by_id={i:[] for i in selected_ids}
 data=json.loads(annotations.read_text())
 for a in data['annotations']:
  if a['image_id'] in by_id and a['category_id']==8:by_id[a['image_id']].append(a)
 del data
 x,y,part,ids=[],[],[],[]
 for r in rows:
  path=ROOT/r['original_path'];assert sha(path)==r['sha256']
  with Image.open(path) as im:
   image=im.convert('RGB');mask=Image.new('L',image.size);draw=ImageDraw.Draw(mask)
   if r.get('label')=='no_skirt' and by_id[int(r['source_item_id'])]:raise ValueError('Negative has source skirt annotation')
   for a in by_id[int(r['source_item_id'])]:
    if not isinstance(a['segmentation'],list):raise ValueError('Unsupported RLE mask; do not silently skip')
    for polygon in a['segmentation']:
     if len(polygon)>=6:draw.polygon(list(zip(polygon[::2],polygon[1::2])),fill=255)
   x.append(np.asarray(image.resize((224,224),Image.Resampling.BILINEAR),dtype=np.uint8))
   y.append(np.asarray(mask.resize((56,56),Image.Resampling.NEAREST),dtype=np.float32)[...,None]/255)
  part.append(r['split']);ids.append(r['sample_id'])
 x=np.stack(x);y=np.stack(y);train=np.array([i for i,s in enumerate(part) if s=='development_train']);val=np.array([i for i,s in enumerate(part) if s=='development_validation'])
 positive=np.array([r.get('label')!='no_skirt' for r in rows])
 assert sum(positive[train])==292 and sum(positive[val])==80
 save(out/'inputs.json',{'samples':[{'sample_id':r['sample_id'],'image_sha256':r['sha256'],'split':r['split'],'group_hash':r['group_hash'],'annotation_ids':[a['id'] for a in by_id[int(r['source_item_id'])]]} for r in rows]})
 save(out/'labelled-inputs.json',rows)
 report['labelled_inputs_sha256']=sha(out/'labelled-inputs.json')
 import tensorflow as tf
 gpus=tf.config.list_physical_devices('GPU')
 if not gpus:raise RuntimeError('GPU required')
 for gpu in gpus:tf.config.experimental.set_memory_growth(gpu,True)
 tf.config.experimental.enable_tensor_float_32_execution(False);tf.keras.utils.set_random_seed(42)
 base=tf.keras.applications.MobileNetV2(include_top=False,weights='imagenet',input_shape=(224,224,3))
 feature=tf.keras.Model(base.input,base.get_layer('block_13_expand_relu').output);feature.trainable=False
 inp=tf.keras.Input((224,224,3),name='rgb')
 z=tf.keras.layers.Rescaling(1/127.5,offset=-1)(inp)
 z=feature(z,training=False)
 z=tf.keras.layers.Conv2D(32,3,padding='same',activation='relu')(z)
 z=tf.keras.layers.UpSampling2D(4,interpolation='bilinear')(z)
 pred=tf.keras.layers.Conv2D(1,1,activation='sigmoid',name='skirt_mask')(z)
 model=tf.keras.Model(inp,pred)
 def loss(actual,predicted):
  b=tf.keras.backend.binary_crossentropy(actual,predicted)
  return tf.reduce_mean(b*(1+4*actual))
 model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),loss=loss)
 report.update(architecture='Frozen ImageNet MobileNetV2 block13 feature14 + Conv32 3x3 + bilinear4x + Conv1 sigmoid56',seed=42,epochs=epochs,batch_size=8,optimizer='Adam',learning_rate=.001,loss='BCE with positive pixels weight5; negative weight1',preprocessing='RGB full source resized bilinear224; source all-skirt polygon masks nearest56; model normalization inside',gpu=[str(g) for g in gpus],train_images=292,validation_images=80,selection='minimum validation weighted BCE',threshold=.5,versions={'tensorflow':tf.__version__,'numpy':np.__version__},initial_weights_provenance='records/acquisitions/2026-10-04-mobilenetv2-weights.json')
 report.update(train_images=len(train),validation_images=len(val),negative_train_images=int(sum(~positive[train])),negative_validation_images=int(sum(~positive[val])))
 if negative_manifest is not None:report['selection']='Minimum equal-weight positive/negative validation weighted BCE; fixed mask threshold0.5'
 rng=np.random.default_rng(42);best=float('inf');history=[];start=time.monotonic()
 def predict(indices):return np.concatenate([model(x[indices[i:i+8]].astype('float32'),training=False).numpy() for i in range(0,len(indices),8)])
 for epoch in range(epochs):
  order=rng.permutation(train)
  for j in range(0,len(order),8):
   batch=order[j:j+8];bx=x[batch].astype('float32');by=y[batch].copy();flip=rng.random(len(batch))<.5;bx[flip]=bx[flip,:,::-1,:];by[flip]=by[flip,:,::-1,:];model.train_on_batch(bx,by)
  prob=predict(val)
  value=float(loss(y[val],prob).numpy()) if negative_manifest is None else float((loss(y[val][positive[val]],prob[positive[val]])+loss(y[val][~positive[val]],prob[~positive[val]]))/2)
  binary=prob>=.5;truth=y[val]>=.5
  inter=(binary&truth).sum((1,2,3));union=(binary|truth).sum((1,2,3));iou=inter/np.maximum(union,1)
  item={'epoch':epoch+1,'validation_loss':value,'mean_positive_mask_iou':float(iou[positive[val]].mean())};history.append(item);print(json.dumps(item),flush=True);save(out/'history.json',history)
  if value<best:best=value;model.save_weights(out/'best.weights.h5');report['selected_epoch']=epoch+1
 model.load_weights(out/'best.weights.h5');prob=predict(val);binary=prob>=.5;truth=y[val]>=.5;iou=(binary&truth).sum((1,2,3))/np.maximum((binary|truth).sum((1,2,3)),1)
 report['metrics']={'mean_mask_iou':float(iou[positive[val]].mean()),'median_mask_iou':float(np.median(iou[positive[val]])),'mask_iou_at_least_point5':float(np.mean(iou[positive[val]]>=.5))}
 save(out/'validation-predictions.json',[{'sample_id':ids[index],'mask_iou':float(i),'positive_grid_pixels':int(b.sum())} for index,i,b in zip(val,iou,binary)])
 np.savez_compressed(out/'validation-masks.npz',probabilities=prob,truth=y[val],sample_ids=np.array([ids[i] for i in val]))
 model.save(out/'model.keras');model.export(str(out/'saved_model'),input_signature=[tf.TensorSpec([1,224,224,3],tf.float32)])
 converter=tf.lite.TFLiteConverter.from_saved_model(str(out/'saved_model'));converter.target_spec.supported_ops=[tf.lite.OpsSet.TFLITE_BUILTINS];blob=converter.convert();(out/'model.tflite').write_bytes(blob)
 interpreter=tf.lite.Interpreter(model_content=blob,num_threads=2);interpreter.allocate_tensors();exported=[]
 for index in val:
  interpreter.set_tensor(interpreter.get_input_details()[0]['index'],x[index:index+1].astype('float32'));interpreter.invoke();exported.append(interpreter.get_tensor(interpreter.get_output_details()[0]['index'])[0])
 delta=float(np.abs(np.stack(exported)-prob).max());report['export']={'sha256':sha(out/'model.tflite'),'bytes':len(blob),'maximum_absolute_error':delta,'tolerance':.001,'pi_verified':False}
 if delta>.001:raise RuntimeError('Export parity failed')
 report['duration_seconds']=time.monotonic()-start;report['status']='completed'

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--epochs',type=int,default=10);p.add_argument('--negative-manifest',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 report={'status':'started','started_at':datetime.now(timezone.utc).isoformat(),'source_sha256':sha(__file__),'limitations':['Development images all contain skirts; no image-level negative validation','Physical garment grouping and agent appearance confirmation unresolved','No camera, body landmarks, length, fabric or Pi verification','Localization candidate, not deployment-approved']}
 if a.negative_manifest:report['limitations'][0]='Agent-reviewed development negatives; no independent final camera-domain test'
 shutil.copyfile(__file__,a.output/'training_source.py')
 try:
  subprocess.run([sys.executable,str(ROOT/'tools/collect_environment.py'),'--role','training-wsl-localization','--output',str(a.output/'environment.json')],check=True)
  run(a.output,report,a.epochs,a.negative_manifest)
 except Exception as exc:report.update(status='failed',error=str(exc),traceback=traceback.format_exc())
 report['finished_at']=datetime.now(timezone.utc).isoformat();save(a.output/'run.json',report);print(json.dumps(report),flush=True)
 return 0 if report['status']=='completed' else 1
if __name__=='__main__':raise SystemExit(main())
