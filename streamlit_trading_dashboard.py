import streamlit as st

import yfinance as yf

import pandas as pd

import time

from datetime import datetime, time as dtime

from zoneinfo import ZoneInfo

from pathlib import Path

from twilio.rest import Client

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO")

st.caption("Scanner + Alerts + Paper Trading + Volume Confirmation")

LOG_FILE = Path("paper_trade_log.csv")

# ✅ BEST WATCHLIST (UPDATED)

symbols_input = st.sidebar.text_input(

    "Watchlist",

    "SPY, QQQ, AAPL, MSFT, NVDA, TSLA, AMD, META, AMZN, GOOGL, XOM"

)

symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

send_texts = st.sidebar.checkbox("Send SMS Alerts", True)

# ---------- SETTINGS ----------

st.sidebar.subheader("Risk Settings")

account_size = st.sidebar.number_input("Account Size ($)", value=1000)

risk_percent = st.sidebar.slider("Risk Per Trade (%)", 0.5, 5.0, 1.0)

st.sidebar.subheader("Trade Plan")

entry_buffer_percent = st.sidebar.slider("Entry Buffer (%)", 0.05, 1.0, 0.15)

stop_percent = st.sidebar.slider("Stop Loss (%)", 0.5, 5.0, 1.0)

reward_ratio = st.sidebar.slider("Reward Ratio", 1.0, 5.0, 2.0)

# ✅ VOLUME FILTER

st.sidebar.subheader("Volume Filter")

min_volume_ratio = st.sidebar.slider("Minimum Volume Strength", 1.0, 3.0, 1.2)

minimum_score = 40

cooldown_minutes = 15

if "last_alerts" not in st.session_state:

    st.session_state.last_alerts = {}

# ---------- MARKET ----------

def market_is_open():

    now = datetime.now(ZoneInfo("America/New_York"))

    return now.weekday() < 5 and dtime(9,30) <= now.time() <= dtime(16,0), now

# ---------- SMS ----------

def send_sms(msg):

    try:

        client = Client(

            st.secrets["TWILIO_ACCOUNT_SID"],

            st.secrets["TWILIO_AUTH_TOKEN"]

        )

        client.messages.create(

            body=msg,

            from_=st.secrets["TWILIO_PHONE_NUMBER"],

            to=st.secrets["YOUR_PHONE_NUMBER"]

        )

        return True

    except:

        return False

# ---------- DATA ----------

def get_data(symbol):

    try:

        d = yf.Ticker(symbol).history(period="1d", interval="5m")

        if d is None or len(d) < 10:

            return None

        return d

    except:

        return None

def analyze(symbol):

    d = get_data(symbol)

    if d is None:

        return None

    closes = d["Close"]

    highs = d["High"]

    lows = d["Low"]

    volumes = d["Volume"]

    price = closes.iloc[-1]

    start = closes.iloc[-5]

    prev = closes.iloc[-2]

    change = ((price - start) / start) * 100

    pullback = price < prev

    vol_now = volumes.iloc[-1]

    vol_avg = volumes.iloc[-10:-1].mean()

    vol_ratio = vol_now / vol_avg if vol_avg > 0 else 0

    return {

        "price": price,

        "change": change,

        "pullback": pullback,

        "recent_high": highs.iloc[-5:].max(),

        "recent_low": lows.iloc[-5:].min(),

        "volume_ratio": vol_ratio,

        "volume_ok": vol_ratio >= min_volume_ratio

    }

def get_market(change):

    if change >= 0.05: return "BULLISH"

    if change <= -0.05: return "BEARISH"

    return "CHOPPY"

def get_signal(change, pullback, market):

    if market == "BULLISH":

        if change >= 0.10 and pullback: return "🚀 STRONG BUY"

    if market == "BEARISH":

        if change <= -0.10 and pullback: return "🔻 STRONG SELL"

    return "⚪ NO TRADE"

def build_trade(symbol, d, signal, market):

    if not d["volume_ok"]:

        return None

    price = d["price"]

    if "BUY" in signal:

        entry = d["recent_high"] * (1 + entry_buffer_percent / 100)

        stop = price * (1 - stop_percent / 100)

        risk = entry - stop

        target = entry + risk * reward_ratio

        direction = "BUY"

    else:

        return None

    if risk <= 0:

        return None

    shares = int((account_size * (risk_percent / 100)) // risk)

    score = abs(d["change"]) * 100 + 10

    if score < minimum_score:

        return None

    return {

        "Symbol": symbol,

        "Entry": round(entry,2),

        "Stop": round(stop,2),

        "Target": round(target,2),

        "Shares": shares,

        "Score": score,

        "Volume": round(d["volume_ratio"],2)

    }

# ---------- PAPER LOG ----------

def load_log():

    if LOG_FILE.exists():

        return pd.read_csv(LOG_FILE)

    return pd.DataFrame()

def save_log(df):

    df.to_csv(LOG_FILE, index=False)

# ---------- MAIN ----------

def run():

    open_now, now = market_is_open()

    st.subheader("Market")

    st.metric("Time", now.strftime("%I:%M:%S"))

    spy = analyze("SPY")

    if not spy:

        return

    market = get_market(spy["change"])

    st.metric("Market", market)

    setups = []

    for s in symbols:

        d = analyze(s)

        if not d:

            continue

        signal = get_signal(d["change"], d["pullback"], market)

        trade = build_trade(s, d, signal, market)

        if trade:

            setups.append(trade)

    if setups:

        df = pd.DataFrame(setups).sort_values("Score", ascending=False)

        top = df.iloc[0]

        st.subheader("Top Setup")

        st.write(top)

        if open_now and send_texts:

            if send_sms(f"{top['Symbol']} BUY @ {top['Entry']}"):

                st.success("SMS sent")

    else:

        st.info("No setups")

run()

time.sleep(60)

st.rerun()
