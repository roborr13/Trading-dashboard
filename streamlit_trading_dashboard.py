import streamlit as st

import yfinance as yf

import pandas as pd

st.set_page_config(page_title="Trading Scanner", layout="wide")

st.title("📈 Trading Scanner")

st.caption("Safe reset version — no SMS yet.")

symbols = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA"]

def get_data(symbol):

    try:

        data = yf.Ticker(symbol).history(period="1d", interval="5m")

        if data is None or len(data) < 5:

            return None

        return data

    except Exception:

        return None

if st.button("Run Scan"):

    results = []

    for symbol in symbols:

        data = get_data(symbol)

        if data is None:

            results.append({

                "Symbol": symbol,

                "Price": "-",

                "20m %": "-",

                "Signal": "DATA ERROR"

            })

            continue

        price = data["Close"].iloc[-1]

        start = data["Close"].iloc[-5]

        change = ((price - start) / start) * 100

        if change >= 0.10:

            signal = "🚀 STRONG BUY"

        elif change >= 0.03:

            signal = "🟢 BUY"

        elif change <= -0.10:

            signal = "🔻 STRONG SELL"

        elif change <= -0.03:

            signal = "🔴 SELL"

        else:

            signal = "⚪ NO TRADE"

        results.append({

            "Symbol": symbol,

            "Price": round(float(price), 2),

            "20m %": round(float(change), 3),

            "Signal": signal

        })

    df = pd.DataFrame(results)

    st.subheader("Scan Results")

    st.dataframe(df, use_container_width=True)

st.subheader("Notes")

st.text_area("Journal")
