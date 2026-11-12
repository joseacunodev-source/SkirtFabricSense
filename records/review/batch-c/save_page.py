import json,sys
from pathlib import Path
root=Path.cwd(); idx=json.loads((root/'records/review/batch-c/index.json').read_text())
page=int(sys.argv[1]); entries=json.loads(sys.argv[2]); assert len(entries)==len(idx[page*16:page*16+16])
out=root/'data/labels/skirt-review-batch-c.jsonl'; existing=[json.loads(s) for s in out.read_text().splitlines()] if out.exists() else []
ids={r['sample_id'] for r in idx[page*16:page*16+16]}; existing=[r for r in existing if r['sample_id'] not in ids]
for item,(code,note) in zip(idx[page*16:page*16+16],entries):
 label={'n':'non_pleated','p':'pleated','u':'unknown'}[code[0]]; full=code[1]=='1'
 existing.append(dict(sample_id=item['sample_id'],image_sha256=item['image_sha256'],appearance_label=label,full_skirt_view=full,evidence=note,exclude_auxiliary=label=='unknown' or not full,review_artifact=item['sheet'],reviewer='codex-visual-agent-c',independent_human_review=False))
out.write_text(''.join(json.dumps(r)+'\n' for r in sorted(existing,key=lambda r:r['sample_id'])),encoding='utf-8');print(len(existing))
