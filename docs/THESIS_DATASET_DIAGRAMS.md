# Training, validation and test diagrams

Four additional figures are supplied in [the dataset diagram folder](../output/thesis_dataset_diagrams), as vector PDFs and 300-dpi PNGs. [Download the four-page PDF](../output/thesis_dataset_diagrams/Training_Validation_Test_Diagrams.pdf). These complement the [original five figures](THESIS_FIGURES.md). The first two describe actual archived inputs; the last two explain the planned evaluation and grouping method.

## Figures and suggested captions

| Figure | PNG for Word / slides | Suggested caption |
|---|---|---|
| Actual split and test status | [06_training_validation_test.png](../output/thesis_dataset_diagrams/06_training_validation_test.png) | Recorded training and development-validation membership of category-presence v1: 420 and 118 original images, respectively. The 12 protected external sanity photographs are separate from the uncollected final device-domain test. |
| Dataset sizes by component | [07_datasets_by_model.png](../output/thesis_dataset_diagrams/07_datasets_by_model.png) | Training and development-validation counts for the selected pleating, localization and presence components and the experimental fabric smoke model. Rows overlap and must not be summed as unique images or garments. |
| Future train / validation / test workflow | [08_planned_train_validation_test_workflow.png](../output/thesis_dataset_diagrams/08_planned_train_validation_test_workflow.png) | Proposed garment-group evaluation workflow, separating weight fitting, model-selection validation, calibration validation and untouched final testing. The diagram specifies methodology, not completed collection or a measured split ratio. |
| Prevention of related-image leakage | [09_grouping_prevents_data_leakage.png](../output/thesis_dataset_diagrams/09_grouping_prevents_data_leakage.png) | Illustrative assignment of connected garment observations to one partition. Frames, views, software crops and derivatives inherit their garment group's assignment; additional frames do not increase the independent specimen count. |

Change the figure numbers to match the thesis. Keep “development validation” in the current-result captions: these images have been reused for epoch/model selection and diagnostics. Do not label those results as final test accuracy. The methodology figures use hypothetical garment IDs; they are not acquisition records.

## Verified numbers and interpretation

| Actual selected experiment | Training images | Development validation | Total |
|---|---:|---:|---:|
| Pleating fine-tune v1 | 292 | 80 | 372 |
| Localizer v2 | 348 | 99 | 447 |
| Category presence v1 | 420 | 118 | 538 |
| Fabric appearance smoke v1 | 12 | 5 | 17 |

The 420/118 split is 78.1%/21.9% of that experiment's 538 images. It does not describe all 1,932 registered original images or every component's training history. Its positives come from the 331-image worn subset (265/66); its negatives are 155/52. The original pleating and localizer models also used secondary-presentation examples. Recorded source-group identifiers do not establish physical garment independence.

The complete evidence and class counts are in [the partition guide](DATASET_PARTITION_EVIDENCE.md), backed by [the metadata audit](../records/validation/2026-11-04-dataset-partitions-audit.json). Final project test membership and metrics remain absent, and actual wearer/hem geometry has zero observed annotations. Protected publisher partitions and downloaded metadata cannot substitute for independently labelled camera-domain garments.

## Reproduction and quality checks

[create_dataset_diagrams.py](../tools/create_dataset_diagrams.py) checks the audit's source hashes and independently recounts the five relevant original manifests before rendering. It refuses to overwrite output. For a later rerender, choose a fresh directory:

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B tools/create_dataset_diagrams.py --output output/thesis_dataset_diagrams-rerender
```

The source audit includes the training/evaluation plans as observed on November 4. If those plans or input manifests later change, preserve the existing figure set and create a new reviewed audit/version rather than rewriting the old evidence to make its hash pass. [Source data](../output/thesis_dataset_diagrams/source-data.json) preserves the exact audit used for these figures.

Existing ReportLab, pypdf and Poppler produce the PDFs and PNGs; no dependencies were installed. All four rendered PNGs were visually reviewed for layout and legibility. For Word, insert the PNG at the full text width while preserving aspect ratio; use the vector PDF when the thesis workflow supports it. No external garment photographs were embedded, no model was rerun and no source/test partition was changed.

The separate [partition auditor](DATA_PARTITION_AUDIT.md) adds a read-only semantic check of already assigned manifests. This safeguards future work; a passing metadata audit does not certify labels, rights, specimen independence, model accuracy or Raspberry Pi readiness.
