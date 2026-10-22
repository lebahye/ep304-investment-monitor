"""Shared watchlist, roles and Manager plan caps (single source of truth for checks.py and web.py).
pull.py / ta.py / portfolio.py keep their own literal lists; keep them in sync with WATCH."""
WATCH = set("GRID CEG GEV ETN VST NEE RUN PWR EME FIX SMH NVDA TSM MSFT GOOGL AMZN MU AVGO VRT EQIX DLR RIOT IREN CIFR "
            "CRWV CCJ URA FCX EQT WMB OKLO COWZ SPCX TSLA ROK BOTZ SYM LLY CRWD IBIT".split())
ETFS = {"GRID", "SMH", "URA", "COWZ", "BOTZ", "IBIT"}
SPECULATIVE = {"RUN", "RIOT", "IREN", "CIFR", "CRWV", "OKLO", "SYM", "IBIT"}
CORE = {"GRID", "CEG", "GEV", "ETN", "PWR", "SMH", "NVDA", "TSM", "MSFT", "GOOGL", "AMZN", "COWZ"}
THEMES = {
    "Compute & AI": (24, "SMH NVDA TSM MSFT GOOGL AMZN MU AVGO"),
    "Power & grid": (22, "GRID CEG GEV ETN VST NEE RUN"),
    "Cash flow": (12, "COWZ"),
    "Data centers": (10, "VRT EQIX DLR RIOT IREN CIFR CRWV"),
    "Trades": (8, "PWR EME FIX"),
    "Fuel & materials": (8, "CCJ URA FCX EQT WMB OKLO"),
    "Robotics & space": (8, "SPCX TSLA ROK BOTZ SYM"),
    "Health & security": (6, "LLY CRWD"),
    "Bitcoin": (2, "IBIT"),
}
CASH_FLOOR_PCT = 15
CRYPTO_COMBINED_CAP_PCT = 3  # RIOT + IBIT


def cap_pct(t):
    """Same order as the dashboard: Speculative 1.5%, ETF 12%, Core stock 5%, else Satellite 3%."""
    if t in SPECULATIVE: return 1.5
    if t in ETFS: return 12
    if t in CORE: return 5
    return 3


def theme_of(t):
    for th, (_, names) in THEMES.items():
        if t in names.split(): return th
    return "Other"
