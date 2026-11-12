"""Map existing frozen identity inventory; create zero geometry observations."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.evaluate_worn_geometry import CONVENTION, PROJECTION, evaluate_from_files


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2); stream.write('\n')


def main():
    source = ROOT/'data/manifests/worn-pleating-development-v1.jsonl'
    if sha(source) != '876bb315009592fdbcf0a646703b21d99801756f4e37b1807a66675bdbd98ec2':
        raise ValueError('Frozen source changed')
    rows = [json.loads(line) for line in source.read_text(encoding='utf-8').splitlines()]
    inventory = [{'sample_id':r['sample_id'],'garment_group_id':r['group_hash'],
        'split':r['split'],'original_path':r['original_path'],'image_sha256':r['sha256']} for r in rows]
    folder = ROOT/'records/geometry/2026-10-21-readiness'
    folder.mkdir(parents=True,exist_ok=False)
    inv, ann, pred = (folder/name for name in ('frozen-inventory.json','annotations-empty.json','predictions-empty.json'))
    save(inv,inventory)
    save(ann,{'schema_version':1,'data_kind':'observed_development_geometry_annotations',
              'coordinate_convention':CONVENTION,'projection':PROJECTION,'examples':[],
              'note':'No actual geometry observations exist. Schema readiness only; no coordinates are supplied.'})
    save(pred,{'schema_version':1,'prediction_kind':'saved_geometry_extractor_inputs',
        'coordinate_convention':CONVENTION,'projection':PROJECTION,
        'annotation_sha256':sha(ann),'split_sha256':sha(inv),'predictions':[],
        'producer':{'name':'empty_readiness_inventory_no_detector',
                    'source_sha256':sha(Path(__file__)),
                    'evidence':'No observed geometry annotations or saved detector inputs are available.'}})
    output = ROOT/'records/validation/2026-10-21-geometry-readiness.json'
    report = evaluate_from_files(ann,inv,pred,output,source_root=ROOT)
    if report['counts']['observed_development_examples'] != 0 or report['image_coverage'] is not None:
        raise ValueError('Empty readiness unexpectedly claimed geometry evidence')
    mapping = {'status':'inventory_mapped_no_geometry_observations',
        'source':{'path':source.relative_to(ROOT).as_posix(),'sha256':sha(source)},
        'inventory':{'path':inv.relative_to(ROOT).as_posix(),'sha256':sha(inv)},
        'source_rows':len(rows),'observed_geometry_examples':0,
        'unannotated_validation_members':len(report['unannotated_validation_inventory_members']),
        'group_mapping':'garment_group_id equals preserved source group_hash; physical identity unverified',
        'split_changed':False,'training_admissions':0,'packages_installed':0,
        'source_sha256':sha(Path(__file__))}
    save(folder/'mapping.json',mapping)
    print(json.dumps(mapping,indent=2))


if __name__ == '__main__':
    main()
