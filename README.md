# CS-44 INFS Pedagogical Innovation Corpus

This repository implements the CS-44 project scope as an auditable proof of concept. It collects the listed University of Sydney Business Information Systems (INFS) public 2026 unit outlines, selects Semester 2 when both main semesters are available, and classifies evidence against all seven supplied pedagogical-innovation categories.

## Coverage

- 12 undergraduate and 15 postgraduate unit codes from the supplied scope
- Public 2026 outlines only
- Course overview/description, learning outcomes, assessment types, assessment descriptions and weekly schedule
- Seven taxonomy categories: work-integrated/applied, simulation/case-based, project/problem-based, community, entrepreneurial, technology-mediated and hybrid learning
- Discipline-wide totals and UG-versus-PG comparison
- Per-item evidence text, score, matched rule and source URL for review

If a requested outline is not publicly available, the pipeline records it in the failure register instead of silently substituting another year.

## Run

Requirements: Python 3.10+, `pandas`, `lxml`, and `Pillow`.

```bash
python src/run_pipeline.py --output-dir pilot-output
```

The collector uses up to six concurrent requests so that an unusually slow public page does not block the entire corpus.

## Outputs

```text
pilot-output/
├── data/
│   ├── raw/cs44_2026_infs_corpus.json
│   └── processed/
│       ├── classification_results.json
│       ├── classified_evidence.csv
│       ├── unit_category_mapping.csv
│       └── category_aggregate.csv
├── reports/corpus_results.md
└── visualisations/
    ├── discipline_category_units.png
    └── ug_pg_comparison.png
```

## Counting and interpretation

Classification is multi-label. A unit is counted once in a category when at least one distinct outline item reaches that category's threshold. Evidence-item totals are also retained, but are not raw keyword frequencies: one item is one overview, learning outcome, assessment row, assessment-description block or weekly-schedule row.

The rule-based method is deliberately transparent and conservative. A zero means no explicit phrase reached the configured threshold in the public outline; it does not prove that the teaching practice is absent. Results should be manually sampled and validated before being treated as final research findings.

## Key source files

| File | Purpose |
|---|---|
| `src/fetch_corpus.py` | Discovers the preferred 2026 outline and collects the full unit list |
| `src/fetch_outline.py` | Extracts auditable sections from one outline |
| `src/taxonomy_config.py` | Stores all seven supplied taxonomy categories and rules |
| `src/classify_corpus.py` | Classifies units and creates UG/PG/discipline aggregates |
| `src/visualize_corpus.py` | Produces discipline and UG/PG charts |
| `src/run_pipeline.py` | Runs the end-to-end workflow |

This is an educational research prototype using publicly accessible pages. It does not access restricted or student-level data and does not make claims about teaching quality or causal effectiveness.
