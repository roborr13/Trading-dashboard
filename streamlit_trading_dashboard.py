import streamlit as st

import yfinance as yf

import pandas as pd

import time

from datetime import datetime

from twilio.rest import Client

# ========================

# TWILIO SETUP

# ========================

try:

    client = Client(

        st.secrets["TWILIO_ACCOUNT_SID"],

        st.secrets["TWILIO_AUTH_TOKEN"]

    )

    TWILIO_FROM = st.secrets["TWILIO_PHONE_NUMBER"]

    YOUR_PHONE = st.secrets["YOUR_PHONE_NUMBER"]

except:

    client = None

def send_sms(msg):

    if client:

        try:

            client.messages.create(

                body=msg,

                from_=TWILIO_FROM,

                to=YOUR_PHONE

            )

            return True

        except Exception as e:

            st.error(f"SMS Error: {e}")

    return False

# ========================

# UI

# ========================

st.title("📈 Trading Scanner PRO")

st.subheader("Stop Alert System")

# ========================

# TRADE INPUT

# ========================

symbol = st.text_input("Symbol", value="AAPL").upper()

entry = st.number_input("Entry Price", value=273.5)

stop = st.number_input("Stop Price", value=272.0)

target = st.number_input("Target Price", value=276.0)

# ========================

# STORE STATE

# ========================

if "trade_active" not in st.session_state:

    st.session_state.trade_active = False

if "alert_sent" not in st.session_state:

    st.session_state.alert_sent = False

# ========================

# START TRADE

# ========================

if st.button("Start Monitoring"):

    st.session_state.trade_active = True

    st.session_state.alert_sent = False

    st.success("Monitoring started")

# ========================

# STOP MONITOR

# ========================

if st.session_state.trade_active:

    data = yf.Ticker(symbol).history(period="1d", interval="1m")

    if not data.empty:

        price = data["Close"].iloc[-1]

        st.write(f"Current Price: {round(price,2)}")

        # STOP HIT

        if price <= stop and not st.session_state.alert_sent:

            msg = f"{symbol} STOP HIT at {round(price,2)}"

            if send_sms(msg):

                st.error(msg)

                st.session_state.alert_sent = True

        # TARGET HIT

        elif price >= target and not st.session_state.alert_sent:

            msg = f"{symbol} TARGET HIT at {round(price,2)}"

            if send_sms(msg):

                st.success(msg)

                st.session_state.alert_sent = True

        else:

            st.info("Monitoring...")

# ========================

# AUTO REFRESH

# ========================

time.sleep(60)

st.rerun()
