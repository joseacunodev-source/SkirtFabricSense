"""Freeze source-appearance pipeline-smoke data; never composition ground truth."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLASSES = ['source_cotton_appearance', 'source_denim_appearance', 'source_leather_appearance', 'source_chiffon_appearance']
# Original-pixel visual ROIs reviewed by the agent, not automatic localization.
ROIS = {
 '00000003': [103,568,440,908], '00000111':[197,619,578,1037],
 '00000200':[194,407,381,784], '00000334':[290,388,466,755],
 '00000467':[257,363,462,715], '00000545':[183,400,352,777],
 '00000644':[266,578,690,983], '00000670':[159,613,659,1053],
 '00000699':[151,389,467,996], '00002711':[253,374,571,813],
 '00004182':[261,383,528,920], '00004335':[282,389,523,650],
 '00004513':[193,619,515,1013], '00005519':[199,399,482,1057],
 '00005894':[102,582,598,1034], '00006184':[218,611,612,1060],
 '00007127':[173,399,418,731],
}
EXCLUDED = {
 '00000328':'Top hides waistband; retain outside full-skirt smoke pool.',
 '00000992':'Blouse hides waistband.',
 '00002342':'Large handbag occludes substantial skirt surface.',
 '00003178':'Top hides waistband and leaning pose distorts view.',
 '00003386':'Seated; top hides waist; lace/net appearance makes source chiffon interpretation ambiguous.',
 '00003995':'Shirt hides waistband.',
 '00005441':'Top hides waistband.',
 '00006548':'Top hides part of waistband.',
}
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def prepare(rows):
    seen_ids, seen_hashes, seen_groups = set(), set(), set()
    admitted, review = [], []
    for row in rows:
        token = row['source_item_token'].removeprefix('id_')
        for value, seen in [(row['sample_id'],seen_ids),(row['sha256'],seen_hashes),(row['group_id'],seen_groups)]:
            if value in seen: raise ValueError('Duplicate identity, hash or source group')
            seen.add(value)
        if row['source_partition'] != 'train': raise ValueError('Protected source partition')
        if token not in ROIS and token not in EXCLUDED: raise ValueError('No explicit visual review')
        label = 'source_' + row['source_lower_fabric_label'] + '_appearance'
        if label not in CLASSES: raise ValueError('Unsupported appearance label')
        review.append({'sample_id':row['sample_id'],'sha256':row['sha256'], 'original_opened':True,
            'decision':'smoke_only' if token in ROIS else 'excluded',
            'reason':EXCLUDED.get(token,'Waist-to-hem region visible; modest hand occlusions remain. Source appearance label preserved, not visually verified composition.'),
            'roi_xyxy':ROIS.get(token)})
        if token in ROIS:
            box=ROIS[token]
            if not (0 <= box[0] < box[2] <= row['width'] and 0 <= box[1] < box[3] <= row['height']): raise ValueError('Invalid ROI')
            admitted.append(dict(row, label=label,roi_xyxy=box,training_admitted=True,
                admission_scope='internal_pipeline_smoke_only', full_skirt_visibility='agent_reviewed',
                composition_verified=False, independent_human_review=False))
    for label in CLASSES:
        group = sorted([r for r in admitted if r['label']==label],key=lambda r:hashlib.sha256(('42:'+r['group_id']).encode()).hexdigest())
        if len(group)<2: raise ValueError('At least two source groups required per smoke class')
        nv = max(1,len(group)//4)
        for i,row in enumerate(group): row['split']='development_validation' if i<nv else 'development_train'
    return admitted,review

def main():
    source=ROOT/'data/manifests/fullview-fabric-candidates-v1.jsonl'
    rows=[json.loads(x) for x in source.read_text().splitlines()]
    for r in rows:
        if sha(ROOT/r['original_path'])!=r['sha256']: raise ValueError('Image hash mismatch')
    admitted,review=prepare(rows)
    outputs={
      ROOT/'data/labels/fabric-pilot-v1.jsonl': ''.join(json.dumps(r,sort_keys=True)+'\n' for r in admitted),
      ROOT/'data/labels/fabric-pilot-v1-splits.json': json.dumps({'seed':42,'purpose':'pipeline smoke only; not reliable validation','assignments':[{'sample_id':r['sample_id'],'group_id':r['group_id'],'split':r['split']} for r in admitted]},indent=2)+'\n',
      ROOT/'records/review/2026-10-11-fabric-pilot.json':json.dumps({'source_sha256':sha(source),'reviewer':'codex_fabric_pilot_agent','independent_human_review':False,'originals_opened':25,'source_terms':'records/acquisitions/2026-10-09-deepfashion-multimodal/LICENSE','terms_sha256':sha(ROOT/'records/acquisitions/2026-10-09-deepfashion-multimodal/LICENSE'),'rights_scope':'Noncommercial research; internal copies only; not redistribution','classes':CLASSES,'review':review,'counts':dict(Counter(r['label'] for r in admitted)), 'limitations':['Source item groups are not verified physical specimens','No near-identical skirts apparent in original review; styling/model/background correlations remain','Cotton source category does not establish fiber composition','Only two groups each for leather and chiffon; metrics cannot establish feasibility','Original query/gallery excluded; no final test']},indent=2)+'\n'}
    for path,content in outputs.items():
        if path.exists() and path.read_text()!=content: raise FileExistsError(path)
    for path,content in outputs.items(): path.write_text(content)
    print(json.dumps({'admitted':len(admitted),'excluded':len(review)-len(admitted),'splits':dict(Counter(r['split'] for r in admitted))}))
if __name__=='__main__': main()
