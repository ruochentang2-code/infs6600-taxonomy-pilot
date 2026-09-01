from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from classify import classify  # noqa: E402
from taxonomy_config import load_taxonomy  # noqa: E402


class Week4RegressionTests(unittest.TestCase):
    def test_expected_three_categories_without_simulation_inheritance(self) -> None:
        snapshot = {
            "unit_code": "INFS6600",
            "unit_title": "Business Information Systems Capstone",
            "session": "Semester 2, 2026",
            "source_url": "https://www.sydney.edu.au/units/INFS6600/2026-S2C-NE-CC",
            "retrieved_at": "2026-09-01T00:00:00+00:00",
            "items": [
                {
                    "item_id": "OV01",
                    "section": "overview",
                    "label": "Overview paragraph 1",
                    "text": "Theory and practice in authentic situations with practical teamwork experience and career readiness.",
                },
                {
                    "item_id": "LO02",
                    "section": "learning_outcome",
                    "label": "Learning outcome 2",
                    "text": "Analyse open-ended business scenarios.",
                },
                {
                    "item_id": "LO03",
                    "section": "learning_outcome",
                    "label": "Learning outcome 3",
                    "text": "Resolve an actual business problem.",
                },
                {
                    "item_id": "WK01",
                    "section": "weekly_schedule",
                    "label": "Project immersion",
                    "text": "Project immersion.",
                },
                {
                    "item_id": "AS01",
                    "section": "assessment",
                    "label": "Partner report",
                    "text": "Type: Case studies. Description: Partner report.",
                },
            ],
        }
        result = classify(snapshot, load_taxonomy())
        positive = {
            row["category_id"]
            for row in result["summary"]
            if row["belongs_to_category"]
        }
        self.assertTrue(
            {
                "work_integrated_applied",
                "case_based",
                "project_problem_based",
            }.issubset(positive)
        )
        self.assertNotIn("simulation", positive)
        self.assertTrue(
            result["week4_regression"]["expected_categories_present"]
        )


if __name__ == "__main__":
    unittest.main()
