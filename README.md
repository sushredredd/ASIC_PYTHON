# RTL Automation Portfolio

A curated set of **Python automation utilities** for RTL/PD flows — STA report parsing, SDC generation, CTS tuning, ECO assistance, and more.

> Owner: **Sushanth Reddy** · Location: Chandler, AZ  
> Focus: **FPGA/RTL/ASIC/Physical Design**, Cadence (Genus/Innovus/Tempus/Conformal), timing closure, ECOs, Python automation.

---

## 📦 Tools

- `tools/sta_report_parser.py` — Parse Cadence Tempus/Primetime reports; extract WNS/TNS, worst paths, violators.
- `tools/sdc_generator.py` — Generate SDC constraints from a YAML spec (clocks, IO delays, exceptions).
- `tools/tempus_eco_helper.py` — Suggest ECO actions (buffer/gate resize, cell swap) from critical paths CSV.
- `tools/cts_tuner.py` — Tune CTS knobs (skew targets, insertion cap) from run logs; emit recommendations.
- `tools/netlist_diff.py` — Structural RTL/netlist diff with module-level stats.
- `tools/spef_probe.py` — Probe SPEF parasitics; summarize cap/rc on selected nets.
- `tools/lib_check.py` — Quick sanity checks on .lib corners (max transition/cap, missing cells).

Each tool has:
- CLI via `argparse`
- Logging (`--verbose`)
- I/O using CSV/YAML/JSON
- Minimal unit tests in `tests/`

---

## 🚀 Quickstart

```bash
# 1) (Optional) Create venv
python -m venv .venv && source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt

# 3) Try a tool
python tools/sta_report_parser.py --report samples/tempus_report.txt --out outputs/sta_summary.csv
```

---

## 🧪 Tests & Lint

```bash
pytest -q
ruff check .
black --check .
```

---

## 🛠 Project Layout

```
rtl-automation-portfolio/
├─ tools/
├─ tests/
├─ samples/
├─ outputs/              # gitignored
├─ pyproject.toml
├─ requirements.txt
├─ README.md
└─ .github/workflows/python.yml
```

---

## 🔗 Scripts Overview

See `--help` for each script. Example:
```bash
python tools/sdc_generator.py --spec samples/constraints_spec.yaml --out outputs/top.sdc
```

---

## 📄 License

[MIT](LICENSE)
