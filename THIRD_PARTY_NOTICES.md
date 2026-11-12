# Third-party material and licensing status

This research repository records a skirt-classification project. Its public visibility is not a blanket license grant for the project source, photographs, annotations, pretrained weights, reference illustrations or dependency packages. No project-wide open-source license has been selected. Obtain the appropriate permission before reuse or redistribution.

## Dataset and reference material

The authoritative local source/terms records are [docs/DATASETS.md](docs/DATASETS.md), [data/registry.json](data/registry.json), the referenced acquisition records and individual attribution files. Their historical entries must be read with the current registry; a downloaded candidate is not necessarily admitted training data. Preserve author, source, license, retrieval evidence and modification notices where required.

- Fashionpedia annotations/ontology and underlying photographs have separate terms. The catalogue records the annotation terms and image-specific source evidence. For the saved licensed seed images, retain [their attribution file](data/external/fashionpedia/ATTRIBUTION.md).
- DeepFashion-derived material has source-specific research-use and redistribution restrictions recorded in the dataset catalogue. Publicly accessible files do not establish public redistribution rights.
- Other fabric/texture, museum or web-source candidates retain their original terms and admission gates. Unresolved rights or labels must remain unresolved in project records; do not turn a candidate entry into a license grant.
- Supplied UI/hemline references and generated progress artifacts do not establish ownership of any third-party photographs or illustrations they depict. Check their source rights before republication beyond the authorized research use.

Large source images, downloaded archives and model binaries are excluded from normal Git synchronization. A private asset bundle is a transfer mechanism, not permission to redistribute its contents. Do not publish one as a GitHub release without a separate source-specific rights review.

## Libraries and pretrained weights

Dependency versions and observed environments are recorded in [records/installations.jsonl](records/installations.jsonl), [requirements](requirements/README.md) and environment snapshots. Packages retain their own copyright and license files. Installing or importing a package does not establish rights for every dataset or pretrained weight it can download.

Project code uses or evaluates image-processing and machine-learning components, including Pillow and TensorFlow/Keras/MobileNetV2 workflows. Follow the exact upstream package and pretrained-weight terms for the versions actually used. A model checkpoint's provenance, training data and export record must accompany any redistribution decision. Documentation of a proposed dependency is not evidence it has been installed or shipped on the Pi.

This notice is a navigation aid, not an exhaustive software bill of materials, legal opinion or new license. A release intended for redistribution still needs an inventory of the exact shipped artifacts and their corresponding notices.
