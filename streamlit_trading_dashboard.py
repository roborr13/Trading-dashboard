import streamlit as st

import yfinance as yf

import pandas as pd

import time

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO (ENTRY SYSTEM)")

st.caption("Paper-trading scanner only. No real trades are placed.")

st.sidebar.header("Settings")

symbols_input = st.sidebar.text_input(

    "Watchlist",

    "SPY, QQQ, AAPL, MSFT, NVDA, TSLA"

)

symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

mode = st.sidebar.selectbox("Mode", ["AUTO", "TREND", "CHOP"])

alert_threshold = st.sidebar.slider("Alert Score Threshold", 50, 200, 100)

auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", True)

st.sidebar.subheader("Risk")

account_size = st.sidebar.number_input("Account Size ($)", value=1000)

risk_percent = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

st.sidebar.subheader("Trade Plan")

entry_buffer_percent = st.sidebar.slider("Entry Buffer (%)", 0.05, 1.0, 0.15)

stop_percent = st.sidebar.slider("Stop Loss (%)", 0.5, 5.0, 1.0)

reward_ratio = st.sidebar.slider("Reward Ratio", 1.0, 5.0, 2.0)

def get_data(symbol):

    try:

        data = yf.Ticker(symbol).history(period="1d", interval="5m")

        if data is None or len(data) < 6:

            return None

        return data

    except:

        return None

def analyze(symbol):

    data = get_data(symbol)

    if data is None:

        return None

    closes = data["Close"]

    highs = data["High"]

    lows = data["Low"]

    price = closes.iloc[-1]

    start = closes.iloc[-5]

    prev = closes.iloc[-2]

    change = ((price - start) / start) * 100

    pullback = price < prev

    recent_high = highs.iloc[-5:].max()

    recent_low = lows.iloc[-5:].min()

    return {

        "price": float(price),

        "change": float(change),

        "pullback": bool(pullback),

        "recent_high": float(recent_high),

        "recent_low": float(recent_low),

    }

def get_market(change):

    if change >= 0.05:

        return "BULLISH"

    elif change <= -0.05:

        return "BEARISH"

    return "CHOPPY"

def trend_signal(change, pullback):

    if change >= 0.10 and pullback:

        return "🚀 STRONG BUY"

    elif change >= 0.05 and pullback:

        return "🟢 BUY"

    if change <= -0.10 and pullback:

        return "🔻 STRONG SELL"

    elif change <= -0.05 and pullback:

        return "🔴 SELL"

    return None

def chop_signal(change):

    if change >= 0.15:

        return "🔻 FADE SELL"

    elif change <= -0.15:

        return "🚀 FADE BUY"

    return None

def build_trade_plan(price, signal, recent_high, recent_low):

    max_risk_dollars = account_size * (risk_percent / 100)

    if "BUY" in signal:

        entry = recent_high * (1 + entry_buffer_percent / 100)

        stop = price * (1 - stop_percent / 100)

        risk_per_share = entry - stop

        target = entry + (risk_per_share * reward_ratio)

    elif "SELL" in signal:

        entry = recent_low * (1 - entry_buffer_percent / 100)

        stop = price * (1 + stop_percent / 100)

        risk_per_share = stop - entry

        target = entry - (risk_per_share * reward_ratio)

    else:

        return None

    if risk_per_share <= 0:

        return None

    shares = int(max_risk_dollars // risk_per_share)

    return {

        "Entry": round(entry, 2),

        "Stop": round(stop, 2),

        "Target": round(target, 2),

        "Risk/Share": round(risk_per_share, 2),

        "Shares": shares,

        "Max Risk $": round(shares * risk_per_share, 2),

    }

if "last_top" not in st.session_state:

    st.session_state.last_top = None

placeholder = st.empty()

while True:

    spy = analyze("SPY")

    if spy is None:

        st.error("Could not load SPY data.")

        break

    market = get_market(spy["change"])

    results = []

    for symbol in symbols:

        data = analyze(symbol)

        if data is None:

            continue

        price = data["price"]

        change = data["change"]

        pullback = data["pullback"]

        recent_high = data["recent_high"]

        recent_low = data["recent_low"]

        active_mode = mode

        if mode == "AUTO":

            active_mode = "TREND" if market != "CHOPPY" else "CHOP"

        signal = None

        if active_mode == "TREND":

            signal = trend_signal(change, pullback)

            if market == "BULLISH" and signal and "BUY" not in signal:

                signal = None

            if market == "BEARISH" and signal and "SELL" not in signal:

                signal = None

        elif active_mode == "CHOP":

            signal = chop_signal(change)

        if not signal:

            continue

        plan = build_trade_plan(price, signal, recent_high, recent_low)

        if plan is None:

            continue

        score = round(abs(change) * 300 + (5 if pullback else 0), 1)

        results.append({

            "Score": score,

            "Symbol": symbol,

            "Price": round(price, 2),

            "20m %": round(change, 3),

            "Signal": signal,

            "Pullback": "✔" if pullback else "",

            **plan

        })

    df = pd.DataFrame(results)

    with placeholder.container():

        st.subheader("Market")

        c1, c2, c3 = st.columns(3)

        c1.metric("SPY", round(spy["price"], 2))

        c2.metric("20m %", round(spy["change"], 3))

        c3.metric("Market", market)

        st.subheader("🎯 Entry Setups")

        if df.empty:

            st.warning("No clean entry setups right now. Wait.")

        else:

            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            df.index = df.index + 1

            st.dataframe(df, use_container_width=True)

            top = df.iloc[0]

            if top["Score"] >= alert_threshold:

                if st.session_state.last_top != top["Symbol"]:

                    st.session_state.last_top = top["Symbol"]

                    st.success(

                        f"🚨 TOP ENTRY: {top['Symbol']} | {top['Signal']} | "

                        f"Entry {top['Entry']} | Stop {top['Stop']} | Target {top['Target']} | "

                        f"Shares {top['Shares']}"

                    )

                else:

                    st.info(f"Top setup still: {top['Symbol']} | {top['Signal']}")

            else:

                st.info("No high-quality entry alerts.")

    if not auto_refresh:

        break

    time.sleep(30)

    st.rerun()

st.subheader("Notes")

st.text_area("Journal")
