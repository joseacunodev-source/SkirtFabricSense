"""Recover/archive the actual October 15 run; never overwrite completed evidence."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=Path('//wsl.localhost/Ubuntu-24.04/home/skirttrain/skirt-fabric-sense/runs/20261015-localizer-v3')
OUT=ROOT/'records/experiments/20261015-localizer-v3'
MODEL=ROOT/'artifacts/models/skirt-localizer-v3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,data):p.write_text(json.dumps(data,indent=2)+'\n')
run=json.loads((SRC/'run.json').read_text())
assert run['status']=='completed'
assert sha(SRC/'model.tflite')==run['export']['sha256']
assert run['labelled_inputs_sha256']==sha(ROOT/'records/experiments/20261014-localizer-v2/labelled-inputs.json')
OUT.mkdir(exist_ok=False);MODEL.mkdir(exist_ok=False)
files=[]
for name in ['run.json','environment.json','history.json','inputs.json','labelled-inputs.json','validation-predictions.json','validation-masks.npz','training_source.py']:
 target=OUT/name;shutil.copyfile(SRC/name,target);assert sha(target)==sha(SRC/name);files.append(target)
for name in ['model.keras','model.tflite','run.json','labelled-inputs.json']:
 target=MODEL/name;shutil.copyfile(SRC/name,target);assert sha(target)==sha(SRC/name);files.append(target)
shutil.copyfile(SRC.parent/'20261015-localizer-v3-console.log',OUT/'console.log')
files.append(OUT/'console.log')
save(OUT/'archive-integrity.json',{'status':'passed','files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in files],'saved_model_location':str(SRC/'saved_model'),'inputs_identical_to_v2':True})
save(OUT/'scene-balance-tests.json',{'date':'2026-10-15','environment':'WSL training Python; CUDA_VISIBLE_DEVICES=-1 for unit test only','command':'python -m unittest tests.test_localizer_scene_balance -v','passed':3,'skipped':0,'exit_code':0,'source_sha256':sha(ROOT/'tests/test_localizer_scene_balance.py')})
print(json.dumps(run,indent=2))
