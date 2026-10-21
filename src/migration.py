"""Rating migration analysis.

A portfolio's credit quality is not static: counterparties get upgraded,
downgraded or default over time. A rating migration (transition) matrix gives the
one-year probabilities of moving between rating grades. Applying it to the current
rating distribution projects the portfolio's quality forward and quantifies the
expected downgrade and default pressure, which is exactly the "evolution of the
portfolio dynamics over time" the strategic-risk mission describes.

The transition matrix here is a representative through-the-cycle corporate matrix
(S&P-style), rows summing to one, with an absorbing default state.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .portfolio import RATINGS

__all__ = ["STATES", "transition_matrix", "project_distribution", "multi_year", "migration_report"]

STATES = RATINGS + ["D"]  # add absorbing default state

# Representative 1-year transition matrix (%). Rows: from, Cols: to (AAA..CCC, D).
_TM = np.array([
    # AAA     AA      A      BBB     BB      B      CCC     D
    [90.0,   9.0,   0.6,   0.3,   0.1,   0.0,   0.0,   0.0],   # AAA
    [ 0.6,  90.0,   8.0,   1.0,   0.3,   0.1,   0.0,   0.0],   # AA
    [ 0.1,   2.3,  91.0,   5.5,   0.7,   0.2,   0.1,   0.1],   # A
    [ 0.0,   0.3,   5.0,  88.5,   4.5,   1.0,   0.4,   0.3],   # BBB
    [ 0.0,   0.1,   0.5,   6.5,  83.0,   7.5,   1.4,   1.0],   # BB
    [ 0.0,   0.1,   0.2,   0.5,   6.5,  82.5,   5.5,   4.7],   # B
    [ 0.0,   0.0,   0.1,   0.3,   1.5,  12.0,  60.0,  26.1],   # CCC
]) / 100.0


def transition_matrix() -> pd.DataFrame:
    """The 1-year transition matrix as a DataFrame (from-rows x to-cols)."""
    # append the absorbing default row
    full = np.vstack([_TM, np.eye(len(STATES))[-1]])
    return pd.DataFrame(full, index=STATES, columns=STATES)


def _current_vector(df: pd.DataFrame) -> np.ndarray:
    """Exposure-weighted current rating distribution (over RATINGS, no D)."""
    w = df.groupby("rating")["ead"].sum().reindex(RATINGS, fill_value=0.0)
    total = w.sum()
    v = (w / total).values if total > 0 else w.values
    return np.append(v, 0.0)  # no exposure currently in default


def project_distribution(df: pd.DataFrame, years=1) -> pd.DataFrame:
    """Project the rating distribution forward `years` using the matrix power."""
    tm = transition_matrix().values
    v = _current_vector(df)
    mat = np.linalg.matrix_power(tm, years)
    projected = v @ mat
    return pd.DataFrame({
        "rating": STATES,
        "current": np.append(v[:-1], 0.0),
        "projected": projected,
    })


def multi_year(df: pd.DataFrame, horizon=5) -> pd.DataFrame:
    """Cumulative default probability of the portfolio over 1..horizon years."""
    tm = transition_matrix().values
    v = _current_vector(df)
    rows = []
    for y in range(1, horizon + 1):
        proj = v @ np.linalg.matrix_power(tm, y)
        rows.append({"year": y, "cumulative_default_prob": float(proj[-1])})
    return pd.DataFrame(rows)


def migration_report(df: pd.DataFrame) -> dict:
    proj1 = project_distribution(df, 1)
    # downgrade pressure: expected 1y default probability of the portfolio
    pd_1y = float(proj1.loc[proj1["rating"] == "D", "projected"].iloc[0])
    # expected EAD defaulting in 1y
    ead_default_1y = pd_1y * df["ead"].sum()
    return {
        "projected_1y": proj1,
        "portfolio_pd_1y": pd_1y,
        "expected_ead_default_1y": ead_default_1y,
        "multi_year_pd": multi_year(df, 5),
        "transition_matrix": transition_matrix(),
    }
