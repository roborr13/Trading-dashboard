import streamlit as st

import yfinance as yf

import pandas as pd

import time

st.set_page_config(page_title="Trading Dashboard", layout="wide")

st.title("📈 Trading Dashboard (LIVE)")

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

auto_refresh = st.sidebar.checkbox("Auto Refresh (every 60s)", value=True)

def get_intraday_data(symbol):

    try:

        ticker = yf.Ticker(symbol)

        data = ticker.history(period="1d", interval="5m")

        if data is None or len(data) < 4:

            return None

        return data

    except Exception:

        return None

def get_signal(change_percent):

    if change_percent >= 0.10:

        return "🚀 STRONG BUY"

    elif change_percent >= 0.03:

        return "🟢 BUY"

    elif change_percent <= -0.10:

        return "🔻 STRONG SELL"

    elif change_percent <= -0.03:

        return "🔴 SELL"

    else:

        return "⚪ NO TRADE"

def run_scan():

    results = []

    for symbol in symbols:

        data = get_intraday_data(symbol)

        if data is None:

            results.append({

                "Symbol": symbol,

                "Price": "-",

                "20m Change %": "-",

                "Signal": "DATA ERROR",

                "Stop Loss": "-",

                "Target": "-",

                "Risk $": "-"

            })

            continue

        price = data["Close"].iloc[-1]

        recent = data["Close"].iloc[-4:]

        start_price = recent.iloc[0]

        end_price = recent.iloc[-1]

        change = end_price - start_price

        change_percent = (change / start_price) * 100

        signal = get_signal(change_percent)

        risk_amount = account_size * (risk_percent / 100)

        stop_loss = price * (1 - stop_loss_percent / 100)

        target = price * (1 + target_percent / 100)

        results.append({

            "Symbol": symbol,

            "Price": round(float(price), 2),

            "20m Change %": round(float(change_percent), 3),

            "Signal": signal,

            "Stop Loss": round(float(stop_loss), 2),

            "Target": round(float(target), 2),

            "Risk $": round(float(risk_amount), 2)

        })

    return pd.DataFrame(results)

placeholder = st.empty()

while True:

    df = run_scan()

    with placeholder.container():

        st.subheader("Scan Results (20-Min Momentum)")

        st.dataframe(df, use_container_width=True)

        st.subheader("Notes / Journal")

        st.text_area("Write your thoughts here after reviewing trades")

    if not auto_refresh:

        break

    time.sleep(60)

    st.rerun()
