"""Generate a readable Markdown summary of the extracted unit information."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def esc(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))

    lines = [
        "# INFS6600 course information",
        "",
        f"**Unit:** {data['unit_code']} - {data['unit_title']}",
        f"**Session:** {data['session']}",
        f"**Official source:** {data['source_url']}",
        f"**Retrieved:** {data['retrieved_at']}",
        "",
        "**Delivery note:** This Week 4 source summary forms part of the tutor-feedback v2 release completed collaboratively by the eight-member CS-44 project team.",
        "",
        "## Overview",
        "",
    ]
    lines.extend(data["overview"])
    lines += ["", "## Unit details", "", "| Field | Value |", "|---|---|"]
    for key, value in data["details"].items():
        lines.append(f"| {esc(key)} | {esc(value)} |")
    lines += ["", "## Teaching staff", "", "| Role | Name |", "|---|---|"]
    for key, value in data.get("teaching_staff", {}).items():
        lines.append(f"| {esc(key)} | {esc(value)} |")

    lines += ["", "## Learning outcomes", ""]
    for outcome in data["learning_outcomes"]:
        lines.append(f"- {outcome}")

    lines += [
        "",
        "## Assessments",
        "",
        "| Type | Description | Weight | Due | Length |",
        "|---|---|---:|---|---|",
    ]
    for row in data["assessments"]:
        lines.append(
            f"| {esc(row['type'])} | {esc(row['description'])} | {esc(row['weight'])} | {esc(row['due'])} | {esc(row['length'])} |"
        )

    lines += [
        "",
        "## Weekly schedule",
        "",
        "| Week | Topic | Activity | Learning outcomes |",
        "|---|---|---|---|",
    ]
    for row in data["weekly_schedule"]:
        lines.append(
            f"| {esc(row['week'])} | {esc(row['topic'])} | {esc(row['activity'])} | {esc(row['learning_outcomes'])} |"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote unit summary to {args.output}")


if __name__ == "__main__":
    main()
