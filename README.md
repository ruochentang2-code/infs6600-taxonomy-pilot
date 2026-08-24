# INFS6600 Taxonomy Pilot

This repository contains a small, transparent extraction-to-visualisation pipeline developed for the CS-44 project. It uses the University of Sydney's public 2026 INFS6600 Unit of Study Outline as an initial use case.

The pilot tests whether public course-outline evidence can support classification against the first two supplied taxonomy categories:

1. **Work-Integrated and Applied Learning**
2. **Simulation and Case-Based Learning**

The pipeline is intentionally designed as an auditable baseline that can be completed and reviewed within a few days. It does not claim to be a final production classifier.

## Current pilot result

For the 2026 Semester 2 INFS6600 outline, the current rules identify:

| Category | Classified evidence items | Interpretation |
|---|---:|---|
| Work-Integrated and Applied Learning | 11 | Strong evidence across the overview, learning outcomes, assessments and weekly schedule |
| Simulation and Case-Based Learning | 3 | Provisional evidence; client confirmation is recommended |

The second classification is provisional because two items use the official assessment type **Case studies**, while their task descriptions may be better interpreted as applied partner-project work. The learning outcome referring to **open-ended business scenarios** provides direct evidence for this category.

## What the pipeline does

The complete workflow:

1. Downloads the public INFS6600 Unit of Study Outline.
2. Extracts the overview, learning outcomes, assessment rows and weekly schedule.
3. Converts the outline into distinct, auditable evidence items.
4. Applies weighted taxonomy phrase rules and a classification threshold.
5. Produces detailed JSON and CSV evidence records.
6. Generates a course-to-category mapping and concise Markdown reports.
7. Creates PNG visualisations of category counts and evidence locations.

## Requirements

- Python 3.10 or later
- Internet access to the public University of Sydney outline
- Python packages: `pandas`, `lxml` and `Pillow`

## Installation

Clone the repository:

```bash
git clone https://github.com/ruochentang2-code/infs6600-taxonomy-pilot.git
cd infs6600-taxonomy-pilot
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install pandas lxml pillow
```

## Run the complete pipeline

From the repository root, run:

```bash
python src/run_pipeline.py --output-dir pilot-output
```

By default, the pipeline processes the official 2026 Semester 2 INFS6600 outline:

<https://www.sydney.edu.au/units/INFS6600/2026-S2C-NE-CC>

To process another compatible public outline, provide its URL:

```bash
python src/run_pipeline.py --url "PUBLIC_OUTLINE_URL" --output-dir pilot-output
```

## Generated outputs

The output directory will contain:

```text
pilot-output/
├── data/
│   ├── raw/infs6600_outline.json
│   └── processed/
│       ├── classification_results.json
│       └── classified_evidence.csv
├── reports/
│   ├── infs6600_course_information.md
│   ├── pilot_results.md
│   ├── course_category_mapping.md
│   └── course_category_mapping.csv
└── visualisations/
    ├── category_summary.png
    └── evidence_by_section.png
```

Generated data, reports and images are local outputs and are not stored in this repository.

## Classification logic

The baseline classifier uses transparent weighted phrase rules:

- Each outline item is evaluated independently against each category.
- Strong, explicit evidence normally receives a weight of `3.5` or `4.0`.
- Supporting evidence normally receives a weight between `1.5` and `2.5`.
- An item is classified when its category score reaches the threshold of `3.0`.
- A rule contributes its weight once per item, even if several alternative phrases from that rule appear.
- Sub-threshold matches are retained in a review queue instead of being counted.
- Classification is multi-label, so one course or evidence item may belong to more than one category.

The built-in rules are defined in `src/taxonomy_config.py`. A different taxonomy JSON file can be supplied without changing the remaining pipeline:

```bash
python src/run_pipeline.py --taxonomy path/to/taxonomy.json --output-dir pilot-output
```

## Source files

| File | Purpose |
|---|---|
| `src/fetch_outline.py` | Downloads and structures the public outline |
| `src/taxonomy_config.py` | Stores the default two-category taxonomy rules |
| `src/classify.py` | Scores and classifies auditable outline items |
| `src/generate_unit_summary.py` | Produces a readable course-information summary |
| `src/generate_course_mapping.py` | Produces the course-to-category comparison table |
| `src/generate_report.py` | Produces the evidence-led pilot report |
| `src/visualize.py` | Generates the PNG charts |
| `src/run_pipeline.py` | Runs the complete workflow in the correct order |

## Limitations

- Public outline structures may vary across units and may require parser adjustments.
- Phrase rules favour explainability over semantic coverage and may miss paraphrased evidence.
- Public assessment labels can be ambiguous and should be checked against task descriptions.
- The taxonomy definitions and unit list should be updated when the client provides the refined versions.
- Before scaling to 10–15 BIS postgraduate units, the results should be compared with a small manually reviewed reference set.

## Intended use

This repository is an educational research prototype. It processes publicly available course-outline information and is intended to support discussion with the project client, not to make automated high-stakes decisions.
