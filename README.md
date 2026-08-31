# INFS6600 Taxonomy Pilot

This repository contains the transparent extraction-to-visualisation proof of concept developed for the CS-44 project. It analyses the University of Sydney's public 2026 INFS6600 Unit of Study Outline and retains every source evidence item, matched rule, score, and official URL.

## Tutor-feedback v2

The `tutor-feedback-v2` update implements the client's 26 August 2026 document comments and meeting feedback without rewriting repository history. The original two-category version remains available on the `main` branch and in earlier commits.

The v2 release:

- expands the configuration to all eight supplied taxonomy categories;
- separates **Simulation** from **Case-Based Learning**;
- treats categories as non-mutually-exclusive multi-label outcomes;
- updates the four commented WIL weights;
- reports positive evidence, review signals, classified score, and review score separately;
- downgrades an administrative `Case studies` assessment label to a review-only signal;
- adds automated regression tests for the tutor's expected INFS6600 allocation;
- creates versioned CSV/JSON, Markdown, PNG, and PDF deliverables.

### Week 4 scope boundary

This release is limited to applying the tutor's comments to the existing
INFS6600 pilot. The remaining taxonomy categories are configured because the
tutor asked the team to proceed with the rest of the taxonomy, but they are not
presented as client-validated classifications. No additional units,
discipline-wide UG/PG analysis, landing page, LLM/RAG component, or formal
model-evaluation study is included in this update.

## Current INFS6600 result

The v2 pipeline positively allocates INFS6600 to the three categories identified by the tutor:

1. **Work-Integrated and Applied Learning**
2. **Case-Based Learning**
3. **Project- and Problem-Based Learning**

| Category | Positive items | Review items | Classified score | Review score | Result |
|---|---:|---:|---:|---:|---|
| Work-Integrated and Applied Learning | 11 | 1 | 48.5 | 2.0 | Positive |
| Simulation | 0 | 0 | 0.0 | 0.0 | No match |
| Case-Based Learning | 1 | 2 | 3.5 | 4.0 | Positive + review items |
| Project- and Problem-Based Learning | 4 | 2 | 14.5 | 4.0 | Positive + review items |
| Community Learning | 0 | 0 | 0.0 | 0.0 | No match |
| Entrepreneurial Learning | 0 | 2 | 0.0 | 4.0 | Review only |
| Technology-Mediated Learning | 0 | 0 | 0.0 | 0.0 | No match |
| Hybrid Learning | 0 | 0 | 0.0 | 0.0 | No match |

Counts are distinct outline items, not raw keyword occurrences. Categories are not mutually exclusive, so counts and future category percentages are not expected to sum to 100%.

## Reviewed v2 visualisations

![Positive and review evidence by category](output/v2/visualisations/category_summary.png)

![Classified and review scores by category](output/v2/visualisations/category_scores.png)

![Positive evidence by source section](output/v2/visualisations/evidence_by_section.png)

The original v1 visualisations remain in `visualisations/` and are not deleted.

## Taxonomy v2

The source-of-truth configuration is [`config/taxonomy_v2.json`](config/taxonomy_v2.json). It contains:

- category definitions;
- phrase-rule alternatives and weights;
- category overlap notes;
- review guidance;
- multi-label and deduplication policy;
- provisional positive and high-confidence thresholds.

The eight categories are:

1. Work-Integrated and Applied Learning
2. Simulation
3. Case-Based Learning
4. Project- and Problem-Based Learning
5. Community Learning
6. Entrepreneurial Learning
7. Technology-Mediated Learning
8. Hybrid Learning

## Tutor-adjusted WIL weights

| Rule group | v1 | v2 | Status |
|---|---:|---:|---|
| Authentic practice | 3.5 | 4.0 | Tutor: “Give 4” |
| Theory-practice integration | 2.5 | 2.0 | Tutor: “Give 2” |
| Practical teamwork | 2.0 | 2.0 | Tutor: “Give 2” |
| Career readiness | 1.5 | 2.0 | Tutor: “Maybe 2 here” - provisional |

The positive threshold (`3.0`) and high-confidence threshold (`5.0`) remain configurable and explicitly marked as provisional pending client confirmation.

## Requirements

- Python 3.10 or later
- Internet access when fetching the public outline
- Packages listed in `requirements.txt`

```bash
python -m pip install -r requirements.txt
```

## Run the complete v2 pipeline

From the repository root:

```bash
python src/run_pipeline.py
```

The default public source is:

<https://www.sydney.edu.au/units/INFS6600/2026-S2C-NE-CC>

For a reproducible offline run using an existing extracted snapshot:

```bash
python src/run_pipeline.py \
  --snapshot output/v2/data/raw/infs6600_outline.json
```

To use a different compatible taxonomy:

```bash
python src/run_pipeline.py \
  --taxonomy path/to/taxonomy.json \
  --output-dir output/custom \
  --pdf-output-dir output/custom-pdf
```

## Generated and committed v2 deliverables

```text
output/
├── pdf/
│   ├── 02_Classification_Algorithm_Detailed_v2.pdf
│   └── 05_INFS6600_Course_Category_Mapping_v2.pdf
└── v2/
    ├── data/
    │   ├── raw/infs6600_outline.json
    │   └── processed/
    │       ├── classification_results.json
    │       ├── classified_evidence.csv
    │       ├── review_queue.csv
    │       └── unit_category_summary.csv
    ├── reports/
    │   ├── infs6600_course_information.md
    │   ├── pilot_results_v2.md
    │   ├── course_category_mapping_v2.md
    │   └── course_category_mapping_v2.csv
    ├── visualisations/
    │   ├── category_summary.png
    │   ├── category_scores.png
    │   └── evidence_by_section.png
    └── release_manifest_v2.json
```

The release manifest records SHA-256 hashes for the generated deliverables.

## Tests

Run the offline unit and regression tests:

```bash
python -m unittest discover -s tests -v
```

The regression suite verifies:

- exactly eight configured categories;
- separate Simulation and Case-Based categories;
- tutor-adjusted WIL weights;
- one weight contribution per rule even when several alternatives match;
- true multi-label item classification;
- review-only handling of administrative case labels;
- separate positive and review score aggregation;
- the tutor's expected three-category INFS6600 result without Simulation inheritance.

## Source files

| File | Purpose |
|---|---|
| `config/taxonomy_v2.json` | Versioned eight-category definitions, rules, policies, and weights |
| `src/fetch_outline.py` | Downloads and structures the public outline |
| `src/taxonomy_config.py` | Loads and validates the taxonomy configuration |
| `src/classify.py` | Scores multi-label evidence and writes positive/review/summary outputs |
| `src/generate_unit_summary.py` | Produces a readable course-information summary |
| `src/generate_course_mapping.py` | Produces the complete eight-category mapping |
| `src/generate_report.py` | Produces the evidence-led Markdown report |
| `src/visualize.py` | Generates the three v2 PNG figures |
| `src/generate_pdf_reports.py` | Generates the two PDF deliverables |
| `src/run_pipeline.py` | Runs and hashes the complete workflow |
| `tests/` | Offline unit and tutor-feedback regression tests |

## Limitations and outstanding client decisions

- The current phrase rules favour transparency over semantic coverage.
- The parser depends on the current public outline structure.
- The thresholds have not been client-validated.
- The Career readiness weight of 2.0 follows a tentative tutor comment.
- The current release reruns INFS6600 only; no additional-unit or discipline-wide analysis is included.

See [`docs/client_decisions_required.md`](docs/client_decisions_required.md) for the unresolved questions and [`docs/week4_delivery_checklist.md`](docs/week4_delivery_checklist.md) for the delivery status.

## Intended use

This repository is an educational research prototype using public unit-outline information. It supports transparent client review and does not make automated high-stakes decisions about teaching quality.
