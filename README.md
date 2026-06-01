# Onshore Wind Farm Layout & Techno-Economic Optimisation

**MSc Coursework (SEF01, Wind Energy) - Imperial College London (2025-26)**

A full technical and economic assessment of an onshore wind farm near **Camborne, Cornwall**, taking one year of Met Office wind data all the way through to an optimised turbine layout and a 22-year discounted-cash-flow model with end-of-life strategy comparison.

> **My role:** group project; I led the **technical assessment (the PyWake / TopFarm modelling in `technical_analysis_pywake.ipynb`)** and contributed to the **economic analysis**. The full author list is in the report PDF.

---

## What it does

**Part A - Technical assessment**
- Characterises the wind resource from Met Office records: cleans missing/outlier data, fits a **Weibull distribution**, builds an annual **wind rose** for directional variability, and extrapolates wind speed to hub height with a **power-law profile**.
- Selects a suitable site within a 15 km search radius on the Cornish coast.
- Screens commercially-available turbines, then **optimises the layout** (turbine count, inter-turbine spacing, array orientation, hub height, yaw) using **PyWake** with the Simple Bastankhah Gaussian wake model, plus **TopFarm** for layout optimisation, maximising annual energy yield against wake losses.

**Part B - Economic assessment**
- Builds a full **CAPEX / OPEX** breakdown and a 22-year **discounted-cash-flow** model, reporting LCOE, NPV, IRR and payback.
- Compares three end-of-life strategies: **decommissioning, life-extension, and repowering**.

## Headline results *(from the report)*

| Metric | Value |
|---|---|
| Optimal configuration | **13 x GE 2.5-120** turbines, 139 m hub height, 360 deg yaw control |
| Wake losses | **1.8 %** |
| Capacity factor | **59.0 %** |
| Annual energy production | **170.0 GWh/yr** |
| LCOE | **£0.053 / kWh** |
| NPV / IRR | **£26.6 M / 12.9 %** |
| Preferred end-of-life strategy | **Repowering** (sustained generation outweighs higher reinvestment) |

---

## Repository contents

| File | What it is |
|---|---|
| `technical_analysis_pywake.ipynb` | Wind resource characterisation + PyWake / TopFarm layout optimisation (my main contribution) |
| `economic_analysis_short_term.py` | Short-term economic / DCF analysis |
| `economic_analysis_long_term.py` | Long-term economic model (life-extension vs repowering) |
| `Wind_Farm_Report.pdf` | Full group report (methodology, results, authors) |

## Tech

`Python` · `PyWake` · `TopFarm` · `NumPy` / `SciPy` / `pandas` · `numpy-financial` · `windrose` · `shapely` · `xarray` · `matplotlib` / `seaborn`.

## Running it

The technical notebook needs `py_wake`, `topfarm` and the scientific-Python stack (see imports at the top). The economic scripts run on plain Python and take inputs interactively. The committed report PDF has the full results and figures if you do not want to run the code.

---

*Aryan Bansal - MSc Sustainable Energy Futures, Imperial College London · [LinkedIn](https://www.linkedin.com/in/aryanbansal1210)*
