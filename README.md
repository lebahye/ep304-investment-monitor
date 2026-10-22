# EP #304 investment monitor

A watchlist, technical-analysis engine and **$10,000 paper portfolio** built around the investment themes discussed on
*Moonshots with Peter Diamandis* EP #304 (with Chamath Palihapitiya, Oct 2026): AI compute, power and the grid, data centers,
skilled trades, fuel and materials, robotics and space, cash-flow compounders, and bitcoin as a tracked risk.

> **Not financial advice.** Paper trading only; nothing here places real orders. Data comes from free, unofficial sources and can be wrong or late.

## What it does
- **40-name watchlist** in 9 themes with role caps (Core 5%, ETF 12%, Satellite 3%, Speculative 1.5%) – see `portfolio_rules.py`.
- **Daily refresh** (`pull.py` → `ta.py` → `ta_verdict.py` → `portfolio.py point`): last close, 52-week high, 200-day average; then per ticker
  Minervini stage, trend template, daily/weekly/monthly trend, 12-1 momentum, RSI, MACD, relative strength vs SPY and a sector benchmark,
  approximate volume profile (POC / value area), OBV, ATR% and Bollinger-squeeze volatility regimes, golden/death cross,
  and a 3x ATR chandelier trailing stop. Each ticker gets a verdict: *Strong entry, Accumulate, Re-entry setup, Hold, Tighten stop, Exit* with a one-line reason.
- **Paper portfolio** (`data/ledger.json`): append-only trade ledger, replayed and valued at the latest close, compared against the same $10,000 in SPY.
- **Web view** (`web.py`, Flask): portfolio, weights vs caps, TA table, ledger, JSON APIs, and an optional trade form.
- **Checks** (`checks.py`): ledger reconciliation, data integrity, TA checksum, secret scan.

## Files
| File | Purpose |
|---|---|
| `main.py` | Entry point: `web` (default), `summary`, `refresh`, `trade '<line>'`, `check` |
| `web.py` | Flask web view + background scheduler (refresh on start if stale, weekdays 4:30 PM ET) |
| `pull.py` | Latest prices → `data/prices.json` |
| `ta.py` | 5-year daily/weekly bars + indicators → `data/ta.json` (`python ta.py ASOF=2026-06-30` for reproducible reruns) |
| `ta_verdict.py` | Verdict rules → `data/ta.json` (+ a TS paste block used by the original dashboard, git-ignored) |
| `portfolio.py` | Ledger engine: `check`, `add '<line>'`, `point`, `ts` |
| `portfolio_rules.py` | Watchlist, roles, caps, theme targets |
| `checks.py` | Automated integrity checks |
| `refresh.sh` | Same pipeline as `main.py refresh`, for cron |
| `data/` | Sample data as of the Oct 22, 2026 close (prices, TA, ledger with 8 paper trades) |
| `CLAUDE.md` / `AGENTS.md` | Rules for AI agents and humans working on the repo |
| `plan.md`, `checks.md`, `progress.md` | Roadmap, check results with evidence, status log |

## Run locally
```bash
git clone https://github.com/lebahye/ep304-investment-monitor.git
cd ep304-investment-monitor
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python main.py summary      # print portfolio + TA from the sample data
python main.py refresh      # fetch fresh data (~20-60 s), then print the summary
python main.py check        # integrity checks
python main.py              # web view on http://localhost:5000
```
Python 3.9+ (uses `zoneinfo`). The data pipeline is standard-library only; Flask is needed only for the web view.

## Run on Replit
1. Replit → **Create App** → **Import from GitHub** → paste `https://github.com/lebahye/ep304-investment-monitor` → Import.
2. Optional: **Tools → Secrets**, add `ADMIN_TOKEN` (any long password you choose) to enable the trade form and the Refresh button.
3. Press **Run**. It installs Flask, starts the web view on port 5000 (shown in the Webview/preview pane), and refreshes data if it's older than the last close.
4. In the **Shell** tab you can also run `python main.py summary`, `python main.py trade 'paper BUY GEV $500'`, `python main.py check`.

Notes: the built-in scheduler only runs while the app is running. For a daily refresh without keeping it open, use a Replit **Scheduled Deployment**
running `python main.py refresh` at 4:30 PM ET on weekdays. Deployed apps may not keep files written at runtime, so for durable history
keep using the workspace or add persistent storage (see `plan.md`).

| Env var / Secret | Default | Meaning |
|---|---|---|
| `ADMIN_TOKEN` | unset | Enables the web trade form + Refresh button (the form asks for it) |
| `PORT` | 5000 | Web port |
| `AUTO_REFRESH` | 1 | 0 disables refresh-on-start and the 4:30 PM ET scheduler |
| `EP304_DATA_DIR` | `./data` | Where the JSON files live |

## Trade-line format (`portfolio.py add`)
```
paper BUY  GEV  $1000                       # dollar amount, fills at the latest refreshed close
paper BUY  MSFT 0.5 sh                      # share count
paper SELL LLY  ALL                         # whole position
paper BUY  NEE  $300 @ 81.90 on 2026-10-22 -- Re-entry setup (rule 2)
```
`@ price` overrides the fill, `on YYYY-MM-DD` sets the trade date, `-- note` records why. The ticker must be on the watchlist; a buy can't exceed cash and a sell can't exceed shares held.
The ledger is append-only: fix mistakes with an offsetting trade.

## Data sources and caveats
- **Prices and bars:** Yahoo Finance `query1.finance.yahoo.com/v8/finance/chart/{ticker}` – free, **unofficial and undocumented**; it can rate-limit, change, or disappear without notice. End-of-day only (today's partial bar is dropped until 4:15 PM ET). Verify anything important at your broker.
- **Sector benchmarks:** XLU, XLI, XLV, XLE, XLB, XLK, XLRE, QQQ, ITA, BTC-USD from the same source.
- **SPCX** (SpaceX) has under a year of trading history, so its stage and 200-day signals aren't computable yet.
- No fundamentals, earnings dates or news yet (see `plan.md`).

## X (Twitter) monitoring – not included
The original setup also monitored X for each ticker and ~100 industry accounts through a hosted integration that isn't part of this repo.
To add it you'd need your **own X API key** (paid X developer access) stored as a Secret such as `X_BEARER_TOKEN`; it's on the roadmap.

## License
MIT – see `LICENSE`.
