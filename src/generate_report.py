"""Generate the evidence-led tutor-feedback v2 Markdown pilot report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from taxonomy_config import load_taxonomy


def esc(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _rule_text(row: dict) -> str:
    return "; ".join(match["rule"] for match in row["matched_rules"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument(
        "--taxonomy",
        type=Path,
        help="Optional JSON override. If omitted, tutor-feedback taxonomy v2 is used.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    taxonomy = load_taxonomy(args.taxonomy)

    positive_categories = [
        row["category"] for row in result["summary"] if row["belongs_to_category"]
    ]
    thresholds = result["decision_thresholds"]
    lines = [
        "# INFS6600 taxonomy pilot v2",
        "",
        f"**Unit:** {result['unit_code']} - {result['unit_title']}  ",
        f"**Outline:** {result['session']}  ",
        f"**Taxonomy:** {result['taxonomy_version']}  ",
        f"**Official source:** {result['source_url']}",
        "",
        "## Executive result",
        "",
        "INFS6600 is positively classified into: "
        + ", ".join(f"**{name}**" for name in positive_categories)
        + ".",
        "",
        "This is a multi-label result. Categories are not mutually exclusive, and one evidence item may support more than one category.",
        "",
        "| Category | Status | Positive items | Review items | Classified score | Review score |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for summary in result["summary"]:
        lines.append(
            f"| {summary['category']} | {summary['classification_status']} | "
            f"{summary['evidence_item_count']} | {summary['review_item_count']} | "
            f"{summary['classified_score_total']} | {summary['review_score_total']} |"
        )

    lines += [
        "",
        "## Tutor changes implemented",
        "",
        "- Simulation and Case-Based Learning are separate categories.",
        "- INFS6600 may appear in several categories; the classifier does not force a single winner.",
        "- Authentic practice is weighted 4.0; theory-practice integration 2.0; practical teamwork 2.0; career readiness 2.0 (the last remains provisional because the tutor wrote 'Maybe 2').",
        "- Administrative `Case studies` assessment labels are weak review signals with weight 2.0, rather than automatic positive evidence.",
        "- Total classified score, review score, distinct evidence count, and source-section distribution are reported separately.",
        "",
        "## Positive evidence",
        "",
        "| Category | Section | Item | Score | Confidence | Matched rules |",
        "|---|---|---|---:|---|---|",
    ]
    for row in result["evidence"]:
        lines.append(
            f"| {esc(row['category'])} | {row['section']} | {esc(row['item_id'] + ' ' + row['label'])} | "
            f"{row['score']} | {row['confidence']} | {esc(_rule_text(row))} |"
        )

    lines += [
        "",
        "## Manual-review queue",
        "",
        "| Category | Section | Item | Score | Reason |",
        "|---|---|---|---:|---|",
    ]
    for row in result["review_queue"]:
        reason = (
            "Review-only rule"
            if all(match["review_required"] for match in row["matched_rules"])
            else "Below positive threshold"
        )
        lines.append(
            f"| {esc(row['category'])} | {row['section']} | {esc(row['item_id'] + ' ' + row['label'])} | "
            f"{row['score']} | {reason}: {esc(_rule_text(row))} |"
        )

    lines += [
        "",
        "## Scoring and aggregation",
        "",
        "1. Split the public outline into distinct overview, learning-outcome, assessment, and weekly-schedule items.",
        "2. Normalise case, whitespace, apostrophes, and dash variants while preserving the original evidence text.",
        "3. Evaluate each item once against every category. Alternative phrases inside one rule contribute that rule's weight only once.",
        "4. A positive item must reach the provisional positive threshold and must contain at least one non-review-only rule.",
        "5. Deduplicate at item-category level. The same item may count once in several categories because the taxonomy is multi-label.",
        "6. Sum positive item scores to obtain the classified unit-category total. Report review scores separately rather than mixing ambiguous labels into the positive total.",
        "",
        f"The current thresholds are positive >= {thresholds['positive']} and high confidence >= {thresholds['high_confidence']}. Their status is `{thresholds['status']}`; they remain configurable and are not presented as client-validated cut-offs.",
        "",
        "## Category standards",
        "",
    ]
    for category in taxonomy["categories"]:
        lines += [
            f"### {category['name']}",
            "",
            category["definition"],
            "",
            f"Overlap: {category.get('overlap_notes', 'None documented')}",
            "",
            f"Review guidance: {category.get('review_guidance', 'None documented')}",
            "",
        ]

    lines += [
        "## Limitations and decisions still required",
        "",
        "- The 3.0 and 5.0 thresholds are provisional and require client confirmation or sensitivity testing against reviewed labels.",
        "- Career readiness is set to 2.0 following a tentative tutor comment and remains marked provisional in the configuration.",
        "- Phrase matching does not understand negation, complex context, or semantic equivalence.",
        "- This Week 4 iteration reruns INFS6600 only; no additional-unit or discipline-wide analysis is included.",
        "- Landing-page, LLM/RAG, and formal model-evaluation work are outside this update.",
        "",
        "## Visualisations",
        "",
        "![Positive and review evidence by category](../visualisations/category_summary.png)",
        "",
        "![Classified and review scores by category](../visualisations/category_scores.png)",
        "",
        "![Positive evidence by source section](../visualisations/evidence_by_section.png)",
        "",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote report to {args.output}")


if __name__ == "__main__":
    main()
