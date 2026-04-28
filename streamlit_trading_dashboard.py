import streamlit as st

import yfinance as yf

import pandas as pd

import time

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO (A+ SETUPS ONLY)")

st.caption("Paper trading system — filters for high-quality trades only")

# ---------------- SETTINGS ----------------

st.sidebar.header("Settings")

symbols_input = st.sidebar.text_input(

    "Watchlist",

    "SPY, QQQ, AAPL, MSFT, NVDA, TSLA"

)

symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

mode = st.sidebar.selectbox("Mode", ["AUTO", "TREND", "CHOP"])

auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", True)

st.sidebar.subheader("Risk")

account_size = st.sidebar.number_input("Account Size ($)", value=1000)

risk_percent = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

st.sidebar.subheader("Trade Plan")

entry_buffer_percent = st.sidebar.slider("Entry Buffer (%)", 0.05, 1.0, 0.15)

stop_percent = st.sidebar.slider("Stop Loss (%)", 0.5, 5.0, 1.0)

reward_ratio = st.sidebar.slider("Reward Ratio", 1.0, 5.0, 2.0)

# ---------------- DATA ----------------

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

    return price, change, pullback, recent_high, recent_low

# ---------------- MARKET ----------------

def get_market(change):

    if change >= 0.05:

        return "BULLISH"

    elif change <= -0.05:

        return "BEARISH"

    return "CHOPPY"

# ---------------- SIGNAL ----------------

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

# ---------------- TRADE PLAN ----------------

def build_plan(price, signal, high, low):

    max_risk = account_size * (risk_percent / 100)

    if "BUY" in signal:

        entry = high * (1 + entry_buffer_percent / 100)

        stop = price * (1 - stop_percent / 100)

        risk_per_share = entry - stop

        target = entry + (risk_per_share * reward_ratio)

    elif "SELL" in signal:

        entry = low * (1 - entry_buffer_percent / 100)

        stop = price * (1 + stop_percent / 100)

        risk_per_share = stop - entry

        target = entry - (risk_per_share * reward_ratio)

    else:

        return None

    if risk_per_share <= 0:

        return None

    shares = int(max_risk // risk_per_share)

    return entry, stop, target, shares, risk_per_share

# ---------------- GRADING SYSTEM ----------------

def grade_trade(change, pullback, market, signal):

    score = abs(change) * 100

    if pullback:

        score += 10

    if market == "BULLISH" and "BUY" in signal:

        score += 10

    if market == "BEARISH" and "SELL" in signal:

        score += 10

    if score >= 30:

        grade = "A+"

    elif score >= 20:

        grade = "A"

    elif score >= 10:

        grade = "B"

    else:

        grade = "C"

    return score, grade

# ---------------- APP ----------------

placeholder = st.empty()

while True:

    spy = analyze("SPY")

    if spy is None:

        st.error("SPY data failed")

        break

    spy_price, spy_change, _, _, _ = spy

    market = get_market(spy_change)

    results = []

    for symbol in symbols:

        data = analyze(symbol)

        if data is None:

            continue

        price, change, pullback, high, low = data

        active_mode = mode

        if mode == "AUTO":

            active_mode = "TREND" if market != "CHOPPY" else "CHOP"

        signal = trend_signal(change, pullback)

        if not signal:

            continue

        if market == "BULLISH" and "BUY" not in signal:

            continue

        if market == "BEARISH" and "SELL" not in signal:

            continue

        plan = build_plan(price, signal, high, low)

        if not plan:

            continue

        entry, stop, target, shares, risk_ps = plan

        score, grade = grade_trade(change, pullback, market, signal)

        # 🔥 ONLY SHOW GOOD TRADES

        if grade not in ["A+", "A"]:

            continue

        results.append({

            "Grade": grade,

            "Score": round(score,1),

            "Symbol": symbol,

            "Price": round(price,2),

            "20m %": round(change,3),

            "Signal": signal,

            "Entry": round(entry,2),

            "Stop": round(stop,2),

            "Target": round(target,2),

            "Shares": shares

        })

    df = pd.DataFrame(results)

    with placeholder.container():

        st.subheader("Market")

        c1, c2, c3 = st.columns(3)

        c1.metric("SPY", round(spy_price,2))

        c2.metric("20m %", round(spy_change,3))

        c3.metric("Market", market)

        st.subheader("🎯 A+ Trade Setups")

        if df.empty:

            st.warning("No A+ setups — wait.")

        else:

            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            df.index += 1

            st.dataframe(df, use_container_width=True)

            top = df.iloc[0]

            st.success(

                f"🔥 TOP TRADE: {top['Symbol']} | {top['Signal']} | "

                f"Entry {top['Entry']} → Target {top['Target']}"

            )

    if not auto_refresh:

        break

    time.sleep(30)

    st.rerun()

st.subheader("Notes")

st.text_area("Journal")
