import streamlit as st

import yfinance as yf

import pandas as pd

# ---- SAFE TWILIO IMPORT ----

try:

    from twilio.rest import Client

    TWILIO_ENABLED = True

except:

    TWILIO_ENABLED = False

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO (Alerts Safe Mode)")

# ---- SETTINGS ----

symbols = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA"]

account_size = 1000

risk_percent = 1

# ---- DATA ----

def get_data(symbol):

    try:

        data = yf.download(symbol, period="1d", interval="5m")

        if data is None or data.empty:

            return None

        return data

    except:

        return None

# ---- SIGNAL ----

def get_signal(change):

    if change > 0.2:

        return "🚀 STRONG BUY"

    elif change > 0.05:

        return "🟢 BUY"

    elif change < -0.2:

        return "🔻 STRONG SELL"

    elif change < -0.05:

        return "🔴 SELL"

    else:

        return "⚪ NO TRADE"

# ---- SMS FUNCTION (SAFE) ----

def send_sms(message):

    if not TWILIO_ENABLED:

        return

    try:

        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]

        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]

        from_number = st.secrets["TWILIO_PHONE_NUMBER"]

        to_number = st.secrets["YOUR_PHONE_NUMBER"]

        client = Client(account_sid, auth_token)

        client.messages.create(

            body=message,

            from_=from_number,

            to=to_number

        )

    except:

        pass  # NEVER crash app

# ---- RUN ----

if st.button("Run Scan"):

    results = []

    alerts = []

    for symbol in symbols:

        data = get_data(symbol)

        if data is None or len(data) < 5:

            continue

        price = data["Close"].iloc[-1]

        old_price = data["Close"].iloc[-5]

        change_pct = ((price - old_price) / old_price) * 100

        signal = get_signal(change_pct)

        score = abs(change_pct) * 100

        results.append({

            "Score": round(score, 1),

            "Symbol": symbol,

            "Price": round(float(price), 2),

            "5m %": round(change_pct, 3),

            "Signal": signal

        })

        # ---- ALERT TRIGGER ----

        if "STRONG" in signal:

            alerts.append(f"{symbol} {signal} ({round(change_pct,2)}%)")

    df = pd.DataFrame(results).sort_values(by="Score", ascending=False)

    st.subheader("📊 Trade Opportunities")

    st.dataframe(df, use_container_width=True)

    # ---- ALERT DISPLAY ----

    st.subheader("🚨 Alerts")

    if alerts:

        for alert in alerts:

            st.error(alert)

        # send ONE SMS (not spam)

        send_sms(" | ".join(alerts))

    else:

        st.success("No strong alerts")
