"""Climate risk stress testing: transition and physical risk.

Climate risk enters a portfolio through two channels, following the NGFS (Network
for Greening the Financial System) framing that supervisors now expect:

  Transition risk - the cost of moving to a low-carbon economy. A carbon price
      shock raises costs for carbon-intensive sectors, lifting their default
      probability and generating credit losses. Three NGFS-style scenarios:
      Orderly, Disorderly, and Hot House World.

  Physical risk - the cost of climate change itself (floods, heat, storms). A
      geography-based hazard factor drives a value haircut on exposures.

The module translates each into an estimated portfolio loss, the quantified view a
risk committee and the strategic-risk function need.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .portfolio import SECTORS, GEOGRAPHIES

__all__ = ["NGFS_SCENARIOS", "transition_loss", "physical_loss", "climate_report"]

# NGFS-style scenarios: carbon price (USD/tonne) and a PD-sensitivity multiplier.
NGFS_SCENARIOS = {
    "Orderly (net zero 2050)":   dict(carbon_price=130, pd_sensitivity=0.6),
    "Disorderly (delayed)":      dict(carbon_price=250, pd_sensitivity=1.0),
    "Hot House World (>3C)":     dict(carbon_price=25,  pd_sensitivity=0.3, physical_mult=2.2),
}

# baseline loss-given-default assumption for climate-driven losses
_LGD = 0.45


def transition_loss(df: pd.DataFrame, carbon_price: float, pd_sensitivity: float) -> float:
    """Estimated credit loss from a carbon-price shock on carbon-intensive names.

    Each counterparty's PD uplift is proportional to its sector carbon intensity
    times the carbon price times a scenario sensitivity; loss = uplift x EAD x LGD.
    """
    df = df.copy()
    carbon = df["sector"].map(lambda s: SECTORS[s]["carbon"])
    # normalise carbon intensity to ~[0,1] (650 is the max sector intensity)
    intensity = carbon / 650.0
    # PD uplift in decimal: scaled so a disorderly 250 USD shock lifts the worst
    # sector PD by a few percentage points
    pd_uplift = intensity * (carbon_price / 250.0) * pd_sensitivity * 0.08
    loss = (pd_uplift * df["ead"] * _LGD).sum()
    return float(loss)


def physical_loss(df: pd.DataFrame, physical_mult: float = 1.0) -> float:
    """Estimated loss from physical hazard, by geography hazard factor."""
    df = df.copy()
    hazard = df["geography"].map(GEOGRAPHIES)
    # value haircut proportional to hazard, scaled modestly
    haircut = hazard * 0.03 * physical_mult
    loss = (haircut * df["ead"]).sum()
    return float(loss)


def climate_report(df: pd.DataFrame) -> dict:
    total_ead = df["ead"].sum()
    rows = []
    for name, sc in NGFS_SCENARIOS.items():
        trans = transition_loss(df, sc["carbon_price"], sc["pd_sensitivity"])
        phys = physical_loss(df, sc.get("physical_mult", 1.0))
        total = trans + phys
        rows.append({
            "scenario": name,
            "carbon_price": sc["carbon_price"],
            "transition_loss": trans,
            "physical_loss": phys,
            "total_climate_loss": total,
            "loss_pct_ead": 100 * total / total_ead if total_ead else 0.0,
        })
    tbl = pd.DataFrame(rows)
    # sector contribution to transition loss under the disorderly scenario
    disorderly = NGFS_SCENARIOS["Disorderly (delayed)"]
    d = df.copy()
    carbon = d["sector"].map(lambda s: SECTORS[s]["carbon"])
    intensity = carbon / 650.0
    pd_uplift = intensity * (disorderly["carbon_price"] / 250.0) * disorderly["pd_sensitivity"] * 0.08
    d["transition_loss"] = pd_uplift * d["ead"] * _LGD
    by_sector = d.groupby("sector")["transition_loss"].sum().sort_values(ascending=False)
    return {
        "scenarios": tbl,
        "transition_loss_by_sector": by_sector.reset_index(),
        "worst_scenario": tbl.loc[tbl["total_climate_loss"].idxmax(), "scenario"],
        "worst_loss": float(tbl["total_climate_loss"].max()),
    }
