#!/usr/bin/env python3
"""Paper portfolio engine (mirror of the Page's LEDGER block).
ledger.json = {"start": {...}, "trades": [...], "history": [...]}
  python3 portfolio.py check                      -> replay + validate ledger, print positions/value
  python3 portfolio.py add 'paper BUY GEV $1000 on 2026-10-22 -- note'   -> validate, append trade
  python3 portfolio.py point                      -> append/replace today's value point from prices.json
  python3 portfolio.py ts                         -> print the LEDGER/VALUE_HISTORY TS block for the Page
Fills default to the latest refreshed close in prices.json (the Page's PX block)."""
import os
DATA_DIR = os.environ.get("EP304_DATA_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True); os.chdir(DATA_DIR)  # all JSON files are read/written here
import json, re, sys, datetime
from zoneinfo import ZoneInfo
TODAY = datetime.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
WATCH = set("GRID CEG GEV ETN VST NEE RUN PWR EME FIX SMH NVDA TSM MSFT GOOGL AMZN MU AVGO VRT EQIX DLR RIOT IREN CIFR CRWV CCJ URA FCX EQT WMB OKLO COWZ SPCX TSLA ROK BOTZ SYM LLY CRWD IBIT".split())
L = json.load(open("ledger.json")); PX = json.load(open("prices.json"))
EPS = 1e-9
import math
def round2(x): return math.floor(x * 100 + 0.5) / 100  # same as Math.round(x*100)/100 on the Page

def replay(trades):
    cash = L["start"]["cash"]; pos = {}; realized = 0.0
    for i, tr in enumerate(trades, 1):
        t, side, sh, px = tr["t"], tr["side"], tr["shares"], tr["price"]
        if t not in WATCH: raise SystemExit(f"trade {i}: {t} is not on the watchlist")
        if sh <= 0 or px <= 0: raise SystemExit(f"trade {i}: shares and price must be positive")
        p = pos.setdefault(t, {"shares": 0.0, "cost": 0.0})
        if side == "BUY":
            amt = round2(sh * px)
            if amt > cash + 0.005: raise SystemExit(f"trade {i}: needs ${amt:,.2f}, only ${cash:,.2f} cash")
            cash -= amt; p["shares"] += sh; p["cost"] += amt
        elif side == "SELL":
            if sh > p["shares"] + EPS: raise SystemExit(f"trade {i}: selling {sh} {t}, only {p['shares']} held")
            avg = p["cost"] / p["shares"]; amt = round2(sh * px)
            realized += amt - avg * sh; cash += amt
            p["cost"] -= avg * sh; p["shares"] -= sh
            if p["shares"] < EPS: p["shares"] = 0.0; p["cost"] = 0.0
        else: raise SystemExit(f"trade {i}: side must be BUY or SELL")
    return cash, pos, realized

def value(cash, pos):
    return cash + sum(p["shares"] * PX[t]["price"] for t, p in pos.items() if p["shares"] > 0)

LINE = re.compile(r"^\s*paper\s+(BUY|SELL)\s+([A-Z]{1,5})\s+(?:\$([\d,]+(?:\.\d+)?)|([\d.]+)\s*sh|(ALL))(?:\s+@\s*\$?([\d.]+))?(?:\s+on\s+(\d{4}-\d{2}-\d{2}))?(?:\s+--\s*(.*))?\s*$", re.I)
def parse(line, cash, pos):
    m = LINE.match(line)
    if not m: raise SystemExit("could not parse trade line")
    side, t, dollars, shares, allf, price, date, note = m.groups()
    side = side.upper(); t = t.upper()
    if t not in WATCH: raise SystemExit(f"{t} is not on the watchlist")
    px = float(price) if price else PX[t]["price"]
    pxdate = PX[t]["date"] if (not price or abs(float(price) - PX[t]["price"]) < 0.005) else "given"
    date = date or TODAY
    if allf: sh = pos.get(t, {"shares": 0})["shares"]
    elif dollars: sh = float(dollars.replace(",", "")) / px
    else: sh = float(shares)
    sh = math.floor(sh * 1e6 + 0.5) / 1e6
    return dict(id=len(L["trades"]) + 1, date=date, t=t, side=side, shares=sh, price=math.floor(px * 100 + 0.5) / 100, pxDate=pxdate, note=(note or "").strip())

cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
cash, pos, realized = replay(L["trades"])
if cmd == "add":
    tr = parse(sys.argv[2], cash, pos)
    replay(L["trades"] + [tr])  # validates
    L["trades"].append(tr); json.dump(L, open("ledger.json", "w"), indent=1)
    print("added", tr); cash, pos, realized = replay(L["trades"])
if cmd == "point":
    d = PX["SPY"]["date"]
    pt = dict(close=d, total=round(value(cash, pos), 2), spy=round(L["start"]["cash"] * PX["SPY"]["price"] / L["start"]["spyPrice"], 2), cash=round(cash, 2))
    L["history"] = [h for h in L["history"] if h["close"] != d] + [pt]
    L["history"].sort(key=lambda h: h["close"]); json.dump(L, open("ledger.json", "w"), indent=1); print("point", pt)
if cmd == "ts":
    print("const PORTFOLIO_START = " + json.dumps(L["start"]) + ";")
    print("const LEDGER: Trade[] = [" + "".join("\n  " + json.dumps(t) + "," for t in L["trades"]) + ("\n" if L["trades"] else "") + "];")
    print("const VALUE_HISTORY: ValuePoint[] = [" + "".join("\n  " + json.dumps(h) + "," for h in L["history"]) + "\n];")
_o = sys.stderr if cmd == "ts" else sys.stdout  # keep ledger_block.ts pure TS
print(f"cash ${cash:,.2f}  realized ${realized:,.2f}  total ${value(cash, pos):,.2f}", file=_o)
for t, p in pos.items():
    if p["shares"] > 0: print(f"  {t} {p['shares']:.6f} sh avg ${p['cost']/p['shares']:.2f} last ${PX[t]['price']}", file=_o)
