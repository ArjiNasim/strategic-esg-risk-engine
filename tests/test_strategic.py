"""Unit tests for the strategic / portfolio risk + ESG engine."""
import numpy as np
import pandas as pd
import pytest

from src import portfolio, concentration, migration, esg, climate


@pytest.fixture
def pf():
    return portfolio.build_portfolio(n=200, seed=42)


# ---- portfolio -------------------------------------------------------------
def test_portfolio_deterministic():
    a = portfolio.build_portfolio(seed=42)
    b = portfolio.build_portfolio(seed=42)
    assert a["ead"].sum() == pytest.approx(b["ead"].sum())


def test_portfolio_fields(pf):
    for col in ["sector", "geography", "rating", "ead", "env_score", "soc_score", "gov_score"]:
        assert col in pf.columns
    assert set(pf["sector"]).issubset(set(portfolio.SECTORS))
    assert set(pf["rating"]).issubset(set(portfolio.RATINGS))


# ---- concentration ---------------------------------------------------------
def test_hhi_bounds(pf):
    h = concentration.hhi(pf["ead"])
    assert 0 < h <= 1


def test_effective_number(pf):
    n = concentration.effective_number(pf["ead"])
    # effective number cannot exceed the actual number of names
    assert 1 <= n <= len(pf)


def test_hhi_single_name_is_one():
    assert concentration.hhi([100]) == pytest.approx(1.0)


def test_top_n_monotonic(pf):
    assert concentration.top_n_concentration(pf["ead"], 20) >= concentration.top_n_concentration(pf["ead"], 10)


def test_gini_bounds(pf):
    g = concentration.gini(pf["ead"])
    assert 0 <= g <= 1


def test_concentration_shares_sum(pf):
    by = concentration.concentration_by(pf, "sector")
    assert by["share"].sum() == pytest.approx(1.0)


# ---- migration -------------------------------------------------------------
def test_transition_matrix_rows_sum_to_one():
    tm = migration.transition_matrix()
    assert np.allclose(tm.sum(axis=1), 1.0)


def test_default_is_absorbing():
    tm = migration.transition_matrix()
    assert tm.loc["D", "D"] == pytest.approx(1.0)


def test_projection_sums_to_one(pf):
    proj = migration.project_distribution(pf, 1)
    assert proj["projected"].sum() == pytest.approx(1.0, abs=1e-9)


def test_cumulative_default_increases(pf):
    my = migration.multi_year(pf, 5)
    assert my["cumulative_default_prob"].is_monotonic_increasing


def test_portfolio_pd_positive(pf):
    rep = migration.migration_report(pf)
    assert 0 < rep["portfolio_pd_1y"] < 0.5
    assert rep["expected_ead_default_1y"] > 0


# ---- ESG -------------------------------------------------------------------
def test_composite_score_range(pf):
    s = esg.composite_score(pf["env_score"], pf["soc_score"], pf["gov_score"])
    assert (s >= 0).all() and (s <= 100).all()


def test_esg_weights_sum_to_one():
    assert sum(esg.ESG_WEIGHTS.values()) == pytest.approx(1.0)


def test_esg_report(pf):
    rep = esg.esg_report(pf)
    assert 0 <= rep["weighted_esg_score"] <= 100
    assert 0 <= rep["sensitive_sector_share"] <= 1
    assert rep["by_band"]["share"].sum() == pytest.approx(1.0, abs=1e-6)


# ---- climate ---------------------------------------------------------------
def test_transition_loss_rises_with_carbon_price(pf):
    low = climate.transition_loss(pf, carbon_price=50, pd_sensitivity=1.0)
    high = climate.transition_loss(pf, carbon_price=250, pd_sensitivity=1.0)
    assert high > low > 0


def test_climate_report_scenarios(pf):
    rep = climate.climate_report(pf)
    assert len(rep["scenarios"]) == 3
    assert (rep["scenarios"]["total_climate_loss"] > 0).all()
    assert rep["worst_loss"] > 0


def test_carbon_sectors_dominate_transition_loss(pf):
    rep = climate.climate_report(pf)
    top_sector = rep["transition_loss_by_sector"].iloc[0]["sector"]
    # the top transition-loss sector should be a carbon-intensive one
    assert portfolio.SECTORS[top_sector]["sensitive"] or portfolio.SECTORS[top_sector]["carbon"] >= 180
