import streamlit as st

import yfinance as yf

import pandas as pd

import time

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO (LIVE ALERTS)")

# ---------------- SETTINGS ----------------

st.sidebar.header("Settings")

symbols_input = st.sidebar.text_input(

    "Watchlist",

    "SPY, QQQ, AAPL, MSFT, NVDA, TSLA"

)

symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

mode = st.sidebar.selectbox("Mode", ["AUTO", "TREND", "CHOP"])

alert_threshold = st.sidebar.slider("Alert Score Threshold", 50, 200, 100)

auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", True)

account_size = st.sidebar.number_input("Account Size", value=1000)

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

    change = ((price - start) / start) * 100

    return float(price), float(change)

# ---------------- MARKET ----------------

def get_market(change):

    if change >= 0.05:

        return "BULLISH"

    elif change <= -0.05:

        return "BEARISH"

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

# ---------------- SESSION STATE ----------------

if "last_top" not in st.session_state:

    st.session_state.last_top = None

# ---------------- MAIN LOOP ----------------

placeholder = st.empty()

while True:

    spy_price, spy_change = get_change("SPY")

    market = get_market(spy_change)

    results = []

    for symbol in symbols:

        price, change = get_change(symbol)

        if price is None:

            continue

        active_mode = mode

        if mode == "AUTO":

            active_mode = "TREND" if market != "CHOPPY" else "CHOP"

        signal = None

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

        risk = account_size * (risk_percent / 100)

        results.append({

            "Score": score,

            "Symbol": symbol,

            "Price": round(price, 2),

            "20m %": round(change, 3),

            "Signal": signal,

            "Risk": round(risk, 2)

        })

    df = pd.DataFrame(results)

    with placeholder.container():

        st.subheader("Market")

        c1, c2, c3 = st.columns(3)

        c1.metric("SPY", round(spy_price, 2))

        c2.metric("20m %", round(spy_change, 3))

        c3.metric("Market", market)

        st.subheader("🎯 Trade Opportunities")

        if df.empty:

            st.warning("No setups — stay patient.")

        else:

            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            df.index = df.index + 1

            st.dataframe(df, use_container_width=True)

            top = df.iloc[0]

            # 🔥 ALERT SYSTEM

            if top["Score"] >= alert_threshold:

                if st.session_state.last_top != top["Symbol"]:

                    st.session_state.last_top = top["Symbol"]

                    st.success(f"🚨 NEW ALERT: {top['Symbol']} | {top['Signal']} | Score {top['Score']}")

                else:

                    st.info(f"Top Trade: {top['Symbol']} | {top['Signal']}")

            else:

                st.info("No high-quality alerts yet")

    if not auto_refresh:

        break

    time.sleep(30)

    st.rerun()

# ---------------- NOTES ----------------

st.subheader("Notes")

st.text_area("Journal")
