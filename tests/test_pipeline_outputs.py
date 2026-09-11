from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from run_pipeline import _manifest_path  # noqa: E402
from visualize_corpus import draw_chart, draw_comparison  # noqa: E402


class PipelineOutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = [
            {
                "category": f"Category {index}",
                "all_units_with_evidence": index,
                "ug_units_with_evidence": index,
                "pg_units_with_evidence": index + 1,
            }
            for index in range(8)
        ]

    def test_corpus_charts_expand_to_fit_all_categories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            chart = Path(directory) / "chart.png"
            comparison = Path(directory) / "comparison.png"
            draw_chart(self.rows, chart, "all_units_with_evidence", "Test")
            draw_comparison(self.rows, comparison)

            with Image.open(chart) as image:
                self.assertGreaterEqual(image.height, 1196)
            with Image.open(comparison) as image:
                self.assertGreaterEqual(image.height, 1266)

    def test_manifest_path_supports_outputs_outside_project(self) -> None:
        project_root = Path("/workspace/project")
        output = Path("/tmp/pilot/report.pdf")
        self.assertEqual(str(output), _manifest_path(output, project_root))


if __name__ == "__main__":
    unittest.main()
