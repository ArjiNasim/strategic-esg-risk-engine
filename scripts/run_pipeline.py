"""End-to-end strategic / portfolio risk + ESG pipeline: portfolio ->
concentration -> migration -> ESG -> climate stress. Prints a full report and
saves the portfolio to data/portfolio.parquet.

Run:  python scripts/run_pipeline.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import portfolio, concentration, migration, esg, climate


def main():
    print(f"\n{'='*66}\nSTRATEGIC / PORTFOLIO RISK + ESG REPORT\n{'='*66}")
    df = portfolio.build_portfolio(n=200, seed=42)
    s = portfolio.portfolio_summary(df)
    print(f"Counterparties: {s['n_counterparties']}   Total EAD: {s['total_ead']:,.0f}M")
    print(f"Sectors: {s['n_sectors']}   Geographies: {s['n_geographies']}   "
          f"Largest name: {s['largest_exposure']:,.0f}M\n")

    print("CONCENTRATION:")
    cr = concentration.concentration_report(df)
    print(f"  HHI (name)           : {cr['hhi_name']:.4f}  "
          f"(effective names {cr['effective_number_names']:.0f})")
    print(f"  Top-10 share         : {cr['top10_share']:.1%}")
    print(f"  Gini                 : {cr['gini']:.3f}")
    print(f"  HHI sector / geo     : {cr['hhi_sector']:.3f} / {cr['hhi_geography']:.3f}")
    print("  Top sectors:")
    print(cr["by_sector"].head(4).to_string(index=False))

    print("\nMIGRATION:")
    mr = migration.migration_report(df)
    print(f"  Portfolio 1y PD      : {mr['portfolio_pd_1y']:.2%}")
    print(f"  Expected EAD default : {mr['expected_ead_default_1y']:,.0f}M (1y)")
    print("  Cumulative default prob:")
    print(mr["multi_year_pd"].to_string(index=False))

    print("\nESG:")
    er = esg.esg_report(df)
    print(f"  Weighted ESG score   : {er['weighted_esg_score']:.1f} ({er['weighted_band']})")
    print(f"  Sensitive-sector EAD : {er['sensitive_sector_ead']:,.0f}M "
          f"({er['sensitive_sector_share']:.1%})")
    print("  Exposure by ESG band:")
    print(er["by_band"].assign(ead=er["by_band"]["ead"].round(0),
                               share=(er["by_band"]["share"]*100).round(1)).to_string(index=False))

    print("\nCLIMATE STRESS (NGFS scenarios):")
    clr = climate.climate_report(df)
    print(clr["scenarios"][["scenario", "transition_loss", "physical_loss",
                            "total_climate_loss", "loss_pct_ead"]].round(1).to_string(index=False))
    print(f"  Worst scenario       : {clr['worst_scenario']} ({clr['worst_loss']:,.0f}M)")

    os.makedirs("data", exist_ok=True)
    df.to_parquet("data/portfolio.parquet")
    print(f"\nSaved data/portfolio.parquet\n{'='*66}")


if __name__ == "__main__":
    main()
