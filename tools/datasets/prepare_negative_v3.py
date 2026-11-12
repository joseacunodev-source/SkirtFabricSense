"""Freeze original-reviewed negative extension without changing prior assignments."""
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.datasets.prepare_negative_extension import prepare, rows, sha
from tools.training.train_presence import validate


def main():
    target = ROOT/'data/labels/negative-reviewed-v3.jsonl'
    report_path = target.with_suffix('.report.json')
    if target.exists() or report_path.exists():
        raise FileExistsError('Frozen extension already exists')
    source = ROOT/'data/manifests/negative-candidates-v3.jsonl'
    previous = ROOT/'data/labels/negative-reviewed-v2.jsonl'
    audit_path = ROOT/'records/validation/2026-10-17-expansion-v3-audit.json'
    review_paths = [ROOT/'records/review/2026-10-17-negative-v3-a.json',
                    ROOT/'records/review/2026-10-18-negative-v3-b.json',
                    ROOT/'records/review/2026-10-18-negative-v3-c.json']
    candidates, old = rows(source), rows(previous)
    reviews = []
    for path in review_paths:
        record = json.loads(path.read_text(encoding='utf-8'))
        reviews.extend(record if isinstance(record, list) else record['reviews'])
    audit = json.loads(audit_path.read_text())
    if audit['counts']['integrity_errors'] or audit['exact_duplicate_groups'] or audit['pixel_duplicate_groups']:
        raise ValueError('Unresolved image integrity or exact duplicates')
    new_ids = {r['sample_id'] for r in candidates}
    excluded = set()
    for pair in audit['near_duplicate_candidates']:
        if new_ids.intersection(pair['sample_ids']):
            excluded.update(new_ids.intersection(pair['sample_ids']))
    for review in reviews:
        if review.get('related_sample_ids'):
            excluded.add(review['sample_id'])
            excluded.update(new_ids.intersection(review['related_sample_ids']))
    # Root cross-batch review can add conservative unresolved session flags.
    root_flags = ROOT/'records/review/2026-10-18-negative-v3-root-grouping.json'
    if root_flags.exists():
        for flag in json.loads(root_flags.read_text())['flags']:
            excluded.update(new_ids.intersection(flag['sample_ids']))
    result = prepare(candidates, reviews, old, excluded)
    admitted = [r for r in result if r['training_eligibility']['approved']]
    positives = rows(ROOT/'data/manifests/worn-pleating-development-v1.jsonl')
    validate([{**r, 'presence_target':1} for r in positives] + [{**r, 'presence_target':0} for r in admitted])
    for row in candidates:
        if sha(ROOT/row['original_path']) != row['sha256']:
            raise ValueError('Changed original')
    if result[:len(old)] != old:
        raise ValueError('Prior records changed')
    with target.open('x', encoding='utf-8') as f:
        for row in result:
            f.write(json.dumps(row, sort_keys=True)+'\n')
    sources = [source, previous, audit_path, *review_paths]
    if root_flags.exists():
        sources.append(root_flags)
    report = {'date_asia_manila':'2026-10-18', 'status':'frozen_agent_reviewed_development_only',
              'inputs':[{'path':p.relative_to(ROOT).as_posix(), 'sha256':sha(p)} for p in sources],
              'source_sha256':sha(Path(__file__)),
              'reused_preparation_source_sha256':sha(ROOT/'tools/datasets/prepare_negative_extension.py'),
              'manifest_sha256':sha(target), 'prior_assignments_preserved':True,
              'counts':{'rows':len(result), 'new_candidates':len(candidates), 'admitted':len(admitted),
                        'new_admitted':sum(r['training_eligibility']['approved'] for r in result[len(old):]),
                        'by_split':dict(Counter(r['split'] for r in admitted))},
              'new_excluded_for_known_group_or_near_match':sorted(excluded),
              'limitations':['Single-agent original-image review; independent human truth pending',
                             'Physical garment identity unknown; unresolved links excluded',
                             'No empty-scene or camera-domain evidence added',
                             'All previous assignments preserved; no protected data reassigned']}
    with report_path.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps(report['counts']))


if __name__ == '__main__':
    main()
