# Methodology note — Strategic / Portfolio Risk + ESG Engine

A one-page note on the choices behind the engine, mapped to the offer's
"Strategic Risk Analyst" mission: deliver strategic portfolio risk analysis and
analytics on the evolution of portfolio dynamics over time, and contribute to
strengthening the ESG risk framework in APAC.

## Scope

Strategic and portfolio risk analysis takes the whole book of exposures and asks
where the risk is concentrated, how its credit quality will drift, and how exposed
it is to ESG and climate risk. The engine computes concentration analytics, a
rating-migration projection, an ESG risk score, and an NGFS climate stress test.

## Data

Portfolio data is confidential, so the engine runs on a deterministic, seeded
portfolio of 200 counterparties calibrated to a diversified APAC corporate bank:
exposure (EAD), sector, geography, credit rating, and E/S/G sub-scores. Sector
carbon intensity and ESG baselines drive the climate and ESG modules; geography
drives physical climate risk.

## Concentration

A portfolio can look diversified on average and still be concentrated in one name,
sector or country. The engine computes the Herfindahl-Hirschman Index (and its
reciprocal, the effective number of names), the top-N concentration share, the
Gini coefficient of the exposure distribution, and the HHI by sector and
geography. These are the standard measures a risk committee monitors against
single-name and sector limits.

## Rating migration

Credit quality drifts over time. A representative through-the-cycle corporate
transition matrix (S&P-style, with an absorbing default state) gives the one-year
probabilities of moving between grades. Applying it to the current
exposure-weighted rating distribution projects the portfolio forward, and matrix
powers give the cumulative default probability over multiple years. This quantifies
the "evolution of portfolio dynamics over time" the mission asks for.

## ESG risk scoring

ESG is treated as a risk lens, not a label. Each counterparty carries E, S and G
sub-scores (0-100); the composite weights them (35/30/35, governance slightly
higher for a bank's view) and maps to risk bands (Leader / Average / Laggard /
High-risk). The engine reports the exposure-weighted portfolio ESG score, the
exposure by band, the share in ESG-sensitive sectors, and the names that
contribute most to ESG risk (low score times large exposure).

## Climate stress (NGFS)

Climate risk enters through two channels, following the NGFS framework supervisors
now expect. **Transition risk**: a carbon-price shock raises costs for
carbon-intensive sectors, lifting their default probability and generating credit
losses; three scenarios (Orderly, Disorderly, Hot House World) vary the carbon
price and sensitivity. **Physical risk**: a geography hazard factor drives a value
haircut. Each scenario's loss is reported in absolute terms and as a share of EAD.

## Limitations and next steps

- ESG and carbon-intensity inputs are modelled at sector level; counterparty-level
  data from an ESG provider would sharpen the scores.
- The transition matrix is through-the-cycle; a point-in-time or conditional matrix
  would make the migration projection cycle-sensitive.
- Climate loss uses a stylised PD-uplift mapping; a full NGFS pathway model with
  sectoral GVA shocks is the production step.

*Stating the model's own assumptions explicitly is itself a second-line posture.*
