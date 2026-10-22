# Agent rules for this repo (CLAUDE.md, mirrored as AGENTS.md)

Read this before changing anything. It applies to every AI agent (Replit Agent, Claude, Cursor, Codex…) and to humans.
This is a **paper-trading** research tool inspired by themes from Moonshots EP #304. It never places real orders. Not financial advice.

## 1. The ledger is sacred
- `data/ledger.json` is **append-only**. Never edit, reorder, or delete a past trade, and never rewrite `start`.
- Trades are recorded **only** through `python portfolio.py add '<line>'` (or `python main.py trade '<line>'` / the web form, which call it). Never hand-edit trades into the JSON.
- A mistaken trade is fixed with an offsetting trade plus a `-- correction of #N` note, not by deleting.
- `portfolio.py point` may replace the value-history point for the current price date; earlier points are history and stay.

## 2. Never invent prices
- Every price must come from a fetched data source (`pull.py`/`ta.py`, currently the unofficial Yahoo chart endpoint) or an explicit, dated quote the user supplied (`@ 123.45` with `pxDate` recorded).
- If a fetch fails, report the failure and leave the old data in place. Do not fill gaps, interpolate, or "estimate" a close.
- Do not fabricate fundamentals, news, or X posts either. Unknown is a valid answer.

## 3. Trading and cap rules (Manager plan)
Checked at each after-close refresh; fills use that day's close.
1. **Stop or Exit**: sell the whole position on a close below its 3x ATR trailing stop (highest close of 22 days minus 3x ATR) or when the TA verdict turns *Exit*. Sell half when the verdict turns *Tighten stop* while still above the stop.
2. **Add**: buy/add on *Strong entry*, *Accumulate* or *Re-entry setup* only if the close is above the trailing stop and the name isn't on Watch. Size = the smaller of the 1%-portfolio-risk size and the role cap.
3. **Hold starter**: a *Hold* name gets a half-cap starter only if the close is above its stop and the weekly trend isn't Down.
4. **Caps** (% of total portfolio): Core stock 5% · ETF 12% · Satellite 3% · Speculative 1.5% · RIOT + IBIT 3% combined. Trim back to the cap when a position is more than 1 point over. Source of truth: `portfolio_rules.py`.
5. **Cash floor**: keep at least 15% cash. Fill the most underweight theme first (theme targets in `portfolio_rules.py`).
6. **Crypto**: a bitcoin exit/reduce trigger overrides every buy rule. RIOT stays out until its Corsicana LOI becomes a signed lease.

Every trade note states which rule fired and the evidence (verdict, stop, cap).

## 4. How to change code
- Keep diffs **small and auditable**: one concern per commit, explain *why* in the message.
- Don't add dependencies without a reason; the pipeline is stdlib-only, the web view needs only Flask.
- Don't change indicator math or verdict rules silently. If you do, say so in the commit, update `checks.md`, and note it in `progress.md`.
- Keep the watchlist lists in `pull.py`, `ta.py`, `portfolio.py` and `portfolio_rules.py` in sync.
- No secrets in the repo. Keys go in environment variables / Replit Secrets (`ADMIN_TOKEN`, future `X_BEARER_TOKEN`).

## 5. Run checks before committing
```
python main.py check      # same as python checks.py; must print "8/8 checks passed"
```
Then update the evidence column in `checks.md` if results changed.

## 6. Record lessons learned
When something breaks or surprises you (a data-source change, a rule edge case, a bad fill), add a dated line below and, if it changes behavior, to `progress.md`.

### Lessons learned
- 2026-10-22: Yahoo returns a partial bar for today before the close; `ta.py` drops it until 4:15 PM ET so verdicts only use completed sessions.
- 2026-10-22: Recording a trade must be followed by `portfolio.py point`, or the value-history cash won't reconcile (`main.py trade` and the web form do this).
- 2026-10-22: On a broad down day most names fail the entry rules; holding cash as planned buy-backs is the intended outcome, not a bug.
