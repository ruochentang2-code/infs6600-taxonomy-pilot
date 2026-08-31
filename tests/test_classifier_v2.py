from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from classify import classify, score_item  # noqa: E402
from taxonomy_config import load_taxonomy  # noqa: E402


def snapshot(*items: dict) -> dict:
    return {
        "unit_code": "TEST1000",
        "unit_title": "Test Unit",
        "session": "Semester 2, 2026",
        "source_url": "https://example.edu/TEST1000",
        "retrieved_at": "2026-09-01T00:00:00+00:00",
        "items": list(items),
    }


def item(item_id: str, text: str, section: str = "overview") -> dict:
    return {
        "item_id": item_id,
        "section": section,
        "label": item_id,
        "text": text,
    }


class TaxonomyV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.taxonomy = load_taxonomy()
        self.categories = {
            category["id"]: category for category in self.taxonomy["categories"]
        }

    def test_eight_categories_and_separate_simulation_case(self) -> None:
        self.assertEqual(8, len(self.taxonomy["categories"]))
        self.assertIn("simulation", self.categories)
        self.assertIn("case_based", self.categories)
        self.assertNotIn("simulation_case_based", self.categories)

    def test_tutor_adjusted_wil_weights(self) -> None:
        weights = {
            rule["label"]: float(rule["weight"])
            for rule in self.categories["work_integrated_applied"]["rules"]
        }
        self.assertEqual(4.0, weights["authentic practice"])
        self.assertEqual(2.0, weights["theory-practice integration"])
        self.assertEqual(2.0, weights["practical teamwork"])
        self.assertEqual(2.0, weights["career readiness"])

    def test_rule_alternatives_count_once(self) -> None:
        category = {
            "rules": [
                {
                    "label": "one rule",
                    "pattern": "case study|case studies",
                    "weight": 4.0,
                }
            ]
        }
        score, matches = score_item("Case study and case studies", category)
        self.assertEqual(4.0, score)
        self.assertEqual(1, len(matches))
        self.assertEqual(2, len(matches[0]["matched_phrases"]))

    def test_multi_label_same_item(self) -> None:
        result = classify(
            snapshot(item("LO01", "Resolve an actual business problem")),
            self.taxonomy,
        )
        positive = {row["category_id"] for row in result["evidence"]}
        self.assertIn("work_integrated_applied", positive)
        self.assertIn("project_problem_based", positive)

    def test_administrative_case_label_is_review_only(self) -> None:
        result = classify(
            snapshot(
                item(
                    "AS01",
                    "Type: Case studies. Description: Partner business model report",
                    "assessment",
                )
            ),
            self.taxonomy,
        )
        self.assertFalse(
            any(row["category_id"] == "case_based" for row in result["evidence"])
        )
        reviews = [
            row for row in result["review_queue"] if row["category_id"] == "case_based"
        ]
        self.assertEqual(1, len(reviews))
        self.assertEqual(2.0, reviews[0]["score"])

    def test_summary_reports_positive_and_review_scores_separately(self) -> None:
        result = classify(
            snapshot(
                item("LO02", "Analyse open-ended business scenarios", "learning_outcome"),
                item("AS01", "Type: Case studies. Description: Report", "assessment"),
            ),
            self.taxonomy,
        )
        case_summary = next(
            row for row in result["summary"] if row["category_id"] == "case_based"
        )
        self.assertEqual(1, case_summary["evidence_item_count"])
        self.assertEqual(1, case_summary["review_item_count"])
        self.assertEqual(3.5, case_summary["classified_score_total"])
        self.assertEqual(2.0, case_summary["review_score_total"])
        self.assertEqual(5.5, case_summary["total_matched_score"])


if __name__ == "__main__":
    unittest.main()
