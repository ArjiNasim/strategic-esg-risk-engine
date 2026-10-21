"""ESG risk scoring for the portfolio.

The offer asks to contribute to "strengthening of the ESG risk framework in APAC".
This module scores the portfolio on Environmental, Social and Governance
dimensions, aggregates an exposure-weighted ESG score, bands each counterparty,
and measures the book's exposure to ESG-sensitive sectors. ESG is framed as a risk
lens: low scores and sensitive-sector concentration are risk, not virtue signalling.

Scores are 0-100 (higher is better). The composite ESG score weights E/S/G and
maps to risk bands (Leader / Average / Laggard / High-risk).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .portfolio import SECTORS

__all__ = ["composite_score", "esg_band", "score_portfolio", "esg_report", "ESG_WEIGHTS"]

# weighting of the three pillars in the composite (governance slightly higher for banks)
ESG_WEIGHTS = {"env": 0.35, "soc": 0.30, "gov": 0.35}

_BANDS = [(0, 35, "High-risk"), (35, 50, "Laggard"), (50, 70, "Average"), (70, 101, "Leader")]


def composite_score(env, soc, gov) -> np.ndarray:
    return (ESG_WEIGHTS["env"] * np.asarray(env)
            + ESG_WEIGHTS["soc"] * np.asarray(soc)
            + ESG_WEIGHTS["gov"] * np.asarray(gov))


def esg_band(score) -> str:
    for lo, hi, name in _BANDS:
        if lo <= score < hi:
            return name
    return "High-risk"


def score_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["esg_score"] = composite_score(out["env_score"], out["soc_score"], out["gov_score"]).round(1)
    out["esg_band"] = out["esg_score"].apply(esg_band)
    out["sensitive_sector"] = out["sector"].map(lambda s: SECTORS[s]["sensitive"])
    return out


def esg_report(df: pd.DataFrame) -> dict:
    scored = score_portfolio(df)
    total = scored["ead"].sum()
    weighted = float((scored["esg_score"] * scored["ead"]).sum() / total) if total else 0.0
    sensitive_ead = float(scored.loc[scored["sensitive_sector"], "ead"].sum())
    # exposure by band
    band_ead = scored.groupby("esg_band")["ead"].sum().reindex(
        ["Leader", "Average", "Laggard", "High-risk"], fill_value=0.0
    )
    band_tbl = pd.DataFrame({
        "band": band_ead.index,
        "ead": band_ead.values,
        "share": band_ead.values / total if total else band_ead.values,
    })
    # worst names by ESG, weighted by exposure
    scored["esg_risk_contribution"] = (100 - scored["esg_score"]) * scored["ead"]
    worst = scored.nlargest(10, "esg_risk_contribution")[
        ["counterparty", "sector", "ead", "esg_score", "esg_band"]
    ]
    return {
        "weighted_esg_score": weighted,
        "weighted_band": esg_band(weighted),
        "sensitive_sector_ead": sensitive_ead,
        "sensitive_sector_share": sensitive_ead / total if total else 0.0,
        "by_band": band_tbl,
        "worst_contributors": worst,
        "scored": scored,
    }
