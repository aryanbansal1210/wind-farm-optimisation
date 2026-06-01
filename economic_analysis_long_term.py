# -*- coding: utf-8 -*-
"""
Created on Mon Oct 27 16:31:51 2025
@author: Christoforos
"""

import numpy_financial as npf
import matplotlib.pyplot as plt
import pandas as pd

# ==============================
# User Inputs
# ==============================
capacity_mw = float(input("Enter wind farm capacity (MW): ").replace(",", "."))
aep_gwh = float(input("Enter annual energy production (GWh): ").replace(",", "."))
hub_height = float(input("Enter hub height (m): ").replace(",", "."))

# Convert AEP to kWh
aep_kwh = aep_gwh * 1_000_000

# ==============================
# Fixed Parameters
# ==============================
energy_price_start = 0.068  # £/kWh
inflation_rate = 0.03  # 3%
discount_rate = 0.08  # 8%
aging_factor = 0.04  # 4%
lifetime_operational = 22  # 2 setup + 20 production

# ==============================
# CAPEX values
# ==============================
capex_pre_licensing = 64 * capacity_mw * 1000  # £64/kW
capex_regulatory = 45.9 * capacity_mw * 1000  # £45.9/kW
capex_infrastructure = 3_322_000  # Fixed

# Hub height cost factor
hub_height_factor = (1 + (0.15 / 2) * ((hub_height - 80) / 80))

# Apply hub height factor
capex_turbine_supply = 2_000_000 * capacity_mw * hub_height_factor
decommissioning_turbines = 150_000 * capacity_mw * hub_height_factor
repowering_cost = 1_000_000 * capacity_mw * hub_height_factor
life_extension_cost = 100_000 * capacity_mw * hub_height_factor

# ==============================
# OPEX assumptions
# ==============================
fixed_opex_per_mw = 22_000
variable_opex_per_mwh = 5.22
insurance_per_mw = 1_441
connection_charge_per_mw = 3_109

# ==============================
# Simulation Function
# ==============================
def simulate_case(extra_years=0, end_cost_year=None, end_cost=0, 
                  no_prod_years=None, reset_aging_year=None, decommission_year=None):
    total_years = lifetime_operational + extra_years
    cash_flows = []
    energy_generated = []
    yearly_details = []
    cum_cf = 0

    for year in range(1, total_years + 1):
        price = energy_price_start * ((1 + inflation_rate) ** (year - 1))
        capex = 0

        # Setup CAPEX
        if year == 1:
            capex = (capex_pre_licensing + capex_regulatory) * ((1 + inflation_rate) ** (year - 1))
        elif year == 2:
            capex = (capex_infrastructure + capex_turbine_supply) * ((1 + inflation_rate) ** (year - 1))

        # End-of-life or repowering/life extension CAPEX
        if end_cost_year and year == end_cost_year:
            capex += end_cost * ((1 + inflation_rate) ** (year - 1))
        if decommission_year and year == decommission_year:
            # Apply same decommissioning logic as other strategies
            capex += decommissioning_turbines * ((1 + inflation_rate) ** (year - 1))

        # Determine production
        if no_prod_years and year in no_prod_years:
            produces_energy = False
        elif year <= 2:
            produces_energy = False
        else:
            produces_energy = True

        # Aging logic
        if reset_aging_year and year >= reset_aging_year:
            aging_year = year - reset_aging_year
        else:
            aging_year = year - 1
        aging_multiplier = (1 + aging_factor) ** max(0, aging_year)

        if produces_energy:
            fixed_opex = (fixed_opex_per_mw + insurance_per_mw + connection_charge_per_mw) * capacity_mw * (
                (1 + inflation_rate) ** (year - 1)
            )
            var_opex = variable_opex_per_mwh * (aep_kwh / 1000) * (
                (1 + inflation_rate) ** (year - 1)
            ) * aging_multiplier
            total_opex = fixed_opex + var_opex
            revenue = aep_kwh * price
            energy_generated.append(aep_kwh)
        else:
            fixed_opex = var_opex = total_opex = revenue = 0

        net_cf = revenue - total_opex - capex
        cum_cf += net_cf
        cash_flows.append(net_cf)

        yearly_details.append({
            "Year": year,
            "Price (£/kWh)": price,
            "Fixed OPEX (£)": fixed_opex,
            "Var OPEX (£)": var_opex,
            "Total OPEX (£)": total_opex,
            "CAPEX (£)": capex,
            "Revenue (£)": revenue,
            "Net CF (£)": net_cf,
            "Cumulative Cash Flow (£)": cum_cf
        })

    # Financial metrics
    npv = npf.npv(discount_rate, cash_flows)
    irr = npf.irr(cash_flows)
    total_energy = sum(energy_generated)
    cum = 0
    payback_year = None
    for i, cf in enumerate(cash_flows, start=1):
        prev_cum = cum
        cum += cf
        if cum >= 0:
            if cf != 0:
                payback_year = i - 1 + abs(prev_cum) / cf
            else:
                payback_year = i
            break
    discounted_costs = [cf if cf < 0 else 0 for cf in cash_flows]
    lcoe = -npf.npv(discount_rate, discounted_costs) / (
        npf.npv(discount_rate, energy_generated) if total_energy > 0 else 1
    )
    return {
        "npv": npv,
        "irr": irr,
        "payback_year": payback_year,
        "lcoe": lcoe,
        "details": yearly_details,
    }

# ==============================
# Strategy Simulations
# ==============================
# 1. Decommissioning (no production in years 1–2, 23)
decom_result = simulate_case(
    extra_years=1, end_cost_year=23,
    no_prod_years=[1, 2, 23], decommission_year=23
)

# 2. Life Extension (no production in years 1–2, 23, 29)
life_ext_result = simulate_case(
    extra_years=7, end_cost_year=23, end_cost=life_extension_cost,
    no_prod_years=[1, 2, 23, 29], decommission_year=29
)

# 3. Repowering (no production in years 1–2, 23, 44, reset aging in 24)
repower_result = simulate_case(
    extra_years=22, end_cost_year=23, end_cost=repowering_cost,
    no_prod_years=[1, 2, 23, 44], reset_aging_year=24, decommission_year=44
)

# ==============================
# Plot Tables + Print to Console
# ==============================
def plot_table(df):
    fig, ax = plt.subplots(figsize=(22, 12))
    ax.axis("off")
    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.4, 1.6)
    plt.tight_layout()
    plt.show()

for name, result in [
    ("Decommissioning Strategy", decom_result),
    ("Life Extension Strategy", life_ext_result),
    ("Repowering Strategy", repower_result),
]:
    df = pd.DataFrame(result["details"])
    df = df[["Year", "Price (£/kWh)", "Fixed OPEX (£)", "Var OPEX (£)", "Total OPEX (£)",
             "CAPEX (£)", "Revenue (£)", "Net CF (£)", "Cumulative Cash Flow (£)"]]
    for col in df.columns[1:]:
        df[col] = df[col].map("{:,.0f}".format)
    print(f"\n===== {name} =====\n")
    print(df.to_string(index=False))
    plot_table(df)

# ==============================
# Summary Financial Comparison
# ==============================
comparison_df = pd.DataFrame([
    ["Decommissioning", decom_result["npv"], decom_result["irr"] * 100, decom_result["payback_year"], decom_result["lcoe"]],
    ["Life Extension", life_ext_result["npv"], life_ext_result["irr"] * 100, life_ext_result["payback_year"], life_ext_result["lcoe"]],
    ["Repowering", repower_result["npv"], repower_result["irr"] * 100, repower_result["payback_year"], repower_result["lcoe"]],
], columns=["Strategy", "NPV (£)", "IRR (%)", "Payback Period (yrs)", "LCOE (£/kWh)"])

comparison_df["NPV (£)"] = comparison_df["NPV (£)"].map("{:,.0f}".format)
comparison_df["IRR (%)"] = comparison_df["IRR (%)"].map("{:.1f}".format)
comparison_df["Payback Period (yrs)"] = comparison_df["Payback Period (yrs)"].map("{:.1f}".format)
comparison_df["LCOE (£/kWh)"] = comparison_df["LCOE (£/kWh)"].map("{:.5f}".format)

print("\n===== Financial Comparison of Strategies =====\n")
print(comparison_df.to_string(index=False))

fig, ax = plt.subplots(figsize=(9, 3))
ax.axis("off")
table = ax.table(cellText=comparison_df.values, colLabels=comparison_df.columns, cellLoc="center", loc="center")
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.3, 1.4)
plt.tight_layout()
plt.show()
