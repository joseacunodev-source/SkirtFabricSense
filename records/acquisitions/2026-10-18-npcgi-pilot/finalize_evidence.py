"""Write supplemental inspection evidence; preserve original acquisition report and manifest."""
import hashlib
import json
import importlib.metadata
from pathlib import Path
import sys
import zlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tools.datasets.acquire_npcgi_pilot import verified_index
HERE=Path(__file__).parent
rows=[json.loads(r) for r in (ROOT/'data/manifests/npcgi-pilot-candidates.jsonl').read_text(encoding='utf-8').splitlines()]
notes={
 'F1564':('dress',False,'quarantine_source_category_conflict','Full flat-laid sleeveless belted dress: neck opening, arm openings and upper bodice visible. Source skirt category conflicts with image. Printed F1564 ID visible.'),
 'F0848':('skirt',True,'reviewed_candidate_unadmitted','Flat-laid plaid skirt; entire waistband-to-hem outline contained. Printed F0848 ID visible.'),
 'F1810':('skirt_candidate',None,'quarantine_visibility_uncertain','White elastic-waist garment lies bunched/folded; complete skirt silhouette and hem geometry uncertain. Printed F1810 ID visible.'),
 'F0870':('skirt_candidate',False,'quarantine_incomplete_frame','Black skirt-like garment reaches and is cut by upper image border; complete waistband-to-hem visibility cannot be established. Printed F0870 ID visible.'),
 'F1350':('skirt',True,'reviewed_candidate_unadmitted','Flat-laid dark skirt; waistband and hem contained in image, with some lower material folds. Printed F1350 ID visible.'),
}
review=[]
for r in rows:
 kind,visible,status,note=notes[r['source_item_id']]
 review.append({'source_item_id':r['source_item_id'],'sample_id':r['sample_id'],
   'image_sha256':r['sha256'],'original_path':r['original_path'],
   'reviewer':'agent_fabric_index_recovery','review_date_asia_manila':'2026-10-18',
   'review_method':'Actual original JPEG displayed using view_image; display resized from 4608x3456 to 1824x1368.',
   'observed_garment':kind,'presentation':'flat_laid','care_tag_only':False,
   'visible_source_id_matches':True,'full_garment_visible':visible,'review_status':status,
   'training_eligible':False,'fabric_appearance_label':None,
   'fiber_composition_verified_from_photo':False,'notes':note})
out={'schema_version':1,'date_asia_manila':'2026-10-18','manifest_sha256':hashlib.sha256((ROOT/'data/manifests/npcgi-pilot-candidates.jsonl').read_bytes()).hexdigest(),
     'reviewed_originals':5,'full_view_skirt_candidates':2,'source_category_conflicts':1,
     'training_admissions':0,'worn_photographs':0,'reviews':review,
     'limitations':'One agent visual inspection; source fiber fields are care-label transcriptions, not verified fiber measurements. All flat-laid, so no worn-domain evidence. No appearance taxonomy inferred from fiber names.'}
(HERE/'photo-review.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
ownfiles=['tools/datasets/acquire_npcgi_pilot.py','tests/test_npcgi_pilot.py',
 'tools/datasets/inspect_fabric_7z_header.py','tests/test_fabric_7z_header.py',
 'data/manifests/npcgi-pilot-candidates.jsonl',
 'records/acquisitions/2026-10-18-npcgi-pilot/selection.json',
 'records/acquisitions/2026-10-18-npcgi-pilot/report.json',
 'records/acquisitions/2026-10-18-npcgi-pilot/photo-review.json']
hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ownfiles}
verified_index()
allother=set()
for path in (ROOT/'data/manifests').glob('*.jsonl'):
 if path.name=='npcgi-pilot-candidates.jsonl':continue
 for line in path.read_text(encoding='utf-8-sig').splitlines():
  if not line.strip():continue
  row=json.loads(line)
  value=row.get('sha256')
  if value:allother.add(value)
duplicates=[r['source_item_id'] for r in rows if r['sha256'] in allother]
assert len({r['sha256'] for r in rows})==5 and len({r['decoded_rgb_sha256'] for r in rows})==5
assert not duplicates
for row in rows:
 imagepath=ROOT/row['original_path']
 raw=imagepath.read_bytes()
 assert len(raw)==row['size_bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 assert zlib.crc32(raw)==row['crc32']
 with Image.open(imagepath) as im:
  assert list(im.size)==row['dimensions']
  assert hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()==row['decoded_rgb_sha256']
report={'schema_version':1,'date_asia_manila':'2026-10-18','python':sys.version,
 'python_executable':sys.executable,'pillow_version':importlib.metadata.version('Pillow'),
 'commands':['python tools/datasets/acquire_npcgi_pilot.py',
 'python -m unittest tests.test_fabric_7z_header tests.test_npcgi_pilot -v',
 'python records/acquisitions/2026-10-18-npcgi-pilot/finalize_evidence.py'],
 'outcome':'Five exact-range images acquired; five actual photo inspections; zero training admissions.',
 'focused_tests_passed':16,'packages_installed':0,'hashes':hashes,
 'existing_manifest_file_hashes_compared':len(allother),'exact_file_duplicates_against_other_manifests':duplicates,
 'unique_new_file_hashes':5,'unique_new_rgb_pixel_hashes':5,
 'post_acquisition_original_reverification':'All five file sizes, archive CRC32s, SHA256s, dimensions and RGB pixel hashes rechecked from saved originals.',
 'near_duplicate_and_physical_identity_audit':'Not completed; publisher item IDs provide grouping but are not independent verification of specimen uniqueness.'}
(HERE/'execution.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
idx=ROOT/'records/acquisitions/2026-10-18-fabric-archive-index'
ireport={'schema_version':1,'date_asia_manila':'2026-10-18',
 'outcome':'Recovered existing header bytes offline after parser padding correction; original failed report preserved.',
 'archive_entries':2066,'independent_copy_streams':2066,'solid_folders':0,
 'exact_skirt_ID_matches':25,'header_network_body_bytes':23592,
 'offline_recovery_network_body_bytes':0,'original_images_acquired_by_indexing':0,
 'focused_parser_tests_passed':9,'packages_installed':0,
 'reverification':'decode_header CRC and index equality checked again by verified_index()',
 'sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
 ['tools/datasets/inspect_fabric_7z_header.py','tests/test_fabric_7z_header.py',
  'records/acquisitions/2026-10-18-fabric-archive-index/packed-header.bin',
  'records/acquisitions/2026-10-18-fabric-archive-index/decoded-header.bin',
  'records/acquisitions/2026-10-18-fabric-archive-index/parsed/archive-index.json',
  'records/acquisitions/2026-10-18-fabric-archive-index/parsed/report.json']}}
(idx/'recovery-execution.json').write_text(json.dumps(ireport,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'reviewed':5,'admitted':0,'full_view_skirt_candidates':2,'source_category_conflicts':1,'exact_file_duplicates':duplicates}))
