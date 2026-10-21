"""A representative credit/counterparty portfolio for strategic risk analysis.

Strategic and portfolio risk analysis works off the book of exposures: who the
bank is lent to, in which sectors and geographies, at what rating, and with what
ESG profile. Real portfolios are confidential, so this module builds a
deterministic, seeded portfolio of counterparties calibrated to a diversified
APAC corporate bank, detailed enough for concentration, migration, ESG and
climate analysis.

Each counterparty carries: exposure (EAD), sector, geography (APAC-centric),
credit rating, and E/S/G sub-scores. Sector carbon intensity drives the climate
module; sector ESG baselines drive the ESG module.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["RATINGS", "SECTORS", "GEOGRAPHIES", "build_portfolio"]

RATINGS = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]

# sector: (baseline ESG environmental score 0-100, carbon intensity tonnes/Mn revenue, esg_sensitive)
SECTORS = {
    "Technology":            dict(env=78, carbon=25,  sensitive=False),
    "Financials":            dict(env=70, carbon=15,  sensitive=False),
    "Healthcare":            dict(env=72, carbon=30,  sensitive=False),
    "Consumer":              dict(env=65, carbon=60,  sensitive=False),
    "Industrials":           dict(env=52, carbon=180, sensitive=False),
    "Real Estate":           dict(env=58, carbon=90,  sensitive=False),
    "Utilities (power)":     dict(env=40, carbon=420, sensitive=True),
    "Oil, Gas & Coal":       dict(env=22, carbon=650, sensitive=True),
    "Mining & Metals":       dict(env=33, carbon=380, sensitive=True),
    "Transport & Aviation":  dict(env=38, carbon=310, sensitive=True),
}

GEOGRAPHIES = {
    # name: physical climate risk factor 0-1 (flood/heat/storm exposure)
    "Singapore":   0.25,
    "Malaysia":    0.45,
    "Indonesia":   0.60,
    "Hong Kong":   0.35,
    "Japan":       0.40,
    "Australia":   0.50,
    "India":       0.65,
    "Thailand":    0.55,
}


def build_portfolio(n=200, seed=42) -> pd.DataFrame:
    """Generate a diversified counterparty portfolio (deterministic)."""
    rng = np.random.default_rng(seed)
    sectors = list(SECTORS.keys())
    geos = list(GEOGRAPHIES.keys())
    # sector weights: overweight financials/industrials, some concentration
    sector_w = np.array([0.14, 0.18, 0.08, 0.12, 0.15, 0.09, 0.06, 0.07, 0.06, 0.05])
    sector_w = sector_w / sector_w.sum()
    rating_w = np.array([0.03, 0.10, 0.22, 0.30, 0.20, 0.11, 0.04])

    rows = []
    for i in range(n):
        sector = rng.choice(sectors, p=sector_w)
        geo = rng.choice(geos)
        rating = rng.choice(RATINGS, p=rating_w)
        # exposures are lognormal -> natural concentration in a few large names
        ead = float(np.round(rng.lognormal(3.0, 1.1), 1))  # in millions
        base_env = SECTORS[sector]["env"]
        env = float(np.clip(base_env + rng.normal(0, 8), 0, 100))
        soc = float(np.clip(rng.normal(60, 15), 0, 100))
        gov = float(np.clip(rng.normal(63, 14), 0, 100))
        rows.append({
            "counterparty": f"CP{i+1:03d}",
            "sector": sector,
            "geography": geo,
            "rating": rating,
            "ead": ead,
            "env_score": round(env, 1),
            "soc_score": round(soc, 1),
            "gov_score": round(gov, 1),
        })
    df = pd.DataFrame(rows)
    return df.sort_values("ead", ascending=False).reset_index(drop=True)


def portfolio_summary(df: pd.DataFrame) -> dict:
    return {
        "n_counterparties": len(df),
        "total_ead": float(df["ead"].sum()),
        "n_sectors": df["sector"].nunique(),
        "n_geographies": df["geography"].nunique(),
        "largest_exposure": float(df["ead"].max()),
    }
