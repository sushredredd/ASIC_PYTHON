#!/usr/bin/env python3
"""Generate an SDC file from a YAML spec (clocks, IO delays, exceptions).

Usage:
  python tools/sdc_generator.py --spec samples/constraints_spec.yaml --out outputs/top.sdc
"""
import argparse, sys, logging, csv, json, pathlib
from typing import List, Dict, Any
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

import yaml

def emit_sdc(spec: Dict[str, Any]) -> str:
    lines = []
    for clk in spec.get("clocks", []):
        lines.append(f"create_clock -name {clk['name']} -period {clk['period']} -waveform {{{clk['waveform'][0]} {clk['waveform'][1]}}} [get_ports {clk['port']}]")
    io = spec.get("io_delays", {})
    for ip in io.get("inputs", []):
        lines.append(f"set_input_delay -max {ip['max']} [get_ports {ip['port']}] -clock [get_clocks *]")
        lines.append(f"set_input_delay -min {ip['min']} [get_ports {ip['port']}] -clock [get_clocks *]")
    for op in io.get("outputs", []):
        lines.append(f"set_output_delay -max {op['max']} [get_ports {op['port']}] -clock [get_clocks *]")
    for fp in spec.get("exceptions", {}).get("false_paths", []):
        lines.append(f"set_false_path -from {fp['from'][0]} -to {fp['to'][0]}")
    for mc in spec.get("exceptions", {}).get("multicycle", []):
        lines.append(f"set_multicycle_path {mc['setup']} -setup -from {mc['from'][0]} -to {mc['to'][0]}")
        lines.append(f"set_multicycle_path {mc['hold']} -hold  -from {mc['from'][0]} -to {mc['to'][0]}")
    return "\n".join(lines) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="YAML spec for constraints")
    ap.add_argument("--out", required=True, help="Output SDC file path")
    args = ap.parse_args()

    spec = yaml.safe_load(pathlib.Path(args.spec).read_text())
    sdc = emit_sdc(spec)
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out).write_text(sdc)
    logger.info("Wrote %s", args.out)

if __name__ == "__main__":
    main()
