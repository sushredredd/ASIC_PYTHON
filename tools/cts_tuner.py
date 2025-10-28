#!/usr/bin/env python3
"""
Extract CTS metrics and recommend knob adjustments (incl. insertion delay), optionally using ccopt.skew.rpt.

Usage:
  python tools/cts_tuner.py \
    --log samples/tempus_report.txt \
    --out outputs/cts_reco.json \
    [--skew-rpt path/to/ccopt.skew.rpt] [--wns -0.120] [--has-hold]
"""

import argparse, json, logging, pathlib, re
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------
# Parsing helpers
# ---------------------------

def parse_wns_tns_from_log(text: str) -> Dict[str, Optional[float]]:
    """
    Looks for a line like 'WNS: -0.120  TNS: -57.000' (Tempus/PT)
    Returns dict with WNS/TNS floats if found, else None.
    """
    wns, tns = None, None
    # Common patterns
    pat_combo = re.compile(r"WNS:\s*([+-]?\d+(?:\.\d+)?)\s+TNS:\s*([+-]?\d+(?:\.\d+)?)", re.I)
    m = pat_combo.search(text)
    if m:
        try:
            wns = float(m.group(1))
            tns = float(m.group(2))
        except Exception:
            pass
    else:
        # Try individual patterns if the combined one isn't present
        m1 = re.search(r"WNS:\s*([+-]?\d+(?:\.\d+)?)", text, re.I)
        m2 = re.search(r"TNS:\s*([+-]?\d+(?:\.\d+)?)", text, re.I)
        if m1:
            try: wns = float(m1.group(1))
            except Exception: pass
        if m2:
            try: tns = float(m2.group(1))
            except Exception: pass
    return {"WNS": wns, "TNS": tns}

def parse_hold_presence(text: str) -> bool:
    """
    Very rough detection of hold issues in the log.
    """
    needles = [
        "hold violation",
        "negative hold slack",
        "slack (hold)",
        "Hold Slack (VIOLATED)"
    ]
    t = text.lower()
    return any(n in t for n in needles)

def parse_ccopt_skew_report(skew_text: str) -> Dict[str, Dict[str, float]]:
    """
    Tries to extract per-domain insertion delay and global skew from a ccopt.skew.rpt-like file.
    Expected lines (examples vary by version/env):
      Clock Domain: core_clk
      Average insertion delay: 1.82 ns
      Global skew: 125 ps
    Returns: { "core_clk": {"avg_insertion_ns": 1.82, "global_skew_ps": 125.0}, ... }
    """
    domains: Dict[str, Dict[str, float]] = {}
    current: Optional[str] = None

    for line in skew_text.splitlines():
        line = line.strip()
        mdom = re.match(r"(Clock\s*Domain|Domain)\s*:\s*([^\s]+)", line, re.I)
        if mdom:
            current = mdom.group(2)
            domains.setdefault(current, {})
            continue

        if current:
            mins = re.search(r"(Average\s+insertion\s+delay|Insertion\s+Delay)\s*:\s*([0-9.]+)\s*ns", line, re.I)
            if mins:
                domains[current]["avg_insertion_ns"] = float(mins.group(2))
            mskew = re.search(r"(Global\s+skew|Skew)\s*:\s*([0-9.]+)\s*ps", line, re.I)
            if mskew:
                domains[current]["global_skew_ps"] = float(mskew.group(2))

    return domains

# ---------------------------
# Heuristic policy
# ---------------------------

def recommend_for_domain(
    domain: str,
    wns: Optional[float],
    has_hold: bool,
    avg_insertion_ns: Optional[float],
    global_skew_ps: Optional[float],
) -> Dict[str, Any]:
    """
    Simple, actionable heuristics you can tune:
      - If WNS is negative (setup failing), bias toward *lower* insertion delay (reduce 10–20%) and tighten skew target.
      - If hold issues exist, slightly *increase* insertion delay (5–10%) to add margin (and/or loosen skew a touch).
      - If global skew is high (>120 ps), tighten skew target.
    """
    # Baseline targets if we have no data
    target_insertion = avg_insertion_ns if avg_insertion_ns is not None else 1.50
    target_skew = 80.0  # ps

    notes: List[str] = []

    if wns is not None and wns < -0.02:
        # Setup failing: reduce insertion to prioritize lower latency
        factor = 0.85 if wns < -0.10 else 0.9
        target_insertion = max(0.7, round(target_insertion * factor, 3))
        target_skew = min(70.0, target_skew)  # tighten a bit
        notes.append(
            f"{domain}: Setup failing (WNS={wns:.3f}). Reduce insertion delay ~10–15% and tighten skew target."
        )

    if has_hold:
        # Hold failing: increase insertion slightly, may loosen skew target slightly
        target_insertion = round(target_insertion * 1.08, 3)
        target_skew = max(90.0, target_skew)  # allow a bit more skew if needed
        notes.append(
            f"{domain}: Hold issues detected. Increase insertion delay ~5–10% and review min-delay fixes."
        )

    if global_skew_ps is not None and global_skew_ps > 120.0:
        # Too much global skew, try to tighten
        target_skew = min(target_skew, 70.0)
        notes.append(f"{domain}: High global skew ({global_skew_ps:.0f} ps). Target ≤70–80 ps.")

    # Guardrails
    target_insertion = float(min(max(target_insertion, 0.6), 2.2))  # 0.6–2.2 ns practical band
    target_skew = float(min(max(target_skew, 60.0), 120.0))        # 60–120 ps band

    # Implementation hints
    impl_hints = [
        "Reduce max_transition on long spines; upsize root buffers if latency balloons.",
        "Constrain ccopt with tighter -target_skew where failing, and adjust -max_insertion_delay accordingly.",
        "Rebalance CTS levels on critical domains; avoid over-buffering near sinks.",
        "Re-run STA (setup/hold) across worst/best PVT corners after CTS tweak."
    ]

    return {
        "domain": domain,
        "recommended_insertion_delay_ns": target_insertion,
        "recommended_skew_target_ps": target_skew,
        "observed": {
            "avg_insertion_ns": avg_insertion_ns,
            "global_skew_ps": global_skew_ps,
            "wns": wns,
            "hold_issues": has_hold,
        },
        "notes": notes,
        "implementation_hints": impl_hints,
    }

# ---------------------------
# Main orchestration
# ---------------------------

def propose_tuning(
    log_text: str,
    skew_text: Optional[str],
    wns_override: Optional[float],
    has_hold_override: Optional[bool],
) -> Dict[str, Any]:
    # Parse timing health
    timing = parse_wns_tns_from_log(log_text)
    wns_auto = timing.get("WNS")
    has_hold_auto = parse_hold_presence(log_text)

    wns = wns_override if wns_override is not None else wns_auto
    has_hold = has_hold_override if has_hold_override is not None else has_hold_auto

    # Parse skew report per domain
    domains_data: Dict[str, Dict[str, float]] = {}
    if skew_text:
        domains_data = parse_ccopt_skew_report(skew_text)

    # If no domains detected, assume single implicit domain called "default"
    if not domains_data:
        domains_data = {"default": {"avg_insertion_ns": None, "global_skew_ps": None}}

    # Build per-domain recommendations
    per_domain = []
    for d, vals in domains_data.items():
        per_domain.append(
            recommend_for_domain(
                domain=d,
                wns=wns,
                has_hold=has_hold,
                avg_insertion_ns=vals.get("avg_insertion_ns"),
                global_skew_ps=vals.get("global_skew_ps"),
            )
        )

    # Add global summary
    summary_notes = []
    if wns is None:
        summary_notes.append("WNS not found; consider providing --wns override.")
    if has_hold:
        summary_notes.append("Hold issues detected; verify min-delay fixes after CTS retune.")
    if skew_text and not per_domain:
        summary_notes.append("No domains parsed from skew report; check report format.")

    return {
        "summary": {
            "wns": wns,
            "tns": timing.get("TNS"),
            "hold_issues": has_hold,
            "notes": summary_notes,
        },
        "recommendations": per_domain,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True, help="CTS/STA log (Tempus/PT)")
    ap.add_argument("--out", required=True, help="JSON output path")
    ap.add_argument("--skew-rpt", help="Optional ccopt.skew.rpt for per-domain insertion/skew parsing")
    ap.add_argument("--wns", type=float, help="Override WNS (e.g., --wns -0.120)")
    ap.add_argument("--has-hold", action="store_true", help="Force flag if hold issues exist")
    args = ap.parse_args()

    log_t_
