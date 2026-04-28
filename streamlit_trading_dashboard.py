import streamlit as st

import yfinance as yf

import pandas as pd

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO")

st.caption("Ranks only market-aligned trade setups. No real trades are placed.")

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

def get_data(symbol):

    try:

        data = yf.Ticker(symbol).history(period="1d", interval="5m")

        if data is None or len(data) < 4:

            return None

        return data

    except Exception:

        return None

def get_20m_change(symbol):

    data = get_data(symbol)

    if data is None:

        return None, None

    price = data["Close"].iloc[-1]

    start = data["Close"].iloc[-4]

    change_pct = ((price - start) / start) * 100

    return float(price), float(change_pct)

def get_market_direction(spy_change):

    if spy_change is None:

        return "UNKNOWN"

    if spy_change >= 0.05:

        return "BULLISH"

    elif spy_change <= -0.05:

        return "BEARISH"

    else:

        return "CHOPPY"

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

def get_score(change, signal, market):

    strength = abs(change)

    score = 0

    if "STRONG" in signal:

        score += 60

    elif "BUY" in signal or "SELL" in signal:

        score += 40

    score += min(strength * 200, 40)

    if market == "BULLISH" and "BUY" in signal:

        score += 10

    elif market == "BEARISH" and "SELL" in signal:

        score += 10

    return round(min(score, 100), 1)

if st.button("Run Scan"):

    spy_price, spy_change = get_20m_change("SPY")

    market = get_market_direction(spy_change)

    st.subheader("Market Direction")

    c1, c2, c3 = st.columns(3)

    c1.metric("SPY Price", "-" if spy_price is None else round(spy_price, 2))

    c2.metric("SPY 20m %", "-" if spy_change is None else round(spy_change, 3))

    c3.metric("Market", market)

    results = []

    for symbol in symbols:

        price, change = get_20m_change(symbol)

        if price is None or change is None:

            continue

        signal = get_signal(change)

        if market == "BULLISH" and "BUY" not in signal:

            continue

        if market == "BEARISH" and "SELL" not in signal:

            continue

        if market == "CHOPPY":

            continue

        if signal == "⚪ NO TRADE":

            continue

        risk_amount = account_size * (risk_percent / 100)

        stop = price * (1 - stop_loss_percent / 100)

        target = price * (1 + target_percent / 100)

        score = get_score(change, signal, market)

        results.append({

            "Rank Score": score,

            "Symbol": symbol,

            "Price": round(price, 2),

            "20m %": round(change, 3),

            "Signal": signal,

            "Stop": round(stop, 2),

            "Target": round(target, 2),

            "Risk $": round(risk_amount, 2)

        })

    df = pd.DataFrame(results)

    st.subheader("🎯 Ranked Trade Setups")

    if df.empty:

        st.warning("No valid ranked trades right now. Sit out.")

    else:

        df = df.sort_values(by="Rank Score", ascending=False).reset_index(drop=True)

        df.index = df.index + 1

        st.dataframe(df, use_container_width=True)

        best = df.iloc[0]

        st.success(

            f"Top setup: {best['Symbol']} | {best['Signal']} | Score: {best['Rank Score']}"

        )

st.subheader("Notes / Journal")

st.text_area("Write your thoughts here")
