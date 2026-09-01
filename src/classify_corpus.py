"""Classify every unit and create discipline/UG/PG aggregates."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from classify import classify
from taxonomy_config import load_taxonomy


def classify_all(corpus: dict, taxonomy: dict) -> dict:
    results = []
    for snapshot in corpus["units"]:
        result = classify(snapshot, taxonomy)
        result["level"] = snapshot["level"]
        results.append(result)

    aggregate = []
    for category in taxonomy["categories"]:
        row = {"category_id": category["id"], "category": category["name"]}
        for level in ("UG", "PG"):
            selected = [r for r in results if r["level"] == level]
            summaries = [next(s for s in r["summary"] if s["category_id"] == category["id"]) for r in selected]
            row[f"{level.lower()}_units_with_evidence"] = sum(s["evidence_item_count"] > 0 for s in summaries)
            row[f"{level.lower()}_evidence_items"] = sum(s["evidence_item_count"] for s in summaries)
        row["all_units_with_evidence"] = row["ug_units_with_evidence"] + row["pg_units_with_evidence"]
        row["all_evidence_items"] = row["ug_evidence_items"] + row["pg_evidence_items"]
        aggregate.append(row)
    return {
        "corpus": corpus["corpus"], "retrieved_at": corpus["retrieved_at"],
        "taxonomy_version": taxonomy["version"], "counting_unit": taxonomy["counting_unit"],
        "fetched_unit_count": corpus["fetched_unit_count"], "failures": corpus["failures"],
        "aggregate": aggregate, "units": results,
    }


def write_csvs(output_dir: Path, result: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_fields = ["unit_code", "level", "category", "item_id", "section", "label", "score", "confidence", "text", "matched_rule_labels", "source_url"]
    with (output_dir / "classified_evidence.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=evidence_fields); writer.writeheader()
        for unit in result["units"]:
            for row in unit["evidence"]:
                writer.writerow({**{f: row.get(f, "") for f in evidence_fields}, "level": unit["level"], "matched_rule_labels": "; ".join(m["rule"] for m in row["matched_rules"])})
    mapping_fields = ["unit_code", "unit_title", "level", "session", "category", "evidence_item_count", "has_evidence", "source_url"]
    with (output_dir / "unit_category_mapping.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=mapping_fields); writer.writeheader()
        for unit in result["units"]:
            for summary in unit["summary"]:
                writer.writerow({"unit_code": unit["unit_code"], "unit_title": unit["unit_title"], "level": unit["level"], "session": unit["session"], "category": summary["category"], "evidence_item_count": summary["evidence_item_count"], "has_evidence": "Yes" if summary["evidence_item_count"] else "No", "source_url": unit["source_url"]})
    with (output_dir / "category_aggregate.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result["aggregate"][0])); writer.writeheader(); writer.writerows(result["aggregate"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv-dir", type=Path, required=True); parser.add_argument("--taxonomy", type=Path)
    args = parser.parse_args()
    result = classify_all(json.loads(args.input.read_text(encoding="utf-8")), load_taxonomy(args.taxonomy))
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csvs(args.csv_dir, result)
    print(f"Classified {len(result['units'])} units across {len(result['aggregate'])} categories")


if __name__ == "__main__":
    main()
