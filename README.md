# Water Security & Drought Readiness Lab V1.0

COP31 AI Solutions Lab — Day 7 (November 15, 2026). Independent educational Python project.

**Status:** Source code and automated tests are included. Live Gemini integration, Streamlit UI operation and real-world impact have not been verified on the user's machine.

## Six modules
1. Overview — synthetic basin indicators.
2. Water Stress Monitoring — transparent ratios, reservoir percentage and supply gaps.
3. Monitoring Gaps — missing and stale data flags.
4. Drought Readiness — deterministic what-if arithmetic.
5. AI & Human Review — optional Gemini structured JSON response and SQLite reviewer audit.
6. Export & Methodology — CSV/JSON exports, reference links and limitations.

## Windows / PyCharm (Python 3.12, 8 GB RAM, no GPU)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

To use Gemini, copy `.env.example` to `.env`, set your own API key, and restart Streamlit. **Never commit `.env`.** The other modules work without an API key. Gemini requests are made over the internet to Google's service; no local GPU is needed.

## Provenance and interpretation

All three basin records in `data/scenarios.json` are **synthetic**, not observations of real basins. WMO, FAO AQUASTAT and UN-Water URLs in `data/references.json` are **background references only** and were not used to derive the synthetic numbers. Dates in synthetic records are scenario labels, not observation dates. The 7-day staleness threshold and numeric flags are educational choices, **not official drought thresholds**. Missing values are never converted to zero.

Units: rainfall and baseline in millimetres per 30 days; reservoir in percent; supply and demand in megalitres per day (ML/day). `rainfall_ratio` is dimensionless. `supply_gap_mld = max(0, demand_mld - supply_mld)` when both are present. Demand reductions and additional supply are hypothetical inputs.

## Test and manual evaluation checklist

1. Run `python -m pytest -q` and record the actual result.
2. Start Streamlit and inspect all six tabs.
3. Confirm Basin C's missing rainfall and supply show as N/A, never zero.
4. Confirm stale and incomplete data flags are visible.
5. Compare demand-reduction scenarios; check results against manual arithmetic.
6. Optionally configure your own Gemini API key, invoke a single request, inspect the structured response and confirm only known scenario IDs are cited.
7. Save a `needs_revision` human review, inspect SQLite and export CSV/JSON.
8. Capture real screenshots only after executing these steps.

## Limitations

Not a drought early-warning system. No live ingestion, calibration, satellite observations, spatial modelling, hydrological forecasting, operational water allocation, measured environmental impact or scientific validation. AI can hallucinate despite schema checks; valid IDs do not prove factual support. SQLite audit is local and editable. No personal information is needed; use reviewer role/pseudonym.

**Evidence first. Engineering second. Measurable impact as the goal.**
