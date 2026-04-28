import streamlit as st

import yfinance as yf

import pandas as pd

st.set_page_config(page_title="Trading Dashboard", layout="wide")

st.title("📈 Trading Dashboard")

# Sidebar settings

st.sidebar.header("Settings")

symbols_input = st.sidebar.text_input("Watchlist (comma separated)", "SPY,QQQ,AAPL,MSFT,NVDA,TSLA")

symbols = [s.strip().upper() for s in symbols_input.split(",")]

st.sidebar.subheader("Risk Settings")

account_size = st.sidebar.number_input("Account Size ($)", value=1000)

risk_percent = st.sidebar.slider("Risk per trade (%)", 0.5, 5.0, 1.0)

# Function to get data

@st.cache_data

def get_data(symbol):

    data = yf.download(symbol, period="1d", interval="5m")

    return data

# Scan button

if st.button("Run Scan"):

    results = []

    for symbol in symbols:

        try:

            data = get_data(symbol)

            if data.empty:

                continue

            latest = data.iloc[-1]

            prev = data.iloc[-2]

            price = latest["Close"]

            prev_price = prev["Close"]

            change = price - prev_price

            signal = "NO TRADE"

            if change > 0.3:

                signal = "BUY WATCH"

            elif change < -0.3:

                signal = "EXIT"

            risk_amount = account_size * (risk_percent / 100)

            results.append({

                "Symbol": symbol,

                "Price": round(price, 2),

                "Change": round(change, 2),

                "Signal": signal,

                "Risk $": round(risk_amount, 2)

            })

        except Exception as e:

            results.append({

                "Symbol": symbol,

                "Price": "-",

                "Change": "-",

                "Signal": "ERROR",

                "Risk $": "-"

            })

    df = pd.DataFrame(results)

    st.subheader("Scan Results")

    st.dataframe(df, use_container_width=True)

# Simple journal placeholder

st.subheader("Notes / Journal")

notes = st.text_area("Write your thoughts here after reviewing trades")
