"""Create a deterministic local QA contact sheet from a candidate JSONL manifest.

Outputs are inspection artifacts, never additional training samples.
Requires Pillow in the interpreter used to run this script.
"""
import argparse
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--count', type=int, default=24)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    if not 1 <= args.count <= 60:
        parser.error('--count must be from 1 to 60')
    root = Path(__file__).resolve().parents[2]
    rows = [json.loads(line) for line in args.manifest.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not rows:
        parser.error('manifest contains no samples')
    chosen = random.Random(args.seed).sample(rows, min(args.count, len(rows)))
    columns, cell_w, cell_h = 6, 240, 280
    canvas = Image.new('RGB', (columns * cell_w, ((len(chosen) + columns - 1) // columns) * cell_h), 'white')
    draw = ImageDraw.Draw(canvas)
    positions = []
    for index, row in enumerate(chosen):
        path = root / row.get('original_path', row.get('path', ''))
        with Image.open(path) as opened:
            image = ImageOps.exif_transpose(opened).convert('RGB')
            image.thumbnail((cell_w - 12, cell_h - 42))
        x, y = (index % columns) * cell_w, (index // columns) * cell_h
        canvas.paste(image, (x + (cell_w - image.width) // 2, y + 4))
        sample_id = str(row.get('sample_id', path.stem))
        draw.text((x + 5, y + cell_h - 32), f'{index + 1}: {sample_id}'[:37], fill='black')
        labels = str(row.get('source_labels', ''))
        draw.text((x + 5, y + cell_h - 17), labels[:37], fill='black')
        positions.append({'position': index + 1, 'sample_id': sample_id, 'original_path': str(path.relative_to(root)),
                          'source_labels': row.get('source_labels')})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output)
    args.output.with_suffix('.json').write_text(json.dumps({'manifest': str(args.manifest), 'seed': args.seed,
        'use': 'visual QA only; not training data or additional original-image count', 'samples': positions}, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {len(chosen)}-sample QA sheet: {args.output}')


if __name__ == '__main__':
    main()
