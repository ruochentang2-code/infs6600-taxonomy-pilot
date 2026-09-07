"""Run either the full INFS corpus workflow or the INFS6600 pilot workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from fetch_outline import DEFAULT_URL
from taxonomy_config import DEFAULT_TAXONOMY_PATH


def run(script: Path, *arguments: object) -> None:
    subprocess.run(
        [sys.executable, str(script), *(str(value) for value in arguments)],
        check=True,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_corpus(args: argparse.Namespace, source_dir: Path) -> None:
    output_dir = args.output_dir.resolve()
    raw = output_dir / "data" / "raw" / "cs44_2026_infs_corpus.json"
    result = output_dir / "data" / "processed" / "classification_results.json"
    processed = output_dir / "data" / "processed"
    visualisations = output_dir / "visualisations"

    if args.snapshot:
        snapshot = args.snapshot.resolve()
        raw.parent.mkdir(parents=True, exist_ok=True)
        if snapshot != raw:
            shutil.copyfile(snapshot, raw)
    else:
        run(source_dir / "fetch_corpus.py", "--output", raw)

    run(
        source_dir / "classify_corpus.py",
        "--input", raw,
        "--output", result,
        "--csv-dir", processed,
        "--taxonomy", args.taxonomy.resolve(),
    )
    run(
        source_dir / "generate_corpus_report.py",
        "--input", result,
        "--output", output_dir / "reports" / "corpus_results.md",
    )
    run(
        source_dir / "visualize_corpus.py",
        "--input", result,
        "--output-dir", visualisations,
    )
    print(f"Corpus pipeline complete: {output_dir}")


def run_pilot(args: argparse.Namespace, source_dir: Path) -> None:
    output_dir = args.output_dir.resolve()
    pdf_output_dir = args.pdf_output_dir.resolve()
    raw = output_dir / "data" / "raw" / "infs6600_outline.json"
    result = output_dir / "data" / "processed" / "classification_results.json"
    evidence_csv = output_dir / "data" / "processed" / "classified_evidence.csv"
    review_csv = output_dir / "data" / "processed" / "review_queue.csv"
    summary_csv = output_dir / "data" / "processed" / "unit_category_summary.csv"
    course_summary = output_dir / "reports" / "infs6600_course_information.md"
    pilot_report = output_dir / "reports" / "pilot_results_v2.md"
    mapping_md = output_dir / "reports" / "course_category_mapping_v2.md"
    mapping_csv = output_dir / "reports" / "course_category_mapping_v2.csv"
    visualisations = output_dir / "visualisations"

    raw.parent.mkdir(parents=True, exist_ok=True)
    if args.snapshot:
        snapshot = args.snapshot.resolve()
        if snapshot != raw:
            shutil.copyfile(snapshot, raw)
    else:
        run(source_dir / "fetch_outline.py", "--url", args.url, "--output", raw)

    run(source_dir / "generate_unit_summary.py", "--input", raw, "--output", course_summary)
    run(
        source_dir / "classify.py",
        "--input", raw,
        "--taxonomy", args.taxonomy.resolve(),
        "--output", result,
        "--csv", evidence_csv,
        "--review-csv", review_csv,
        "--summary-csv", summary_csv,
    )
    run(
        source_dir / "generate_course_mapping.py",
        "--input", result,
        "--taxonomy", args.taxonomy.resolve(),
        "--markdown", mapping_md,
        "--csv", mapping_csv,
    )
    run(
        source_dir / "generate_report.py",
        "--result", result,
        "--taxonomy", args.taxonomy.resolve(),
        "--output", pilot_report,
    )
    run(source_dir / "visualize.py", "--input", result, "--output-dir", visualisations)

    pdf_files: list[Path] = []
    if not args.skip_pdf:
        run(
            source_dir / "generate_pdf_reports.py",
            "--result", result,
            "--taxonomy", args.taxonomy.resolve(),
            "--visualisations", visualisations,
            "--output-dir", pdf_output_dir,
        )
        pdf_files = [
            pdf_output_dir / "02_Classification_Algorithm_Detailed_v2.pdf",
            pdf_output_dir / "05_INFS6600_Course_Category_Mapping_v2.pdf",
        ]

    classification = json.loads(result.read_text(encoding="utf-8"))
    release_files = [
        raw, result, evidence_csv, review_csv, summary_csv, course_summary,
        pilot_report, mapping_md, mapping_csv,
        visualisations / "category_summary.png",
        visualisations / "category_scores.png",
        visualisations / "evidence_by_section.png",
        *pdf_files,
    ]
    manifest = {
        "release": "final-scoring-baseline",
        "taxonomy_version": classification["taxonomy_version"],
        "source_url": classification["source_url"],
        "retrieved_at": classification.get("retrieved_at", ""),
        "positive_categories": [
            row["category"]
            for row in classification["summary"]
            if row["belongs_to_category"]
        ],
        "week4_regression": classification["week4_regression"],
        "files": [
            {
                "path": str(path.relative_to(source_dir.parent)),
                "sha256": _sha256(path),
            }
            for path in release_files
            if path.exists()
        ],
    }
    (output_dir / "release_manifest_v2.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"INFS6600 pilot pipeline complete: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("corpus", "pilot"), default="corpus")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY_PATH)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--pdf-output-dir", type=Path, default=Path("output/pdf"))
    parser.add_argument("--skip-pdf", action="store_true")
    args = parser.parse_args()

    if args.output_dir is None:
        args.output_dir = Path("pilot-output" if args.mode == "corpus" else "output/v2")

    source_dir = Path(__file__).resolve().parent
    if args.mode == "corpus":
        run_corpus(args, source_dir)
    else:
        run_pilot(args, source_dir)


if __name__ == "__main__":
    main()
