"""Render thesis partition diagrams from the November 4 metadata audit.

No sampling, predictions, training, or split changes. Existing ReportLab, pypdf
and pdftoppm only. Refuses to overwrite a previous output directory.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
INK = HexColor('#202d35')
MUTED = HexColor('#54646c')
BLUE = HexColor('#155b75')
TEAL = HexColor('#287e79')
PALE = HexColor('#edf4f5')
GREY = HexColor('#ced8db')
PAPER = HexColor('#f6f8f8')
AMBER = HexColor('#8f531a')
CREAM = HexColor('#fff7eb')
WIDTH, HEIGHT = 792, 540


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(c, x, y, value, size=13, bold=False, color=INK, align='left'):
    font = 'Helvetica-Bold' if bold else 'Helvetica'
    c.setFont(font, size)
    c.setFillColor(color)
    method = {'left': c.drawString, 'center': c.drawCentredString, 'right': c.drawRightString}[align]
    method(x, y, value)


def rule(c, x1, y1, x2, y2, color=GREY, width=1.2, dashed=False):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(width)
    if dashed:
        c.setDash(5, 4)
    c.line(x1, y1, x2, y2)
    c.restoreState()


def arrow(c, x1, y1, x2, y2, color=MUTED, dashed=False):
    import math
    rule(c, x1, y1, x2, y2, color, dashed=dashed)
    a = math.atan2(y2-y1, x2-x1)
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2-8*math.cos(a-.43), y2-8*math.sin(a-.43))
    p.lineTo(x2-8*math.cos(a+.43), y2-8*math.sin(a+.43))
    p.close()
    c.setFillColor(color)
    c.drawPath(p, stroke=0, fill=1)


def box(c, x, y, w, h, title, lines=(), color=BLUE, pending=False, size=13):
    c.saveState()
    c.setFillColor(CREAM if pending else PALE)
    c.setStrokeColor(color)
    c.setLineWidth(1.2)
    if pending:
        c.setDash(5, 4)
    c.roundRect(x, y, w, h, 4, stroke=1, fill=1)
    c.restoreState()
    title_lines = title.split('\n')
    yy = y+h-25
    for s in title_lines:
        if stringWidth(s, 'Helvetica-Bold', size) > w-20:
            raise ValueError('Title overflows: '+s)
        text(c, x+w/2, yy, s, size, True, color, 'center')
        yy -= 18
    yy -= 5
    for s in lines:
        if stringWidth(s, 'Helvetica', 12) > w-20:
            raise ValueError('Box text overflows: '+s)
        text(c, x+w/2, yy, s, 12, align='center')
        yy -= 17
    if lines and yy+17 < y+10:
        raise ValueError('Box text height overflows: '+title)


def page(out, stem, title, subtitle):
    c = canvas.Canvas(str(out/(stem+'.pdf')), pagesize=(WIDTH, HEIGHT), invariant=1)
    c.setTitle(title)
    c.setAuthor('SkirtFabricSense engineering project')
    text(c, 30, 506, title, 20, True)
    text(c, 30, 483, subtitle, 12, color=MUTED)
    rule(c, 30, 469, 762, 469)
    return c


def finish(c, out, stem, converter):
    c.showPage()
    c.save()
    subprocess.run([converter, '-f', '1', '-l', '1', '-singlefile', '-png', '-r', '300',
                    str(out/(stem+'.pdf')), str(out/stem)], check=True,
                   timeout=60, capture_output=True)


def figure_actual(out, converter):
    stem = '06_training_validation_test'
    c = page(out, stem, 'Actual training, validation and test status',
             'Selected category-presence experiment | Recorded state: November 4, 2026')
    box(c, 30, 376, 472, 70, '538 admitted development images',
        ['Fashionpedia train2020 source; frozen project assignments'])
    rule(c, 266, 376, 266, 352)
    rule(c, 144, 352, 388, 352)
    arrow(c, 144, 352, 144, 331)
    arrow(c, 388, 352, 388, 331)
    box(c, 30, 181, 228, 149, 'TRAINING',
        ['420 images (78.1%)', '265 worn skirts + 155 negatives',
         'Used to fit model weights', 'Recorded groups: 420'])
    box(c, 274, 181, 228, 149, 'VALIDATION',
        ['118 images (21.9%)', '66 worn skirts + 52 negatives',
         'Reused for model selection', 'Recorded groups: 118'], color=TEAL)
    box(c, 530, 181, 232, 149, 'FINAL DEVICE TEST',
        ['Not collected or frozen', 'Needs unseen physical garments',
         'No final accuracy measured', 'Separate future collection'], color=AMBER, pending=True)
    text(c, 646, 397, 'No random re-split', 14, True, AMBER, 'center')
    text(c, 646, 376, 'of reused development data', 12, color=MUTED, align='center')
    box(c, 30, 75, 732, 80, 'Separate protected source sanity pool: 12 photos',
        ['Original Fashionpedia val2020. Excluded from model fitting and tuning.',
         'These are not the final camera / Raspberry Pi test set.'], color=MUTED)
    text(c, 30, 48, 'Percentages refer to 538 images, not all 1,932 registered originals.', 11, color=MUTED)
    text(c, 30, 31, 'Recorded source groups are not verified physical garments. Dashed box = pending.', 11, color=MUTED)
    finish(c, out, stem, converter)
    return stem


def figure_subsystems(out, converter):
    stem = '07_datasets_by_model'
    c = page(out, stem, 'Dataset sizes differ across the models',
             'Actual experiment inputs | Counts are original images, not new crops or garments')
    xs = [44, 375, 495, 620]
    for x, label in zip(xs, ['Component / experiment', 'Train', 'Validation', 'Total']):
        text(c, x, 435, label, 13, True)
    rows = [
        ('Pleating fine-tune v1', '292', '80', '372', 'Both worn and secondary presentations'),
        ('Localizer v2', '348', '99', '447', '292 + 56 negatives / 80 + 19 negatives'),
        ('Category presence v1', '420', '118', '538', '265 + 155 negatives / 66 + 52 negatives'),
        ('Fabric appearance smoke v1', '12', '5', '17', 'Very small source-appearance pilot; not accepted'),
    ]
    for i, row in enumerate(rows):
        y = 379-i*65
        if i % 2 == 0:
            c.setFillColor(PAPER)
            c.rect(30, y-26, 732, 61, stroke=0, fill=1)
        text(c, 44, y+9, row[0], 13, True)
        for x, val in zip(xs[1:], row[1:4]):
            text(c, x+19, y+9, val, 18, True, BLUE, 'center')
        text(c, 44, y-12, row[4], 11, color=MUTED)
    rule(c, 30, 145, 762, 145)
    text(c, 44, 124, 'Worn-skirt subset: 265 train / 66 validation (331 total).', 12, True)
    text(c, 44, 105, 'It supplies category-presence positives and the current chain comparison.', 12)
    text(c, 44, 78, 'Pools overlap: do not add these rows to obtain a unique dataset size.', 12, True, AMBER)
    text(c, 44, 56, 'Hemline: zero observed geometry annotations; measured calibration remains pending.', 11, color=MUTED)
    text(c, 44, 36, 'No accepted independent device-domain final test exists for these components.', 11, color=MUTED)
    finish(c, out, stem, converter)
    return stem


def figure_protocol(out, converter):
    stem = '08_planned_train_validation_test_workflow'
    c = page(out, stem, 'Planned development and final-test workflow',
             'Methodology diagram | Future physical collection; no completed split ratio implied')
    box(c, 30, 368, 732, 77, 'Acquire and review full-skirt observations',
        ['Record garment identity, source rights, independent labels and capture sessions.',
         'Keep every frame, crop and derivative with its related garment group.'])
    rule(c, 396, 368, 396, 350)
    rule(c, 143, 350, 655, 350)
    for x in [143, 399, 655]:
        arrow(c, x, 350, x, 331)
    box(c, 30, 199, 226, 131, 'TRAINING GROUPS',
        ['Fit weights and preprocessing', 'Training augmentation only',
         'INT8 representative inputs', 'come from training groups'])
    box(c, 286, 199, 226, 131, 'VALIDATION GROUPS',
        ['Model selection: architecture,', 'stopping epoch and crop policy',
         'Separate calibration groups:', 'thresholds and score calibration'], color=TEAL)
    box(c, 542, 199, 220, 131, 'LOCKED TEST GROUPS',
        ['Reserve before development', 'Unseen physical garments',
         'Labels frozen before outputs', 'No tuning on these groups'], color=AMBER, pending=True)
    arrow(c, 143, 199, 143, 172)
    arrow(c, 399, 199, 399, 172)
    box(c, 30, 88, 482, 83, 'Freeze one complete candidate',
        ['Model, code, thresholds, calibration, runtime and protocol.',
         'Check export parity before final evaluation.'])
    arrow(c, 652, 199, 652, 172, AMBER, dashed=True)
    box(c, 542, 88, 220, 83, 'Final evaluation',
        ['Report errors and coverage;', 'verify real camera and Pi.'], color=AMBER, pending=True)
    arrow(c, 512, 127, 542, 127)
    text(c, 30, 57, 'Choose group counts per class before ratios. No final-test data returns to tuning.', 11, color=MUTED)
    text(c, 30, 37, 'If test findings guide changes, use a new independent test for the revised candidate.', 11, color=MUTED)
    finish(c, out, stem, converter)
    return stem


def figure_grouping(out, converter):
    stem = '09_grouping_prevents_data_leakage'
    c = page(out, stem, 'Keep related observations in one partition',
             'Illustrative grouping rule | These example garment IDs are not acquired specimens')
    groups = [
        ('GARMENT A', 'Frames, views, native crops', 'and training augmentations', 'TRAINING', BLUE),
        ('GARMENT B', 'Frames, views and related', 'product / session images', 'VALIDATION', TEAL),
        ('GARMENT C', 'All held-out presentations', 'and same-garment derivatives', 'LOCKED TEST', AMBER),
    ]
    for i, (label, l1, l2, role, color) in enumerate(groups):
        y = 345-i*108
        box(c, 30, y, 181, 81, label, ['One connected identity'], color=color)
        arrow(c, 211, y+40, 239, y+40, color)
        box(c, 239, y, 279, 81, 'Related observations', [l1, l2], color=color)
        arrow(c, 518, y+40, 546, y+40, color)
        box(c, 546, y, 216, 81, role, ['One group, one partition'], color=color)
    text(c, 30, 96, 'Connect identities using garment, product, parent frame, clip/session and duplicate links.', 11)
    text(c, 30, 76, 'Never randomly split frames or crops from the same garment across these partitions.', 11, True)
    text(c, 30, 53, 'More frames do not create more independent garments.', 12, True, AMBER)
    text(c, 30, 33, 'Unresolved identity is excluded from final-test acceptance until reviewed.', 11, color=MUTED)
    finish(c, out, stem, converter)
    return stem


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'output/thesis_dataset_diagrams')
    parser.add_argument('--audit', type=Path, default=ROOT/'records/validation/2026-11-04-dataset-partitions-audit.json')
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Preserve existing figures; use a fresh output folder')
    audit = json.loads(args.audit.read_text(encoding='utf-8'))
    # Audit data are copied as a source-bound companion, not silently replaced by
    # newly computed training partitions. Assertions below bind diagram numbers.
    verify_diagram_counts(audit)
    converter = shutil.which('pdftoppm')
    if not converter:
        raise RuntimeError('Existing pdftoppm required')
    out.mkdir(parents=True, exist_ok=True)
    stems = [f(out, converter) for f in
             (figure_actual, figure_subsystems, figure_protocol, figure_grouping)]
    writer = PdfWriter()
    for stem in stems:
        reader = PdfReader(str(out/(stem+'.pdf')))
        if len(reader.pages) != 1:
            raise ValueError('Each standalone figure must contain one page')
        writer.add_page(reader.pages[0])
    with (out/'Training_Validation_Test_Diagrams.pdf').open('wb') as stream:
        writer.write(stream)
    source = {'recorded_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'audit': {'path': args.audit.relative_to(ROOT).as_posix(), 'sha256': digest(args.audit)},
              'generator': {'path': Path(__file__).relative_to(ROOT).as_posix(), 'sha256': digest(Path(__file__))},
              'diagrams': stems, 'source_audit': audit,
              'scope': 'Two actual metadata diagrams; two proposed methodology diagrams. No new training or split.',
              'dpi': 300, 'pdf_vector': True}
    (out/'source-data.json').write_text(json.dumps(source, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': 'generated_pending_visual_review', 'directory': str(out), 'diagrams': len(stems)}))


def verify_diagram_counts(audit):
    """Fail rather than reuse stale counts if the bound records change."""
    if audit.get('status') != 'completed_metadata_partition_audit':
        raise ValueError('Completed metadata audit required')
    for item in audit['sources'].values():
        path = (ROOT/item['path']).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != item['sha256']:
            raise ValueError('Evidence differs: '+item['path'])
    expected = {
        'pleating_finetune': (292, 80, 'pleating'),
        'localizer_v2': (348, 99, 'localizer'),
        'category_presence_v1': (420, 118, 'category'),
        'fabric_smoke': (12, 5, 'fabric'),
        'worn_subset': (265, 66, 'worn'),
    }
    for name, (train, val, source) in expected.items():
        item = audit['subsystems'][name]
        parts = item['partitions']
        if (parts['development_train']['images'], parts['development_validation']['images'],
                item['total_images']) != (train, val, train+val):
            raise ValueError('Diagram counts disagree: '+name)
        path = ROOT/audit['sources'][source]['path']
        body = path.read_text(encoding='utf-8')
        rows = [json.loads(s) for s in body.splitlines() if s.strip()] if path.suffix == '.jsonl' else json.loads(body)
        counts = [sum(r['split'] == s for r in rows) for s in ('development_train', 'development_validation')]
        if counts != [train, val] or len(rows) != train+val:
            raise ValueError('Original membership disagrees: '+name)
    if audit['protected_source_sanity']['images'] != 12 or audit['protected_source_sanity']['final_project_test']:
        raise ValueError('Source sanity pool status changed')
    if audit['final_project_test']['status'] != 'not_collected_or_frozen':
        raise ValueError('Final-test figure requires updating')
    if audit['geometry']['observed_annotated_originals'] != 0:
        raise ValueError('Geometry figure requires updating')


if __name__ == '__main__':
    main()
