"""Strategic / Portfolio Risk + ESG dashboard.

Five views mirroring a Strategic Risk Analyst's toolkit and the offer's mission:
  1. Portfolio      - the book of exposures by sector, geography, rating
  2. Concentration  - HHI, top-N, Gini, concentration by dimension
  3. Migration      - rating transition matrix, projected quality, cumulative PD
  4. ESG            - E/S/G scoring, bands, sensitive-sector exposure
  5. Climate stress - NGFS transition & physical loss scenarios

Runs with no data files and no token: the portfolio is built deterministically.
"""
import os
import sys

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import portfolio, concentration, migration, esg, climate

st.set_page_config(page_title="Strategic & ESG Risk Engine", layout="wide")
NAVY = "#0d2538"

st.title("Strategic / Portfolio Risk & ESG Engine")
st.caption(
    "Concentration (HHI, Gini) · rating migration · ESG scoring · NGFS climate stress. "
    "Portfolio analytics for senior-management risk reporting, no token required."
)


@st.cache_data(show_spinner=False)
def get_portfolio(n, seed):
    return portfolio.build_portfolio(n=n, seed=seed)


with st.sidebar:
    st.header("Portfolio")
    n = st.slider("Counterparties", 100, 400, 200, step=50)
    seed = st.number_input("Seed", value=42, step=1)
    df = get_portfolio(n, int(seed))
    s = portfolio.portfolio_summary(df)
    st.metric("Total EAD", f"{s['total_ead']:,.0f}M")
    st.caption(f"{s['n_counterparties']} names · {s['n_sectors']} sectors · {s['n_geographies']} geographies")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Portfolio", "Concentration", "Migration", "ESG", "Climate stress"]
)

# ---- 1. Portfolio ----------------------------------------------------------
with tab1:
    st.subheader("Exposures")
    st.dataframe(df[["counterparty", "sector", "geography", "rating", "ead"]],
                 hide_index=True, use_container_width=True, height=300)
    c1, c2 = st.columns(2)
    c1.bar_chart(df.groupby("sector")["ead"].sum().sort_values(ascending=False))
    c2.bar_chart(df.groupby("geography")["ead"].sum().sort_values(ascending=False))

# ---- 2. Concentration ------------------------------------------------------
with tab2:
    st.subheader("Concentration analytics")
    cr = concentration.concentration_report(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("HHI (name)", f"{cr['hhi_name']:.4f}")
    c2.metric("Effective names", f"{cr['effective_number_names']:.0f}")
    c3.metric("Top-10 share", f"{cr['top10_share']:.1%}")
    c4.metric("Gini", f"{cr['gini']:.3f}")
    st.markdown("**By sector**")
    bs = cr["by_sector"].copy(); bs["share"] = (bs["share"] * 100).round(1)
    st.dataframe(bs, hide_index=True, use_container_width=True)
    st.bar_chart(cr["by_sector"].set_index("sector")["ead"])
    c1, c2 = st.columns(2)
    c1.metric("HHI sector", f"{cr['hhi_sector']:.3f}")
    c2.metric("HHI geography", f"{cr['hhi_geography']:.3f}")

# ---- 3. Migration ----------------------------------------------------------
with tab3:
    st.subheader("Rating migration")
    mr = migration.migration_report(df)
    c1, c2 = st.columns(2)
    c1.metric("Portfolio 1Y PD", f"{mr['portfolio_pd_1y']:.2%}")
    c2.metric("Expected EAD default (1Y)", f"{mr['expected_ead_default_1y']:,.0f}M")
    proj = mr["projected_1y"]
    proj_disp = proj[proj["rating"] != "D"].set_index("rating")[["current", "projected"]]
    st.bar_chart(proj_disp)
    st.markdown("**Cumulative default probability**")
    st.line_chart(mr["multi_year_pd"].set_index("year")["cumulative_default_prob"])
    with st.expander("1-year transition matrix"):
        st.dataframe((mr["transition_matrix"] * 100).round(1), use_container_width=True)

# ---- 4. ESG ----------------------------------------------------------------
with tab4:
    st.subheader("ESG risk scoring")
    er = esg.esg_report(df)
    c1, c2, c3 = st.columns(3)
    c1.metric("Weighted ESG score", f"{er['weighted_esg_score']:.1f}", er["weighted_band"])
    c2.metric("Sensitive-sector EAD", f"{er['sensitive_sector_ead']:,.0f}M")
    c3.metric("Sensitive-sector share", f"{er['sensitive_sector_share']:.1%}")
    st.bar_chart(er["by_band"].set_index("band")["ead"])
    st.markdown("**Top ESG risk contributors** (low score × large exposure)")
    st.dataframe(er["worst_contributors"], hide_index=True, use_container_width=True)

# ---- 5. Climate stress -----------------------------------------------------
with tab5:
    st.subheader("Climate stress — NGFS scenarios")
    clr = climate.climate_report(df)
    sc = clr["scenarios"].copy()
    for col in ["transition_loss", "physical_loss", "total_climate_loss"]:
        sc[col] = sc[col].round(1)
    sc["loss_pct_ead"] = sc["loss_pct_ead"].round(2)
    st.dataframe(sc, hide_index=True, use_container_width=True)
    st.bar_chart(clr["scenarios"].set_index("scenario")[["transition_loss", "physical_loss"]])
    st.metric("Worst scenario", clr["worst_scenario"], f"{clr['worst_loss']:,.0f}M loss")
    st.markdown("**Transition loss by sector (disorderly scenario)**")
    st.bar_chart(clr["transition_loss_by_sector"].set_index("sector")["transition_loss"])
    st.caption("Transition: carbon-price shock on carbon-intensive sectors. "
               "Physical: geography hazard. NGFS Orderly / Disorderly / Hot House World.")
