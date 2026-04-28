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

def get_data(symbol):

    try:

        data = yf.download(

            symbol,

            period="5d",

            interval="5m",

            progress=False,

            auto_adjust=True,

            threads=False

        )

        if data is None or data.empty:

            return None

        return data

    except Exception:

        return None

if st.button("Run Scan"):

    results = []

    for symbol in symbols:

        data = get_data(symbol)

        if data is None or len(data) < 2:

            results.append({

                "Symbol": symbol,

                "Price": "-",

                "Change": "-",

                "Signal": "DATA ERROR",

                "Risk $": "-"

            })

            continue

        try:

            price = float(data["Close"].iloc[-1])

            previous_price = float(data["Close"].iloc[-2])

            change = price - previous_price

            signal = "NO TRADE"

            if change > 0:

                signal = "BUY WATCH"

            elif change < 0:

                signal = "EXIT / AVOID"

            risk_amount = account_size * (risk_percent / 100)

            results.append({

                "Symbol": symbol,

                "Price": round(price, 2),

                "Change": round(change, 2),

                "Signal": signal,

                "Risk $": round(risk_amount, 2)

            })

        except Exception:

            results.append({

                "Symbol": symbol,

                "Price": "-",

                "Change": "-",

                "Signal": "CALC ERROR",

                "Risk $": "-"

            })

    df = pd.DataFrame(results)

    st.subheader("Scan Results")

    st.dataframe(df, use_container_width=True)

st.subheader("Notes / Journal")

st.text_area("Write your thoughts here after reviewing trades")
