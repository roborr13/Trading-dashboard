import streamlit as st

import yfinance as yf

import pandas as pd

from twilio.rest import Client

# -------------------------

# 🔑 TWILIO SETTINGS (FILL THESE)

# -------------------------

ACCOUNT_SID = "PASTE_YOUR_SID"

AUTH_TOKEN = "PASTE_YOUR_TOKEN"

TWILIO_NUMBER = "+1XXXXXXXXXX"

YOUR_NUMBER = "+1XXXXXXXXXX"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# -------------------------

# APP CONFIG

# -------------------------

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO (LIVE SMS ALERTS)")

symbols = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA"]

# -------------------------

# GET DATA

# -------------------------

def get_data(symbol):

    try:

        data = yf.download(symbol, period="1d", interval="5m")

        if data is None or data.empty:

            return None

        return data

    except:

        return None

# -------------------------

# SEND SMS

# -------------------------

def send_sms(message):

    try:

        client.messages.create(

            body=message,

            from_=TWILIO_NUMBER,

            to=YOUR_NUMBER

        )

    except Exception as e:

        st.error(f"SMS failed: {e}")

# -------------------------

# RUN SCAN

# -------------------------

if st.button("Run Scan"):

    results = []

    alerts = []

    for symbol in symbols:

        data = get_data(symbol)

        if data is None or len(data) < 5:

            continue

        price = float(data["Close"].iloc[-1])

        prev = float(data["Close"].iloc[-5])

        change_pct = ((price - prev) / prev) * 100

        signal = "NO TRADE"

        # STRONG SIGNALS

        if change_pct > 0.3:

            signal = "🚀 STRONG BUY"

        elif change_pct < -0.3:

            signal = "🔻 STRONG SELL"

        elif change_pct > 0.1:

            signal = "BUY"

        elif change_pct < -0.1:

            signal = "SELL"

        score = abs(change_pct) * 100

        results.append({

            "Score": round(score, 1),

            "Symbol": symbol,

            "Price": round(price, 2),

            "5m %": round(change_pct, 3),

            "Signal": signal

        })

        # ALERT CONDITION

        if "STRONG" in signal:

            alerts.append((symbol, signal, price, change_pct))

    df = pd.DataFrame(results).sort_values(by="Score", ascending=False)

    st.subheader("📊 Trade Opportunities")

    st.dataframe(df, use_container_width=True)

    # -------------------------

    # 🚨 SEND ALERTS

    # -------------------------

    for symbol, signal, price, change in alerts:

        msg = f"{symbol} | {signal} | Price: {round(price,2)} | Move: {round(change,2)}%"

        st.warning(f"🚨 ALERT: {msg}")

        send_sms(msg)

    if not alerts:

        st.info("No strong alerts right now.")
