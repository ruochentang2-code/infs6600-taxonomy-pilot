"""Generate a course-to-category mapping table from classification results."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REPRESENTATIVE_EVIDENCE = {
    "work_integrated_applied": (
        "actual business organisation; actual business problem; actual business professionals; "
        "Partner Briefing; Pitch to Partner; Boardroom Presentation"
    ),
    "simulation_case_based": (
        "open-ended business scenarios; assessment type 'Case studies' for Business Models and Group Report"
    ),
}


def build_rows(result: dict) -> list[dict]:
    rows = []
    for summary in result["summary"]:
        provisional = summary["category_id"] == "simulation_case_based"
        rows.append(
            {
                "unit_code": result["unit_code"],
                "unit_title": result["unit_title"],
                "level": "Postgraduate",
                "session": result["session"],
                "category": summary["category"],
                "belongs_to_category": "Yes - provisional" if provisional else "Yes - strong evidence",
                "evidence_item_count": summary["evidence_item_count"],
                "source_sections": "; ".join(
                    f"{section}={count}" for section, count in summary["section_counts"].items()
                ),
                "representative_evidence": REPRESENTATIVE_EVIDENCE[summary["category_id"]],
                "review_note": (
                    "Confirm whether the official assessment type 'Case studies' should be counted when the task content is an applied partner project/report."
                    if provisional
                    else "No material classification issue identified in the pilot."
                ),
                "source_url": result["source_url"],
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict], result: dict) -> None:
    lines = [
        "# Course-to-taxonomy mapping",
        "",
        "This table uses multi-label classification: one unit may belong to more than one pedagogical innovation category. The current pilot covers INFS6600 and the first two taxonomy categories only.",
        "",
        "| Unit | Level/session | Category | Classification | Evidence items | Source sections |",
        "|---|---|---|---|---:|---|",
    ]
    for row in rows:
        belongs = "Yes - provisional; client confirmation required" if "provisional" in row["belongs_to_category"] else "Yes - strong evidence"
        sections = row["source_sections"].replace("overview", "Overview").replace("learning_outcome", "Learning Outcomes").replace("assessment", "Assessments").replace("weekly_schedule", "Weekly Schedule")
        lines.append(
            f"| {row['unit_code']} {row['unit_title']} | PG / 2026 S2 | {row['category']} | {belongs} | {row['evidence_item_count']} | {sections} |"
        )

    lines += [
        "",
        "## Evidence comparison",
        "",
        "| Unit | Category | Representative evidence | Rationale |",
        "|---|---|---|---|",
    ]
    for row in rows:
        if "provisional" in row["belongs_to_category"]:
            note = "LO2 explicitly contains open-ended business scenarios. Two additional items use the official assessment type 'Case studies', but their content resembles a partner project/report, so the classification is provisional."
        else:
            note = "The overview, learning outcomes, assessments and weekly schedule contain direct evidence of actual organisations, business partners and professional presentations."
        lines.append(
            f"| {row['unit_code']} | {row['category']} | {row['representative_evidence']} | {note} |"
        )

    lines += [
        "",
        "## Conclusion",
        "",
        "- **INFS6600 clearly belongs to Work-Integrated and Applied Learning.**",
        "- **INFS6600 provisionally belongs to Simulation and Case-Based Learning.** LO2 is direct evidence; the client should confirm whether the two Case studies assessment types should be counted.",
        "- No classification is inferred for other BIS units until their outlines are acquired and processed through the same pipeline.",
        "",
        f"Official source: {result['source_url']}",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.input.read_text(encoding="utf-8"))
    rows = build_rows(result)
    write_markdown(args.markdown, rows, result)
    write_csv(args.csv, rows)
    print(f"Wrote {len(rows)} course-category rows")


if __name__ == "__main__":
    main()

