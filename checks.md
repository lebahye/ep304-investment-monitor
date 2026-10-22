# Checks

Automated: `python main.py check` (runs `checks.py`, exit code 0 = pass). Re-run before every commit and update this table when evidence changes.
Last run: 2026-10-22 ~5:15 PM ET on a fresh `git clone` into a new Python 3.13 venv (Flask 3.1.3), data as of the Oct 22, 2026 close.

| step | requirement | verdict | evidence |
|---|---|---|---|
| 1 | Ledger replays cleanly | PASS | `portfolio.py check`: cash $6,450.00, realized $0.00, total $10,001.99; 8 trades, ids 1..8 sequential, all tickers on watchlist, prices > 0 |
| 2 | Ledger reconciles with value history | PASS | Recomputed total $10,001.99 / cash $6,450.00 = history point 2026-10-22 ($10,001.99 / $6,450.00). SPY baseline $9,881.90 (-1.18%) |
| 3 | Cash rule | PASS | Cash 64.5% ≥ 15% floor (planned buy-backs held in cash) |
| 4 | prices.json complete | PASS | 42 tickers (40 watchlist + SPY + XLU), no errors, single price date 2026-10-22 |
| 5 | ta.json complete and finite | PASS | 40/40 tickers as of 2026-10-22, every ticker has a verdict, no NaN/inf |
| 6 | TA checksum | PASS | Recomputed 54156.99 = stored `meta.checksum` 54156.99 = `TA_CHECKSUM` on the original dashboard |
| 7 | Verdicts unchanged by repo port | PASS | Verdicts in repo `ta.json` identical to the live pipeline's for all 40 tickers (3 Strong entry, 3 Re-entry, 6 Hold, 16 Tighten stop, 12 Exit) |
| 8 | `main.py summary` runs | PASS | Prints portfolio (8 positions, $10,001.99, +0.02%) and verdict groups from a clean clone |
| 9 | `main.py refresh` runs | PASS | Full pipeline (pull → ta → verdict → point) fetched live Yahoo data in ~21 s, then 8/8 checks still passed |
| 10 | Web view loads | PASS | `GET /` 200 (~21 KB), `/api/portfolio` total 10001.99 with 8 rows, `/healthz` ok, stale=false |
| 11 | Trade form gated + saves | PASS | No `ADMIN_TOKEN`: form hidden, POST rejected. Wrong token: "Trade rejected". Right token: trade #9 appended and value point refreshed, 8/8 checks pass. Off-watchlist ticker rejected ("ZZZZ is not on the watchlist") |
| 12 | No secrets / personal info | PASS | `checks.py` regex scan of all 23 tracked files (GitHub/OpenAI/AWS/Slack/X token patterns, private keys, emails, absolute machine paths): 0 hits. Commits use the GitHub noreply address |
