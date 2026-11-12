# Fabric readiness and next admission gate

Later October22: the actual2018 rules were read in a browser; acceptance remains pending. The existing TextileNet training URL manifest was audited against its official blob, exposing repeated identities and absent skirt/product mapping. No new photographs or labels were admitted. [Current source gate, counts and offline tool](FABRIC_SOURCE_GATE_OCT22.md).

October22 current gate: [the source search](FABRIC_SOURCE_SEARCH_OCT21.md) identifies iMaterialist2018 terms, grouping and skirt-specific label association as the next data task. Existing Fashionpedia attributes add zero usable fabric admissions. [Station-v2](STATION_PACKAGE.md) can load the tiny source-appearance smoke only with explicit research opt-in; this does not approve fabric quality. Older disconnection/admission wording below records its dated state. No new fabric training is justified from unsupported labels or the unchanged17-group smoke alone.

October 17 update: the audit now accepts an optional `--presentation-review` supplement. The [current audited result](../records/validation/2026-10-17-fabric-readiness.json) validates the frozen manifest/split hashes, exact complete membership of 17 records, image hashes/paths, groups, partitions, labels and original-image review attribution. It reports 17 worn examples from that supplement, rather than incorrectly retaining a missing-presentation blocker. Counts are recomputed from validated entries, not copied from the review summary. Composition, independent human confirmation and live approval remain false. The frozen inputs and older audit are unchanged; omitting the option still audits only the historical manifest.

October 16, 2026. The offline [readiness audit](../records/validation/2026-10-16-fabric-readiness.json) verifies the frozen pilot manifest, split and saved terms hashes, checks the 17 original file hashes/sizes, rejects source holdouts and cross-split groups, and reports evidence gaps. It does not approve the model. No files were downloaded, dependencies installed, labels changed or training repeated for this audit.

| Source appearance annotation | Training source groups | Validation source groups |
|---|---:|---:|
| Cotton | 6 | 2 |
| Denim | 4 | 1 |
| Leather | 1 | 1 |
| Chiffon | 1 | 1 |

These are 17 source item groups, not verified independent physical garments. There are zero independent human confirmations and zero verified composition labels. Three classes have just one development-validation group. The archived smoke result of 4/5 correct is not a live performance estimate.

After that audit, all 17 original images were opened individually and visually reviewed in a [supplemental presentation record](../records/review/2026-10-16-fabric-presentation.json). All 17 show a worn skirt, preserving 12 training / 5 validation source groups. Ten show the wearer's feet; seven crop the lower legs/feet. Per-image notes record hand occlusion, angled/bent poses, uneven hems, dominant prints and texture visibility. One scene also includes a held shirt beside the worn skirt. Feet visibility does not establish valid geometry or calibrated length. The frozen manifest still has no presentation field; this separate agent-reviewed annotation provides provenance without rewriting historical inputs. It is not independent human confirmation or a new performance evaluation. The earlier readiness report is preserved as the pre-review state.

The fabric toggle must continue reporting unavailable until a candidate is approved. Keep source appearance labels separate from fiber composition; the four smoke labels are not a finalized product ontology. Automatic localization-to-fabric crops, unsupported inputs, worn-domain performance and hardware behavior have not been evaluated by this smoke experiment.

## Concrete next work

1. Completed for the 17 admitted pilot originals: explicit worn presentation and visibility notes in the supplemental record. The eight previously excluded candidates remain excluded; this pass does not admit them. Obtain independent label confirmation before treating agent labels as established truth.
2. Resolve the operational appearance taxonomy and mixed/unknown policy. Any composition claim requires separate garment-tag or supplier evidence; a visual class cannot certify it.
3. Expand distinct rare-class groups from a rights-compatible full-view source with supported item identities and original partitions. The current MultiModal train pool already supplied all 15 non-cotton source groups available there. Downloading 30 more cotton examples does not repair the rare-class shortage.
4. For the alternative Anno_fine source, obtain a publisher-supported item identity mapping before admission. All 422 original-training references currently share descriptive folder groups with holdouts. Do not bypass this conflict, use the 258 encountered holdout metadata rows in training, or count metadata as acquired images. See [source feasibility](ATTRIBUTE_SOURCE_FEASIBILITY.md).
5. Freeze a new evidence-backed dataset only after grouping, label and rights review. Then compare manual versus automatic same-frame ROI performance, preserve per-class coverage/errors and evaluate unknown inputs before live integration. No new acceptance threshold or statistically sufficient sample target is invented by this audit; fix evaluation criteria before candidate selection.

The next expansion gate is source-identity resolution or a new source with distinct rare-class garment groups, rather than another training run on the unchanged 17 groups. Actual garment collection remains necessary for target-camera evaluation, and a real Pi remains necessary for deployment verification.

## Reproduction

Run from the workspace using an existing Python interpreter; standard library only:

```text
python -m unittest tests.test_fabric_readiness -v
python tools/datasets/fabric_readiness.py --output records/validation/fabric-readiness-recheck.json
python tools/datasets/fabric_readiness.py --presentation-review records/review/2026-10-16-fabric-presentation.json --output records/validation/fabric-readiness-with-presentation-recheck.json
```

The output path must be new so earlier evidence is preserved. Eight focused checks passed on October 16 with the recorded bundled Python environment. An integrity pass only establishes consistency of the existing smoke inputs; `live_approved` remains false. This tool does not inspect test images, modify the registry, retrain models or grant permission to redistribute research images.

On October 17, all 16 focused tests passed with the existing bundled Python interpreter. Added checks cover altered hash bindings, incomplete/duplicate/unknown membership, changed provenance, missing original-image review or attribution, unsupported composition/admission claims, untrusted summary counts and missing review files. An invalid supplement fails the integrity audit and contributes no presentation counts.
