import os
DATA_DIR = os.environ.get("EP304_DATA_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True); os.chdir(DATA_DIR)  # all JSON files are read/written here
import json,urllib.request,datetime,sys
T="CEG VST NEE GEV ETN PWR EME FIX VRT NVDA TSM MU AVGO MSFT GOOGL AMZN EQIX DLR SPCX TSLA ROK SYM CCJ FCX EQT WMB LLY CRWD RIOT IREN CIFR CRWV OKLO RUN IBIT COWZ GRID SMH BOTZ XLU URA SPY".split()
out={}
for t in T:
    try:
        r=urllib.request.urlopen(urllib.request.Request(f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?range=1y&interval=1d",headers={"User-Agent":"Mozilla/5.0"}),timeout=20)
        d=json.load(r)["chart"]["result"][0]; m=d["meta"]
        ts=d["timestamp"]; c=d["indicators"]["quote"][0]["close"]; h=d["indicators"]["quote"][0]["high"]
        pairs=[(a,b) for a,b in zip(ts,c) if b is not None]
        last_t,last=pairs[-1]
        hi=max(x for x in h if x is not None)
        closes=[b for a,b in pairs]
        ma200=sum(closes[-200:])/min(200,len(closes))
        out[t]=dict(price=round(last,2),date=datetime.datetime.fromtimestamp(last_t).strftime("%Y-%m-%d"),hi52=round(m.get("fiftyTwoWeekHigh",hi),2),hiCalc=round(hi,2),ma200=round(ma200,2),n=len(closes),name=m.get("longName") or m.get("shortName"))
    except Exception as e:
        out[t]=dict(err=str(e))
json.dump(out,open("prices.json","w"),indent=1)
for t,v in out.items():
    if "err" in v: print(t,"ERR",v["err"]); continue
    print(f'{t:6} {v["price"]:>9} {v["date"]} hi52={v["hi52"]} calc={v["hiCalc"]} off={100*(v["price"]/v["hi52"]-1):6.1f}% ma200={v["ma200"]} vsMA={100*(v["price"]/v["ma200"]-1):6.1f}% n={v["n"]} {v["name"]}')
