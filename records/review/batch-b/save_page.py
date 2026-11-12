import json, sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
idx=json.loads((root/'records/review/batch-b/index.json').read_text())
page=int(sys.argv[1]); annotations=json.loads(sys.argv[2])
path=root/'data/labels/skirt-review-batch-b.jsonl'
rows=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
for j,(code,note) in enumerate(annotations):
    r=dict(idx[(page-1)*12+j]); r.pop('index')
    r.update(appearance_label={'N':'non_pleated','P':'pleated','U':'unknown'}[code.upper()],full_skirt_view=code.isupper() and code!='U', evidence=note,exclude_auxiliary=code not in ('N','P'),reviewer='codex-visual-agent-b',independent_human_review=False)
    assert not any(x['sample_id']==r['sample_id'] for x in rows)
    rows.append(r)
path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
print(len(rows))
