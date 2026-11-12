"""Verify saved metadata and emit a candid source-search decision record."""
import csv
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def html_text(name):
    parser = TextOnly()
    parser.feed((HERE/name).read_text(encoding='utf-8'))
    return ' '.join(' '.join(parser.parts).split())


def main():
    acquisition = json.loads((HERE/'acquisition.json').read_text(encoding='utf-8'))
    files = []
    for record in acquisition['requests']:
        if record['outcome'].startswith('saved'):
            path = HERE/record['path']
            require(path.stat().st_size == record['body_bytes'] and sha(path) == record['sha256'],
                    'Saved response changed: '+record['path'])
            files.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),
                          'bytes':path.stat().st_size,'url':record['url'],'http_status':record['http_status']})
    require(sum(r['body_bytes'] for r in acquisition['requests']) == acquisition['total_body_bytes_read']
            <= acquisition['body_budget_bytes'], 'Body accounting mismatch')
    labels = list(csv.DictReader(io.StringIO((HERE/'imaterialist2018-label-map.csv').read_text(encoding='utf-8'))))
    require(len(labels) == 228 and len({r['labelId'] for r in labels}) == 228, 'Label-map count mismatch')
    label_ids = {'Chiffon':44,'Cotton':53,'Denim':59,'Knit':97,'Lace':98,'Leather':99,
                 'Polyester':137,'Satin':158,'Skirts':170,'Pencil Skirts':127,'Pleated':133}
    observed = {}
    for name, expected in label_ids.items():
        found = [r for r in labels if r['labelName'] == name]
        require(len(found) == 1 and int(found[0]['labelId']) == expected, 'Exact label identity changed: '+name)
        observed[name] = {'label_id':expected,'task_id':int(found[0]['taskId']),'task_name':found[0]['taskName']}
    imat2020 = (HERE/'imaterialist2020-README.md').read_text(encoding='utf-8')
    require('github.com/cvdfoundation/fashionpedia' in imat2020, '2020 COCO source bridge absent')
    textile = (HERE/'textilenet-README.md').read_text(encoding='utf-8')
    require('MIT' in textile and 'Author Accepted Manuscript' in textile, 'Repository license wording changed')
    textile_paper = html_text('textilenet-paper.html')
    require('Creative Commons Attribution' in textile_paper and 'collected data' in textile_paper,
            'Paper dataset-licence claim not found')
    require('garment items rather than textile items' in textile_paper
            and 'cropped images with human faces' in textile_paper,
            'Garment/cropping source claim missing')
    require('not included fibre blends' in textile_paper and 'Label noise' in textile_paper,
            'Source blend/noise limitations missing')
    homepage = next(r for r in acquisition['requests'] if r['url'] == 'https://fashion-gen.com/')
    require(homepage['http_status'] == 403, 'Observed homepage status differs from planned report')
    report = {
        'schema_version':1,'date_asia_manila':'2026-10-21','status':'primary_metadata_review_complete_no_image_admission',
        'reviewer':'codex-agent-fabric_search_oct21','scope':'Official repositories and papers; bounded public metadata snapshots only.',
        'acquisition':{'path':(HERE/'acquisition.json').relative_to(ROOT).as_posix(),'sha256':sha(HERE/'acquisition.json'),
                       'direct_response_body_bytes':acquisition['total_body_bytes_read'],
                       'direct_response_body_budget_bytes':acquisition['body_budget_bytes'],
                       'responses':len(acquisition['requests']),'http200_responses':sum(r['http_status']==200 for r in acquisition['requests']),
                       'error_bodies_saved':sum(r['http_status']!=200 for r in acquisition['requests']),
                       'note':'Byte accounting covers this direct acquisition script; web-tool search/open reads are separate and not locally measured.'},
        'checked_snapshots':files,'repository_revisions':acquisition['resolved_repository_revisions'],
        'sources':[
            {'source_id':'imaterialist-fashion-2018','priority':1,
             'official_url':'https://github.com/visipedia/imat_fashion_comp',
             'paper_url':'https://openaccess.thecvf.com/content_ICCVW_2019/papers/CVFAD/Guo_The_iMaterialist_Fashion_Attribute_Dataset_ICCVW_2019_paper.pdf',
             'observed_label_map_rows':228,'selected_exact_label_rows':observed,
             'source_annotation_scope':'Image-level multiple labels; material and garment category co-occurrence is not an instance-level fabric assignment.',
             'advertised_source_partition_images':{'train':1012947,'validation':9897,'test':39706},
             'advertised_counts_not_project_counts':True,
             'locally_acquired_annotation_records':0,'locally_acquired_garment_images':0,
             'source_schema_fields':{'images':['image_id','url'],'annotations':['image_id','label_id']},
             'product_identity_field_published_in_readme_schema':False,
             'terms_status':'No explicit photo-use grant observed in saved README/repository metadata; Kaggle rules page had no readable text in web tool.',
             'readable_rules_verified':False,'photo_rights_verified':False,'product_grouping_verified':False,
             'training_admitted':False,
             'next_step':'Resolve exact image-use/attribution terms, then declare a bounded official-train-only metadata intake and item/near-duplicate grouping review before selecting full-skirt photos.'},
            {'source_id':'imaterialist-fashion-2020','priority':None,
             'official_url':'https://github.com/visipedia/imat_comp',
             'annotation_link_resolves_to':'https://github.com/cvdfoundation/fashionpedia',
             'status':'Existing Fashionpedia source, not a distinct fabric-label expansion',
             'new_images':0,'training_admitted':False},
            {'source_id':'textilenet','priority':2,'official_url':'https://github.com/hahashu/TextileNet',
             'paper_url':'https://arxiv.org/html/2301.06160v1',
             'source_presentation':'Garment-oriented Internet images; source processing includes face/body cropping. Complete worn skirts are not guaranteed.',
             'source_overlap':'Paper says reconstructed iMaterialist and Amazon images plus Google Image Search; do not treat as an independent source holdout without identity audit.',
             'label_limitations':'Separate fibre/fabric taxonomies; absent blend metadata, query/crowdsourcing noise and ambiguous multiple material labels.',
             'repository_license_claim':'MIT for collection code; CC BY sentence refers to Author Accepted Manuscript.',
             'paper_appendix_f_license_claim':'CC BY asserted for extending the taxonomies and collected data; code MIT.',
             'rights_interpretation':'Preserve both statements. The paper provides a dataset-level CC BY claim, but exact version, third-party photo attribution/authority and source-specific terms remain unverified for project admission.',
             'full_skirt_visibility_verified':False,'source_grouping_verified':False,'photo_rights_verified':False,
             'new_images':0,'training_admitted':False,
             'next_step':'Reconcile publisher grant/version and source-photo attribution; inspect metadata for original partitions and iMaterialist/product overlap before a bounded skirt-only photo review.'},
            {'source_id':'fashiongen','priority':3,'paper_url':'https://arxiv.org/html/1806.08317v2',
             'official_url':'https://fashion-gen.com/','observed_homepage_http_status':403,
             'access_interpretation':'Official homepage inaccessible in web tool and direct request denied. This does not establish a login requirement or dataset-wide unavailability.',
             'paper_evidence':'Product descriptions and multiple views per item; grouping would be essential if access becomes available.',
             'current_dataset_access_verified':False,'photo_rights_verified':False,'new_images':0,'training_admitted':False}
        ],
        'new_garment_images':0,'new_training_admissions':0,'verified_fabric_labels_added':0,
        'frozen_splits_changed':False,'packages_installed':0,'hardware_verified':False,
        'safety_of_interpretation':'Publisher labels remain publisher evidence, missing labels stay missing, overlapping fibre/construction labels are retained separately; no composition measurement or skirt-specific label is inferred.',
        'web_access_observations':[
            {'url':'https://www.kaggle.com/competitions/imaterialist-challenge-fashion-2018/rules','outcome':'Web tool returned no readable page text; no rules conclusion derived'},
            {'url':'https://github.com/visipedia/imat_fashion_comp_2020','outcome':'404 mistaken candidate URL; actual2020 repository is visipedia/imat_comp'}],
        'analysis_source_sha256':sha(Path(__file__)),
        'local_cross_checks':'Every saved response size/hash, total body accounting,228 unique label IDs,11 exact selected label IDs,2020 source link and TextileNet paper/repository claims rechecked from snapshots.'
    }
    output = ROOT/'records/review/2026-10-21-fabric-source-search.json'
    with output.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,indent=2,ensure_ascii=False); stream.write('\n')
    print(json.dumps({'snapshots_verified':len(files),'label_map_rows':len(labels),
                      'material_label_rows':sum(r['taskName']=='material' for r in labels),'new_images':0,'admissions':0}))


if __name__ == '__main__':
    main()
