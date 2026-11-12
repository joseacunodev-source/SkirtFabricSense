"""Validate local documentation links, JSON records, acquisition integrity and skill sync."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote
try:
    from tools.raw_http_records import verified_raw_responses
except ModuleNotFoundError:
    from raw_http_records import verified_raw_responses


def verify_reference_tree(root, value, errors):
    """Check nested local evidence references without following paths outside root."""
    checked = 0
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            relative = value['path']
            if not isinstance(relative, str) or not relative:
                errors.append('Invalid evidence reference path')
            else:
                file = (root / relative).resolve()
                if (not file.is_relative_to(root.resolve()) or not file.is_file()
                        or hashlib.sha256(file.read_bytes()).hexdigest() != value['sha256']):
                    errors.append(f'Evidence reference mismatch: {relative}')
                else:
                    checked += 1
        for child in value.values():
            checked += verify_reference_tree(root, child, errors)
    elif isinstance(value, list):
        for child in value:
            checked += verify_reference_tree(root, child, errors)
    return checked


def validate(root: Path, report_output: Path | None = None) -> dict:
    errors = []
    markdown = [root / 'README.md', root / 'CHANGELOG.md', *sorted((root / 'docs').glob('*.md')),
                *sorted((root / 'requirements').glob('*.md'))]
    checked_links = 0
    for path in markdown:
        if not path.exists():
            errors.append(f'Missing document: {path.name}')
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                continue
            target = unquote(target.split('#')[0].strip('<>'))
            checked_links += 1
            resolved = (path.parent / target).resolve()
            # The report may link to itself before this first atomic write.
            is_this_report = report_output is not None and resolved == report_output.resolve()
            if not resolved.exists() and not is_this_report:
                errors.append(f'{path.relative_to(root)}: missing link {target}')
    checked_json = 0
    raw_responses = set()
    try:
        raw_responses = verified_raw_responses(root)
    except (ValueError, OSError, KeyError, TypeError, IndexError) as exc:
        errors.append('Raw HTTP response recovery invalid: ' + str(exc))
    for folder in ('templates', 'records', 'data/provenance'):
        for path in (root / folder).rglob('*'):
            try:
                if path.suffix == '.json':
                    if path.relative_to(root).as_posix() in raw_responses:
                        continue
                    json.loads(path.read_text(encoding='utf-8-sig'))
                    checked_json += 1
                elif path.suffix == '.jsonl':
                    for line in path.read_text(encoding='utf-8-sig').splitlines():
                        if line.strip():
                            json.loads(line)
                            checked_json += 1
            except (ValueError, OSError) as exc:
                errors.append(f'{path.relative_to(root)}: {exc}')
    registry = json.loads((root / 'data/registry.json').read_text(encoding='utf-8'))
    for key in ('acquisition_manifest', 'verification_audit'):
        entry = registry[key]
        path = root / entry['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            errors.append(f'Registry hash mismatch: {entry["path"]}')
    manifest = json.loads((root / registry['acquisition_manifest']['path']).read_text())
    for entry in manifest['artifacts']:
        body = (root / entry['path']).read_bytes()
        if len(body) != entry['size_bytes'] or hashlib.sha256(body).hexdigest() != entry['sha256']:
            errors.append(f'Acquired file mismatch: {entry["path"]}')
    expansion_images = 0
    for acquisition in registry.get('expansion_acquisitions', []):
        for key in ('manifest', 'report'):
            item = acquisition[key]
            if hashlib.sha256((root / item['path']).read_bytes()).hexdigest() != item['sha256']:
                errors.append(f'Expansion evidence hash mismatch: {item["path"]}')
        for line in (root / acquisition['manifest']['path']).read_text(encoding='utf-8').splitlines():
            item = json.loads(line)
            file_path = (root / item['original_path']).resolve()
            if not file_path.is_relative_to(root.resolve()):
                errors.append('Expansion image path escapes workspace')
                continue
            if hashlib.sha256(file_path.read_bytes()).hexdigest() != item['sha256']:
                errors.append(f'Expansion image mismatch: {item["sample_id"]}')
            expansion_images += 1
    for entry in [registry.get('expansion_audit'), *registry.get('development_splits', [])]:
        if entry and hashlib.sha256((root / entry['path']).read_bytes()).hexdigest() != entry['sha256']:
            errors.append(f'Expansion audit/split mismatch: {entry["path"]}')
    for key in ['label_preparation', 'label_preparation_history', 'development_experiments', 'pretrained_assets',
                'supplementary_metadata', 'research_updates_oct22', 'selected_research_station']:
        verify_reference_tree(root, registry.get(key), errors)
    continuation_path = root / 'records/continuation/latest.json'
    continuation_refs = 0
    if continuation_path.exists():
        try:
            continuation = json.loads(continuation_path.read_text(encoding='utf-8'))
            if not isinstance(continuation, dict) or type(continuation.get('schema_version')) is not int or continuation['schema_version'] != 1:
                errors.append('Unsupported continuation schema')
            else:
                continuation_refs = verify_reference_tree(root, continuation, errors)
        except (ValueError, OSError) as exc:
            errors.append('Unreadable continuation record: ' + str(exc))
    installed = Path.home() / '.codex/skills/skirt-fabric-project/SKILL.md'
    portable = root / 'skills/skirt-fabric-project/SKILL.md'
    if not installed.exists() or not portable.exists() or installed.read_bytes() != portable.read_bytes():
        errors.append('Installed and portable project skill differ or installed copy is unavailable')
    return {'recorded_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
            'status': 'passed' if not errors else 'failed',
            'local_links_checked': checked_links, 'json_records_parsed': checked_json,
            'raw_http_failure_bodies_verified': len(raw_responses),
            'acquired_artifacts_verified': len(manifest['artifacts']),
            'expansion_image_hashes_verified': expansion_images,
            'continuation_record_present': continuation_path.exists(),
            'continuation_evidence_references_verified': continuation_refs,
            'skill_copy_matches': not any('skill differ' in e for e in errors), 'errors': errors,
            'limits': 'Documentation/integrity checks only; not model training or Raspberry Pi verification.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = validate(Path(__file__).resolve().parents[1], args.output)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['errors']))
