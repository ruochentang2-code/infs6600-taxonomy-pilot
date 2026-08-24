"""Fetch and normalise an official University of Sydney unit outline.

The parser intentionally retains whole outline items instead of scraping isolated
keywords. That makes each later classification decision traceable to a public
source item and reduces duplicate counting.
"""

from __future__ import annotations

import argparse
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import lxml.html
import pandas as pd


DEFAULT_URL = "https://www.sydney.edu.au/units/INFS6600/2026-S2C-NE-CC"


def clean(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "INFS6600-taxonomy-pilot/1.0 (educational research; public page)"
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def find_table(tables: list[pd.DataFrame], required: set[str]) -> pd.DataFrame:
    for table in tables:
        columns = {clean(column) for column in table.columns}
        if required.issubset(columns):
            return table.copy()
    raise ValueError(f"Could not find table with columns: {sorted(required)}")


def extract(url: str) -> dict:
    html = fetch_html(url)
    root = lxml.html.fromstring(html)
    tables = pd.read_html(io.StringIO(html), keep_default_na=False)

    title = clean(root.xpath("string(//h1)"))
    session_candidates = [
        clean(node.text_content())
        for node in root.xpath("//h3")
        if clean(node.text_content()).startswith("Semester")
    ]
    session = session_candidates[0] if session_candidates else ""

    all_paragraphs = [clean(node.text_content()) for node in root.xpath("//p")]
    overview = []
    for text in all_paragraphs:
        if (
            text.startswith("This unit bridges the gap")
            or text.startswith("This experiential learning opportunity")
        ) and text not in overview:
            overview.append(text)

    learning_outcomes = []
    for node in root.xpath("//li"):
        text = clean(node.text_content())
        if re.match(r"^LO\d+\.", text) and text not in learning_outcomes:
            learning_outcomes.append(text)

    details_table = tables[0]
    details = {
        clean(row.iloc[0]): clean(row.iloc[1])
        for _, row in details_table.iterrows()
        if len(row) >= 2 and clean(row.iloc[0])
    }
    staff_table = tables[1]
    teaching_staff = {
        clean(row.iloc[0]): clean(row.iloc[1])
        for _, row in staff_table.iterrows()
        if len(row) >= 2 and clean(row.iloc[0])
    }

    assessment_table = find_table(tables, {"Type", "Description", "Weight"})
    assessments = []
    for _, row in assessment_table.iterrows():
        kind = clean(row.get("Type"))
        description = clean(row.get("Description"))
        if not kind or kind.startswith("Outcomes assessed") or kind.startswith("="):
            continue
        assessments.append(
            {
                "type": kind,
                "description": description,
                "weight": clean(row.get("Weight")),
                "due": clean(row.get("Due")),
                "length": clean(row.get("Length")),
            }
        )

    schedule_table = find_table(tables, {"WK", "Topic", "Learning activity"})
    schedule = []
    for _, row in schedule_table.iterrows():
        schedule.append(
            {
                "week": clean(row.get("WK")),
                "topic": clean(row.get("Topic")),
                "activity": clean(row.get("Learning activity")),
                "learning_outcomes": clean(row.get("Learning outcomes")),
            }
        )

    items = []
    for index, text in enumerate(overview, 1):
        items.append(
            {
                "item_id": f"OV{index:02d}",
                "section": "overview",
                "label": f"Overview paragraph {index}",
                "text": text,
            }
        )
    for index, text in enumerate(learning_outcomes, 1):
        items.append(
            {
                "item_id": f"LO{index:02d}",
                "section": "learning_outcome",
                "label": f"Learning outcome {index}",
                "text": text,
            }
        )
    for index, assessment in enumerate(assessments, 1):
        items.append(
            {
                "item_id": f"AS{index:02d}",
                "section": "assessment",
                "label": assessment["description"] or assessment["type"],
                "text": f"Type: {assessment['type']}. Description: {assessment['description']}",
                "metadata": assessment,
            }
        )
    for index, week in enumerate(schedule, 1):
        items.append(
            {
                "item_id": f"WK{index:02d}",
                "section": "weekly_schedule",
                "label": f"{week['week']}: {week['topic']}",
                "text": f"{week['topic']}. Learning activity: {week['activity']}",
                "metadata": week,
            }
        )

    return {
        "unit_code": title.split(":", 1)[0],
        "unit_title": title.split(":", 1)[1].strip() if ":" in title else title,
        "session": session,
        "source_url": url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "details": details,
        "teaching_staff": teaching_staff,
        "overview": overview,
        "learning_outcomes": learning_outcomes,
        "assessments": assessments,
        "weekly_schedule": schedule,
        "items": items,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = extract(args.url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(payload['items'])} auditable outline items to {args.output}")


if __name__ == "__main__":
    main()
