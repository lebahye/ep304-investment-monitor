"""TA verdict rules, applied to ta.json -> writes verdicts into ta.json and ta_block.ts."""
import os
DATA_DIR = os.environ.get("EP304_DATA_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True); os.chdir(DATA_DIR)  # all JSON files are read/written here
import json
def verdict(x):
    st, c = x["stage"], x["close"]
    s20, s50 = x["sma20"], x["sma50"]
    mh, rd = x["macdHist"], x["rsiD"]
    below = x["belowStop"]
    rs = (x["rsSpy"] or {}).get("pct")
    vp = x["vp"] or {}
    if st is None:
        return "Hold", "Under 200 trading days of history; stage not computable"
    if st in (1, 4) and s20 and s50 and c > s20 and c > s50 and mh is not None and mh > 0 and rd is not None and 50 <= rd <= 70:
        return "Re-entry setup", f"Stage {st}, but price is back above its 20- and 50-day averages with MACD histogram positive and RSI {rd:.0f}"
    if st == 1 and x["squeeze"] and vp.get("abovePoc"):
        return "Re-entry setup", "Stage 1 base with a Bollinger squeeze and price above the volume point of control"
    if st == 4 and x["wTrend"] == "Down":
        return "Exit", "Stage 4 (below a falling 200-day) and the weekly trend is down"
    if st == 4:
        return "Tighten stop", "Stage 4, but the weekly trend isn't fully down yet"
    if st in (2, 3) and below:
        return "Tighten stop", f"Stage {st}; close is below the 3x ATR trailing stop ({x['stop']})"
    if rd is not None and rd >= 75:
        return "Tighten stop", f"Daily RSI {rd:.0f} is overextended"
    if st == 2 and x["template"] and x["wTrend"] == "Up" and rs is not None and rs >= 70:
        return "Strong entry", f"Stage 2 trend template passes; weekly trend up; RS vs SPY in the {rs:.0f}th percentile"
    if st == 2 and x["wTrend"] != "Down":
        return "Accumulate", "Stage 2 uptrend, but not every strong-entry test passes"
    return "Hold", f"Stage {st}; no entry or exit rule fired"

d = json.load(open("ta.json"))
from collections import Counter
cnt = Counter()
for t, x in d["ta"].items():
    v, why = verdict(x); x["verdict"] = v; x["why"] = why; cnt[v] += 1
    print(f"{t:5} {v:15} {why}")
print(dict(cnt))
json.dump(d, open("ta.json", "w"), indent=1)
keys = ["date","close","bars","sma20","sma50","sma200","sma200Slope","dTrend","wTrend","mTrend","mom121","rsiD","rsiW","macdHist","macdDir","bench","rsSpy","rsSec","vp","obv","udr","atr","atrPct","atrPctile","bbw","bbwPctile","squeeze","rv","rvPctile","volRegime","hi52","lo52","fromHi","fromLo","ddFromHighClose","stage","template","cross","crossDays","hh22","stop","belowStop","verdict","why"]
lines = [f'const TA_META = {json.dumps(d["meta"])};', "const TA: Record<string, TAData> = {"]
def clean(o):
    if isinstance(o, float) and o.is_integer(): return int(o)
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items() if k != "days"}
    return o
for t, x in d["ta"].items():
    lines.append(f'  {t}: {json.dumps(clean({k: x[k] for k in keys}), separators=(",", ":"))},')
lines.append("};")
def z(v): return v if isinstance(v,(int,float)) and not isinstance(v,bool) else 0
cs = 0.0
for t, x in d["ta"].items():
    cs += z(x["close"]) + z(x["stop"]) + z(x["atr"]) + z(x["rsiD"]) + z(x["sma200"]) + z((x["vp"] or {}).get("poc")) + z((x["rsSpy"] or {}).get("pct")) + z(x["stage"]) + z(x["mom121"]) + z(x["udr"]) + z(x["bbwPctile"]) + z(x["fromHi"])
d["meta"]["checksum"] = round(cs, 2)  # checks.py recomputes this from ta.json
json.dump(d, open("ta.json", "w"), indent=1)
lines.append(f"const TA_CHECKSUM = {round(cs, 2)}; // sum of close+stop+atr+rsiD+sma200+poc+rsSpy.pct+stage+mom121+udr+bbwPctile+fromHi; the Page recomputes it to catch paste errors")
open("ta_block.ts", "w").write("\n".join(lines) + "\n")
