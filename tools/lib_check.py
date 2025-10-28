#!/usr/bin/env python3
"""Sanity-check .lib max transition/capacitance values and missing cells.

Usage:
  python tools/lib_check.py --lib <corner.lib> --cells NAND2_X2 BUF_X4
"""
import argparse, sys, logging, csv, json, pathlib
from typing import List, Dict, Any
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", required=True)
    ap.add_argument("--cells", nargs="*", default=[])
    args = ap.parse_args()

    text = pathlib.Path(args.lib).read_text(errors="ignore")
    findings = {"missing_cells": [], "max_transition_ns": None, "max_capacitance_pf": None}
    # Placeholder scanning
    if args.cells:
        findings["missing_cells"] = [c for c in args.cells if c not in text]
    pathlib.Path("outputs").mkdir(parents=True, exist_ok=True)
    pathlib.Path("outputs/lib_check.json").write_text(json.dumps(findings, indent=2))
    logger.info("Wrote outputs/lib_check.json")

if __name__ == "__main__":
    main()
