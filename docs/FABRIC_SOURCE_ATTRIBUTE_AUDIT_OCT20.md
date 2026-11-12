# Existing Fashionpedia fabric-source audit — October 20, 2026

The existing 1,000 Fashionpedia skirt originals do **not** provide a defensible expansion of the current cotton/denim/leather/chiffon appearance pilot. The official ontology lacks those exact fabric/fibre class names. Manufacturing and pattern tags must not be silently converted into fabric labels. No new dataset, labels, split assignments or training admissions were created.

The [hash-bound audit](../records/review/2026-10-20-fabric-source-attribute-audit.json) checked the saved official `train2020` annotations, not a filename or title heuristic. All 1,000 selected skirt annotation IDs match category8, source image IDs, exact boxes, polygons and attribute lists. All originals were rehashed, decoded and dimension-checked. **15,000 per-original consistency checks passed, with zero failures.** Only the two material-family examples described below were newly inspected visually; this was not a new visual review of all 1,000 photographs.

## What the source actually labels

The ontology contains no exact `cotton`, `polyester`, `denim`, `chiffon`, `leather`, `lace`, `knit`, `knitted`, `velvet`, `satin`, `silk`, `wool` or `linen` attribute name. It does contain the leather-family children `suede`290, `shearling`291, `crocodile`292 and `snakeskin`293, and the non-textile-material tag `fur`289. Across the existing 1,000 selected skirt instances:

| Source tag | Exact ID | Training originals | Validation originals |
|---|---:|---:|---:|
| Fur | 289 | 1 | 0 |
| Suede | 290 | 0 | 0 |
| Shearling | 291 | 0 | 0 |
| Crocodile | 292 | 0 | 0 |
| Snakeskin | 293 | 1 | 0 |
| No non-textile material | 295 | 731 | 169 |

Other non-textile tags occur as plastic14, metal6, feather4 and gem2. Such tags do not establish a mutually exclusive dominant base fabric; material or embellishment evidence must be interpreted separately. Excluding the explicit `no non-textile material` tag, 973 originals have no non-textile material tag, 26 have one and one has two. Counts overlap and must not be added as independent garments. Missing tags remain missing.

Several tempting lexical mappings are incorrect:

| Actual source annotation | Count | Why it does not supply the desired class |
|---|---:|---|
| `lace up`227 | 3 | Opening type; not lace fabric |
| `washed`298 | 28 | Finishing; not denim evidence |
| `fair isle`324 | 3 | Stored as a pattern; not verified knit construction |
| `herringbone (pattern)`330 | 0 | Pattern terminology does not certify weave or fibre |
| `no non-textile material`295 | 900 | Does not identify cotton, polyester or any particular textile |

Textile finishing tags such as printed103, gathering128 and pleat137 can support their own source annotation tasks. They cannot replace a fabric ontology or establish fibre composition. The audit retains all exact manufacturing and pattern definitions/counts, including overlapping tags.

## Actual inspection of the two material-family examples

Both are in the existing development-training partition and have different preserved connected-group hashes. Neither has an existing admission to the 372-image full-skirt pilot or its 331-image worn subset. Their new observations remain supplemental evidence only.

- **4437, source fur289:** a runway wearer has a dark fuzzy lower garment and a separate leather-like jacket. Side pose, hand and upper garment obscure part of the skirt/waist. Appearance does not establish real versus faux fur or fibre composition; the jacket must not supply the skirt's fabric label.
- **18214, source snakeskin293:** a wearer has a short fitted reptile-patterned skirt. A hand overlaps the front and a black top covers part of the waistband. Pattern and sheen do not verify leather or genuine snakeskin.

Each original was displayed directly and its actual hash, source annotation, source partition and group were recorded. No source label was replaced and neither example was admitted to fabric training. Two isolated training examples, with zero corresponding validation examples and unresolved appearance truth, cannot support a stronger fabric experiment.

## Grouping, terms and next gate

All 1,000 original images retain official `train2020` membership and the existing **810 training/190 development-validation** assignments. There are 995 source-page groups and 991 conservatively connected groups; zero connected groups cross those project partitions. These group counts are not independently verified physical specimens. No protected validation seed was inspected, relabelled or moved into training by this audit.

The acquisition manifest preserves individual source-photo licenses and URLs. Annotation licensing is separate; it does not grant a blanket license to redistribute the photographs or altered crops. See [source acquisition and rights](SKIRT_ACQUISITION.md). No image was downloaded, no dependency was installed and no model changed.

The useful next gate remains a rights-compatible full-view worn-garment source with explicit visual material annotations or garment-tag/supplier evidence linked to item identity, followed by visibility, grouping and label review. Preserve fibre percentages/blends separately from appearance. The [five-photo composition-source pilot](NPCGI_PILOT.md) has different presentation and supplies no new worn training admission. More training on unsupported Fashionpedia fabric mappings would not resolve this gap. [Current fabric requirements](FABRIC_NEXT_GATE.md), [training protocol](TRAINING_PLAN.md).
