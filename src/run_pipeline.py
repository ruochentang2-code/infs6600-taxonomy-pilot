"""Run the complete CS-44 2026 INFS corpus pipeline."""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def run(script: Path, *arguments: object) -> None:
    subprocess.run([sys.executable, str(script), *(str(v) for v in arguments)], check=True)

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--output-dir",type=Path,default=Path("pilot-output")); p.add_argument("--taxonomy",type=Path); a=p.parse_args()
    source=Path(__file__).resolve().parent; output=a.output_dir.resolve(); raw=output/"data/raw/cs44_2026_infs_corpus.json"; result=output/"data/processed/classification_results.json"; processed=output/"data/processed"; visuals=output/"visualisations"
    run(source/"fetch_corpus.py","--output",raw)
    classification=["--input",raw,"--output",result,"--csv-dir",processed]
    if a.taxonomy: classification += ["--taxonomy",a.taxonomy.resolve()]
    run(source/"classify_corpus.py",*classification)
    run(source/"generate_corpus_report.py","--input",result,"--output",output/"reports/corpus_results.md")
    run(source/"visualize_corpus.py","--input",result,"--output-dir",visuals)
    print(f"Pipeline complete: {output}")
if __name__=="__main__": main()
