"""Freeze conservative agent-reviewed negatives; no original split is changed."""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA = 'c4306ef7afacfde2e35daf1c6d5144c026075e5944180e2f38d46b9730470d02'
# All admitted records were inspected as full originals, not just thumbnails.
CLEAR = {
 '27765': 'Continuous blue dress from bodice through hem; isolated subject on dark background.',
 '21184': 'Separate shorts legs clearly visible on isolated beach subject.',
 '30036': 'Flag-print shorts with separate leg openings; isolated studio subject.',
 '1853': 'Rear-view blue romper has visible separate leg openings; isolated beach subject.',
 '42119': 'Visible divided denim legs above tall boots; no separate skirt.',
 '49787': 'Continuous white one-shoulder gown from bodice to floor hem; studio subject.',
 '43635': 'Two clearly separated red trouser legs; isolated studio subject.',
 '3886': 'Continuous white gown from bodice to hem; isolated beach subject.',
 '13377': 'Black trousers have separate full visible legs; single event-wall subject.',
 '35794': 'Continuous patterned shirt dress on mannequin, collar to hem visible.',
 '43923': 'Continuous striped maxi dress from bodice to hem; isolated outdoor subject.',
 '13841': 'Black fitted trousers with clearly separate legs; isolated posed subject.'}
FULL_REVIEW = set(CLEAR) | {'43158','20870','15267','19184','32440','13916','39262','21106','49655','47945'}
RUNWAY = {'25065','2544','23236','17620','10008','10970','16930','19986','1632','12125','12902','11929','10484','10014','7444','4708','6493','1410','14673','25061','21531'}
GROUP_UNRESOLVED = {'15267','32440','13916'}  # recurring eyestrain photographer watermark
CROWDED = {'43158','20870','37200','12088','48320','5176','19184','47223','24908','24817','7572'}
ALLOWED = {'Attribution License','Attribution-ShareAlike License','Attribution-NonCommercial License','Attribution-NonCommercial-ShareAlike License','Public Domain Dedication'}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def assign_splits(rows):
    """Category-stratified groups; deterministic hash rank, nearest 25% held out."""
    groups = defaultdict(list)
    for r in rows:
        groups[r['group_id']].append(r)
    buckets = defaultdict(list)
    for gid, members in groups.items():
        cats = {r['sampling_bucket'] for r in members}
        if len(cats) != 1:
            raise ValueError('mixed-category group requires explicit split policy')
        buckets[next(iter(cats))].append(gid)
    result = {}
    for gids in buckets.values():
        gids.sort(key=lambda g: hashlib.sha256(('negative-v1-seed-20261011:' + g).encode()).hexdigest())
        nval = max(1, round(len(gids) * .25)) if len(gids) > 1 else 0
        for i, gid in enumerate(gids):
            result[gid] = 'development_validation' if i < nval else 'development_train'
    return result

def prepare(source, root=ROOT, positive=None):
    if sha(source) != SOURCE_SHA:
        raise ValueError('candidate source hash mismatch: review does not apply')
    rows = [json.loads(line) for line in Path(source).read_text().splitlines() if line]
    if len(rows) != 90 or len({r['sample_id'] for r in rows}) != 90:
        raise ValueError('expected 90 unique candidates')
    positive = positive or []
    positive_groups = {r['group_id'] for r in positive}
    positive_hashes = {r['sha256'] for r in positive}
    out = []
    for i, original in enumerate(rows):
        r = deepcopy(original)
        sid = r['source_item_id']
        if sha(root / r['original_path']) != r['sha256']:
            raise ValueError('original image hash mismatch: ' + sid)
        reasons = []
        if r['source_license']['name'] not in ALLOWED:
            reasons.append('rights_review_pending: ND restriction or non-CC/unknown terms; conservative exclusion, not a legal finding')
        if sid == '1632':
            reasons.append('unresolved cross-pool perceptual matches with skirt1796 and skirt7330')
        if sid in RUNWAY:
            reasons.append('runway/session correlation and background audience unresolved; not assigned across splits')
        if sid in GROUP_UNRESOLVED:
            reasons.append('recurring eyestrain watermark/source correlation requires cross-pool session audit')
        if sid in CROWDED:
            reasons.append('additional cropped/background people make whole-image absence uncertain')
        if sid not in CLEAR:
            reasons.append('not admitted: cropped/obscured garment, ambiguous silhouette, or unresolved source/session evidence in conservative review')
        if r['group_id'] in positive_groups or r['sha256'] in positive_hashes:
            reasons.append('positive source-group or hash overlap')
        admitted = not reasons
        r.update(label='no_skirt' if admitted else None, split=None,
                 task='agent_reviewed_skirt_absence_v1',
                 label_status='single_agent_visual_review_pending_human_review',
                 grouping_review_pending=not admitted,
                 group_hash=hashlib.sha256(r['group_id'].encode()).hexdigest())
        r['project_labels'] = {'skirt_presence': 'no_skirt' if admitted else None,
                               'status': 'agent_reviewed_pilot' if admitted else 'quarantined'}
        r['training_eligibility'] = {'approved': admitted, 'scope': 'internal_noncommercial_development_only',
                                     'reason': CLEAR[sid] if admitted else '; '.join(reasons)}
        r['label_evidence'] = {'reviewer':'codex_negative_admission_agent', 'independent_human_review':False,
                              'review_date':'2026-10-11', 'image_sha256':r['sha256'],
                              'original_inspected': sid in FULL_REVIEW,
                              'contact_sheet':f'records/acquisitions/2026-10-11-negatives/contact-sheet-{i//24+1:02d}.jpg',
                              'observation':CLEAR.get(sid, '; '.join(reasons)), 'quarantine_reasons':reasons}
        r['grouping_evidence'] = {'method':'source URL group plus combined exact/pixel/dhash audit; conservative visual exclusion of recurring sessions',
                                  'audit':'records/validation/2026-10-11-combined-intake-audit.json',
                                  'physical_garment_identity_verified':False}
        out.append(r)
    assignments = assign_splits([r for r in out if r['training_eligibility']['approved']])
    for r in out:
        r['split'] = assignments.get(r['group_id']) if r['training_eligibility']['approved'] else None
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output', type=Path, default=ROOT/'data/labels/negative-reviewed-v1.jsonl')
    p.add_argument('--report', type=Path, default=ROOT/'data/labels/negative-reviewed-v1.report.json')
    a=p.parse_args()
    source=ROOT/'data/manifests/negative-candidates-v1.jsonl'
    positives=[json.loads(x) for x in (ROOT/'data/labels/skirt-baseline-v1.jsonl').read_text().splitlines()]
    rows=prepare(source, positive=positives)
    text=''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows)
    if a.output.exists() or a.report.exists():
        raise SystemExit('Refusing to overwrite frozen outputs')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(text, encoding='utf-8', newline='\n')
    admitted=[r for r in rows if r['training_eligibility']['approved']]
    report={'schema_version':1,'date':'2026-10-11','manifest':a.output.relative_to(ROOT).as_posix(),
            'manifest_sha256':sha(a.output),'source_manifest_sha256':SOURCE_SHA,
            'preparation_source_sha256':sha(__file__),
            'reviewed_candidates':len(rows),'admitted_images':len(admitted),'quarantined_images':len(rows)-len(admitted),
            'full_originals_inspected':len(FULL_REVIEW),'split_counts':dict(Counter(r['split'] for r in admitted)),
            'split_category_counts':dict(Counter(r['split']+':'+r['sampling_bucket'] for r in admitted)),
            'split_hash':hashlib.sha256(json.dumps(sorted((r['sample_id'],r['group_hash'],r['split']) for r in admitted)).encode()).hexdigest(),
            'positive_manifest_sha256':sha(ROOT/'data/labels/skirt-baseline-v1.jsonl'),
            'source_partitions_preserved':True,'human_review':False,
            'limitations':['Small agent-reviewed development pilot, not independent test truth.',
                           'No empty room, blur or webcam domain examples.',
                           'Source license metadata retained; original photographer title attribution and distribution clearance remain required before redistribution.',
                           'No independently verified physical garment or capture-session IDs; visually recurring sessions excluded.']}
    a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
