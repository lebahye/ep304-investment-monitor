"""Minimal Flask web view: paper portfolio, TA verdicts, watchlist. Reads the JSON in data/.
Trade form and Refresh button are enabled only when the ADMIN_TOKEN env var (a Replit Secret) is set."""
import datetime, hmac, html, os, threading, time
from flask import Flask, request, redirect, jsonify
import main as core
from portfolio_rules import WATCH, cap_pct, theme_of, THEMES

app = Flask(__name__)
ADMIN = os.environ.get("ADMIN_TOKEN", "")
STATE = {"msg": "", "refreshing": False, "last_refresh": None}
LOCK = threading.Lock()
TONE = {"Strong entry": "#0a7d32", "Accumulate": "#2e8b57", "Re-entry setup": "#1f6feb", "Hold": "#666",
        "Tighten stop": "#b35900", "Exit": "#c62828"}


def do_refresh():
    if not LOCK.acquire(blocking=False):
        return
    STATE["refreshing"] = True
    try:
        core.refresh(); STATE["msg"] = "Refresh complete."
        STATE["last_refresh"] = datetime.datetime.now(core.ET).strftime("%Y-%m-%d %H:%M ET")
    except Exception as e:
        STATE["msg"] = f"Refresh failed: {e}"
    finally:
        STATE["refreshing"] = False; LOCK.release()


def stale():
    """True if prices.json is older than the most recent completed weekday session."""
    px = core.load("prices.json", {}) or {}
    have = (px.get("SPY") or {}).get("date")
    now = datetime.datetime.now(core.ET); d = now.date()
    if now.weekday() >= 5 or (now.hour, now.minute) < (16, 15):
        d -= datetime.timedelta(days=1)
    while d.weekday() >= 5:
        d -= datetime.timedelta(days=1)
    return have is None or have < d.isoformat()


def scheduler():
    """Refresh at start if stale, then every weekday at 4:30 PM ET (only while the process is running)."""
    if stale():
        do_refresh()
    done = None
    while True:
        now = datetime.datetime.now(core.ET)
        if now.weekday() < 5 and (now.hour, now.minute) >= (16, 30) and done != now.date():
            do_refresh(); done = now.date()
        time.sleep(60)


def authed():
    return bool(ADMIN) and hmac.compare_digest(request.form.get("token", ""), ADMIN)


def money(v): return "" if v is None else f"${v:,.2f}"


@app.route("/")
def index():
    s = core.portfolio_state()
    ta = core.load("ta.json", {}) or {}
    px = core.load("prices.json", {}) or {}
    e = html.escape
    out = [f"""<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1">
<title>EP304 investment monitor</title><style>
body{{font:14px system-ui,sans-serif;margin:16px;max-width:1400px;color:#222}} h1{{font-size:20px}} h2{{font-size:16px;margin-top:28px}}
table{{border-collapse:collapse;width:100%}} th,td{{padding:4px 8px;border-bottom:1px solid #eee;text-align:right;white-space:nowrap}}
th{{background:#f6f6f6}} td.l,th.l{{text-align:left;white-space:normal}} .wrap{{overflow-x:auto}}
.kpi{{display:inline-block;margin:0 24px 8px 0}} .kpi b{{display:block;font-size:20px}} .msg{{background:#fff7e0;padding:8px}}
.pos{{color:#0a7d32}} .neg{{color:#c62828}} .note{{color:#666;font-size:12px}}</style></head><body>
<h1>Moonshots EP #304 investment monitor</h1>
<p class=note>Paper trading only. Not financial advice. Prices: last daily close from Yahoo Finance (unofficial endpoint) as of {e(str(s['asOf']))}.
TA as of {e(str(ta.get('meta', {}).get('asOf')))}. {'Refreshing now…' if STATE['refreshing'] else ''}</p>"""]
    if STATE["msg"]:
        out.append(f"<p class=msg>{e(STATE['msg'])}</p>")
    cls = lambda v: "pos" if v > 0 else "neg" if v < 0 else ""
    spy = s["spy"]
    out.append(f"""<div><span class=kpi>Total<b>{money(s['total'])}</b></span>
<span class=kpi>Gain/loss<b class={cls(s['gain'])}>{s['gain']:+,.2f} ({s['gainPct']:+.2f}%)</b></span>
<span class=kpi>Cash<b>{money(s['cash'])} ({100*s['cash']/s['total']:.0f}%)</b></span>
<span class=kpi>Same start in SPY<b>{money(spy)}{f' ({(spy/s["start"]["cash"]-1)*100:+.2f}%)' if spy else ''}</b></span></div>""")
    out.append("<h2>Positions</h2><div class=wrap><table><tr><th class=l>Ticker</th><th class=l>Theme</th><th>Shares</th><th>Avg</th><th>Last</th><th>Value</th><th>Weight / cap</th><th>Gain</th><th>Stop</th><th class=l>TA verdict</th></tr>")
    for r in s["rows"]:
        w = 100 * r["value"] / s["total"]
        out.append(f"<tr><td class=l><b>{r['t']}</b></td><td class=l>{theme_of(r['t'])}</td><td>{r['shares']:.4f}</td><td>{r['avg']:.2f}</td><td>{r['last']:.2f}</td><td>{money(r['value'])}</td>"
                   f"<td>{w:.1f}% / {cap_pct(r['t'])}%</td><td class={cls(r['gain'])}>{r['gain']:+.2f} ({r['gainPct']:+.1f}%)</td><td>{r['stop'] or ''}</td>"
                   f"<td class=l style='color:{TONE.get(r['verdict'],'#222')}'>{e(str(r['verdict']))}</td></tr>")
    out.append("</table></div>")
    if ADMIN:
        out.append("""<h2>Record a paper trade</h2><form method=post action=/trade>
<input name=line size=50 placeholder="paper BUY GEV $500 -- reason" required> <input name=token type=password placeholder="ADMIN_TOKEN" required>
<button>Record</button></form><p class=note>Formats: <code>paper BUY GEV $500</code>, <code>paper SELL AMZN 1.5 sh</code>, <code>paper SELL LLY ALL</code>,
optional <code>@ 123.45</code>, <code>on 2026-10-23</code>, <code>-- note</code>. Fills at the latest refreshed close unless a price is given.</p>
<form method=post action=/refresh><input name=token type=password placeholder="ADMIN_TOKEN" required> <button>Refresh data now</button></form>""")
    else:
        out.append("<p class=note>Set an <code>ADMIN_TOKEN</code> secret to enable the trade form and Refresh button. Or use the Shell: <code>python main.py trade 'paper BUY GEV $500'</code>.</p>")
    out.append("<h2>Watchlist and TA verdicts</h2><div class=wrap><table><tr><th class=l>Ticker</th><th class=l>Theme</th><th>Close</th><th>From 52w high</th><th>Stage</th><th class=l>D/W/M trend</th><th>RSI</th><th>RS vs SPY pct</th><th class=l>Vol regime</th><th>Stop</th><th class=l>Verdict</th><th class=l>Why</th></tr>")
    order = {t: i for i, t in enumerate(THEMES)}
    for t, x in sorted(ta.get("ta", {}).items(), key=lambda kv: (order.get(theme_of(kv[0]), 99), kv[0])):
        rs = (x.get("rsSpy") or {}).get("pct")
        out.append(f"<tr><td class=l><b>{t}</b><br><span class=note>{e(str((px.get(t) or {}).get('name') or ''))}</span></td><td class=l>{theme_of(t)}</td><td>{x['close']}</td><td>{x['fromHi']}%</td><td>{x['stage']}</td>"
                   f"<td class=l>{x['dTrend']}/{x['wTrend']}/{x['mTrend']}</td><td>{x['rsiD']}</td><td>{'' if rs is None else int(rs)}</td><td class=l>{x['volRegime']}</td><td>{x['stop']}</td>"
                   f"<td class=l style='color:{TONE.get(x.get('verdict'),'#222')}'><b>{e(str(x.get('verdict')))}</b></td><td class=l class=note>{e(str(x.get('why','')))}</td></tr>")
    out.append("</table></div><h2>Trade ledger</h2><div class=wrap><table><tr><th>#</th><th class=l>Date</th><th class=l>Side</th><th class=l>Ticker</th><th>Shares</th><th>Price</th><th class=l>Note</th></tr>")
    for t in reversed(s["trades"]):
        out.append(f"<tr><td>{t['id']}</td><td class=l>{t['date']}</td><td class=l>{t['side']}</td><td class=l>{t['t']}</td><td>{t['shares']:.6f}</td><td>{t['price']:.2f}</td><td class=l>{e(t.get('note',''))}</td></tr>")
    out.append("</table></div><p class=note>JSON: <a href=/api/portfolio>/api/portfolio</a> · <a href=/api/ta>/api/ta</a> · <a href=/api/prices>/api/prices</a></p></body></html>")
    return "".join(out)


@app.post("/trade")
def trade():
    if not authed():
        STATE["msg"] = "Trade rejected: wrong or missing ADMIN_TOKEN."
    else:
        try:
            STATE["msg"] = core.record_trade(request.form.get("line", ""))
        except Exception as ex:
            STATE["msg"] = f"Trade rejected: {ex}"
    return redirect("/")


@app.post("/refresh")
def refresh():
    if not authed():
        STATE["msg"] = "Refresh rejected: wrong or missing ADMIN_TOKEN."
    else:
        threading.Thread(target=do_refresh, daemon=True).start(); STATE["msg"] = "Refresh started (takes about 1-2 minutes); reload the page."
    return redirect("/")


@app.get("/api/portfolio")
def api_portfolio(): return jsonify(core.portfolio_state())
@app.get("/api/ta")
def api_ta(): return jsonify(core.load("ta.json", {}))
@app.get("/api/prices")
def api_prices(): return jsonify(core.load("prices.json", {}))
@app.get("/healthz")
def healthz(): return jsonify(ok=True, stale=stale(), refreshing=STATE["refreshing"])


def serve():
    if os.environ.get("AUTO_REFRESH", "1") == "1":
        threading.Thread(target=scheduler, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
