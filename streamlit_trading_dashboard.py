import streamlit as st

import yfinance as yf

import pandas as pd

st.set_page_config(page_title="Trading Scanner", layout="wide")

st.title("📈 Trading Scanner — Next Level")

st.caption("Paper-trading scanner only. No real trades are placed.")

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

def get_intraday_data(symbol):

    try:

        ticker = yf.Ticker(symbol)

        data = ticker.history(period="1d", interval="5m")

        if data is None or len(data) < 4:

            return None

        return data

    except Exception:

        return None

def get_20m_change(symbol):

    data = get_intraday_data(symbol)

    if data is None:

        return None, None

    price = data["Close"].iloc[-1]

    recent = data["Close"].iloc[-4:]

    start_price = recent.iloc[0]

    end_price = recent.iloc[-1]

    change_percent = ((end_price - start_price) / start_price) * 100

    return float(price), float(change_percent)

def market_direction(spy_change):

    if spy_change is None:

        return "UNKNOWN"

    if spy_change >= 0.05:

        return "BULLISH"

    elif spy_change <= -0.05:

        return "BEARISH"

    else:

        return "CHOPPY"

def get_signal(change_percent, market):

    confidence = 0

    if change_percent >= 0.10:

        signal = "🚀 STRONG BUY"

        confidence = 85

    elif change_percent >= 0.03:

        signal = "🟢 BUY"

        confidence = 65

    elif change_percent <= -0.10:

        signal = "🔻 STRONG SELL"

        confidence = 85

    elif change_percent <= -0.03:

        signal = "🔴 SELL"

        confidence = 65

    else:

        signal = "⚪ NO TRADE"

        confidence = 25

    if market == "BULLISH" and "BUY" in signal:

        confidence += 10

    elif market == "BEARISH" and "SELL" in signal:

        confidence += 10

    elif market == "BULLISH" and "SELL" in signal:

        confidence -= 20

    elif market == "BEARISH" and "BUY" in signal:

        confidence -= 20

    confidence = max(0, min(confidence, 100))

    if confidence >= 80 and signal != "⚪ NO TRADE":

        quality = "A SETUP"

    elif confidence >= 60 and signal != "⚪ NO TRADE":

        quality = "B SETUP"

    else:

        quality = "PASS"

    return signal, confidence, quality

if st.button("Run Scan"):

    spy_price, spy_change = get_20m_change("SPY")

    market = market_direction(spy_change)

    st.subheader("Market Direction")

    c1, c2, c3 = st.columns(3)

    c1.metric("SPY Price", "-" if spy_price is None else round(spy_price, 2))

    c2.metric("SPY 20m Change %", "-" if spy_change is None else round(spy_change, 3))

    c3.metric("Market", market)

    results = []

    for symbol in symbols:

        price, change_percent = get_20m_change(symbol)

        if price is None or change_percent is None:

            results.append({

                "Symbol": symbol,

                "Price": "-",

                "20m Change %": "-",

                "Signal": "DATA ERROR",

                "Confidence": "-",

                "Quality": "-",

                "Stop Loss": "-",

                "Target": "-",

                "Risk $": "-"

            })

            continue

        signal, confidence, quality = get_signal(change_percent, market)

        risk_amount = account_size * (risk_percent / 100)

        stop_loss = price * (1 - stop_loss_percent / 100)

        target = price * (1 + target_percent / 100)

        results.append({

            "Symbol": symbol,

            "Price": round(price, 2),

            "20m Change %": round(change_percent, 3),

            "Signal": signal,

            "Confidence": confidence,

            "Quality": quality,

            "Stop Loss": round(stop_loss, 2),

            "Target": round(target, 2),

            "Risk $": round(risk_amount, 2)

        })

    df = pd.DataFrame(results)

    st.subheader("Scanner Results")

    st.dataframe(df, use_container_width=True)

    st.subheader("Best Setups")

    best = df[df["Quality"].isin(["A SETUP", "B SETUP"])]

    if best.empty:

        st.info("No clean setups right now. That is a valid trading signal: wait.")

    else:

        st.dataframe(best, use_container_width=True)

st.subheader("Notes / Journal")

st.text_area("Write your thoughts here after reviewing trades")
