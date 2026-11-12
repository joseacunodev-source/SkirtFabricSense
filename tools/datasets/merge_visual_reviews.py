"""Merge complete disjoint review batches; quarantine conflicts with prior reviews."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def read(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x]


def ref(path):
    return dict(path=str(path.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    target=(ROOT/args.output).resolve()
    if target.exists(): raise ValueError('Output exists')
    originals={r['sample_id']:r for r in read(ROOT/'data/manifests/skirt_candidates.jsonl')}
    prior={r['sample_id']:r for r in read(ROOT/'data/labels/skirt-visual-reviews-v1.jsonl')}
    paths=[ROOT/f'data/labels/skirt-review-batch-{batch}.jsonl' for batch in 'abc']
    reviews={}
    conflicts=[]
    for path in paths:
        for row in read(path):
            sid=row['sample_id']
            if sid in reviews or sid not in originals: raise ValueError('Duplicate/unknown review ID')
            if row['image_sha256']!=originals[sid]['sha256']: raise ValueError('Wrong reviewed image hash')
            if row['appearance_label'] not in ['unknown','pleated','non_pleated'] or type(row['full_skirt_view']) is not bool:
                raise ValueError('Invalid review values')
            if not row['evidence'] or not (ROOT/row['review_artifact']).is_file(): raise ValueError('Missing review evidence')
            previous=prior.get(sid)
            # Different positive/negative judgments or a framing disagreement need
            # reconciliation. Unknown-to-known changes remain review-version changes.
            if previous and ((previous['appearance_label']!='unknown' and row['appearance_label']!='unknown'
                    and previous['appearance_label']!=row['appearance_label']) or
                    previous['full_skirt_view']!=row['full_skirt_view']):
                conflicts.append(dict(sample_id=sid,prior=previous,current=row.copy()))
                row=dict(row,appearance_label='unknown',exclude_auxiliary=True,
                         evidence=row['evidence']+' Prior/current review disagreement; quarantined pending reconciliation.',
                         review_conflict=True)
            reviews[sid]=row
    if set(reviews)!=set(originals): raise ValueError(f'Incomplete review: {len(reviews)}/1000')
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x',encoding='utf-8') as stream:
        for sid in sorted(reviews): stream.write(json.dumps(reviews[sid],ensure_ascii=False)+'\n')
    summary=dict(inputs=[ref(p) for p in paths],output=ref(target),reviewed=len(reviews),
        appearance_counts=dict(Counter(r['appearance_label'] for r in reviews.values())),
        full_view_candidate_count=sum(r['full_skirt_view'] and r['appearance_label']!='unknown' for r in reviews.values()),
        conflicts_quarantined=len(conflicts),conflicts=conflicts,
        limits='Agent visual review only; no independently verified garments, composition or physical length')
    with target.with_suffix('.report.json').open('x',encoding='utf-8') as stream:json.dump(summary,stream,indent=2)
    print(json.dumps({k:v for k,v in summary.items() if k!='conflicts'},indent=2))


if __name__=='__main__': main()
