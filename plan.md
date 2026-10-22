# Roadmap

Horizon: 2030–2035 retirement growth, themes from Moonshots EP #304. Paper portfolio first; real money stays at the user's broker.

| # | Item | Why | Status |
|---|------|-----|--------|
| 1 | **Live intraday prices** | Today everything runs on daily closes from an unofficial Yahoo endpoint that can break without notice. Add an official/keyed quote API (e.g. a broker or market-data provider) behind an env var, with Yahoo as fallback. | Open |
| 2 | **Trade form that saves** | Record paper trades from the browser instead of chat. | **Done (v1)**: web form gated by `ADMIN_TOKEN`; persists to `data/ledger.json`. Next: undo-by-offset button, confirmation preview. |
| 3 | **Valuation and earnings data** | Rules only see the chart. Add P/E, EV/sales, revenue growth, FCF yield and next earnings date so buys/trims can consider valuation and avoid entries right before earnings. | Open |
| 4 | **Backtest the rules against SPY** | Replay the Manager plan on 2021–2026 bars (`ta.py ASOF=` already supports truncation) to see whether it beats SPY after drawdowns. | Open |
| 5 | **Compare real Schwab holdings to the caps** | Import a Schwab positions CSV export (no credentials in the repo) and flag over/under-weights vs the role caps and theme targets. | Open |
| 6 | **X monitoring with the user's own API key** | The original monitor used a hosted X integration that isn't in this repo. Re-add with `X_BEARER_TOKEN` (paid X developer access) for per-ticker counts and key accounts. | Open |
| 7 | Bitcoin-to-zero risk triggers in code | Encode the crypto exit/reduce triggers (spot-ETF holdings, price levels) so rule 6 is automatic. | Open |
| 8 | Persistent storage on Replit deployments | Deployment file systems can reset; move `data/` to Replit DB/Object Storage or commit snapshots. | Open |
