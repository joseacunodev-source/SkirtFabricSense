"""Freeze reviewed extension; preserve every v1 assignment and quarantine unresolved links."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.datasets.prepare_negative_pilot import assign_splits
from tools.datasets.expand_negatives_v2 import permitted_license
from tools.training.train_presence import validate

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rows(path):return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

def prepare(candidates,reviews,old,excluded):
    by_id={r['sample_id']:r for r in reviews}
    if len(by_id)!=len(reviews) or set(by_id)!={r['sample_id'] for r in candidates}:
        raise ValueError('Review coverage missing or duplicated')
    output=[]
    for row in candidates:
        review=by_id[row['sample_id']]
        if review.get('sha256')!=row['sha256'] or review.get('original_inspected') is not True:
            raise ValueError('Review does not bind inspected original')
        if type(review.get('approve_no_skirt')) is not bool or not review.get('observation'):
            raise ValueError('Review decision/evidence required')
        eligible=(review['approve_no_skirt'] and row['sample_id'] not in excluded
                  and not review.get('related_sample_ids') and permitted_license(row['source_license']))
        if row['source_partition']!='train2020':raise ValueError('Protected source')
        output.append({**row,'label':'no_skirt' if eligible else None,'split':None,
            'group_hash':hashlib.sha256(row['group_id'].encode()).hexdigest(),
            'grouping_review_pending':not eligible,
            'label_evidence':{**review,'independent_human_review':False},
            'training_eligibility':{'approved':bool(eligible),'scope':'internal_noncommercial_development_only',
               'reason':'Original reviewed; no known unresolved grouping link' if eligible else 'Ambiguous label or unresolved related-image evidence'},
            'physical_garment_identity_verified':False})
    admitted=[r for r in output if r['training_eligibility']['approved']]
    assignment=assign_splits(admitted)
    for row in admitted:row['split']=assignment[row['group_id']]
    old_ids={r['sample_id'] for r in old}
    if old_ids.intersection(r['sample_id'] for r in output):raise ValueError('Duplicate extension')
    return old+output

def main():
    target=ROOT/'data/labels/negative-reviewed-v2.jsonl'
    report_path=ROOT/'data/labels/negative-reviewed-v2.report.json'
    if target.exists() or report_path.exists():raise FileExistsError('Frozen outputs already exist')
    source=ROOT/'data/manifests/negative-candidates-v2.jsonl'
    review_paths=[ROOT/f'records/review/2026-10-14-negative-v2-{part}.json' for part in ('a','b')]
    candidates=rows(source);old_path=ROOT/'data/labels/negative-reviewed-v1.jsonl';old=rows(old_path)
    reviews=[item for p in review_paths for item in json.loads(p.read_text())['reviews']]
    audit_path=ROOT/'records/validation/2026-10-13-expansion-v2-audit.json'
    audit=json.loads(audit_path.read_text())
    excluded={sid for pair in audit['new_near_duplicate_candidates'] for sid in pair['sample_ids']}
    triage_path=ROOT/'records/review/2026-10-13-root-negative-v2-triage.json'
    for flag in json.loads(triage_path.read_text())['flags']:
        excluded.update('fashionpedia-negative-v2-'+sid for sid in flag['source_item_ids'])
    for review in reviews:
        if review.get('related_sample_ids'):
            excluded.add(review['sample_id']);excluded.update(review['related_sample_ids'])
    result=prepare(candidates,reviews,old,excluded)
    positives=rows(ROOT/'data/labels/skirt-baseline-v1.jsonl')
    admitted=[r for r in result if r['training_eligibility']['approved']]
    validate([{**r,'presence_target':1} for r in positives]+[{**r,'presence_target':0} for r in admitted])
    for row in candidates:
        if sha(ROOT/row['original_path'])!=row['sha256']:raise ValueError('Source changed')
    target.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in result),encoding='utf-8')
    report={'status':'frozen_development_only','source_manifest_sha256':sha(source),'manifest_sha256':sha(target),
        'review_sources':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in review_paths],
        'grouping_evidence':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in (audit_path,triage_path)],
        'source_sha256':sha(__file__),'prior_manifest_sha256':sha(old_path),'prior_assignments_preserved':result[:len(old)]==old,
        'counts':{'all_rows':len(result),'admitted':len(admitted),'new_admitted':len(admitted)-sum(r['training_eligibility']['approved'] for r in old),
                  'by_split':dict(Counter(r['split'] for r in admitted))},
        'limitations':['Agent reviewed, not independent human truth','Physical identity not verified','Known ambiguous links quarantined','Source-domain development only']}
    report_path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']))

if __name__=='__main__':main()
