"""Create source-bound thesis figures from archived development evidence.

No model execution, training, sampling or dataset changes. Requires existing
ReportLab and pdftoppm. PDF is vector; PNG is 300-dpi rasterized from PDF.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess, sys
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color, white
from reportlab.pdfbase.pdfmetrics import stringWidth

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/thesis_figures'
EVIDENCE=ROOT/'records/validation/2026-10-23-detection-uncertainty.json'
INPUTS=ROOT/'records/experiments/20261021-category-presence-v1/inputs.json'
INK=HexColor('#202b32'); BLUE=HexColor('#165d73'); PALE=HexColor('#e3eef0'); LIGHT=HexColor('#f3f5f4'); ORANGE=HexColor('#a95b26'); GREY=HexColor('#77878d')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def txt(c,x,y,t,size=10,font='Helvetica',color=INK):
 c.setFont(font,size);c.setFillColor(color);c.drawString(x,y,t)
def center(c,x,y,t,size=10,font='Helvetica',color=INK):
 c.setFont(font,size);c.setFillColor(color);c.drawCentredString(x,y,t)
def line(c,x1,y1,x2,y2,color=GREY,width=1):
 c.setStrokeColor(color);c.setLineWidth(width);c.line(x1,y1,x2,y2)
def arrow(c,x1,y1,x2,y2):
 line(c,x1,y1,x2,y2);p=c.beginPath();p.moveTo(x2,y2);p.lineTo(x2-7,y2+3);p.lineTo(x2-7,y2-3);p.close();c.setFillColor(GREY);c.drawPath(p,fill=1,stroke=0)
def rect(c,x,y,w,h,title,lines,fill=LIGHT,stroke=GREY):
 c.setFillColor(fill);c.setStrokeColor(stroke);c.roundRect(x,y,w,h,5,fill=1,stroke=1)
 center(c,x+w/2,y+h-19,title,10,'Helvetica-Bold')
 for j,text in enumerate(lines):center(c,x+w/2,y+h-35-j*13,text,8.6)
def base(name,title,subtitle):
 c=canvas.Canvas(str(OUT/(name+'.pdf')),pagesize=(720,410),pageCompression=1)
 txt(c,28,381,title,16,'Helvetica-Bold');txt(c,28,363,subtitle,9,color=GREY);line(c,28,351,692,351,color=PALE)
 return c
def finish(c,name,converter):
 c.showPage();c.save()
 subprocess.run([converter,'-f','1','-l','1','-singlefile','-png','-r','300',str(OUT/(name+'.pdf')),str(OUT/name)],check=True,timeout=120,capture_output=True)

def robustness_figure():
 source=ROOT/'records/experiments/20261104-image-robustness/results.json'
 evidence=ROOT/'records/validation/2026-11-04-thesis-figures.json'
 source_data=OUT/'source-data.json'
 if (OUT/'05_image_robustness.pdf').exists() or (OUT/'05_image_robustness.png').exists():raise FileExistsError('Robustness figure exists; preserve previous output')
 report=json.loads(source.read_text(encoding='utf-8'))
 if report.get('status')!='completed' or report.get('original_reference_match') is not True:raise ValueError('Completed matched original reference required')
 conditions=['original','brightness_0.8','gaussian_blur_radius_1']; baseline=None
 for name in conditions:
  rows=report['results'][name];counts=report['per_condition'][name]
  ids={r['sample_id'] for r in rows}
  if len(rows)!=118 or len(ids)!=118:raise ValueError('Condition must contain 118 unique original parents')
  if baseline is None:baseline={r['sample_id']:(r['target'],r['truth'],r['image_sha256']) for r in rows}
  if {r['sample_id']:(r['target'],r['truth'],r['image_sha256']) for r in rows}!=baseline:raise ValueError('Condition parent or truth differs')
  calculated={'positive_total':sum(r['target']==1 for r in rows),'positive_accepted':sum(r['target']==1 and r['accepted'] for r in rows),'correct_pleating':sum(r['target']==1 and r['accepted'] and r['prediction']==r['truth'] for r in rows),'negative_total':sum(r['target']==0 for r in rows),'negative_rejected':sum(r['target']==0 and not r['accepted'] for r in rows)}
  if counts!=calculated:raise ValueError('Condition counts disagree with saved predictions')
 converter=shutil.which('pdftoppm')
 if not converter:raise RuntimeError('pdftoppm required')
 c=base('05_image_robustness','Saved-image robustness diagnostic','Same 118 source-domain development parents; synthetic operations only')
 labels=['Original','Brightness × 0.8','Gaussian blur, radius 1 px']; columns=['Skirts accepted','Correct pleating','Negatives rejected'];xs=[270,425,580]
 for x,label in zip(xs,columns):center(c,x,300,label,10,'Helvetica-Bold')
 for i,(name,label) in enumerate(zip(conditions,labels)):
  y=245-i*72;txt(c,35,y+19,label,11,'Helvetica-Bold');v=report['per_condition'][name]
  for x,value,total in zip(xs,[v['positive_accepted'],v['correct_pleating'],v['negative_rejected']],[66,66,52]):
   c.setFillColor(PALE if i==0 else LIGHT);c.rect(x-56,y,112,52,stroke=0,fill=1);center(c,x,y+17,f'{value}/{total}',16,'Helvetica-Bold',BLUE if i==0 else INK)
 txt(c,35,60,'Brightness and blur are synthetic modifications of the same 118 parent images.',9,color=GREY)
 txt(c,35,43,'Reused validation data; no new garments, independent accuracy or model improvement.',9,color=GREY)
 finish(c,'05_image_robustness',converter)
 data=json.loads(source_data.read_text(encoding='utf-8'));data['image_robustness']={'source':{'path':source.relative_to(ROOT).as_posix(),'sha256':sha(source)},'per_condition':report['per_condition'],'same_parent_images':118,'synthetic_modifications':['brightness_0.8','gaussian_blur_radius_1'],'figure_source_code_sha256':sha(Path(__file__)),'new_training':False}
 source_data.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
 audit=json.loads(evidence.read_text(encoding='utf-8'));audit['figures']=5;audit['robustness_source']={'path':source.relative_to(ROOT).as_posix(),'sha256':sha(source)}
 audit['artifacts']=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file()]
 evidence.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':'completed','additional_figure':'05_image_robustness','parents':118}))

def main():
 if OUT.exists() and any(OUT.iterdir()):raise FileExistsError('Output directory not empty; preserve previous output')
 converter=shutil.which('pdftoppm')
 if not converter:raise RuntimeError('pdftoppm required to rasterize vector PDF')
 OUT.mkdir(parents=True,exist_ok=True)
 report=json.loads(EVIDENCE.read_text(encoding='utf-8'))
 assert report['status']=='completed_saved_prediction_analysis'
 assert sha(INPUTS)==report['inputs_sha256']
 inputs=json.loads(INPUTS.read_text(encoding='utf-8'))
 for split,target,expected in [('development_train',1,265),('development_train',0,155),('development_validation',1,66),('development_validation',0,52)]:
  assert sum(r['split']==split and r['presence_target']==target for r in inputs)==expected
 m=report['raw_image_metrics']['candidate']; matrix=m['confusion_matrix']; inv=report['inventory']
 assert (m['positive_count'],m['positive_accepted'],m['correct_pleating'],m['negative_count'],m['negative_rejected'])==(66,44,38,52,42)
 assert sum(matrix['pleated'].values())==17 and sum(matrix['non_pleated'].values())==49
 assert (inv['training_images'],inv['validation_images'])==(420,118)
 c=base('01_system_architecture','Single-frame research system and remaining work','Implementation state is desktop research; Raspberry Pi operation is unverified')
 rect(c,30,230,128,64,'One live camera',['Full-skirt source frame','Browser preview'])
 rect(c,202,230,138,64,'Presence + localization',['Experimental detection','Same-frame skirt region'],PALE,BLUE)
 rect(c,390,247,129,59,'Pleating',['Provisional prediction','Experimental'],PALE,BLUE)
 rect(c,390,166,129,59,'Fabric appearance',['Optional smoke model','Not accepted'],LIGHT,ORANGE)
 rect(c,390,85,129,59,'Hemline length',['References + calibration','Not yet validated'],LIGHT,ORANGE)
 rect(c,562,188,125,112,'Results interface',['Independent states','Fabric toggle','9 length categories','Availability + status'])
 arrow(c,158,262,202,262);line(c,340,262,365,262);line(c,365,262,365,276);arrow(c,365,276,390,276);arrow(c,519,276,562,276)
 # Branches are conceptual; geometry needs independent source-frame evidence.
 line(c,340,257,365,257);line(c,365,257,365,196);arrow(c,365,196,390,196)
 line(c,94,230,94,114);line(c,94,114,383,114);arrow(c,383,114,390,114)
 line(c,519,196,562,196);line(c,519,114,548,114);line(c,548,114,548,188);arrow(c,548,188,562,188)
 txt(c,31,40,'Solid teal = experimental desktop path; orange outline = required work not accepted.',9,color=GREY)
 finish(c,'01_system_architecture',converter)
 c=base('02_detection_results','Detection and pleating on the reused development set','Counts are images, not verified independent garments or live-camera accuracy')
 vals=[('Skirts accepted',m['positive_accepted'],m['positive_count']),('Correct pleating / all skirts',m['correct_pleating'],m['positive_count']),('Non-skirts rejected',m['negative_rejected'],m['negative_count'])]
 for i,(label,n,d) in enumerate(vals):
  y=288-i*73;txt(c,35,y+8,label,11,'Helvetica-Bold');c.setFillColor(LIGHT);c.rect(260,y,345,24,fill=1,stroke=0);c.setFillColor(BLUE);c.rect(260,y,345*n/d,24,fill=1,stroke=0);txt(c,616,y+6,f'{n}/{d}  ({100*n/d:.1f}%)',10,'Helvetica-Bold')
 txt(c,35,67,'Remaining: 22/66 skirt results unavailable; 10/52 negative images falsely accepted.',10,'Helvetica-Bold',ORANGE)
 txt(c,35,48,'Validation groups were reused for model selection. Labels are not independently confirmed.',9,color=GREY)
 finish(c,'02_detection_results',converter)
 c=base('03_pleating_outcomes','Pleating outcomes by provisional reference class','Unavailable predictions remain in the class denominators')
 classes=['pleated','non_pleated'];pred=['pleated','non_pleated','unavailable'];cols=['Predicted pleated','Predicted non-pleated','Unavailable'];xs=[240,385,530]
 for x,t in zip(xs,cols):center(c,x+61,304,t,9,'Helvetica-Bold')
 for i,truth in enumerate(classes):
  y=221-i*75;txt(c,35,y+24,('Pleated (n=17)' if i==0 else 'Non-pleated (n=49)'),11,'Helvetica-Bold')
  for j,p in enumerate(pred):
   value=matrix[truth][p];x=xs[j];c.setFillColor(PALE if j==i else LIGHT);c.setStrokeColor(white);c.rect(x,y,123,58,fill=1,stroke=1);center(c,x+61,y+20,str(value),17,'Helvetica-Bold',BLUE if j==i else INK)
 txt(c,35,75,'Rows: source-reviewed reference class. Columns: model output or unavailable.',9,color=GREY)
 txt(c,35,55,'Repeated development set; these counts do not establish independent generalization.',9,color=GREY)
 finish(c,'03_pleating_outcomes',converter)
 c=base('04_development_split','Frozen development inputs for the detection comparison','Original source partition: Fashionpedia train2020; source groups remain intact')
 rect(c,37,230,160,80,'538 input images',['420 development train','118 development validation'],PALE,BLUE)
 rect(c,280,270,184,65,'Training inputs',['265 worn skirt images','155 non-skirt images'])
 rect(c,280,165,184,65,'Validation inputs',['66 worn skirt images','52 non-skirt images'])
 rect(c,520,205,165,80,'Evaluation conditions',['No locked test in this figure','Groups are source identities','Physical garments unverified'],LIGHT,ORANGE)
 line(c,197,270,236,270);line(c,236,270,236,302);arrow(c,236,302,280,302);line(c,236,270,236,197);arrow(c,236,197,280,197);line(c,464,197,492,197);line(c,492,197,492,245);arrow(c,492,245,520,245)
 txt(c,37,85,'The full 1,932-image collection is broader than this 538-image comparison.',10,'Helvetica-Bold')
 txt(c,37,65,'Splits and review status are frozen development evidence; no final accuracy is implied.',9,color=GREY)
 finish(c,'04_development_split',converter)
 data={'source_report':{'path':EVIDENCE.relative_to(ROOT).as_posix(),'sha256':sha(EVIDENCE)},'frozen_inputs':{'path':INPUTS.relative_to(ROOT).as_posix(),'sha256':sha(INPUTS)},'counts':{'comparison':{k:m[k] for k in ('positive_count','positive_accepted','positive_unavailable','correct_pleating','negative_count','negative_rejected','negative_falsely_accepted')},'confusion_matrix':matrix,'inputs':{'train':420,'validation':118,'train_skirt':265,'train_negative':155,'validation_skirt':66,'validation_negative':52}},'limitations':report['limitations'],'source_code_sha256':sha(Path(__file__)),'python':sys.version,'reportlab_version':__import__('reportlab').Version,'recorded_utc':datetime.now(timezone.utc).isoformat(),'no_training':True,'no_new_inference':True}
 (OUT/'source-data.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
 artifacts=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file()]
 (ROOT/'records/validation/2026-11-04-thesis-figures.json').write_text(json.dumps({'status':'generated','figures':4,'formats':['vector PDF','300 dpi PNG'],'artifacts':artifacts,'source':data['source_report'],'new_training':False},indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'figures':4,'artifacts':len(artifacts),'output':str(OUT)},indent=2))
if __name__=='__main__':
 if sys.argv[1:]==['--robustness-only']:robustness_figure()
 elif not sys.argv[1:]:main()
 else:raise SystemExit('Usage: create_thesis_figures.py [--robustness-only]')
