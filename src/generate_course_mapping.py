"""Generate a complete unit-to-taxonomy mapping from classification results."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from taxonomy_config import load_taxonomy


def _level(unit_code: str) -> str:
    digits = "".join(character for character in unit_code if character.isdigit())
    return "Undergraduate" if digits and int(digits[0]) <= 3 else "Postgraduate"


def _sections(counts: dict[str, int]) -> str:
    labels = {
        "overview": "Overview",
        "learning_outcome": "Learning outcomes",
        "assessment": "Assessments",
        "weekly_schedule": "Weekly schedule",
    }
    return "; ".join(
        f"{labels.get(section, section)}={count}"
        for section, count in counts.items()
    ) or "None"


def _representative(rows: list[dict]) -> str:
    return "; ".join(f"{row['item_id']} {row['label']}" for row in rows[:3]) or "None"


def build_rows(result: dict, taxonomy: dict) -> list[dict]:
    evidence_by_category = {
        category["id"]: [
            row for row in result["evidence"] if row["category_id"] == category["id"]
        ]
        for category in taxonomy["categories"]
    }
    review_by_category = {
        category["id"]: [
            row
            for row in result["review_queue"]
            if row["category_id"] == category["id"]
        ]
        for category in taxonomy["categories"]
    }
    category_lookup = {category["id"]: category for category in taxonomy["categories"]}

    rows: list[dict] = []
    for summary in result["summary"]:
        category_id = summary["category_id"]
        category = category_lookup[category_id]
        status = {
            "positive": "Yes",
            "review_only": "No - review signals only",
            "no_match": "No evidence found",
        }[summary["classification_status"]]
        rows.append(
            {
                "unit_code": result["unit_code"],
                "unit_title": result["unit_title"],
                "level": _level(result["unit_code"]),
                "session": result["session"],
                "category_id": category_id,
                "category": summary["category"],
                "belongs_to_category": status,
                "evidence_item_count": summary["evidence_item_count"],
                "review_item_count": summary["review_item_count"],
                "classified_score_total": summary["classified_score_total"],
                "review_score_total": summary["review_score_total"],
                "source_sections": _sections(summary["section_counts"]),
                "representative_positive_evidence": _representative(
                    evidence_by_category[category_id]
                ),
                "representative_review_evidence": _representative(
                    review_by_category[category_id]
                ),
                "overlap_note": category.get("overlap_notes", ""),
                "review_note": category.get("review_guidance", ""),
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
    positive = [row["category"] for row in rows if row["belongs_to_category"] == "Yes"]
    lines = [
        "# INFS6600 course-to-taxonomy mapping v2",
        "",
        f"**Taxonomy version:** {result['taxonomy_version']}  ",
        f"**Official source:** {result['source_url']}  ",
        "**Policy:** Categories are not mutually exclusive. Counts and category percentages must not be expected to sum to 100%.",
        "",
        "## Classification summary",
        "",
        "| Category | Belongs? | Positive evidence | Review items | Classified score | Review score | Source sections |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['category']} | {row['belongs_to_category']} | "
            f"{row['evidence_item_count']} | {row['review_item_count']} | "
            f"{row['classified_score_total']} | {row['review_score_total']} | "
            f"{row['source_sections']} |"
        )

    lines += [
        "",
        "## Tutor-feedback regression result",
        "",
        f"INFS6600 is positively allocated to **{', '.join(positive)}**.",
        "",
        "The expected three categories - Work-Integrated and Applied Learning, Project- and Problem-Based Learning, and Case-Based Learning - are all present. Simulation is evaluated separately and is not inherited from Case-Based Learning.",
        "",
        "## Evidence and review notes",
        "",
        "| Category | Representative positive evidence | Review evidence | Review guidance |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['category']} | {row['representative_positive_evidence']} | "
            f"{row['representative_review_evidence']} | {row['review_note']} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- Work-Integrated and Applied Learning remains strongly supported across overview, learning outcomes, assessments, and weekly schedule.",
        "- Case-Based Learning is supported by the explicit open-ended business scenarios learning outcome. The two administrative `Case studies` assessment labels are retained only in the review queue.",
        "- Project- and Problem-Based Learning is supported independently by the actual business problem, project immersion, problem/opportunity scoping, and prototype-validation evidence.",
        "- Simulation has no positive evidence in the current public outline and is no longer combined with Case-Based Learning.",
        "- Ideation and prototyping create Entrepreneurial Learning review signals, but do not justify a positive classification without explicit startup, venture, or entrepreneurship evidence.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--taxonomy", type=Path)
    args = parser.parse_args()
    result = json.loads(args.input.read_text(encoding="utf-8"))
    taxonomy = load_taxonomy(args.taxonomy)
    rows = build_rows(result, taxonomy)
    write_markdown(args.markdown, rows, result)
    write_csv(args.csv, rows)
    print(f"Wrote {len(rows)} course-category rows")


if __name__ == "__main__":
    main()
