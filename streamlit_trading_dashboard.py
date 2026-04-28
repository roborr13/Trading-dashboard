import streamlit as st

import yfinance as yf

import pandas as pd

# --- SAFE TWILIO SETUP ---

try:

    from twilio.rest import Client

    TWILIO_READY = True

except:

    TWILIO_READY = False

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO")

st.caption("With SMS Alerts (safe mode)")

symbols = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA"]

# --- GET DATA ---

def get_data(symbol):

    try:

        data = yf.Ticker(symbol).history(period="1d", interval="5m")

        if data is None or len(data) < 5:

            return None

        return data

    except:

        return None

# --- SIGNAL LOGIC ---

def get_signal(change):

    if change >= 0.30:

        return "🚀 STRONG BUY"

    elif change >= 0.08:

        return "🟢 BUY"

    elif change <= -0.30:

        return "🔻 STRONG SELL"

    elif change <= -0.08:

        return "🔴 SELL"

    else:

        return "⚪ NO TRADE"

# --- SEND SMS ---

def send_sms(message):

    if not TWILIO_READY:

        return

    try:

        client = Client(

            st.secrets["TWILIO_ACCOUNT_SID"],

            st.secrets["TWILIO_AUTH_TOKEN"]

        )

        client.messages.create(

            body=message,

            from_=st.secrets["TWILIO_PHONE_NUMBER"],

            to=st.secrets["YOUR_PHONE_NUMBER"]

        )

    except:

        pass  # prevents crash

# --- RUN SCAN ---

if st.button("Run Scan"):

    results = []

    alerts = []

    for symbol in symbols:

        data = get_data(symbol)

        if data is None:

            continue

        price = data["Close"].iloc[-1]

        start = data["Close"].iloc[-5]

        change = ((price - start) / start) * 100

        signal = get_signal(change)

        results.append({

            "Symbol": symbol,

            "Price": round(float(price), 2),

            "20m %": round(float(change), 3),

            "Signal": signal

        })

        # --- ALERT TRIGGER ---

        if "STRONG" in signal:

            alerts.append(f"{symbol} {signal} ({round(change,2)}%)")

    df = pd.DataFrame(results)

    st.subheader("Scan Results")

    st.dataframe(df, use_container_width=True)

    # --- ALERT DISPLAY ---

    st.subheader("🚨 Alerts")

    if alerts:

        for alert in alerts:

            st.error(alert)

        # send ONE combined SMS

        send_sms(" | ".join(alerts))

    else:

        st.success("No strong alerts")

st.subheader("Notes")

st.text_area("Journal")
