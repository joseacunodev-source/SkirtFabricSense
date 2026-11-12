import pathlib,hashlib,json,zipfile,collections,urllib.request
out=pathlib.Path('records/acquisitions/2026-10-11-fabric-partition')
src=out/'response.bin'
lines=src.read_text().splitlines(); declared=int(lines[0]); assert lines[1].split()==['image_name','item_id','evaluation_status']
rows=[l.split() for l in lines[2:] if l.strip()]
assert len(rows)==declared==52712 and all(len(r)==3 for r in rows)
assert set(r[2] for r in rows)=={'train','query','gallery'}
lookup={r[0].removeprefix('img/').replace('/','-'):r for r in rows}; assert len(lookup)==len(rows)
zpath=pathlib.Path('records/acquisitions/2026-10-09-deepfashion-multimodal/labels-response.bin')
with zipfile.ZipFile(zpath) as z: fabric=[l.split() for l in z.read('labels/texture/fabric_ann.txt').decode().splitlines() if l.startswith('WOMEN-Skirts-')]
assert len(fabric)==848
joined=[]
for r in fabric:
 s=lookup.get(r[0]); token=r[0].split('-')[2]
 joined.append({'filename':r[0],'filename_item_token':token,'lower_fabric_source_code':int(r[2]),'official_image_name':s[0] if s else None,'official_item_id':s[1] if s else None,'official_split':s[2] if s else None,'project_split':None,'training_admitted':False})
(out/'skirt-partition-join.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in joined),encoding='utf-8')
groups=collections.defaultdict(set)
for r in joined:
 if r['official_item_id']: groups[r['official_item_id']].add(r['official_split'])
cross=[k for k,v in groups.items() if 'train' in v and (v & {'query','gallery'})]
unknown=[r['filename'] for r in joined if r['official_split'] is None]
counts=dict(collections.Counter(r['official_split'] for r in joined))
labelcounts={s:dict(collections.Counter(r['lower_fabric_source_code'] for r in joined if r['official_split']==s)) for s in ['train','query','gallery']}
url='https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html'
with urllib.request.urlopen(url,timeout=45) as r: terms=r.read(1000000)
(out/'official-terms.html').write_bytes(terms)
rec={'schema_version':1,'date_asia_manila':'2026-10-11','status':'official_partition_acquired_and_joined','partition_rows':len(rows),'partition_counts':dict(collections.Counter(r[2] for r in rows)),'candidate_skirt_rows':len(joined),'candidate_counts_by_original_partition':counts,'unmatched_filenames':unknown,'filename_item_tokens':len(set(r['filename_item_token'] for r in joined)),'official_item_ids':len(groups),'train_item_ids_overlapping_query_or_gallery':cross,'query_gallery_shared_item_ids':sum(v=={'query','gallery'} for v in groups.values()),'candidate_group_partition_combinations':dict(collections.Counter('+'.join(sorted(v)) for v in groups.values())),'filename_token_official_id_mismatches':sum(r['official_item_id'] is not None and r['filename_item_token']!=r['official_item_id'] for r in joined),'lower_fabric_source_code_counts_by_partition':labelcounts,'join_rule':'Remove literal img/ prefix from official image path, replace path separators with hyphens; require exact full filename match. No fuzzy or inferred membership.','labels_zip_sha256':hashlib.sha256(zpath.read_bytes()).hexdigest(),'source_urls':[json.loads((out/'retry.json').read_text())['url'],url],'terms_summary':'Non-commercial research only. Further copying/publication/distribution restricted; internal single-site copies in same organization allowed. No images downloaded and no encrypted data accessed.','complete_new_images':0,'training_admission':False,'project_splits_promoted':False,'limitations':['Source item IDs are source grouping evidence, not verified physical specimens.','Query and gallery are original retrieval test partitions; shared test item IDs are expected and must remain together for project grouping.','Visual label/full-view suitability/duplicates and project fabric ontology remain unresolved.','No original source held-out images may be promoted to training.']}
rec['artifacts']=[{'path':str(p).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.iterdir() if p.is_file()]
pathlib.Path('records/review/2026-10-11-fabric-partition.json').write_text(json.dumps(rec,indent=2)+'\n')
print(json.dumps(rec,indent=2))
