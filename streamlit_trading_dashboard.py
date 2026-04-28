import streamlit as st

import yfinance as yf

import pandas as pd

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO")

st.caption("Only shows trades aligned with market direction")

# ---------------- SETTINGS ----------------

st.sidebar.header("Settings")

symbols_input = st.sidebar.text_input(

    "Watchlist",

    "SPY, QQQ, AAPL, MSFT, NVDA, TSLA"

)

symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

st.sidebar.subheader("Risk Settings")

account_size = st.sidebar.number_input("Account Size ($)", value=1000)

risk_percent = st.sidebar.slider("Risk per trade (%)", 0.5, 5.0, 1.0)

st.sidebar.subheader("Trade Settings")

stop_loss_percent = st.sidebar.slider("Stop loss (%)", 0.5, 5.0, 1.0)

target_percent = st.sidebar.slider("Target (%)", 0.5, 10.0, 2.0)

# ---------------- DATA ----------------

def get_data(symbol):

    try:

        data = yf.Ticker(symbol).history(period="1d", interval="5m")

        if data is None or len(data) < 4:

            return None

        return data

    except:

        return None

def get_20m_change(symbol):

    data = get_data(symbol)

    if data is None:

        return None, None

    price = data["Close"].iloc[-1]

    start = data["Close"].iloc[-4]

    change_pct = ((price - start) / start) * 100

    return float(price), float(change_pct)

# ---------------- MARKET ----------------

def get_market_direction(spy_change):

    if spy_change >= 0.05:

        return "BULLISH"

    elif spy_change <= -0.05:

        return "BEARISH"

    else:

        return "CHOPPY"

# ---------------- SIGNAL ----------------

def get_signal(change):

    if change >= 0.10:

        return "🚀 STRONG BUY"

    elif change >= 0.03:

        return "🟢 BUY"

    elif change <= -0.10:

        return "🔻 STRONG SELL"

    elif change <= -0.03:

        return "🔴 SELL"

    else:

        return "⚪ NO TRADE"

# ---------------- SCAN ----------------

if st.button("Run Scan"):

    spy_price, spy_change = get_20m_change("SPY")

    market = get_market_direction(spy_change)

    st.subheader("Market Direction")

    c1, c2, c3 = st.columns(3)

    c1.metric("SPY Price", round(spy_price, 2))

    c2.metric("SPY 20m %", round(spy_change, 3))

    c3.metric("Market", market)

    results = []

    for symbol in symbols:

        price, change = get_20m_change(symbol)

        if price is None:

            continue

        signal = get_signal(change)

        # 🔥 KEY FILTER (THIS IS THE UPGRADE)

        if market == "BULLISH" and "BUY" not in signal:

            continue

        if market == "BEARISH" and "SELL" not in signal:

            continue

        risk_amount = account_size * (risk_percent / 100)

        stop = price * (1 - stop_loss_percent / 100)

        target = price * (1 + target_percent / 100)

        results.append({

            "Symbol": symbol,

            "Price": round(price, 2),

            "20m %": round(change, 3),

            "Signal": signal,

            "Stop": round(stop, 2),

            "Target": round(target, 2),

            "Risk $": round(risk_amount, 2)

        })

    df = pd.DataFrame(results)

    st.subheader("🎯 TRADE SETUPS ONLY")

    if df.empty:

        st.warning("No valid trades — market not aligned. Sit out.")

    else:

        st.dataframe(df, use_container_width=True)

# ---------------- NOTES ----------------

st.subheader("Notes / Journal")

st.text_area("Write your thoughts here")
