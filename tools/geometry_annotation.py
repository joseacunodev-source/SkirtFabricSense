"""Create an offline, single-original geometry annotation editor.

Exports pending-review observations only. Never supplies calibration, physical
length, model truth or evaluator approval. Existing Pillow is required.
"""
import argparse
import base64
from datetime import date
import hashlib
import io
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageOps
from tools.evaluate_worn_geometry import validate_inventory

DEFAULT_INVENTORY = ROOT/'records/geometry/2026-10-21-readiness/frozen-inventory.json'
CONVENTION = 'source_rgb_pixels_after_exif_transpose'
AXES = ('waist_y', 'hem_y', 'floor_y')
MAX_PIXELS = 20_000_000
MAX_BYTES = 20*1024*1024


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(body):
    return hashlib.sha256(body).hexdigest()


def load_source(inventory, sample_id, source_root):
    """Reopen frozen identity and original bytes; never infer assignment changes."""
    inventory, source_root = Path(inventory), Path(source_root).resolve(strict=True)
    raw = inventory.read_bytes()
    rows = validate_inventory(json.loads(raw.decode('utf-8-sig')))
    require(sample_id in rows, 'Selected sample is absent from the frozen inventory')
    row = rows[sample_id]
    require(row['split'] == 'development_validation', 'Only frozen development_validation samples are supported')
    path = (source_root/row['original_path']).resolve(strict=True)
    require(path.is_relative_to(source_root) and path.is_file(), 'Original escapes source root')
    require(path.stat().st_size <= MAX_BYTES, 'Original exceeds the 20 MiB bound')
    body = path.read_bytes()
    require(sha(body) == row['image_sha256'], 'Original image SHA256 differs from frozen inventory')
    with Image.open(io.BytesIO(body)) as image:
        require(image.width*image.height <= MAX_PIXELS, 'Original exceeds 20 megapixels')
        rgb = ImageOps.exif_transpose(image).convert('RGB')
        rgb.load()
    require(min(rgb.size) >= 2, 'Original is too small')
    binding = {k:row[k] for k in ('sample_id','garment_group_id','split','original_path','image_sha256')}
    binding.update(frame_size=list(rgb.size), inventory_sha256=sha(raw),
                   coordinate_convention=CONVENTION)
    return binding, rgb


def validate_draft(draft, inventory=DEFAULT_INVENTORY, source_root=ROOT):
    require(isinstance(draft, dict), 'Draft must be an object')
    expected = {'schema_version','data_kind','review_status','reviewed','evaluator_approved',
                'binding','reviewer','review_date','original_viewed','observations','notes'}
    require(set(draft) == expected, 'Unexpected or missing draft fields')
    require(type(draft['schema_version']) is int and draft['schema_version'] == 1, 'Unsupported draft schema')
    require(draft['data_kind'] == 'pending_source_geometry_observation', 'Only pending geometry drafts are accepted')
    require(draft['review_status'] == 'pending_independent_reconciliation'
            and draft['reviewed'] is False and draft['evaluator_approved'] is False,
            'A draft cannot declare review or evaluation approval')
    binding = draft['binding']
    require(isinstance(binding, dict) and isinstance(binding.get('sample_id'), str), 'Original binding required')
    actual, image = load_source(inventory, binding['sample_id'], source_root)
    image.close()
    require(binding == actual, 'Draft original/inventory/coordinate binding differs')
    reviewer = draft['reviewer']
    require(isinstance(reviewer, dict) and set(reviewer) == {'display_name','actor_kind'}, 'Reviewer identity required')
    require(isinstance(reviewer['display_name'], str) and 1 <= len(reviewer['display_name'].strip()) <= 120,
            'Reviewer name must contain 1 to 120 characters')
    require(reviewer['actor_kind'] in ('human','agent'), 'Reviewer actor kind must be explicit')
    try:
        require(date.fromisoformat(draft['review_date']).isoformat() == draft['review_date'], 'Invalid review date')
    except (TypeError, ValueError):
        raise ValueError('Review date must be an ISO date') from None
    require(draft['original_viewed'] is True, 'Reviewer must explicitly confirm viewing the complete original')
    require(isinstance(draft['notes'], str) and 1 <= len(draft['notes'].strip()) <= 4000,
            'Evidence notes must contain 1 to 4000 characters')
    obs = draft['observations']
    require(isinstance(obs, dict) and set(obs) == set(AXES), 'Exactly waist, hem and floor observations required')
    height = actual['frame_size'][1]
    for axis in AXES:
        value = obs[axis]
        require(isinstance(value, dict) and set(value) == {'visibility','interval'}, 'Invalid axis observation')
        require(value['visibility'] in ('visible','hidden','uncertain'), 'Invalid observation visibility')
        interval = value['interval']
        if value['visibility'] == 'visible':
            require(isinstance(interval,list) and len(interval)==2 and all(
                type(v) in (int,float) and math.isfinite(v) and 0 <= v <= height-1 for v in interval)
                and interval[0] <= interval[1], 'Visible interval must be ordered and inside source pixels')
        else:
            require(interval is None, 'Hidden or uncertain anatomy must have no invented interval')
    return {'status':'valid_pending_draft','sample_id':actual['sample_id'],
            'reviewed':False,'evaluator_approved':False,'physical_calibration_verified':False}


def build_editor(inventory, sample_id, source_root, output):
    output = Path(output)
    require(output.suffix.lower() == '.html', 'Editor output must be an HTML file')
    binding, rgb = load_source(inventory, sample_id, source_root)
    buffer = io.BytesIO()
    rgb.save(buffer, format='PNG')
    rgb.close()
    image_data = 'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode('ascii')
    template = (ROOT/'tools/static/geometry_annotation.html').read_text(encoding='utf-8')
    # Escape script-closing markup even if an untrusted ID/path enters metadata.
    payload = json.dumps({'binding':binding,'image':image_data}).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    html = template.replace('/*GEOMETRY_DOCUMENT*/null', payload)
    require(html != template, 'Editor template placeholder missing')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        stream.write(html)
    return {'status':'offline_editor_created','sample_id':sample_id,
            'output':str(output),'inventory_sha256':binding['inventory_sha256'],
            'image_sha256':binding['image_sha256'],'observations_submitted':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('build','validate'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--inventory', type=Path, default=DEFAULT_INVENTORY)
        cmd.add_argument('--source-root', type=Path, default=ROOT)
        if name == 'build':
            cmd.add_argument('--sample-id', required=True)
            cmd.add_argument('--output', type=Path, required=True)
        else:
            cmd.add_argument('--draft', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'build':
            result = build_editor(args.inventory,args.sample_id,args.source_root,args.output)
        else:
            require(args.draft.stat().st_size <= 64*1024, 'Draft exceeds 64 KiB')
            result = validate_draft(json.loads(args.draft.read_text(encoding='utf-8-sig')),
                                    args.inventory,args.source_root)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({'status':'failed','error':str(exc)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
