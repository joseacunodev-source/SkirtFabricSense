"""Preserve the completed category experiment before independent export checks."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(r'\\wsl.localhost\Ubuntu-24.04\home\skirttrain\skirt-fabric-sense\runs\20261021-category-presence-v1')
ARCHIVE = ROOT/'records/experiments/20261021-category-presence-v1'
MODELS = ROOT/'artifacts/models/skirt-category-presence-v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    run = json.loads((SOURCE/'run.json').read_text(encoding='utf-8'))
    if run['status'] != 'completed':
        raise ValueError('Training not complete')
    for row in run['executed_sources']:
        if sha(SOURCE/row['path']) != row['sha256']:
            raise ValueError('Executed source changed')
    if (sha(SOURCE/'model.tflite') != run['export']['sha256']
            or sha(SOURCE/'inputs.json') != run['frozen_inputs_sha256']
            or sha(SOURCE/'source-category-targets.json') != run['category_targets_sha256']):
        raise ValueError('Run artifact mismatch')
    if ARCHIVE.exists() or MODELS.exists():
        raise FileExistsError('Archive/model destination exists')
    ARCHIVE.mkdir()
    MODELS.mkdir()
    inventory = []
    def copy(source,target):
        shutil.copyfile(source,target)
        if sha(source) != sha(target):
            raise ValueError('Copy mismatch')
        inventory.append({'path':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'bytes':target.stat().st_size})
    for file in sorted(SOURCE.iterdir()):
        if file.suffix in ('.json','.py'):
            copy(file,ARCHIVE/file.name)
    (ARCHIVE/'early_export').mkdir()
    copy(SOURCE/'early_export/model.tflite',ARCHIVE/'early_export/model.tflite')
    for name in ('model.tflite','model.keras','category-model.keras','run.json'):
        copy(SOURCE/name,MODELS/name)
    copy(ROOT/'tools/check_detection_candidate.py',ARCHIVE/'check_detection_candidate.py')
    record = {'status':'passed','source_run_directory':str(SOURCE),'copied_files':inventory,
              'source_sha256':sha(Path(__file__)),'packages_installed':0,'pi_verified':False,
              'training_command':'wsl -d Ubuntu-24.04 -u skirttrain -- /home/skirttrain/skirt-fabric-sense/.venv-training/bin/python /mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense/tools/training/train_category_presence.py --negative-manifest /mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense/data/labels/negative-reviewed-v3.jsonl --joint-comparison-cache /mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense/records/validation/2026-10-19-detection-v4-comparison.json --output /home/skirttrain/skirt-fabric-sense/runs/20261021-category-presence-v1'}
    with (ROOT/'records/validation/2026-10-21-category-presence-archive.json').open('x',encoding='utf-8') as stream:
        json.dump(record,stream,indent=2); stream.write('\n')
    print(json.dumps({'status':'passed','copied_files':len(inventory)}))


if __name__ == '__main__':
    main()
