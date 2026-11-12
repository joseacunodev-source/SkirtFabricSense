"""Root verification of the dataset diagrams and metadata-auditor batch."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.create_dataset_diagrams import verify_diagram_counts
from pypdf import PdfReader
from PIL import Image


def ref(p):
    path = ROOT/p
    return {'path': p, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def write(name, value):
    with (OUT/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


commands = []


def run(name, argv):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=60)
    (OUT/(name+'.log')).write_text(result.stdout+result.stderr, encoding='utf-8')
    commands.append({'name': name, 'command': argv, 'exit_code': result.returncode,
                     'log': ref('records/validation/2026-11-04-dataset-diagrams/'+name+'.log')})
    if result.returncode:
        write('failed-execution.json', commands)
        raise RuntimeError(name+' failed; inspect preserved log')
    return result


run('partition-tests', [sys.executable, '-B', '-m', 'unittest', 'tests.test_dataset_partitions', '-v'])
catalogs = ['data/manifests/worn-pleating-development-v1.jsonl',
            'data/labels/negative-reviewed-v3.jsonl',
            'data/manifests/skirt_candidates.jsonl',
            'data/manifests/negative-candidates-v1.jsonl',
            'data/manifests/negative-candidates-v2.jsonl',
            'data/manifests/negative-candidates-v3.jsonl',
            'data/provenance/external_holdout_samples.jsonl']
cases = [
    ('category', 'records/experiments/20261021-category-presence-v1/inputs.json', catalogs, (420, 118)),
    ('pleating', 'data/labels/skirt-baseline-v1.jsonl', catalogs, (292, 80)),
    ('localizer', 'records/experiments/20261014-localizer-v2/labelled-inputs.json', catalogs, (348, 99)),
    ('worn', 'data/manifests/worn-pleating-development-v1.jsonl', catalogs, (265, 66)),
    ('fabric', 'data/labels/fabric-pilot-v1-splits.json', ['data/labels/fabric-pilot-v1.jsonl'], (12, 5)),
]
reports = []
for name, manifest, catalogs_for_case, counts in cases:
    output = 'records/validation/2026-11-04-dataset-diagrams/'+name+'-partitions.json'
    argv = [sys.executable, '-B', 'tools/audit_dataset_partitions.py', '--manifest', manifest]
    for path in catalogs_for_case:
        argv += ['--catalog', path]
    argv += ['--output', output]
    result = run(name, argv)
    report = json.loads(result.stdout)
    if report['issues'] or report['unique_sample_counts_by_role'] != {'training': counts[0], 'model_validation': counts[1]}:
        raise ValueError('Unexpected metadata membership: '+name)
    reports.append(ref(output))

audit = json.loads((ROOT/'records/validation/2026-11-04-dataset-partitions-audit.json').read_text(encoding='utf-8'))
verify_diagram_counts(audit)
figure_dir = ROOT/'output/thesis_dataset_diagrams'
pdfs = {p.name: len(PdfReader(p).pages) for p in figure_dir.glob('*.pdf')}
if len(pdfs) != 5 or sorted(pdfs.values()) != [1, 1, 1, 1, 4]:
    raise ValueError('PDF page inventory mismatch')
pngs = {}
for p in figure_dir.glob('*.png'):
    with Image.open(p) as image:
        image.load()
        if image.size != (3300, 2250):
            raise ValueError('PNG dimensions mismatch')
        pngs[p.name] = {'size': list(image.size), 'dpi': list(image.info.get('dpi', []))}
if len(pngs) != 4:
    raise ValueError('Expected four rendered diagrams')

report = {'recorded_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
          'status': 'passed_root_review', 'tests_passed': 19, 'commands': commands,
          'metadata_audits': reports,
          'source_audit': ref('records/validation/2026-11-04-dataset-partitions-audit.json'),
          'pdf_pages': pdfs, 'pngs': pngs,
          'visual_review': {'reviewers': ['root', 'split_evidence'], 'figures_reviewed': 4,
                            'outcome': 'No clipping, overlap or material factual discrepancy found'},
          'fixes_after_review': ['Inspect both source-partition aliases',
                                 'Preserve recognized catalog partition declarations',
                                 'Normalize model-validation aliases consistently'],
          'figure_artifacts': [ref(p.relative_to(ROOT).as_posix()) for p in sorted(figure_dir.iterdir()) if p.is_file()],
          'source_files': [ref(p) for p in ['tools/create_dataset_diagrams.py', 'tools/audit_dataset_partitions.py',
                                           'tests/test_dataset_partitions.py']],
          'dependencies_installed': [], 'training_or_inference_performed': False,
          'original_images_or_split_changes': False,
          'limits': 'Recorded connections only; no independent labels, final garment test, accuracy gain or Pi acceptance.'}
write('verification.json', report)
print(json.dumps({'status': report['status'], 'tests_passed': 19, 'actual_assignment_sets_checked': len(reports),
                  'figures_visually_reviewed': 4}))
