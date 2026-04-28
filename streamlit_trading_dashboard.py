import streamlit as st

import yfinance as yf

import pandas as pd

import time

from datetime import datetime, time as dtime

from zoneinfo import ZoneInfo

from twilio.rest import Client

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO")

st.caption("Auto mode ON. Refreshes every 60 seconds.")

# ---------- SETTINGS ----------

st.sidebar.header("Scanner Settings")

symbols_input = st.sidebar.text_input(

    "Watchlist",

    "SPY, QQQ, AAPL, MSFT, NVDA, TSLA"

)

symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

send_texts = st.sidebar.checkbox("Send SMS Alerts", True)

st.sidebar.subheader("Risk Settings")

account_size = st.sidebar.number_input("Account Size ($)", value=1000)

risk_percent = st.sidebar.slider("Risk Per Trade (%)", 0.5, 5.0, 1.0)

st.sidebar.subheader("Trade Plan")

entry_buffer_percent = st.sidebar.slider("Entry Buffer (%)", 0.05, 1.0, 0.15)

stop_percent = st.sidebar.slider("Stop Loss (%)", 0.5, 5.0, 1.0)

reward_ratio = st.sidebar.slider("Reward Ratio", 1.0, 5.0, 2.0)

minimum_score = 40

cooldown_minutes = 15

# ---------- STATE ----------

if "last_alerts" not in st.session_state:

    st.session_state.last_alerts = {}

# ---------- MARKET HOURS ----------

def market_is_open():

    now = datetime.now(ZoneInfo("America/New_York"))

    market_open = dtime(9, 30)

    market_close = dtime(16, 0)

    is_weekday = now.weekday() < 5

    is_open_time = market_open <= now.time() <= market_close

    return is_weekday and is_open_time, now

# ---------- SMS ----------

def send_sms(message):

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

        return True

    except Exception as e:

        st.error(f"SMS error: {e}")

        return False

# ---------- DATA ----------

def get_data(symbol):

    try:

        data = yf.Ticker(symbol).history(period="1d", interval="5m")

        if data is None or len(data) < 6:

            return None

        return data

    except:

        return None

def analyze(symbol):

    data = get_data(symbol)

    if data is None:

        return None

    closes = data["Close"]

    highs = data["High"]

    lows = data["Low"]

    price = closes.iloc[-1]

    start = closes.iloc[-5]

    prev = closes.iloc[-2]

    change = ((price - start) / start) * 100

    pullback = price < prev

    return {

        "price": price,

        "change": change,

        "pullback": pullback,

        "recent_high": highs.iloc[-5:].max(),

        "recent_low": lows.iloc[-5:].min(),

    }

# ---------- MARKET ----------

def get_market(change):

    if change >= 0.05:

        return "BULLISH"

    elif change <= -0.05:

        return "BEARISH"

    return "CHOPPY"

# ---------- SIGNAL ----------

def get_signal(change, pullback, market):

    if market == "BULLISH":

        if change >= 0.10 and pullback:

            return "🚀 STRONG BUY"

        elif change >= 0.05 and pullback:

            return "🟢 BUY"

    elif market == "BEARISH":

        if change <= -0.10 and pullback:

            return "🔻 STRONG SELL"

        elif change <= -0.05 and pullback:

            return "🔴 SELL"

    elif market == "CHOPPY":

        if change >= 0.20:

            return "🔻 FADE SELL"

        elif change <= -0.20:

            return "🚀 FADE BUY"

    return "⚪ NO TRADE"

# ---------- TRADE ----------

def build_trade(symbol, data, signal, market):

    price = data["price"]

    if "BUY" in signal:

        entry = data["recent_high"] * (1 + entry_buffer_percent / 100)

        stop = price * (1 - stop_percent / 100)

        risk = entry - stop

        target = entry + (risk * reward_ratio)

    elif "SELL" in signal:

        entry = data["recent_low"] * (1 - entry_buffer_percent / 100)

        stop = price * (1 + stop_percent / 100)

        risk = stop - entry

        target = entry - (risk * reward_ratio)

    else:

        return None

    if risk <= 0:

        return None

    shares = int((account_size * (risk_percent / 100)) // risk)

    score = abs(data["change"]) * 100

    if data["pullback"]:

        score += 10

    if "STRONG" in signal:

        score += 10

    if market == "BULLISH" and "BUY" in signal:

        score += 10

    if market == "BEARISH" and "SELL" in signal:

        score += 10

    if score < minimum_score:

        return None

    grade = "A+" if score >= 40 else "A"

    return {

        "Symbol": symbol,

        "Signal": signal,

        "Score": round(score, 1),

        "Grade": grade,

        "Entry": round(entry, 2),

        "Stop": round(stop, 2),

        "Target": round(target, 2),

        "Shares": shares

    }

# ---------- ALERT CONTROL ----------

def can_alert(symbol, signal):

    key = f"{symbol}-{signal}"

    now = time.time()

    last = st.session_state.last_alerts.get(key)

    if last is None or (now - last > cooldown_minutes * 60):

        st.session_state.last_alerts[key] = now

        return True

    return False

# ---------- RUN ----------

def run():

    open_now, now_et = market_is_open()

    st.subheader("Market Hours")

    st.metric("Current ET Time", now_et.strftime("%I:%M %p"))

    if open_now:

        st.success("Market OPEN — alerts enabled")

    else:

        st.warning("After hours — monitoring only (no alerts)")

    spy = analyze("SPY")

    if spy is None:

        st.error("SPY failed")

        return

    market = get_market(spy["change"])

    st.subheader("Market")

    st.metric("SPY", round(spy["price"], 2))

    st.metric("20m %", round(spy["change"], 3))

    st.metric("Market", market)

    setups = []

    for s in symbols:

        d = analyze(s)

        if d is None:

            continue

        signal = get_signal(d["change"], d["pullback"], market)

        trade = build_trade(s, d, signal, market)

        if trade:

            setups.append(trade)

    if not setups:

        st.info("No setups")

    else:

        df = pd.DataFrame(setups).sort_values("Score", ascending=False)

        top = df.iloc[0]

        st.subheader("🚨 Top Setup")

        st.error(f"{top['Symbol']} | {top['Grade']} | {top['Signal']}")

        st.success(f"Entry {top['Entry']} | Stop {top['Stop']} | Target {top['Target']}")

        if not open_now:

            st.warning("After hours — SMS blocked")

        elif "STRONG" not in top["Signal"]:

            st.warning("Not strong enough — no SMS")

        elif send_texts and can_alert(top["Symbol"], top["Signal"]):

            msg = f"{top['Symbol']} {top['Signal']} | Entry {top['Entry']} Stop {top['Stop']} Target {top['Target']}"

            if send_sms(msg):

                st.success("SMS sent")

        st.subheader("Ranked")

        st.dataframe(df)

run()

time.sleep(60)

st.rerun()
