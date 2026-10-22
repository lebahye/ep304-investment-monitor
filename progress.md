# Progress

## Done (2026-10-22)
- Watchlist of 40 names in 9 themes from Moonshots EP #304, with role caps and theme targets (`portfolio_rules.py`).
- Daily pipeline: prices, 5-year TA (stage, trend template, multi-timeframe trend, momentum, RSI/MACD, RS vs SPY and sector, volume profile, OBV, ATR/Bollinger/realized-vol regimes, 3x ATR trailing stop) and verdict rules.
- $10,000 paper portfolio started Oct 22, 2026: COWZ, MSFT, AMZN, LLY, WMB, EQT at 3:30 PM ET quotes; NEE and a ROK starter at the close. $10,001.99 (+0.02%) vs SPY $9,881.90 (-1.18%); 64.5% cash held for planned buy-backs.
- Ported from the original box setup to this repo: env/relative data paths, `main.py` entry point, Flask web view with a saving trade form (`ADMIN_TOKEN`), automated `checks.py`, Replit config, agent rules (`CLAUDE.md`/`AGENTS.md`).

## Open
- See `plan.md`: live intraday prices, valuation and earnings data, backtest vs SPY, Schwab holdings vs caps, X monitoring with the user's own key, coded bitcoin-risk triggers, persistent storage on Replit deployments.
- Manager-plan rules 1–6 are applied by hand/agent at each close; they are not yet automated in code.
- The original dashboard and this repo hold separate copies of the ledger; decide which one is the source of truth going forward.

## Next action
Import into Replit, set `ADMIN_TOKEN`, press Run, and confirm the page shows $10,001.99 with 8 positions. Then pick the first `plan.md` item (suggested: automate Manager-plan rules + backtest, item 4).
