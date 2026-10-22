#!/usr/bin/env python3
"""Technical-analysis pass for the EP304 watchlist. Stdlib only.
Pulls Yahoo daily (5y) and weekly (5y) bars, drops today's bar if the US session
is not closed yet, computes indicators, writes ta.json and ta_block.ts (paste-ready).
Usage: python3 ta.py [ASOF=YYYY-MM-DD]  (ASOF truncates bars to that date for reproducible reruns)"""
import os
DATA_DIR = os.environ.get("EP304_DATA_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True); os.chdir(DATA_DIR)  # all JSON files are read/written here
import json, urllib.request, datetime, math, sys, time
from zoneinfo import ZoneInfo
ET = ZoneInfo("America/New_York")
WATCH = "GRID CEG GEV ETN VST NEE RUN PWR EME FIX SMH NVDA TSM MSFT GOOGL AMZN MU AVGO VRT EQIX DLR RIOT IREN CIFR CRWV CCJ URA FCX EQT WMB OKLO COWZ SPCX TSLA ROK BOTZ SYM LLY CRWD IBIT".split()
BENCH = {  # sector benchmark per ticker (None = SPY only)
 "NVDA":"SMH","TSM":"SMH","MU":"SMH","AVGO":"SMH","SMH":"QQQ",
 "CEG":"XLU","VST":"XLU","NEE":"XLU","RUN":"XLU",
 "GEV":"GRID","ETN":"GRID","VRT":"GRID","GRID":"XLI",
 "PWR":"XLI","EME":"XLI","FIX":"XLI",
 "MSFT":"QQQ","GOOGL":"QQQ","AMZN":"QQQ","CRWV":"QQQ","CRWD":"XLK",
 "EQIX":"XLRE","DLR":"XLRE",
 "RIOT":"BTC-USD","IREN":"BTC-USD","CIFR":"BTC-USD","IBIT":"BTC-USD",
 "CCJ":"URA","OKLO":"URA","URA":"XLE","FCX":"XLB","EQT":"XLE","WMB":"XLE",
 "ROK":"BOTZ","SYM":"BOTZ","TSLA":"BOTZ","BOTZ":"XLI","SPCX":"ITA",
 "LLY":"XLV","COWZ":None,
}
EXTRA = ["SPY","XLU","XLI","XLV","XLE","XLB","XLK","XLRE","QQQ","ITA","BTC-USD"]
ASOF = None
for a in sys.argv[1:]:
    if a.startswith("ASOF="): ASOF = a[5:]

def fetch(t, interval):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?range=5y&interval={interval}"
    for i in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"}), timeout=25)
            d = json.load(r)["chart"]["result"][0]; break
        except Exception as e:
            if i == 2: raise
            time.sleep(2)
    q = d["indicators"]["quote"][0]; ts = d["timestamp"]
    tz = ZoneInfo(d["meta"].get("exchangeTimezoneName","America/New_York"))
    bars = []
    for k, t0 in enumerate(ts):
        c = q["close"][k]
        if c is None: continue
        dt = datetime.datetime.fromtimestamp(t0, tz).date().isoformat()
        bars.append(dict(d=dt, o=q["open"][k] or c, h=q["high"][k] or c, l=q["low"][k] or c, c=c, v=q["volume"][k] or 0))
    # dedupe by date (keep last)
    out = {}
    for b in bars: out[b["d"]] = b
    return [out[k] for k in sorted(out)]

now = datetime.datetime.now(ET)
today = now.date().isoformat()
session_closed = now.hour > 16 or (now.hour == 16 and now.minute >= 15)
def trim(bars, weekly=False):
    if ASOF: return [b for b in bars if b["d"] <= ASOF]
    if weekly: return bars
    if bars and bars[-1]["d"] == today and not session_closed: return bars[:-1]
    return bars

def sma(x, n, i=None):
    i = len(x)-1 if i is None else i
    if i+1 < n: return None
    return sum(x[i-n+1:i+1])/n
def ema_series(x, n):
    k = 2/(n+1); out = []; e = None
    for v in x:
        e = v if e is None else v*k + e*(1-k); out.append(e)
    return out
def rsi(x, n=14):
    if len(x) < n+1: return None
    g = l = 0.0
    for i in range(1, n+1):
        d = x[i]-x[i-1]; g += max(d,0); l += max(-d,0)
    g /= n; l /= n
    for i in range(n+1, len(x)):
        d = x[i]-x[i-1]; g = (g*(n-1)+max(d,0))/n; l = (l*(n-1)+max(-d,0))/n
    return 100.0 if l == 0 else 100 - 100/(1+g/l)
def pctrank(series, v):
    s = [a for a in series if a is not None]
    if not s: return None
    return 100*sum(1 for a in s if a <= v)/len(s)
def r(v, n=2): return None if v is None else round(v, n)

def analyze(t, D, W, bench_bars):
    c = [b["c"] for b in D]; h = [b["h"] for b in D]; l = [b["l"] for b in D]; v = [b["v"] for b in D]
    n = len(c); last = c[-1]
    s20, s50, s150, s200 = sma(c,20), sma(c,50), sma(c,150), sma(c,200)
    s200_prev = sma(c,200,n-1-21) if n >= 221 else None
    s200_slope = None if (s200 is None or s200_prev is None) else (s200/s200_prev-1)*100
    def trend(p, fast, slow):
        if fast is None or slow is None: return None
        if p > fast > slow: return "Up"
        if p < fast < slow: return "Down"
        return "Mixed"
    dtrend = trend(last, s50, s200)
    wc = [b["c"] for b in W]
    w10, w40 = sma(wc,10), sma(wc,40)
    wtrend = trend(wc[-1], w10, w40) if wc else None
    # monthly closes from daily
    mclose = {}
    for b in D: mclose[b["d"][:7]] = b["c"]
    mc = [mclose[k] for k in sorted(mclose)]
    m10 = sma(mc,10)
    m10p = sma(mc,10,len(mc)-2) if len(mc) >= 11 else None
    mtrend = None if m10 is None or m10p is None else ("Up" if mc[-1] > m10 and m10 >= m10p else "Down" if mc[-1] < m10 and m10 < m10p else "Mixed")
    mom121 = (c[-22]/c[-253]-1)*100 if n >= 253 else None
    rsid = rsi(c); rsiw = rsi(wc)
    e12, e26 = ema_series(c,12), ema_series(c,26)
    macd = [a-b for a,b in zip(e12,e26)]; sig = ema_series(macd,9)
    hist = [a-b for a,b in zip(macd,sig)]
    macd_ok = n >= 35
    hist_now = hist[-1] if macd_ok else None
    hist_dir = None if not macd_ok else ("Rising" if hist[-1] > hist[-2] else "Falling")
    # relative strength
    def rs_stats(bb):
        if not bb: return None
        bm = {b["d"]: b["c"] for b in bb}
        rs = [(b["d"], b["c"]/bm[b["d"]]) for b in D if b["d"] in bm]
        if len(rs) < 64: return None
        vals = [x for _,x in rs]
        win = vals[-252:]
        slope = (vals[-1]/vals[-64]-1)*100
        return dict(slope3m=r(slope,1), pct=r(pctrank(win, vals[-1]),0), newHigh=vals[-1] >= max(win)*0.999, days=len(win))
    rs_spy = rs_stats(bench_bars.get("SPY")) if t != "SPY" else None
    bk = BENCH.get(t)
    rs_sec = rs_stats(bench_bars.get(bk)) if bk else None
    # volume profile (~1y daily bars)
    vp = None
    seg = D[-252:]
    if len(seg) >= 120 and sum(b["v"] for b in seg) > 0:
        lo = min(b["l"] for b in seg); hi = max(b["h"] for b in seg); NB = 50
        w = (hi-lo)/NB if hi > lo else 1
        bins = [0.0]*NB
        for b in seg:
            a = max(0, min(NB-1, int((b["l"]-lo)/w))); z = max(0, min(NB-1, int((b["h"]-lo)/w)))
            share = b["v"]/(z-a+1)
            for k in range(a, z+1): bins[k] += share
        poc = max(range(NB), key=lambda k: bins[k]); tot = sum(bins)
        a = z = poc; acc = bins[poc]
        while acc < 0.7*tot and (a > 0 or z < NB-1):
            up = bins[z+1] if z < NB-1 else -1; dn = bins[a-1] if a > 0 else -1
            if up >= dn: z += 1; acc += bins[z]
            else: a -= 1; acc += bins[a]
        mid = lambda k: lo + (k+0.5)*w
        vah, val = lo + (z+1)*w, lo + a*w
        pos = "Above value" if last > vah else "Below value" if last < val else "Inside value"
        vp = dict(poc=r(mid(poc)), vah=r(vah), val=r(val), pos=pos, abovePoc=last > mid(poc))
    # OBV and up/down volume
    obv = [0.0]
    for i in range(1, n):
        obv.append(obv[-1] + (v[i] if c[i] > c[i-1] else -v[i] if c[i] < c[i-1] else 0))
    obv_trend = None
    if n >= 70 and sum(v[-50:]) > 0:
        o20, o20p = sma(obv,20), sma(obv,20,n-1-30)
        obv_trend = "Rising" if o20 > o20p else "Falling"
    upv = sum(v[i] for i in range(max(1,n-50), n) if c[i] > c[i-1]); dnv = sum(v[i] for i in range(max(1,n-50), n) if c[i] < c[i-1])
    udr = r(upv/dnv) if dnv > 0 and upv > 0 else None
    # ATR (Wilder 14)
    tr = [h[0]-l[0]] + [max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])) for i in range(1,n)]
    atr = []; a0 = None
    for i, x in enumerate(tr):
        if i < 13: atr.append(None); continue
        a0 = sum(tr[:14])/14 if a0 is None else (a0*13 + x)/14; atr.append(a0)
    atrp_series = [None if atr[i] is None else atr[i]/c[i]*100 for i in range(n)]
    atrp = atrp_series[-1]
    atrp_pct = pctrank(atrp_series[-252:], atrp) if atrp is not None else None
    # Bollinger bandwidth
    bw = []
    for i in range(n):
        if i < 19: bw.append(None); continue
        win = c[i-19:i+1]; m = sum(win)/20; sd = math.sqrt(sum((x-m)**2 for x in win)/20)
        bw.append(4*sd/m*100)
    bw_now = bw[-1]
    bw_pct = pctrank(bw[-126:], bw_now) if bw_now is not None else None
    squeeze = bw_pct is not None and bw_pct <= 10
    # realized vol regime
    lr = [math.log(c[i]/c[i-1]) for i in range(1,n)]
    rv = []
    for i in range(len(lr)):
        if i < 19: rv.append(None); continue
        w_ = lr[i-19:i+1]; m = sum(w_)/20
        rv.append(math.sqrt(sum((x-m)**2 for x in w_)/19)*math.sqrt(252)*100)
    rv_now = rv[-1] if rv else None
    rv_pct = pctrank(rv[-252:], rv_now) if rv_now is not None else None
    regime = None if rv_pct is None else ("Low" if rv_pct < 25 else "High" if rv_pct > 75 else "Normal")
    # 52-week high/low (daily highs/lows), drawdown from high close
    y = D[-252:]
    hi52 = max(b["h"] for b in y); lo52 = min(b["l"] for b in y); hic = max(b["c"] for b in y)
    # stage
    stage = None
    if s50 and s200 and s200_slope is not None:
        if last > s50 > s200 and s200_slope > 0: stage = 2
        elif last < s200 and s200_slope < 0: stage = 4
        elif s200_slope >= 0: stage = 3
        else: stage = 1
    template = None
    if s50 and s150 and s200 and s200_slope is not None:
        template = all([last > s150, last > s200, s150 > s200, s200_slope > 0, s50 > s150, s50 > s200 and last > s50, last >= 1.25*lo52, last >= 0.75*hi52])
    cross = None; cross_days = None
    if n >= 201:
        cur = sma(c,50) > sma(c,200); cross = "Golden (50 > 200)" if cur else "Death (50 < 200)"
        for k in range(1, n-200):
            i = n-1-k
            if (sma(c,50,i) > sma(c,200,i)) != cur: cross_days = k; break
    hh22 = max(c[-22:]); stop = hh22 - 3*atr[-1] if atr[-1] else None
    return dict(
        t=t, date=D[-1]["d"], close=r(last), bars=n,
        sma20=r(s20), sma50=r(s50), sma200=r(s200), sma200Slope=r(s200_slope,2),
        dTrend=dtrend, wTrend=wtrend, mTrend=mtrend,
        mom121=r(mom121,1), rsiD=r(rsid,0), rsiW=r(rsiw,0),
        macdHist=r(hist_now,3), macdDir=hist_dir,
        bench=bk, rsSpy=rs_spy, rsSec=rs_sec, vp=vp, obv=obv_trend, udr=udr,
        atr=r(atr[-1]), atrPct=r(atrp,2), atrPctile=r(atrp_pct,0),
        bbw=r(bw_now,1), bbwPctile=r(bw_pct,0), squeeze=squeeze,
        rv=r(rv_now,0), rvPctile=r(rv_pct,0), volRegime=regime,
        hi52=r(hi52), lo52=r(lo52), fromHi=r((last/hi52-1)*100,1), fromLo=r((last/lo52-1)*100,1),
        ddFromHighClose=r((last/hic-1)*100,1),
        stage=stage, template=template, cross=cross, crossDays=cross_days,
        hh22=r(hh22), stop=r(stop), belowStop=(stop is not None and last < stop),
    )

if __name__ == "__main__":
    allb = {}
    for t in sorted(set(WATCH+EXTRA)):
        try:
            allb[t] = (trim(fetch(t,"1d")), trim(fetch(t,"1wk"), weekly=True))
        except Exception as e:
            print("ERR", t, e)
    bench = {k: v[0] for k, v in allb.items()}
    # drop the current partial week only when asof/day trimming removed today's bar
    res = {}
    for t in WATCH:
        if t not in allb: continue
        D, W = allb[t]
        if W and D and W[-1]["d"] > D[-1]["d"]:
            W = W[:-1] + [dict(W[-1], c=D[-1]["c"])]  # week-to-date bar uses the last completed daily close
        res[t] = analyze(t, D, W, bench)
    spy = allb["SPY"][0]
    meta = dict(asOf=res[WATCH[0]]["date"], generated=now.strftime("%Y-%m-%d %H:%M ET"), spyClose=round(spy[-1]["c"],2), source="Yahoo Finance v8 chart, range=5y, interval=1d and 1wk")
    json.dump(dict(meta=meta, ta=res), open("ta.json","w"), indent=1)
    for t, x in res.items():
        print(f'{t:5} {x["date"]} n={x["bars"]:4} st={x["stage"]} tpl={x["template"]} d/w/m={x["dTrend"]}/{x["wTrend"]}/{x["mTrend"]} m121={x["mom121"]} rsi={x["rsiD"]}/{x["rsiW"]} macd={x["macdDir"]} rsSpy={x["rsSpy"] and x["rsSpy"]["pct"]} rsSec({x["bench"]})={x["rsSec"] and x["rsSec"]["pct"]} vp={x["vp"] and x["vp"]["pos"]} obv={x["obv"]} udr={x["udr"]} atr%={x["atrPct"]}({x["atrPctile"]}) sq={x["squeeze"]} vol={x["volRegime"]} stop={x["stop"]} below={x["belowStop"]}')
    print(meta)
