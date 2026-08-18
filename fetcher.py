"""
Fetches historical stock data via yfinance and computes the three investment curves:
  1. Amount invested (cumulative contributions)
  2. Portfolio value without dividend reinvestment
  3. Portfolio value with dividend reinvestment
"""

import sys
from datetime import datetime

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("[ERROR] yfinance not installed. Run: pip install yfinance pandas")
    sys.exit(1)


def fetch_and_compute(data_config: dict) -> dict:
    ticker      = data_config["ticker"]
    start       = data_config["start_date"]
    end         = data_config.get("end_date", datetime.today().strftime("%Y-%m-%d"))
    weekly_inv  = data_config.get("weekly_investment")
    monthly_inv = data_config.get("monthly_investment")
    inv_amount  = weekly_inv or monthly_inv
    is_weekly   = weekly_inv is not None
    reinvest    = data_config.get("reinvest_dividends", True)
    currency    = data_config.get("currency", "USD")

    if not inv_amount:
        raise ValueError("scenario.data must specify weekly_investment or monthly_investment")

    t = yf.Ticker(ticker)

    # ── Prices (adjusted close) ───────────────────────────────────────────────
    hist = t.history(start=start, end=end, auto_adjust=True)
    if hist.empty:
        raise ValueError(f"No price data found for ticker '{ticker}'")

    hist.index = hist.index.tz_localize(None) if hist.index.tz else hist.index
    prices = hist["Close"].dropna()
    trading_days = prices.index

    # ── Investment schedule → snapped to next available trading day ───────────
    freq = "W-FRI" if is_weekly else "MS"
    raw_schedule = pd.date_range(start=trading_days[0], end=trading_days[-1], freq=freq)
    inv_dates: set = set()
    for d in raw_schedule:
        future = trading_days[trading_days >= d]
        if not future.empty:
            inv_dates.add(future[0])

    # ── Dividends → snapped to next available trading day ────────────────────
    div_map: dict = {}
    if reinvest:
        raw_divs = t.dividends
        if not raw_divs.empty:
            raw_divs.index = raw_divs.index.tz_localize(None) if raw_divs.index.tz else raw_divs.index
            raw_divs = raw_divs[
                (raw_divs.index >= trading_days[0]) &
                (raw_divs.index <= trading_days[-1])
            ]
            for d, v in raw_divs.items():
                snap = trading_days[trading_days >= d]
                if not snap.empty:
                    day = snap[0]
                    div_map[day] = div_map.get(day, 0.0) + float(v)

    # ── Simulate day by day ───────────────────────────────────────────────────
    shares_no_div   = 0.0
    shares_with_div = 0.0
    total_invested  = 0.0
    series = []

    for date in trading_days:
        price = float(prices[date])
        if price <= 0:
            continue

        if date in inv_dates:
            new_shares       = inv_amount / price
            shares_no_div   += new_shares
            shares_with_div += new_shares
            total_invested  += inv_amount

        if date in div_map:
            div_per_share    = div_map[date]
            shares_with_div += (shares_with_div * div_per_share) / price

        series.append({
            "date":           date.strftime("%Y-%m-%d"),
            "invested":       round(total_invested, 2),
            "value_no_div":   round(shares_no_div * price, 2),
            "value_with_div": round(shares_with_div * price, 2),
        })

    has_dividends = bool(div_map) and reinvest

    return {
        "series":        series,
        "has_dividends": has_dividends,
        "ticker":        ticker,
        "currency":      currency,
    }
