"""Fetch the complete 2026 CS-44 INFS corpus from public unit pages."""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import lxml.html

from fetch_outline import extract, fetch_html


UG_UNITS = [
    "INFS1000", "INFS1020", "INFS2010", "INFS2030", "INFS2040", "INFS2050",
    "INFS3040", "INFS3050", "INFS3080", "INFS3120", "INFS3400", "INFS3600",
]
PG_UNITS = [
    "INFS5002", "INFS6002", "INFS6004", "INFS6012", "INFS6015", "INFS6016",
    "INFS6018", "INFS6023", "INFS6024", "INFS6026", "INFS6032", "INFS6066",
    "INFS6071", "INFS6077", "INFS6600",
]


def discover_outline_url(unit_code: str, year: int = 2026) -> tuple[str, list[str]]:
    base = f"https://www.sydney.edu.au/units/{unit_code}"
    root = lxml.html.fromstring(fetch_html(base))
    prefix = f"/units/{unit_code}/{year}-"
    urls = sorted(
        {
            urljoin(base, link)
            for link in root.xpath("//a/@href")
            if link.startswith(prefix)
        }
    )
    if not urls:
        raise ValueError(f"No public {year} outline found for {unit_code}")
    # Scope rule: use Semester 2 when a unit has both Semester 1 and Semester 2.
    semester_2 = [url for url in urls if f"/{year}-S2" in url]
    semester_1 = [url for url in urls if f"/{year}-S1" in url]
    selected_pool = semester_2 or semester_1 or urls
    return selected_pool[0], urls


def fetch_one(code: str, level: str) -> dict:
    selected_url, available_urls = discover_outline_url(code)
    snapshot = extract(selected_url)
    snapshot["level"] = level
    snapshot["available_2026_outlines"] = available_urls
    snapshot["selection_rule"] = "Prefer Semester 2; otherwise Semester 1; otherwise first published 2026 outline."
    return snapshot


def fetch_corpus(delay: float = 0.0, workers: int = 6) -> dict:
    units, failures = [], []
    levels = {**{code: "UG" for code in UG_UNITS}, **{code: "PG" for code in PG_UNITS}}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(fetch_one, code, levels[code]): code for code in levels}
        for future in as_completed(futures):
            code = futures[future]
            try:
                snapshot = future.result()
                units.append(snapshot)
                print(f"Fetched {code} ({snapshot['session']})", flush=True)
            except Exception as exc:  # preserve a complete, auditable failure register
                failures.append({"unit_code": code, "level": levels[code], "error": str(exc)})
                print(f"FAILED {code}: {exc}", flush=True)
            time.sleep(delay)
    order = {code: i for i, code in enumerate(UG_UNITS + PG_UNITS)}
    units.sort(key=lambda row: order[row["unit_code"]])
    failures.sort(key=lambda row: order[row["unit_code"]])
    return {
        "corpus": "CS-44 2026 Business Information Systems units",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "selection_rule": "Latest Semester 2 outline where both main semesters are offered.",
        "requested_unit_count": len(levels),
        "fetched_unit_count": len(units),
        "failed_unit_count": len(failures),
        "units": units,
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    corpus = fetch_corpus(max(0.0, args.delay), args.workers)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(corpus, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {corpus['fetched_unit_count']}/{corpus['requested_unit_count']} units to {args.output}")


if __name__ == "__main__":
    main()
