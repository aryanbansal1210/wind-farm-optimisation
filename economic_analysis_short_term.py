# -*- coding: utf-8 -*-
"""
Created on Mon Oct 27 16:31:51 2025

@author: ChristoforosN
"""

import numpy_financial as npf
import matplotlib.pyplot as plt
import pandas as pd

# ==============================
# User Inputs
# ==============================
capacity_mw = float(input("Enter wind farm capacity (MW): "))
aep_gwh = float(input("Enter annual energy production (GWh): "))
hub_height = float(input("Enter hub height (m): "))

# Convert AEP to kWh
aep_kwh = aep_gwh * 1_000_000

# ==============================
# Fixed Parameters
# ==============================
energy_price_start = 0.068      # £/kWh
inflation_rate = 0.03           # 3%
discount_rate = 0.08            # 8%
aging_factor = 0.04             # 4%
lifetime_operational = 22       # 2 setup years + 20 years production

# ==============================
# CAPEX values
# ==============================
capex_pre_licensing = 64 * capacity_mw * 1000               # £64/kW
capex_regulatory = 45.9 * capacity_mw * 1000                # £45.9/kW
capex_infrastructure = 3_322_000                            # Fixed

# Hub height cost factor
hub_height_factor = (1 + (0.15 / 2) * ((hub_height - 80) / 80))

# Apply hub height factor to turbine-related costs
capex_turbine_supply = 2_000_000 * capacity_mw * hub_height_factor
decommissioning_turbines = 150_000 * capacity_mw * hub_height_factor
repowering_cost = 1_000_000 * capacity_mw * hub_height_factor
life_extension_cost = 100_000 * capacity_mw * hub_height_factor

# ==============================
# OPEX assumptions
# ==============================
fixed_opex_per_mw = 22_000       # £/MW/year
variable_opex_per_mwh = 5.22     # £/MWh
insurance_per_mw = 1_441         # £/MW/year
connection_charge_per_mw = 3_109 # £/MW/year

# ==============================
# Cashflow Simulation
# ==============================
def simulate_case():
    total_years = lifetime_operational
    cash_flows = []
    energy_generated = []
    yearly_details = []

    for year in range(1, total_years + 1):
        price = energy_price_start * ((1 + inflation_rate) ** (year - 1))

        # CAPEX timing
        if year == 1:
            capex = (capex_pre_licensing + capex_regulatory) * ((1 + inflation_rate) ** (year - 1))
        elif year == 2:
            capex = (capex_infrastructure + capex_turbine_supply) * ((1 + inflation_rate) ** (year - 1))
        else:
            capex = 0  # No end-of-life CAPEX (farm assumed to operate normally in year 22)

        # Determine if the year produces energy
        produces_energy = (year >= 3)

        # Aging multiplier
        aging_multiplier = (1 + aging_factor) ** (year - 1)

        # OPEX + Revenue
        if produces_energy:
            fixed_opex = (fixed_opex_per_mw + insurance_per_mw + connection_charge_per_mw) \
                         * capacity_mw * ((1 + inflation_rate) ** (year - 1))
            var_opex = variable_opex_per_mwh * (aep_kwh / 1000) \
                       * ((1 + inflation_rate) ** (year - 1)) * aging_multiplier
            total_opex = fixed_opex + var_opex
            revenue = aep_kwh * price
            energy_generated.append(aep_kwh)
        else:
            total_opex = revenue = 0

        # Net Cash Flow
        net_cf = revenue - total_opex - capex
        cash_flows.append(net_cf)

        yearly_details.append({
            "Year": year,
            "Price (£/kWh)": price,
            "Fixed OPEX (£)": fixed_opex if produces_energy else 0,
            "Var OPEX (£)": var_opex if produces_energy else 0,
            "Total OPEX (£)": total_opex,
            "CAPEX (£)": capex,
            "Revenue (£)": revenue,
            "Net CF (£)": net_cf
        })

    # Financial metrics
    npv = npf.npv(discount_rate, cash_flows)
    irr = npf.irr(cash_flows)
    total_energy = sum(energy_generated)

    # Payback period
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

    # LCOE
    discounted_costs = [cf if cf < 0 else 0 for cf in cash_flows]
    lcoe = -npf.npv(discount_rate, discounted_costs) / (npf.npv(discount_rate, energy_generated) if total_energy > 0 else 1)

    return {
        "npv": npv,
        "irr": irr,
        "payback_year": payback_year,
        "lcoe": lcoe,
        "details": yearly_details
    }

# ==============================
# Run Simulation (Single Case)
# ==============================
result = simulate_case()

# ==============================
# Year 22 Inflation-Adjusted Costs
# ==============================
decommissioning_turbines_22 = decommissioning_turbines * ((1 + inflation_rate) ** (lifetime_operational - 1))
repowering_cost_22 = repowering_cost * ((1 + inflation_rate) ** (lifetime_operational - 1))
life_extension_cost_22 = life_extension_cost * ((1 + inflation_rate) ** (lifetime_operational - 1))

# ==============================
# Plot Financial Table (Years 1–22)
# ==============================
details = result["details"]

# Compute cumulative cash flow
cum_cf = 0
rows = []
for row in details:
    cum_cf += row["Net CF (£)"]
    row["Cumulative CF (£)"] = cum_cf
    rows.append(row)

df = pd.DataFrame(rows)
df = df[["Year", "Price (£/kWh)", "Fixed OPEX (£)", "Var OPEX (£)", "Total OPEX (£)",
         "CAPEX (£)", "Revenue (£)", "Net CF (£)", "Cumulative CF (£)"]]

# Format numeric values
df["Price (£/kWh)"] = df["Price (£/kWh)"].map("{:.4f}".format)
for col in ["Fixed OPEX (£)", "Var OPEX (£)", "Total OPEX (£)", "CAPEX (£)", "Revenue (£)", "Net CF (£)", "Cumulative CF (£)"]:
    df[col] = df[col].map("{:,.0f}".format)

# Plot the table
fig, ax = plt.subplots(figsize=(14, 7))
ax.axis("off")
table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc="center", loc="center")
table.auto_set_font_size(False)
table.set_fontsize(8)
table.scale(1.1, 1.2)
ax.set_title("Simplified Financial Overview (Years 1–22)", fontsize=14, fontweight="bold", pad=20)
plt.tight_layout()
plt.show()

# ==============================
# Plot Only Year 22 Costs
# ==============================
cost_data_22 = [
    ["Decommissioning", f"{decommissioning_turbines_22:,.0f}"],
    ["Repowering", f"{repowering_cost_22:,.0f}"],
    ["Life Extension", f"{life_extension_cost_22:,.0f}"],
]
cost_df_22 = pd.DataFrame(cost_data_22, columns=["Strategy", "Cost (£)"])

fig, ax = plt.subplots(figsize=(6, 2))
ax.axis("off")
table = ax.table(cellText=cost_df_22.values, colLabels=cost_df_22.columns, cellLoc="center", loc="center")
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.4)
ax.set_title("Cost Details (Year 22, Adjusted for Inflation)", fontsize=13, fontweight="bold", pad=10)
plt.tight_layout()
plt.show()

# ==============================
# End-of-Life Strategy Comparison
# ==============================
strategies = {
    "Decommissioning": decommissioning_turbines_22,
    "Repowering": repowering_cost_22,
    "Life Extension": life_extension_cost_22
}

comparison_results = []

for name, end_cost in strategies.items():
    sim = simulate_case()
    cash_flows = [d["Net CF (£)"] for d in sim["details"]]
    cash_flows[-1] -= end_cost  # Apply end-of-life cost at Year 22

    # Energy generation for LCOE
    energy_generated = [aep_kwh if i >= 2 else 0 for i in range(lifetime_operational)]

    npv = npf.npv(discount_rate, cash_flows)
    irr = npf.irr(cash_flows)
    discounted_costs = [cf if cf < 0 else 0 for cf in cash_flows]
    lcoe = -npf.npv(discount_rate, discounted_costs) / npf.npv(discount_rate, energy_generated)

    comparison_results.append([name, npv, irr * 100, lcoe])

# Create comparison table
comparison_df = pd.DataFrame(comparison_results, columns=["Strategy", "NPV, £", "IRR, %", "LCOE, £/kWh"])
comparison_df["NPV, £"] = comparison_df["NPV, £"].map("{:,.0f}".format)
comparison_df["IRR, %"] = comparison_df["IRR, %"].map("{:.1f}".format)
comparison_df["LCOE, £/kWh"] = comparison_df["LCOE, £/kWh"].map("{:.5f}".format)

# Plot comparison table
fig, ax = plt.subplots(figsize=(6, 2.3))
ax.axis("off")
table = ax.table(
    cellText=comparison_df[["NPV, £", "IRR, %", "LCOE, £/kWh"]].values,
    rowLabels=comparison_df["Strategy"],
    colLabels=["NPV, £", "IRR, %", "LCOE, £/kWh"],
    cellLoc="center", loc="center"
)
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.3)
ax.set_title("Financial Comparison of End-of-Life Strategies", fontsize=13, fontweight="bold", pad=10)
plt.tight_layout()
plt.show()
