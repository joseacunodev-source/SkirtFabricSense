"""Freeze the v2 appearance pilot with reviewed garment candidates quarantined."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def ref(path):
    return dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    source=ROOT/'data/labels/skirt-preparation-v2/reviewed-appearance.jsonl'
    split=ROOT/'data/manifests/source-skirt-development-splits.json'
    candidate=ROOT/'records/review/batch-a/group-candidates.json'
    out=ROOT/'data/labels/skirt-baseline-v1.jsonl'
    report=ROOT/'data/labels/skirt-baseline-v1.report.json'
    if out.exists() or report.exists():raise ValueError('Baseline manifest already frozen')
    assignments={r['sample_id']:r for r in json.loads(split.read_text())['assignments']}
    groups=json.loads(candidate.read_text())['groups']
    blocked_ids={sid for group in groups for sid in group['sample_ids']}
    blocked_groups={assignments[sid]['group_hash'] for sid in blocked_ids}
    rows=[json.loads(x) for x in source.read_text(encoding='utf-8').splitlines()]
    admitted=[]; excluded=[]
    for row in rows:
        review=row['label_evidence']
        reason=None
        if row['group_hash'] in blocked_groups:reason='suspected_repeated_garment_component_quarantine'
        elif review.get('exclude_auxiliary') or review.get('review_conflict'):reason='review_exclusion'
        elif review['full_skirt_view'] is not True:reason='not_explicit_full_view'
        if reason:excluded.append(dict(sample_id=row['sample_id'],reason=reason))
        else:admitted.append(row)
    with out.open('x',encoding='utf-8') as f:
        for row in admitted:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    result=dict(inputs=[ref(source),ref(split),ref(candidate)],output=ref(out),source_code=ref(Path(__file__)),
                admitted=len(admitted),class_split_counts=dict(Counter(r['split']+':'+r['label'] for r in admitted)),
                excluded=excluded,suspected_garment_ids=sorted(blocked_ids),quarantined_group_hashes=sorted(blocked_groups),
                policy='Exclude complete existing components; no train/validation reassignment; agent labels remain provisional')
    with report.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
