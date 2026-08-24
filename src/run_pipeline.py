"""Run the complete INFS6600 extraction-to-visualisation pilot."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from fetch_outline import DEFAULT_URL


def run(script: Path, *arguments: object) -> None:
    command = [sys.executable, str(script), *(str(value) for value in arguments)]
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("pilot-output"),
        help="Destination for generated data, reports and PNG visualisations.",
    )
    parser.add_argument(
        "--taxonomy",
        type=Path,
        help="Optional JSON override for the built-in two-category taxonomy.",
    )
    args = parser.parse_args()

    source_dir = Path(__file__).resolve().parent
    output_dir = args.output_dir.resolve()
    raw = output_dir / "data" / "raw" / "infs6600_outline.json"
    result = output_dir / "data" / "processed" / "classification_results.json"
    evidence_csv = output_dir / "data" / "processed" / "classified_evidence.csv"
    course_summary = output_dir / "reports" / "infs6600_course_information.md"
    pilot_report = output_dir / "reports" / "pilot_results.md"
    mapping_md = output_dir / "reports" / "course_category_mapping.md"
    mapping_csv = output_dir / "reports" / "course_category_mapping.csv"
    visualisations = output_dir / "visualisations"

    run(source_dir / "fetch_outline.py", "--url", args.url, "--output", raw)
    run(source_dir / "generate_unit_summary.py", "--input", raw, "--output", course_summary)

    classification_args: list[object] = [
        "--input",
        raw,
        "--output",
        result,
        "--csv",
        evidence_csv,
    ]
    if args.taxonomy:
        classification_args.extend(["--taxonomy", args.taxonomy.resolve()])
    run(source_dir / "classify.py", *classification_args)

    run(
        source_dir / "generate_course_mapping.py",
        "--input",
        result,
        "--markdown",
        mapping_md,
        "--csv",
        mapping_csv,
    )

    report_args: list[object] = ["--result", result, "--output", pilot_report]
    if args.taxonomy:
        report_args.extend(["--taxonomy", args.taxonomy.resolve()])
    run(source_dir / "generate_report.py", *report_args)
    run(source_dir / "visualize.py", "--input", result, "--output-dir", visualisations)

    print("\nPipeline complete")
    print(f"Output directory: {output_dir}")
    print(f"Category chart: {visualisations / 'category_summary.png'}")
    print(f"Section chart: {visualisations / 'evidence_by_section.png'}")


if __name__ == "__main__":
    main()
