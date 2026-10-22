#!/usr/bin/env python3
"""EP #304 investment monitor: entry point.

  python main.py              -> start the web view (default; what Replit's Run button does)
  python main.py summary      -> print the portfolio + TA summary from the saved JSON
  python main.py refresh      -> run the refresh pipeline, then print the summary
  python main.py trade 'paper BUY GEV $500'   -> record a paper trade, then print the summary
  python main.py check        -> run checks.py (ledger reconciliation, data integrity, secret scan)

Environment variables (all optional):
  EP304_DATA_DIR     where the JSON files live (default ./data)
  PORT               web port (default 5000)
  ADMIN_TOKEN        enables the web trade form and the Refresh button; the form asks for it
  AUTO_REFRESH       "1" (default) = refresh on start if data is stale and daily at 4:30 PM ET on weekdays; "0" = off
"""
import json, os, subprocess, sys, datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("EP304_DATA_DIR") or os.path.join(HERE, "data")
ET = ZoneInfo("America/New_York")
PIPELINE = ["pull.py", "ta.py", "ta_verdict.py", ["portfolio.py", "point"]]


def load(name, default=None):
    try:
        with open(os.path.join(DATA_DIR, name)) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def run_script(args, quiet=True):
    args = args if isinstance(args, list) else [args]
    p = subprocess.run([sys.executable, os.path.join(HERE, args[0])] + args[1:], cwd=HERE,
                       capture_output=True, text=True, env={**os.environ, "EP304_DATA_DIR": DATA_DIR})
    if not quiet or p.returncode:
        sys.stdout.write(p.stdout)
    if p.returncode:
        sys.stderr.write(p.stderr)
        raise RuntimeError(f"{' '.join(args)} failed: {(p.stderr or p.stdout).strip().splitlines()[-1:]}")
    return p.stdout


def refresh():
    for step in PIPELINE:
        name = step if isinstance(step, str) else " ".join(step)
        print(f"[refresh] {name} ...", flush=True)
        run_script(step)
    print("[refresh] done", flush=True)


def record_trade(line):
    """Append one validated trade (portfolio.py add), then refresh today's value point so checks reconcile."""
    out = run_script(["portfolio.py", "add", line]).strip().splitlines()[0]
    run_script(["portfolio.py", "point"])
    return out


def portfolio_state():
    """Replay the ledger (same rules as portfolio.py) and value it at the latest prices."""
    L = load("ledger.json", {"start": {"cash": 10000, "spyPrice": None}, "trades": [], "history": []})
    PX = load("prices.json", {})
    TA = (load("ta.json", {}) or {}).get("ta", {})
    cash = L["start"]["cash"]; pos = {}; realized = 0.0
    for tr in L["trades"]:
        p = pos.setdefault(tr["t"], {"shares": 0.0, "cost": 0.0})
        amt = round(tr["shares"] * tr["price"], 2)
        if tr["side"] == "BUY":
            cash -= amt; p["shares"] += tr["shares"]; p["cost"] += amt
        else:
            avg = p["cost"] / p["shares"]; realized += amt - avg * tr["shares"]; cash += amt
            p["cost"] -= avg * tr["shares"]; p["shares"] -= tr["shares"]
            if p["shares"] < 1e-9: p["shares"] = p["cost"] = 0.0
    rows = []
    for t, p in pos.items():
        if p["shares"] <= 0: continue
        last = (PX.get(t) or {}).get("price") or (TA.get(t) or {}).get("close")
        val = p["shares"] * last
        ta = TA.get(t, {})
        rows.append(dict(t=t, shares=p["shares"], avg=p["cost"] / p["shares"], last=last, value=val,
                         gain=val - p["cost"], gainPct=(val / p["cost"] - 1) * 100,
                         stop=ta.get("stop"), verdict=ta.get("verdict")))
    total = cash + sum(r["value"] for r in rows)
    start = L["start"]["cash"]
    spy_now = (PX.get("SPY") or {}).get("price")
    spy_val = start * spy_now / L["start"]["spyPrice"] if spy_now and L["start"].get("spyPrice") else None
    return dict(start=L["start"], cash=cash, realized=realized, total=total, gain=total - start,
                gainPct=(total / start - 1) * 100, spy=spy_val, rows=sorted(rows, key=lambda r: -r["value"]),
                trades=L["trades"], history=L["history"], asOf=(PX.get("SPY") or {}).get("date"))


def summary():
    s = portfolio_state()
    ta = load("ta.json", {}) or {}
    print(f"\n=== Paper portfolio (prices as of {s['asOf']}) ===")
    print(f"Total ${s['total']:,.2f}  ({s['gain']:+,.2f} / {s['gainPct']:+.2f}%)   cash ${s['cash']:,.2f}   realized ${s['realized']:,.2f}")
    if s["spy"]:
        print(f"Same ${s['start']['cash']:,.0f} in SPY: ${s['spy']:,.2f} ({(s['spy'] / s['start']['cash'] - 1) * 100:+.2f}%)")
    for r in s["rows"]:
        print(f"  {r['t']:5} {r['shares']:10.4f} sh  avg {r['avg']:9.2f}  last {r['last']:9.2f}  "
              f"value {r['value']:9.2f}  {r['gainPct']:+6.2f}%  stop {r['stop']}  [{r['verdict']}]")
    meta = ta.get("meta", {})
    print(f"\n=== TA verdicts (as of {meta.get('asOf')}) ===")
    groups = {}
    for t, x in ta.get("ta", {}).items():
        groups.setdefault(x.get("verdict", "?"), []).append(t)
    order = ["Strong entry", "Accumulate", "Re-entry setup", "Hold", "Tighten stop", "Exit"]
    for v in order + [k for k in groups if k not in order]:
        if v in groups:
            print(f"  {v:15} {' '.join(groups[v])}")
    print()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "web"
    if cmd == "refresh":
        refresh(); summary()
    elif cmd == "summary":
        summary()
    elif cmd == "trade":
        print(record_trade(sys.argv[2])); summary()
    elif cmd in ("check", "--check"):
        sys.exit(subprocess.run([sys.executable, os.path.join(HERE, "checks.py")]).returncode)
    elif cmd == "web":
        from web import serve
        serve()
    else:
        print(__doc__); sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr); sys.exit(1)
