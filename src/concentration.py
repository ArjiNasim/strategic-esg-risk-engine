"""Portfolio concentration analytics.

Concentration is the first thing a strategic-risk review looks at: a portfolio can
look diversified on average yet be dangerously exposed to one name, one sector or
one country. This module computes the standard concentration measures a risk
committee monitors.

  HHI (Herfindahl-Hirschman Index) = sum of squared shares. 1/HHI is the
      "effective number" of equal-sized exposures; a low effective number flags
      concentration.
  Top-N concentration = share of the N largest exposures.
  Gini coefficient    = inequality of the exposure distribution (0 even, 1 concentrated).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["hhi", "effective_number", "top_n_concentration", "gini", "concentration_by", "concentration_report"]


def _shares(exposures) -> np.ndarray:
    e = np.asarray(exposures, dtype=float)
    total = e.sum()
    return e / total if total > 0 else e


def hhi(exposures) -> float:
    """Herfindahl-Hirschman Index of the exposure shares (0..1)."""
    s = _shares(exposures)
    return float(np.sum(s**2))


def effective_number(exposures) -> float:
    """Effective number of equal exposures = 1 / HHI."""
    h = hhi(exposures)
    return float(1 / h) if h > 0 else 0.0


def top_n_concentration(exposures, n=10) -> float:
    """Share of total exposure held by the n largest names."""
    e = np.sort(np.asarray(exposures, dtype=float))[::-1]
    total = e.sum()
    return float(e[:n].sum() / total) if total > 0 else 0.0


def gini(exposures) -> float:
    """Gini coefficient of the exposure distribution."""
    e = np.sort(np.asarray(exposures, dtype=float))
    n = len(e)
    if n == 0 or e.sum() == 0:
        return 0.0
    cum = np.cumsum(e)
    return float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)


def concentration_by(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Exposure and share by a dimension (sector, geography, rating)."""
    g = df.groupby(dimension)["ead"].sum().sort_values(ascending=False)
    out = g.to_frame("ead")
    out["share"] = out["ead"] / out["ead"].sum()
    return out.reset_index()


def concentration_report(df: pd.DataFrame) -> dict:
    e = df["ead"].values
    return {
        "hhi_name": hhi(e),
        "effective_number_names": effective_number(e),
        "top10_share": top_n_concentration(e, 10),
        "top20_share": top_n_concentration(e, 20),
        "gini": gini(e),
        "hhi_sector": hhi(df.groupby("sector")["ead"].sum().values),
        "hhi_geography": hhi(df.groupby("geography")["ead"].sum().values),
        "by_sector": concentration_by(df, "sector"),
        "by_geography": concentration_by(df, "geography"),
        "by_rating": concentration_by(df, "rating"),
    }
