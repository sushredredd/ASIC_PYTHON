#!/usr/bin/env python3
"""Structural diff of two netlists (very high level).

Usage:
  python tools/netlist_diff.py --a a.v --b b.v --out outputs/netdiff.json
"""
import argparse, sys, logging, csv, json, pathlib
from typing import List, Dict, Any
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def summarize_modules(text: str) -> Dict[str, int]:
    counts = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("module "):
            name = line.split()[1].split("(")[0]
            counts[name] = counts.get(name, 0) + 1
    return counts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    a = summarize_modules(pathlib.Path(args.a).read_text(errors="ignore"))
    b = summarize_modules(pathlib.Path(args.b).read_text(errors="ignore"))
    delta = {
        "only_in_a": sorted(set(a) - set(b)),
        "only_in_b": sorted(set(b) - set(a)),
        "counts_a": a,
        "counts_b": b,
    }
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps(delta, indent=2))
    logger.info("Wrote %s", args.out)

if __name__ == "__main__":
    main()
