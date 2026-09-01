"""Generate an auditable Markdown corpus summary."""
from __future__ import annotations
import argparse, json
from pathlib import Path
def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--input",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); r=json.loads(a.input.read_text(encoding="utf-8"))
    lines=["# CS-44 2026 INFS corpus results","",f"Fetched **{r['fetched_unit_count']} of 27** requested public unit outlines.","","## Discipline and level comparison","","| Category | All units | UG units | PG units | Evidence items |","|---|---:|---:|---:|---:|"]
    for x in r["aggregate"]: lines.append(f"| {x['category']} | {x['all_units_with_evidence']} | {x['ug_units_with_evidence']} | {x['pg_units_with_evidence']} | {x['all_evidence_items']} |")
    lines += ["","A unit is counted once per category when at least one distinct outline item reaches that category's rule threshold. Evidence-item totals are reported separately.","","## Collection failures",""]
    if r["failures"]:
        lines += ["| Unit | Level | Error |","|---|---|---|"]
        for x in r["failures"]: lines.append(f"| {x['unit_code']} | {x['level']} | {str(x['error']).replace('|','/')} |")
    else: lines.append("None.")
    lines += ["","## Visualisations","","![Discipline categories](../visualisations/discipline_category_units.png)","","![UG vs PG](../visualisations/ug_pg_comparison.png)",""]
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text("\n".join(lines),encoding="utf-8")
if __name__=="__main__": main()
