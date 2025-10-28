#!/usr/bin/env python3
"""Parse STA (Tempus/PrimeTime) reports to extract WNS/TNS and critical paths.

Usage:
  python tools/sta_report_parser.py --report <report.rpt> --out outputs/sta_summary.csv
"""
import argparse, sys, logging, csv, json, pathlib
from typing import List, Dict, Any
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def parse_report_text(text: str) -> Dict[str, Any]:
    # Naive parsing; adjust for your report formatting
    summary = {"WNS": None, "TNS": None, "paths": []}
    for line in text.splitlines():
        if "WNS:" in line and "TNS:" in line:
            try:
                parts = line.replace("WNS:", "WNS ").replace("TNS:", "TNS ").split()
                summary["WNS"] = float(parts[1])
                summary["TNS"] = float(parts[3])
            except Exception:
                pass
        if line.strip().startswith("Startpoint:"):
            path = {"start": line.split("Startpoint:")[1].strip()}
            summary["paths"].append(path)
        if line.strip().startswith("Endpoint:") and summary["paths"]:
            summary["paths"][-1]["end"] = line.split("Endpoint:")[1].strip()
    return summary

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, help="STA report file (Tempus/PT)")
    ap.add_argument("--out", required=True, help="CSV output path")
    args = ap.parse_args()

    text = pathlib.Path(args.report).read_text(errors="ignore")
    data = parse_report_text(text)
    rows = [{"WNS": data["WNS"], "TNS": data["TNS"], "Start": p.get("start",""), "End": p.get("end","")} for p in data["paths"]]
    df = pd.DataFrame(rows or [{"WNS": data["WNS"], "TNS": data["TNS"], "Start": "", "End": ""}])
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    logger.info("Wrote %s", args.out)

if __name__ == "__main__":
    main()
