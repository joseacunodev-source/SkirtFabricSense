# Paired detection uncertainty — October 23, 2026

**These are reused development results.** The same source groups motivated hypotheses and selected checkpoints. Bootstrap intervals describe variation conditional on those groups, provisional labels and saved predictions; they do not remove selection bias or establish independent camera accuracy, physical garment independence or readiness for a public demonstration.

This analysis compares the selected category-presence-v1 gate against presence-v4, using **localizer-v2 plus the unchanged pleating model** in both chains. It reads the two completed saved prediction reports, without rerunning inference, training or adjusting either fixed 0.5 threshold. The [machine result](../records/validation/2026-10-23-detection-uncertainty.json) binds the input, reports, completed runs, source manifests, archived training code and actual exported model bytes by SHA256.

The 538 archived inputs retain 420 training and 118 validation images. The validation set contains 66 skirt and 52 negative source groups, each with one image. All original source partitions are train2020; none crosses the development split. Source grouping does not prove that different groups depict distinct physical garments. The tool joins exact input rows to the frozen manifests and original positive split assignments, but does not reopen or rehash original image bytes in this saved-prediction analysis.

| Saved chain | Accepted skirts | Correct pleating / all skirts | Correct / accepted skirts | Negatives rejected |
|---|---:|---:|---:|---:|
| Presence-v4 + localizer-v2 | 44/66 | 38/66 | 38/44 | 39/52 |
| Category-presence-v1 + localizer-v2 | 44/66 | 38/66 | 38/44 | 42/52 |

Identical aggregate skirt counts hide changes in which images succeed. Three previously correct skirt results become unavailable; three previously unavailable results become correct. Six accepted wrong-pleating results persist. The full report preserves all 11 changed results, including their source groups and provisional truth.

| Provisional skirt truth | Prior accepted / support | Current accepted / support | Prior correct / support | Current correct / support | Current unavailable |
|---|---:|---:|---:|---:|---:|
| Pleated | 14/17 | 15/17 | 9/17 | 10/17 | 2/17 |
| Non-pleated | 30/49 | 29/49 | 29/49 | 28/49 | 20/49 |

The current pleated errors include five predictions of non-pleated; non-pleated errors include one prediction of pleated. Unavailable predictions remain in the class support and end-to-end correctness denominators. Pleating precision/F1 in the JSON uses true-skirt rows; negative false acceptances are reported separately and must not be silently omitted from a system-level claim.

Four prior negative false acceptances are corrected, while one previously rejected shorts image becomes falsely accepted. Nine false acceptances persist. By publisher source category, dress rejection changes from 10/20 to 13/20, pants from 14/17 to 15/17, and shorts from 15/15 to 14/15. These small slices identify failure priorities; they are not independent category-accuracy estimates.

The report uses 2,000 source-group cluster bootstrap resamples, seed 42, with the positive and negative group counts held fixed. Each resample uses the **same selected groups for both models** and retains every member of a selected group. Groups have equal weight, images within a group have equal weight, and selective accuracy is the ratio of group-mean correct to group-mean accepted. It does not split a group into pleating-class strata. For the current one-image groups, point estimates equal the image rates.

| Metric | Current estimate | Paired current minus prior | Conditional 95% percentile interval for change |
|---|---:|---:|---:|
| Skirt coverage | 66.67% | 0.00 percentage points | −7.58 to +7.58 points |
| Correct pleating / all skirts | 57.58% | 0.00 points | −7.58 to +7.58 points |
| Correct pleating / accepted skirts | 86.36% | 0.00 points | −1.64 to +1.67 points |
| Negative rejection | 80.77% | +5.77 points | −1.92 to +13.46 points |

The negative-rejection interval crosses zero. Neither the point improvement nor this conditional interval supplies an independent generalization claim. The observed 10/52 negative false acceptances and 22/66 unavailable skirts remain product gaps. No feature, threshold, model selection or station package changes follow from this analysis. The next evidence needed is independently reviewed unseen groups, including empty/background, difficult negative and actual camera presentations.

Implementation: [standard-library reporter](../tools/report_detection_uncertainty.py), [26 focused tests](../tests/test_detection_uncertainty.py). Tests cover input-byte/hash tampering, frozen source truth/group/split mutation, missing/duplicate/unexpected validation identities, protected partitions, cross-split or mixed-target groups, model/threshold mismatches, inconsistent accepted/rejected predictions, aggregate-count tampering, paired deterministic resampling, unequal image counts per group and undefined zero-accepted selective accuracy. All 26 passed using the existing Windows tooling Python; no dependency installation was needed.

To reproduce the analysis into a **new** output filename:

```powershell
& C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -m unittest tests.test_detection_uncertainty -v
& C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe tools/report_detection_uncertainty.py --output records/validation/detection-uncertainty-recheck.json
```

The CLI refuses to overwrite an existing report. The bootstrap's seed and resample count are configurable for reproducibility checks; changing them does not authorize threshold/model tuning or a new deployment claim. No Pi, camera, fabric or geometry acceptance work is completed by this report.
