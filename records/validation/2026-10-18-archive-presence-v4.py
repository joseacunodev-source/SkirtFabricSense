"""Archive the completed local WSL run without altering the executed sources."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(r'\\wsl.localhost\Ubuntu-24.04\home\skirttrain\skirt-fabric-sense\runs\20261018-presence-v4')
ARCHIVE = ROOT / 'records/experiments/20261018-presence-v4'
MODELS = ROOT / 'artifacts/models/skirt-presence-v4'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    run = json.loads((SOURCE / 'run.json').read_text(encoding='utf-8'))
    if run['status'] != 'completed':
        raise ValueError('Run not complete')
    if sha(SOURCE / 'inputs.json') != run['frozen_inputs_sha256']:
        raise ValueError('Inputs changed')
    for record in run['executed_sources']:
        if sha(SOURCE / record['path']) != record['sha256']:
            raise ValueError('Executed source changed')
    if sha(SOURCE / 'model.tflite') != run['export']['sha256']:
        raise ValueError('Export changed')
    if sha(SOURCE / 'joint-comparison-cache.json') != run['joint_comparison_cache']['sha256']:
        raise ValueError('Selection cache changed')
    if ARCHIVE.exists() or MODELS.exists():
        raise FileExistsError('Archive or model destination already exists')
    ARCHIVE.mkdir()
    MODELS.mkdir()
    copied = []
    def copy(source, target):
        shutil.copyfile(source, target)
        if sha(source) != sha(target):
            raise ValueError('Copy differs')
        copied.append({'path':target.relative_to(ROOT).as_posix(),
                       'sha256':sha(target), 'bytes':target.stat().st_size})
    for file in sorted(SOURCE.iterdir()):
        if file.suffix in ('.json', '.py'):
            copy(file, ARCHIVE / file.name)
    (ARCHIVE / 'early_export').mkdir()
    copy(SOURCE / 'early_export/model.tflite', ARCHIVE / 'early_export/model.tflite')
    for name in ('model.keras', 'model.tflite', 'run.json'):
        copy(SOURCE / name, MODELS / name)
    copy(ROOT / 'tools/check_detection_candidate.py', ARCHIVE / 'check_detection_candidate.py')
    record = {'status':'passed', 'source_run_directory':str(SOURCE),
              'source_script_sha256':sha(Path(__file__)), 'copied_files':copied,
              'packages_installed':0, 'pi_verified':False,
              'training_command':'wsl -d Ubuntu-24.04 -u skirttrain -- /home/skirttrain/skirt-fabric-sense/.venv-training/bin/python /mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense/tools/training/train_presence_finetune.py --negative-manifest /mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense/data/labels/negative-reviewed-v3.jsonl --joint-comparison-cache /mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense/records/validation/2026-10-18-detection-candidate.json --output /home/skirttrain/skirt-fabric-sense/runs/20261018-presence-v4'}
    with (ROOT / 'records/validation/2026-10-18-presence-v4-archive.json').open('x',encoding='utf-8') as stream:
        json.dump(record,stream,indent=2); stream.write('\n')
    print(json.dumps({'archived_files':len(copied),'status':'passed'}))


if __name__ == '__main__':
    main()
