# Fabric-source search — October 21, 2026

Superseding October22 follow-up: the actual2018 rules are now readable, and the existing TextileNet training URL cache has an executable identity audit. The search below preserves its original observations. [Current source gate](FABRIC_SOURCE_GATE_OCT22.md).

The best new metadata lead is **iMaterialist Fashion 2018**, which is distinct from the Fashionpedia-based 2020 challenge. It has relevant material and skirt tags, but photo terms, product grouping and skirt-specific label association remain unresolved. This pass added **zero garment images, zero training admissions and zero verified fabric labels**. Existing splits and the 1,932-original collection are unchanged.

The [source-search record](../records/review/2026-10-21-fabric-source-search.json) binds 15 saved public responses to their hashes and pins three official repositories. Direct acquisition read 497,928 body bytes under a 2 MiB budget; 14 responses succeeded and the FashionGen homepage returned a saved HTTP403 body. Search/open-tool reads are separate from this measured direct-download accounting. No dataset archive, garment photograph, login, package installation or outgoing message was used. [Acquisition and exact URLs](../records/acquisitions/2026-10-21-fabric-source-research/acquisition.json).

## 1. iMaterialist Fashion 2018: investigate first

The [official repository](https://github.com/visipedia/imat_fashion_comp) describes Wish-provided images with multiple image-level labels and separate train/validation/test URL manifests. Its illustrated schema has image IDs, URLs and label lists; it does not document a product identity field. Advertised partition sizes are source metadata, not acquired project images. No image annotation manifest was downloaded in this pass. The pinned revision is `ed94853da2c830667b1f8d67a26d7f782eb2e6b2`.

The [official label CSV](https://github.com/visipedia/imat_fashion_comp/blob/ed94853da2c830667b1f8d67a26d7f782eb2e6b2/iMat_fashion_2018_label_map_228.csv) contains 228 unique labels, including 34 material labels. Exact relevant IDs were checked from the saved CSV:

| Source group | Exact label IDs |
|---|---|
| Material | Chiffon44, Cotton53, Denim59, Knit97, Lace98, Leather99, Polyester137, Satin158 |
| Category | Skirts170, Pencil Skirts127 |
| Style | Pleated133 |

Cotton/polyester and chiffon/denim remain overlapping textile dimensions. Preserve the publisher's material tags rather than forcing an exclusive project class. A skirt tag and material tag on the same outfit do not prove that the material belongs to the skirt; original-photo and garment-association review is mandatory. A Pleated style tag alone does not establish a full visible skirt.

**Current blockers:** no explicit photo-use grant was observed in the saved README/repository metadata; the [competition rules page](https://www.kaggle.com/competitions/imaterialist-challenge-fashion-2018/rules) supplied no readable text through the web tool. Current image-URL availability, complete framing and specimen grouping are untested. Repository visibility and paper availability do not settle image permissions.

**Next action:** resolve the exact image-use and attribution terms, then declare a separately bounded **official-train-only** metadata intake. Audit product/URL and near-duplicate groups before selecting a small skirt/material cohort for actual full-view inspection. Preserve original validation/test membership; do not use those labels to fill class shortages. Do not bulk-download a million-image manifest merely to increase a count.

## 2. TextileNet: relevant garments, qualified rights and label evidence

The [paper](https://arxiv.org/html/2301.06160v1) describes garment-oriented images from Internet queries and reconstructed iMaterialist/Amazon data, including face/body cropping. Complete worn skirts and independent source holdouts are therefore not guaranteed. Its separate fibre/fabric taxonomies have label-noise and blend-metadata limitations.

There is more licence evidence than the earlier repository-only review recorded: Appendix F asserts CC BY for extending the collected data and taxonomies. The [repository README](https://github.com/hahashu/TextileNet) instead explicitly assigns MIT to collection code and phrases its CC BY sentence around an accepted manuscript. Preserve both statements. The paper provides a dataset-level licence claim; it does not independently verify every upstream photo's attribution/authority or resolve overlapping source identities. Neither statement should silently become a blanket photo-permission conclusion.

**Next action:** reconcile the applicable dataset grant/version and source-photo attribution, then inspect original partitions and item/source overlap before a bounded skirt-only review. Earlier failed Wish URLs and archive size observations are historical, not proof that every image is unavailable. No archive or image URL was retried here. Pinned repository revision: `6b4f0579b2abc18422192afea07882f84dcb83e4`.

## 3. FashionGen: access unresolved

The [publisher paper](https://arxiv.org/html/1806.08317v2) describes expert product descriptions and multiple views per item. Grouping all views of each product would be essential. The [official homepage](https://fashion-gen.com/) was inaccessible through the web tool and returned HTTP403 in the bounded direct request. This is an observed access failure, **not** evidence of a current login requirement or permanent dataset unavailability. Current dataset terms, accessible downloads and material-to-skirt association remain unverified. No images were obtained.

## Do not repeat the 2020 source as an expansion

The 2020 challenge's [official repository](https://github.com/visipedia/imat_comp) links its alternate COCO annotations directly to [Fashionpedia](https://github.com/cvdfoundation/fashionpedia). It is not an independent source of the missing fabric classes. The [existing 1,000-image attribute audit](FABRIC_SOURCE_ATTRIBUTE_AUDIT_OCT20.md) already found no defensible expansion for the current appearance pilot. Pinned challenge revision: `f0f93fccc80c343ca187d30090a6eb2cf1099c14`.

These are researched candidates and remaining admission gates, not completed data collection or stronger fabric training. The [fabric readiness plan](FABRIC_NEXT_GATE.md) and [active task board](TASK_BOARD.md) still require credible worn examples, independent label confirmation, grouping and a versioned freeze before a new model is justified.
