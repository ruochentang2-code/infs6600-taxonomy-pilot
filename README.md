# INFS6600 taxonomy pilot

This is a small, reproducible pilot that can be completed and presented within two to three days. It uses the public **2026 Semester 2 INFS6600** outline and analyses the first two categories in the updated taxonomy:

1. Work-Integrated and Applied Learning
2. Simulation and Case-Based Learning

## Quick start

```powershell
python -m pip install -r requirements.txt
python src/fetch_outline.py --output data/raw/infs6600_2026_s2.json
python src/generate_unit_summary.py --input data/raw/infs6600_2026_s2.json --output reports/infs6600_course_information.md
python src/classify.py --input data/raw/infs6600_2026_s2.json --taxonomy config/taxonomy.json --output data/processed/classification_results.json --csv data/processed/classification_evidence.csv
python src/generate_course_mapping.py --input data/processed/classification_results.json --markdown reports/course_category_mapping.md --csv data/processed/course_category_mapping.csv
python src/visualize.py --input data/processed/classification_results.json --output-dir visualisations
python src/generate_report.py --result data/processed/classification_results.json --taxonomy config/taxonomy.json --output reports/pilot_results.md
python -m unittest discover -s tests -v
```

## Data acquisition approach

- Use only public, official University of Sydney pages.
- Use the latest Semester 2 outline when the unit is offered in both semesters.
- Convert the overview, learning outcomes, assessment rows and weekly-schedule rows into distinct evidence items.
- Preserve the original text, section, label, URL and retrieval time for audit.
- Fail explicitly if the page structure changes instead of silently generating incomplete data.

## Classification approach

- Convert the client-provided definitions and examples into transparent weighted phrase rules.
- Strong phrases such as `actual business problem`, `pitch to partner` and `case studies` can independently reach the threshold.
- Generic terms such as `project`, `business` and `presentation` do not independently create a positive result.
- Count each evidence item at most once per category.
- Retain weak, sub-threshold signals in a review queue for manual confirmation.

## Key files

- [Course-to-category mapping](reports/course_category_mapping.md)
- [Complete INFS6600 course information](reports/infs6600_course_information.md)
- [Detailed algorithm and results](reports/algorithm_and_results.md)
- [Evidence-level pilot report](reports/pilot_results.md)
- [Client meeting update and eight-person work report](reports/meeting_update.md)
- [Course-to-category CSV](data/processed/course_category_mapping.csv)
- [Evidence-level CSV](data/processed/classification_evidence.csv)

## Official sources

- Unit page: https://www.sydney.edu.au/units/INFS6600
- 2026 Semester 2 outline: https://www.sydney.edu.au/units/INFS6600/2026-S2C-NE-CC

## Repository structure

- `src/`: acquisition, classification, visualisation and report-generation code
- `config/`: the first two taxonomy categories and their rules
- `data/raw/`: structured snapshot of the official outline
- `data/processed/`: classification JSON and auditable CSV outputs
- `visualisations/`: PNG charts
- `reports/`: course information, algorithm, results and meeting materials
- `tests/`: false-positive and counting safeguards

