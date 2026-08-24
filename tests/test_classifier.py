import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from classify import classify, score_item  # noqa: E402


class ClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taxonomy = json.loads((ROOT / "config" / "taxonomy.json").read_text(encoding="utf-8"))

    def test_generic_project_does_not_count(self):
        category = self.taxonomy["categories"][0]
        score, _ = score_item("Students complete a group project and presentation.", category)
        self.assertLess(score, category["threshold"])

    def test_actual_business_problem_counts_as_applied(self):
        category = self.taxonomy["categories"][0]
        score, _ = score_item("Resolve an actual business problem.", category)
        self.assertGreaterEqual(score, category["threshold"])

    def test_open_ended_business_scenario_counts_as_case_based(self):
        category = self.taxonomy["categories"][1]
        score, _ = score_item("Analyse open-ended business scenarios.", category)
        self.assertGreaterEqual(score, category["threshold"])

    def test_item_is_counted_once_per_category(self):
        snapshot = {
            "unit_code": "TEST0000",
            "unit_title": "Test",
            "session": "Test session",
            "source_url": "https://example.invalid",
            "items": [{"item_id": "X1", "section": "overview", "label": "x", "text": "Pitch to partner and partner briefing"}],
        }
        result = classify(snapshot, self.taxonomy)
        applied = [row for row in result["evidence"] if row["category_id"] == "work_integrated_applied"]
        self.assertEqual(len(applied), 1)


if __name__ == "__main__":
    unittest.main()

