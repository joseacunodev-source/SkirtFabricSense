import json,sys
from pathlib import Path
root=Path.cwd(); rows=sorted([json.loads(x) for x in (root/'data/manifests/skirt_candidates.jsonl').read_text().splitlines()],key=lambda x:x['sample_id'])[:334]
p=int(sys.argv[1]); entries=json.loads(sys.argv[2]); dest=root/'data/labels/skirt-review-batch-a.jsonl'
assert len(entries)==len(rows[(p-1)*12:p*12])
old=[json.loads(x) for x in dest.read_text().splitlines()] if dest.exists() else []
assert not set(x['sample_id'] for x in old)&set(r['sample_id'] for r in rows[(p-1)*12:p*12])
with dest.open('a',encoding='utf8') as f:
 for r,(code,note) in zip(rows[(p-1)*12:p*12],entries):
  label={'p':'pleated','n':'non_pleated','u':'unknown'}[code[0]]; full=code[1]=='1'
  f.write(json.dumps(dict(sample_id=r['sample_id'],image_sha256=r['sha256'],appearance_label=label,full_skirt_view=full,evidence=note,exclude_auxiliary=label=='unknown' or not full,review_artifact=f'records/review/batch-a/page-{p:02}.jpg',reviewer='codex_visual_agent_a',independent_human_review=False))+'\n')
print('appended',len(entries),'page',p)
