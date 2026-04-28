import streamlit as st

import yfinance as yf

import pandas as pd

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO")

# ---------------- SETTINGS ----------------

st.sidebar.header("Settings")

symbols_input = st.sidebar.text_input(

    "Watchlist",

    "SPY, QQQ, AAPL, MSFT, NVDA, TSLA"

)

symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

mode = st.sidebar.selectbox(

    "Trading Mode",

    ["AUTO", "TREND", "CHOP"]

)

account_size = st.sidebar.number_input("Account Size ($)", value=1000)

risk_percent = st.sidebar.slider("Risk %", 0.5, 5.0, 1.0)

# ---------------- DATA ----------------

def get_data(symbol):

    try:

        data = yf.Ticker(symbol).history(period="1d", interval="5m")

        if data is None or len(data) < 4:

            return None

        return data

    except:

        return None

def get_change(symbol):

    data = get_data(symbol)

    if data is None:

        return None, None

    price = data["Close"].iloc[-1]

    start = data["Close"].iloc[-4]

    change_pct = ((price - start) / start) * 100

    return float(price), float(change_pct)

# ---------------- MARKET ----------------

def get_market(spy_change):

    if spy_change >= 0.05:

        return "BULLISH"

    elif spy_change <= -0.05:

        return "BEARISH"

    else:

        return "CHOPPY"

# ---------------- SIGNALS ----------------

def trend_signal(change):

    if change >= 0.10:

        return "🚀 STRONG BUY"

    elif change >= 0.03:

        return "🟢 BUY"

    elif change <= -0.10:

        return "🔻 STRONG SELL"

    elif change <= -0.03:

        return "🔴 SELL"

    return None

def chop_signal(change):

    if change >= 0.10:

        return "🔻 FADE SELL"

    elif change <= -0.10:

        return "🚀 FADE BUY"

    return None

# ---------------- SCAN ----------------

if st.button("Run Scan"):

    spy_price, spy_change = get_change("SPY")

    market = get_market(spy_change)

    st.subheader("Market")

    c1, c2, c3 = st.columns(3)

    c1.metric("SPY", round(spy_price, 2))

    c2.metric("20m %", round(spy_change, 3))

    c3.metric("Market", market)

    results = []

    for symbol in symbols:

        price, change = get_change(symbol)

        if price is None:

            continue

        signal = None

        # 🔥 MODE LOGIC

        active_mode = mode

        if mode == "AUTO":

            active_mode = "TREND" if market != "CHOPPY" else "CHOP"

        if active_mode == "TREND":

            signal = trend_signal(change)

            if market == "BULLISH" and signal and "BUY" not in signal:

                signal = None

            if market == "BEARISH" and signal and "SELL" not in signal:

                signal = None

        elif active_mode == "CHOP":

            signal = chop_signal(change)

        if not signal:

            continue

        score = round(abs(change) * 300, 1)

        risk_amount = account_size * (risk_percent / 100)

        results.append({

            "Score": score,

            "Symbol": symbol,

            "Price": round(price, 2),

            "20m %": round(change, 3),

            "Signal": signal,

            "Risk $": round(risk_amount, 2)

        })

    df = pd.DataFrame(results)

    st.subheader("🎯 Trade Opportunities")

    if df.empty:

        st.warning("No setups — this is normal. Stay patient.")

    else:

        df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

        df.index = df.index + 1

        st.dataframe(df, use_container_width=True)

        top = df.iloc[0]

        st.success(f"Top Trade: {top['Symbol']} | {top['Signal']}")

# ---------------- NOTES ----------------

st.subheader("Notes")

st.text_area("Write your thoughts")
