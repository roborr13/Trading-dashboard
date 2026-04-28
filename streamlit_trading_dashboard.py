import streamlit as st

import yfinance as yf

import pandas as pd

st.set_page_config(page_title="Trading Dashboard", layout="wide")

st.title("📈 Trading Dashboard")

st.sidebar.header("Settings")

symbols_input = st.sidebar.text_input(

    "Watchlist",

    "SPY, QQQ, AAPL, MSFT, NVDA, TSLA"

)

symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

st.sidebar.subheader("Risk Settings")

account_size = st.sidebar.number_input("Account Size ($)", value=1000)

risk_percent = st.sidebar.slider("Risk per trade (%)", 0.5, 5.0, 1.0)

def get_price(symbol):

    try:

        ticker = yf.Ticker(symbol)

        price = ticker.fast_info["lastPrice"]

        return float(price)

    except:

        return None

if st.button("Run Scan"):

    results = []

    for symbol in symbols:

        price = get_price(symbol)

        if price is None:

            results.append({

                "Symbol": symbol,

                "Price": "-",

                "Change": "-",

                "Signal": "DATA ERROR",

                "Risk $": "-"

            })

            continue

        # Fake small change just to simulate signal

        change = round(price * 0.001, 2)

        signal = "BUY WATCH" if change > 0 else "EXIT"

        risk_amount = account_size * (risk_percent / 100)

        results.append({

            "Symbol": symbol,

            "Price": round(price, 2),

            "Change": change,

            "Signal": signal,

            "Risk $": round(risk_amount, 2)

        })

    df = pd.DataFrame(results)

    st.subheader("Scan Results")

    st.dataframe(df, use_container_width=True)

st.subheader("Notes / Journal")

st.text_area("Write your thoughts here after reviewing trades")
