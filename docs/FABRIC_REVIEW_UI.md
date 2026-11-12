# Browser fabric evidence review

The local reviewer is ready for people to record visible observations on the **17 frozen fabric-pilot originals**. It shows one complete original with a fit/original-size control and a form for appearance, presentation, visibility and texture detail. It hides the prior source labels, model predictions, group identifiers and split assignments. Review does not require a camera or Raspberry Pi.

Saving appends a pending observation for later reconciliation. It does not approve a classifier target, confirm fibre composition, change a frozen split or start training. The project queue still has **zero submitted observations** at this software-validation checkpoint.

## Start and stop

Open PowerShell in the project directory and run:

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B tools/serve_fabric_review.py --port 8771
```

Open **http://127.0.0.1:8771/** using the exact address printed by the tool. Keep the terminal open while reviewing. Stop with **Ctrl+C** when finished. The server binds to the laptop loopback address only; it does not make a public website or accept remote reviewers. No dependencies need to be installed for this tool in the existing project environment.

If the port is occupied, stop your previous reviewer instance or choose another unused port, for example `--port 8772`, and use the new printed address. Do not stop unrelated applications. A browser refresh creates no observation. A new server session requires reloading the page before saving because its request token changes.

## Reviewer steps

1. Enter your name and choose the truthful reviewer kind. A person should select **Human reviewer**. Identity is self-reported; the tool does not authenticate independence or expertise.
2. Inspect the complete original. Use **View original size** for detail and **Fit complete original** to restore the full view. Check the viewing declaration only after inspection.
3. State whether the material being described clearly belongs to the skirt. If association is uncertain or the item is not a skirt, appearance stays **Unknown** and descriptors stay empty.
4. Select a single, mixed or unknown visible appearance. Describe literal surface evidence, such as reflective folds or sheer sections. Do not infer cotton, polyester or fibre percentages from appearance. Mixed visible appearance does not verify a fibre blend.
5. Record presentation, skirt visibility and texture detail. Add notes explaining the visible evidence and limitations, including blur, print, lighting, occlusion or another garment.
6. Choose **Save pending observation** to append it to the project event log, or **Download JSON instead** to export a validated submission without appending it. Downloading alone does not complete the project review.
7. Move to the next original. Unsaved edits trigger a discard prompt. Each new image resets its observation fields and viewing declaration; reviewer name/kind remain for convenience. Use unknown whenever evidence is insufficient.

An identical repeated save is acknowledged without another event. A changed observation is a correction and appends a new event; earlier evidence remains intact. Controls are disabled during a request so edits cannot be accidentally reported as saved. A lost response can leave the outcome uncertain: check the verified event log before retrying rather than rewriting or deleting records.

## Downloaded submissions and verification

Downloaded JSON can be imported later through the existing append command. Use the actual path of the downloaded submission:

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B tools/datasets/fabric_evidence_review.py append --directory records/review/2026-10-23-fabric-evidence-review --submission 'C:/PATH/TO/DOWNLOADED-observation.json'
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B tools/datasets/fabric_evidence_review.py verify --directory records/review/2026-10-23-fabric-evidence-review
```

Replace the example path; it is not a file included with the project. Avoid importing a downloaded submission already saved through the browser: the command-line append workflow is separate, and another appended event does not create another independent reviewer or garment.

The form records appearance only. Documentary claims from tags or supplier documents belong in the [separate evidence workflow](FABRIC_EVIDENCE_REVIEW.md), with evidence-to-skirt association retained. Reconciliation must still resolve textile vocabulary, label disagreements, rights and specimen identity before a versioned dataset release.

## Integrity and tested behavior

Only the reviewer page, blind queue and opaque allowlisted image routes are served. Arbitrary paths and the private binding file are unavailable. Requests use strict Host/Origin checks, one session-token header, bounded JSON bodies and same-origin browser protections. Original image and queue bindings are rechecked before observations are accepted. A retained append lock is reported rather than removed automatically.

The [November 11 validation](../records/validation/2026-11-11-fabric-reviewer/verified-r02/verification.json) records **41 passing tests**: 11 UI tests and 30 underlying evidence tests. A real Edge browser exercised 14 checks covering JSON download without append, explicit save, repeated save, image navigation, state reset and unknown/descriptor handling. All writes used temporary synthetic queues. The [reviewer screenshot](../records/validation/2026-11-11-fabric-reviewer/verified-r02/browser-synthetic-review.png) shows synthetic rectangles used for that test; it is not garment-review evidence.

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -m unittest tests.test_fabric_review_ui tests.test_fabric_evidence_review -v
```

The production queue and its empty append-only log remained unchanged, and all owned test servers stopped. A passing test does not establish label truth, fabric accuracy, physical garment independence, source rights or Raspberry Pi performance.
