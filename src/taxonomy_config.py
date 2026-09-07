"""Load and validate the Week 4 v2 taxonomy configuration."""

from __future__ import annotations

import copy
import json
from pathlib import Path


DEFAULT_TAXONOMY_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "taxonomy_v2.json"
)


def validate_taxonomy(taxonomy: dict) -> None:
    """Fail early when a taxonomy cannot be scored reproducibly."""
    required = {"version", "counting_unit", "decision_thresholds", "categories"}
    missing = required - taxonomy.keys()
    if missing:
        raise ValueError(f"Taxonomy is missing required fields: {sorted(missing)}")

    thresholds = taxonomy["decision_thresholds"]
    positive = float(thresholds["positive"])
    high = float(thresholds["high_confidence"])
    if positive <= 0 or high < positive:
        raise ValueError("Decision thresholds must satisfy 0 < positive <= high_confidence")

    category_ids: set[str] = set()
    for category in taxonomy["categories"]:
        for field in ("id", "name", "definition", "rules"):
            if field not in category:
                raise ValueError(f"Category is missing required field: {field}")
        if category["id"] in category_ids:
            raise ValueError(f"Duplicate category id: {category['id']}")
        category_ids.add(category["id"])
        rule_labels: set[str] = set()
        for rule in category["rules"]:
            if not rule.get("label") or not rule.get("pattern"):
                raise ValueError(f"Incomplete rule in category {category['id']}")
            if rule["label"] in rule_labels:
                raise ValueError(
                    f"Duplicate rule label in {category['id']}: {rule['label']}"
                )
            rule_labels.add(rule["label"])
            if float(rule["weight"]) <= 0:
                raise ValueError(
                    f"Rule weight must be positive: {category['id']} / {rule['label']}"
                )


def load_taxonomy(path: Path | None = None) -> dict:
    """Load a caller-supplied taxonomy or the reviewed v2 default."""
    source = path if path is not None else DEFAULT_TAXONOMY_PATH
    taxonomy = json.loads(source.read_text(encoding="utf-8"))
    validate_taxonomy(taxonomy)
    return copy.deepcopy(taxonomy)
