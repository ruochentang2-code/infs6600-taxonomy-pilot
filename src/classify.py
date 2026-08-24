"""Transparent taxonomy classifier for the two-category INFS6600 pilot."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from taxonomy_config import load_taxonomy


def normalise(text: str) -> str:
    text = text.lower().replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def score_item(text: str, category: dict) -> tuple[float, list[dict]]:
    normalised = normalise(text)
    matches = []
    score = 0.0
    for rule in category["rules"]:
        alternatives = [normalise(part) for part in rule["pattern"].split("|")]
        found = [phrase for phrase in alternatives if phrase in normalised]
        if found:
            score += float(rule["weight"])
            matches.append(
                {
                    "rule": rule["label"],
                    "matched_phrases": found,
                    "weight": float(rule["weight"]),
                }
            )
    return round(score, 2), matches


def classify(snapshot: dict, taxonomy: dict) -> dict:
    evidence = []
    review_queue = []
    for item in snapshot["items"]:
        for category in taxonomy["categories"]:
            score, matches = score_item(item["text"], category)
            threshold = float(category["threshold"])
            record = {
                "unit_code": snapshot["unit_code"],
                "category_id": category["id"],
                "category": category["name"],
                "item_id": item["item_id"],
                "section": item["section"],
                "label": item["label"],
                "text": item["text"],
                "score": score,
                "threshold": threshold,
                "matched_rules": matches,
                "source_url": snapshot["source_url"],
            }
            if score >= threshold:
                record["confidence"] = "high" if score >= threshold + 2.0 else "moderate"
                evidence.append(record)
            elif score > 0:
                record["confidence"] = "review"
                review_queue.append(record)

    summary = []
    for category in taxonomy["categories"]:
        category_evidence = [row for row in evidence if row["category_id"] == category["id"]]
        section_counts = {}
        for row in category_evidence:
            section_counts[row["section"]] = section_counts.get(row["section"], 0) + 1
        summary.append(
            {
                "category_id": category["id"],
                "category": category["name"],
                "evidence_item_count": len(category_evidence),
                "section_counts": section_counts,
            }
        )

    return {
        "unit_code": snapshot["unit_code"],
        "unit_title": snapshot["unit_title"],
        "session": snapshot["session"],
        "source_url": snapshot["source_url"],
        "taxonomy_version": taxonomy["version"],
        "counting_unit": taxonomy["counting_unit"],
        "summary": summary,
        "evidence": evidence,
        "review_queue": review_queue,
    }


def write_csv(path: Path, evidence: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "unit_code",
        "category",
        "item_id",
        "section",
        "label",
        "score",
        "confidence",
        "text",
        "matched_rule_labels",
        "source_url",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in evidence:
            writer.writerow(
                {
                    **{field: row.get(field, "") for field in fields},
                    "matched_rule_labels": "; ".join(
                        match["rule"] for match in row["matched_rules"]
                    ),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--taxonomy",
        type=Path,
        help="Optional JSON override. If omitted, the built-in two-category pilot is used.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args()

    snapshot = json.loads(args.input.read_text(encoding="utf-8"))
    taxonomy = load_taxonomy(args.taxonomy)
    result = classify(snapshot, taxonomy)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(args.csv, result["evidence"])
    for row in result["summary"]:
        print(f"{row['category']}: {row['evidence_item_count']} evidence items")


if __name__ == "__main__":
    main()

