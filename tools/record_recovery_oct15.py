"""Register verified recovery artifacts without promoting models or metadata."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def ref(path):return {'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}
def main():
    path=ROOT/'data/registry.json';registry=json.loads(path.read_text())
    model='records/models/2026-10-15-skirt-localizer-v3.json'
    if model not in {r['path'] for r in registry['development_experiments']}:
        registry['development_experiments'].append(ref(model))
    source={'source':'DeepFashion CategoryAttribute Anno_fine',
        'evidence':[ref('records/acquisitions/2026-10-14-attribute-metadata/'+name) for name in ('report.json','feasibility.json','partition-feasibility.json')],
        'metadata_skirt_references':680,'original_partitions':{'train':422,'validation':66,'test':192},
        'broader_holdout_attribute_rows_exposed_during_metadata_inspection':258,
        'complete_images_added':0,'training_admitted':False,'eligible_after_conservative_folder_group_check':0,
        'limitation':'Descriptive folder tokens are not verified garment identities; unresolved overlap with original holdouts'}
    registry['supplementary_metadata']=[r for r in registry.get('supplementary_metadata',[]) if r.get('source')!=source['source']]+[source]
    registry['physical_garment_access']={'date':'2026-10-14','source':'user','status':'neither_skirts_nor_raspberry_pi_available'}
    registry['updated_date_asia_manila']='2026-10-15'
    path.write_text(json.dumps(registry,indent=2)+'\n',encoding='utf-8')
    print('Registered unpromoted v3 and metadata-only source audit; original count unchanged')
if __name__=='__main__':main()
