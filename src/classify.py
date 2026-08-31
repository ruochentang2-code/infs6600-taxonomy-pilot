"""Transparent multi-label taxonomy classifier for the CS-44 pilot."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from taxonomy_config import load_taxonomy


def normalise(text: str) -> str:
    text = text.lower().replace("–", "-").replace("—", "-")
    text = text.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip()


def score_item(text: str, category: dict) -> tuple[float, list[dict]]:
    """Score one item once for one category.

    A rule contributes its weight once even when several alternative phrases match.
    """
    normalised = normalise(text)
    matches: list[dict] = []
    score = 0.0
    for rule in category["rules"]:
        alternatives = [normalise(part) for part in rule["pattern"].split("|")]
        found = list(dict.fromkeys(phrase for phrase in alternatives if phrase in normalised))
        if not found:
            continue
        weight = float(rule["weight"])
        score += weight
        matches.append(
            {
                "rule": rule["label"],
                "matched_phrases": found,
                "weight": weight,
                "review_required": bool(rule.get("review_required", False)),
                "weight_status": rule.get("weight_status", "configured"),
            }
        )
    return round(score, 2), matches


def thresholds_for(category: dict, taxonomy: dict) -> tuple[float, float, str]:
    configured = taxonomy["decision_thresholds"] | category.get("decision_thresholds", {})
    return (
        float(configured["positive"]),
        float(configured["high_confidence"]),
        str(configured.get("status", "unspecified")),
    )


def _section_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["section"]] = counts.get(row["section"], 0) + 1
    return counts


def classify(snapshot: dict, taxonomy: dict) -> dict:
    """Classify every distinct item independently against every category."""
    evidence: list[dict] = []
    review_queue: list[dict] = []

    for item in snapshot["items"]:
        for category in taxonomy["categories"]:
            score, matches = score_item(item["text"], category)
            if not matches:
                continue
            positive_threshold, high_threshold, threshold_status = thresholds_for(
                category, taxonomy
            )
            review_only = all(match["review_required"] for match in matches)
            record = {
                "unit_code": snapshot["unit_code"],
                "category_id": category["id"],
                "category": category["name"],
                "item_id": item["item_id"],
                "section": item["section"],
                "label": item["label"],
                "text": item["text"],
                "score": score,
                "positive_threshold": positive_threshold,
                "high_confidence_threshold": high_threshold,
                "threshold_status": threshold_status,
                "matched_rules": matches,
                "manual_review_required": any(
                    match["review_required"] for match in matches
                ),
                "source_url": snapshot["source_url"],
            }
            if score >= positive_threshold and not review_only:
                record["classification_status"] = "positive"
                record["confidence"] = (
                    "high" if score >= high_threshold else "moderate"
                )
                evidence.append(record)
            else:
                record["classification_status"] = "review"
                record["confidence"] = "review"
                review_queue.append(record)

    summary: list[dict] = []
    for category in taxonomy["categories"]:
        category_evidence = [
            row for row in evidence if row["category_id"] == category["id"]
        ]
        category_review = [
            row for row in review_queue if row["category_id"] == category["id"]
        ]
        positive_total = round(sum(row["score"] for row in category_evidence), 2)
        review_total = round(sum(row["score"] for row in category_review), 2)
        if category_evidence:
            status = "positive"
        elif category_review:
            status = "review_only"
        else:
            status = "no_match"
        summary.append(
            {
                "category_id": category["id"],
                "category": category["name"],
                "classification_status": status,
                "belongs_to_category": bool(category_evidence),
                "evidence_item_count": len(category_evidence),
                "review_item_count": len(category_review),
                "classified_score_total": positive_total,
                "review_score_total": review_total,
                "total_matched_score": round(positive_total + review_total, 2),
                "section_counts": _section_counts(category_evidence),
                "review_section_counts": _section_counts(category_review),
                "overlap_notes": category.get("overlap_notes", ""),
                "review_guidance": category.get("review_guidance", ""),
            }
        )

    observed = {
        row["category_id"] for row in summary if row["belongs_to_category"]
    }
    expected = {
        "work_integrated_applied",
        "project_problem_based",
        "case_based",
    }
    regression = {
        "expected_positive_categories": sorted(expected),
        "observed_positive_categories": sorted(observed),
        "expected_categories_present": expected.issubset(observed),
        "simulation_positive": "simulation" in observed,
        "note": (
            "Simulation is evaluated independently. A true Simulation positive is not "
            "an error, but it must come from Simulation-specific evidence."
        ),
    }

    return {
        "unit_code": snapshot["unit_code"],
        "unit_title": snapshot["unit_title"],
        "session": snapshot["session"],
        "source_url": snapshot["source_url"],
        "retrieved_at": snapshot.get("retrieved_at", ""),
        "taxonomy_version": taxonomy["version"],
        "counting_unit": taxonomy["counting_unit"],
        "decision_thresholds": taxonomy["decision_thresholds"],
        "policies": taxonomy.get("policies", {}),
        "summary": summary,
        "evidence": evidence,
        "review_queue": review_queue,
        "tutor_feedback_regression": regression,
    }


def _rule_labels(row: dict) -> str:
    return "; ".join(match["rule"] for match in row["matched_rules"])


def write_evidence_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "unit_code",
        "category_id",
        "category",
        "item_id",
        "section",
        "label",
        "score",
        "classification_status",
        "confidence",
        "manual_review_required",
        "text",
        "matched_rule_labels",
        "source_url",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            payload = {field: row.get(field, "") for field in fields}
            payload["matched_rule_labels"] = _rule_labels(row)
            writer.writerow(payload)


def write_summary_csv(path: Path, summary: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "category_id",
        "category",
        "classification_status",
        "belongs_to_category",
        "evidence_item_count",
        "review_item_count",
        "classified_score_total",
        "review_score_total",
        "total_matched_score",
        "section_counts",
        "review_section_counts",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in summary:
            payload = {field: row.get(field, "") for field in fields}
            payload["section_counts"] = json.dumps(
                row["section_counts"], ensure_ascii=False, sort_keys=True
            )
            payload["review_section_counts"] = json.dumps(
                row["review_section_counts"], ensure_ascii=False, sort_keys=True
            )
            writer.writerow(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--taxonomy",
        type=Path,
        help="Optional JSON override. If omitted, tutor-feedback taxonomy v2 is used.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--review-csv", type=Path)
    parser.add_argument("--summary-csv", type=Path)
    args = parser.parse_args()

    snapshot = json.loads(args.input.read_text(encoding="utf-8"))
    taxonomy = load_taxonomy(args.taxonomy)
    result = classify(snapshot, taxonomy)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_evidence_csv(args.csv, result["evidence"])
    if args.review_csv:
        write_evidence_csv(args.review_csv, result["review_queue"])
    if args.summary_csv:
        write_summary_csv(args.summary_csv, result["summary"])
    for row in result["summary"]:
        print(
            f"{row['category']}: {row['evidence_item_count']} positive, "
            f"{row['review_item_count']} review, score {row['classified_score_total']}"
        )


if __name__ == "__main__":
    main()
