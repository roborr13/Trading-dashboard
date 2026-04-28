import streamlit as st

import yfinance as yf

import pandas as pd

# --- TWILIO ---

from twilio.rest import Client

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO")

st.caption("SMS Debug Mode")

symbols = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA"]

# --- TEST SMS BUTTON ---

st.subheader("🧪 SMS Test")

if st.button("Send Test SMS"):

    try:

        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]

        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]

        from_number = st.secrets["TWILIO_PHONE_NUMBER"]

        to_number = st.secrets["YOUR_PHONE_NUMBER"]

        client = Client(account_sid, auth_token)

        message = client.messages.create(

            body="🚀 TEST MESSAGE from your Trading App",

            from_=from_number,

            to=to_number

        )

        st.success(f"Message sent! SID: {message.sid}")

    except Exception as e:

        st.error(f"Twilio Error: {e}")

# --- BASIC SCANNER (unchanged) ---

def get_data(symbol):

    try:

        data = yf.Ticker(symbol).history(period="1d", interval="5m")

        if data is None or len(data) < 5:

            return None

        return data

    except:

        return None

if st.button("Run Scan"):

    results = []

    for symbol in symbols:

        data = get_data(symbol)

        if data is None:

            continue

        price = data["Close"].iloc[-1]

        start = data["Close"].iloc[-5]

        change = ((price - start) / start) * 100

        if change >= 0.30:

            signal = "🚀 STRONG BUY"

        elif change >= 0.08:

            signal = "🟢 BUY"

        elif change <= -0.30:

            signal = "🔻 STRONG SELL"

        elif change <= -0.08:

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
