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

st.sidebar.subheader("Trade Settings")

stop_loss_percent = st.sidebar.slider("Stop loss (%)", 0.5, 5.0, 1.0)

target_percent = st.sidebar.slider("Target (%)", 0.5, 10.0, 2.0)

def get_market_data(symbol):

    try:

        ticker = yf.Ticker(symbol)

        info = ticker.fast_info

        price = float(info["lastPrice"])

        previous_close = float(info["previousClose"])

        if price <= 0 or previous_close <= 0:

            return None

        dollar_change = price - previous_close

        percent_change = (dollar_change / previous_close) * 100

        return {

            "price": price,

            "previous_close": previous_close,

            "dollar_change": dollar_change,

            "percent_change": percent_change

        }

    except Exception:

        return None

def get_signal(percent_change):

    if percent_change >= 1.0:

        return "STRONG BUY WATCH"

    elif percent_change >= 0.25:

        return "BUY WATCH"

    elif percent_change <= -1.0:

        return "STRONG EXIT / AVOID"

    elif percent_change <= -0.25:

        return "EXIT / AVOID"

    else:

        return "NO TRADE"

if st.button("Run Scan"):

    results = []

    for symbol in symbols:

        data = get_market_data(symbol)

        if data is None:

            results.append({

                "Symbol": symbol,

                "Price": "-",

                "Prev Close": "-",

                "$ Change": "-",

                "% Change": "-",

                "Signal": "DATA ERROR",

                "Stop Loss": "-",

                "Target": "-",

                "Risk $": "-"

            })

            continue

        price = data["price"]

        previous_close = data["previous_close"]

        dollar_change = data["dollar_change"]

        percent_change = data["percent_change"]

        signal = get_signal(percent_change)

        risk_amount = account_size * (risk_percent / 100)

        stop_loss = price * (1 - stop_loss_percent / 100)

        target = price * (1 + target_percent / 100)

        results.append({

            "Symbol": symbol,

            "Price": round(price, 2),

            "Prev Close": round(previous_close, 2),

            "$ Change": round(dollar_change, 2),

            "% Change": round(percent_change, 2),

            "Signal": signal,

            "Stop Loss": round(stop_loss, 2),

            "Target": round(target, 2),

            "Risk $": round(risk_amount, 2)

        })

    df = pd.DataFrame(results)

    st.subheader("Scan Results")

    st.dataframe(df, use_container_width=True)

st.subheader("Notes / Journal")

st.text_area("Write your thoughts here after reviewing trades")
