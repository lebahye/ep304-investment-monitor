#!/usr/bin/env python3
"""Automated integrity checks. Exit code 0 = all pass.
  python checks.py          (or: python main.py check)
Checks: ledger replays cleanly and reconciles with its value history, every trade is
on the watchlist with a positive price, prices/TA files are complete and finite, the TA
checksum matches, and the tracked files contain no secrets or machine-specific paths."""
import json, math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("EP304_DATA_DIR") or os.path.join(HERE, "data")
results = []


def check(name, ok, evidence):
    results.append((name, bool(ok), evidence))


def load(n):
    with open(os.path.join(DATA, n)) as f:
        return json.load(f)


def ta_checksum(d):
    def z(v): return v if isinstance(v, (int, float)) and not isinstance(v, bool) else 0
    cs = 0.0
    for x in d["ta"].values():
        cs += z(x["close"]) + z(x["stop"]) + z(x["atr"]) + z(x["rsiD"]) + z(x["sma200"]) + z((x["vp"] or {}).get("poc")) \
            + z((x["rsSpy"] or {}).get("pct")) + z(x["stage"]) + z(x["mom121"]) + z(x["udr"]) + z(x["bbwPctile"]) + z(x["fromHi"])
    return round(cs, 2)


def main():
    L, PX, TA = load("ledger.json"), load("prices.json"), load("ta.json")
    from portfolio_rules import WATCH
    # 1 ledger replay via the real engine
    p = subprocess.run([sys.executable, os.path.join(HERE, "portfolio.py"), "check"], capture_output=True, text=True,
                       env={**os.environ, "EP304_DATA_DIR": DATA})
    check("Ledger replays (portfolio.py check)", p.returncode == 0, (p.stdout or p.stderr).strip().splitlines()[0] if (p.stdout or p.stderr) else "")
    # 2 ledger ids sequential, tickers valid, prices positive
    ids = [t["id"] for t in L["trades"]]
    bad = [t for t in L["trades"] if t["t"] not in WATCH or t["price"] <= 0 or t["shares"] <= 0]
    check("Ledger append-only ids + valid trades", ids == list(range(1, len(ids) + 1)) and not bad,
          f"{len(ids)} trades, ids 1..{len(ids)}, {len(bad)} invalid")
    # 3 reconcile last history point with a fresh valuation at prices.json
    cash = L["start"]["cash"]; sh = {}
    for t in L["trades"]:
        amt = math.floor(t["shares"] * t["price"] * 100 + 0.5) / 100
        cash += -amt if t["side"] == "BUY" else amt
        sh[t["t"]] = sh.get(t["t"], 0) + (t["shares"] if t["side"] == "BUY" else -t["shares"])
    total = cash + sum(s * PX[t]["price"] for t, s in sh.items() if s > 1e-9)
    last = L["history"][-1] if L["history"] else None
    same_day = last and last["close"] == PX["SPY"]["date"]
    ok = (not same_day) or (abs(last["total"] - total) < 0.02 and abs(last["cash"] - cash) < 0.02)
    check("Ledger reconciles with value history", ok,
          f"recomputed total ${total:,.2f} cash ${cash:,.2f} vs history {last and last['close']}: ${last and last['total']:,} cash ${last and last['cash']:,}"
          + ("" if same_day else " (history not yet for this price date; skipped)"))
    # 4 cash never negative + cash floor (warn-level info)
    check("Cash non-negative", cash >= -0.005, f"cash ${cash:,.2f} = {100 * cash / total:.1f}% of portfolio (Manager plan floor 15%)")
    # 5 prices complete
    missing = [t for t in WATCH | {"SPY"} if t not in PX or "err" in PX[t] or not (PX[t].get("price") or 0) > 0]
    dates = sorted({PX[t]["date"] for t in PX if "date" in PX[t]})
    check("prices.json complete", not missing, f"{len(PX)} tickers, missing/err: {missing or 'none'}, dates: {dates}")
    # 6 TA complete + finite + checksum
    nonfinite = [t for t, x in TA["ta"].items() for k, v in x.items() if isinstance(v, float) and not math.isfinite(v)]
    miss_ta = sorted(WATCH - set(TA["ta"]))
    noverdict = [t for t, x in TA["ta"].items() if not x.get("verdict")]
    check("ta.json complete and finite", not nonfinite and not miss_ta and not noverdict,
          f"{len(TA['ta'])} tickers as of {TA['meta'].get('asOf')}, missing {miss_ta or 'none'}, non-finite {nonfinite or 'none'}")
    cs = ta_checksum(TA); stored = TA["meta"].get("checksum")
    check("TA checksum matches", stored is not None and abs(cs - stored) < 0.01, f"recomputed {cs} vs stored {stored}")
    # 7 secrets / box paths in tracked files
    pats = re.compile(r"(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-|AAAAAAAAAAAAAAAAAAAAA|"
                      r"BEGIN [A-Z ]*PRIVATE KEY|/workspace/|/home/box|[A-Za-z0-9._%+-]+@(?!users\.noreply)[A-Za-z0-9.-]+\.(com|net|org|io))")
    try:
        files = subprocess.run(["git", "ls-files"], cwd=HERE, capture_output=True, text=True, check=True).stdout.split()
    except Exception:
        files = []
    if not files:
        files = [os.path.relpath(os.path.join(r, f), HERE) for r, ds, fs in os.walk(HERE) for f in fs
                 if not any(x in r for x in (".git", ".venv", "__pycache__", ".pythonlibs"))]
    hits = []
    for f in files:
        if f == "checks.py": continue  # contains the patterns themselves
        try:
            for i, line in enumerate(open(os.path.join(HERE, f), errors="ignore"), 1):
                if pats.search(line): hits.append(f"{f}:{i}")
        except (IsADirectoryError, FileNotFoundError):
            pass
    check("No secrets / emails / box paths", not hits, f"{len(files)} files scanned, hits: {hits or 'none'}")

    w = max(len(n) for n, _, _ in results)
    for n, ok, ev in results:
        print(f"{'PASS' if ok else 'FAIL'}  {n:<{w}}  {ev}")
    fails = sum(1 for _, ok, _ in results if not ok)
    print(f"\n{len(results) - fails}/{len(results)} checks passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
