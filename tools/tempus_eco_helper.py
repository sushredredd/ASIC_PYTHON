#!/usr/bin/env python3
"""Suggest ECOs from STA CSV (e.g., critical path cells/nets).

Usage:
  python tools/tempus_eco_helper.py --paths_csv outputs/sta_summary.csv --out outputs/eco_suggestions.csv
"""
import argparse, sys, logging, csv, json, pathlib
from typing import List, Dict, Any
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def analyze_paths(df: pd.DataFrame) -> pd.DataFrame:
    # Very simple heuristic placeholder
    df = df.copy()
    df["Recommendation"] = df.apply(lambda r: "Consider buffer/gate resize on critical arc" if (pd.notna(r.get("WNS")) and r.get("WNS", 0) < 0) else "No action"), axis=1)
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths_csv", required=True, help="CSV from sta_report_parser")
    ap.add_argument("--out", required=True, help="CSV with ECO suggestions")
    args = ap.parse_args()

    df = pd.read_csv(args.paths_csv)
    out = analyze_paths(df)
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    logger.info("Wrote %s", args.out)

if __name__ == "__main__":
    main()
