"""Generate a concise, evidence-led Markdown pilot report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def esc(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--taxonomy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    taxonomy = json.loads(args.taxonomy.read_text(encoding="utf-8"))
    category_lookup = {row["id"]: row for row in taxonomy["categories"]}

    lines = [
        "# INFS6600 two-category taxonomy pilot",
        "",
        f"**Unit:** {result['unit_code']} - {result['unit_title']}",
        f"**Outline:** {result['session']}",
        f"**Official source:** {result['source_url']}",
        "",
        "## Result",
        "",
        "| Category | Evidence items | Interpretation |",
        "|---|---:|---|",
    ]
    for summary in result["summary"]:
        interpretation = (
            "Strong, repeated evidence across the outline."
            if summary["evidence_item_count"] >= 5
            else "Limited, explicit evidence; manual confirmation recommended."
        )
        lines.append(f"| {summary['category']} | {summary['evidence_item_count']} | {interpretation} |")

    lines += [
        "",
        "The counts are not raw keyword frequencies. One count means one distinct overview paragraph, learning outcome, assessment row or weekly-schedule row classified above the threshold.",
        "",
        "## Evidence",
        "",
        "| Category | Section | Outline item | Score | Confidence | Matched rule |",
        "|---|---|---|---:|---|---|",
    ]
    for row in result["evidence"]:
        rule_text = "; ".join(match["rule"] for match in row["matched_rules"])
        lines.append(
            f"| {esc(row['category'])} | {row['section']} | {esc(row['label'])} | {row['score']} | {row['confidence']} | {esc(rule_text)} |"
        )

    lines += [
        "",
        "## Algorithm",
        "",
        "1. Fetch the latest Semester 2 official outline and split it into auditable items: overview paragraphs, learning outcomes, assessment rows and weekly-schedule rows.",
        "2. Normalise case, whitespace and dash variants without removing the original evidence text.",
        "3. Apply category-specific phrase rules derived from the supplied definitions and examples. Strong explicit phrases score 3.5-4.0; supporting phrases score 1.5-2.5.",
        "4. Classify an item only when its category score reaches 3.0. This prevents isolated generic terms such as 'project', 'business' or 'presentation' from creating a positive result.",
        "5. Deduplicate at item-category level and retain the matched rules, score, source section and official URL for audit.",
        "6. Place sub-threshold matches in a review queue rather than counting them.",
        "",
        "## Category standards used",
        "",
    ]
    for category in taxonomy["categories"]:
        lines += [
            f"### {category['name']}",
            "",
            category["definition"],
            "",
            f"Threshold: {category['threshold']}. Explicit evidence is required; contextual similarity alone is not counted in this two-day pilot.",
            "",
        ]

    lines += [
        "## Limitations and next step",
        "",
        "This is a transparent baseline, not a final semantic classifier. The administrative assessment type 'Case studies' is counted as explicit case-based evidence, but should be confirmed with the client because the task description itself concerns a partner's business model. The next iteration should add client-reviewed labels and compare precision/recall against a small manually annotated set before adding embeddings or an LLM.",
        "",
        "## Visualisations",
        "",
        "![Category evidence counts](../visualisations/category_summary.png)",
        "",
        "![Evidence by source section](../visualisations/evidence_by_section.png)",
        "",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote report to {args.output}")


if __name__ == "__main__":
    main()

