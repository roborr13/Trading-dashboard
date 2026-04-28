import streamlit as st

import yfinance as yf

import pandas as pd

import time

from twilio.rest import Client

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO — Final Version")

st.caption("Paper trading only. Sends SMS alerts for high-quality setups.")

# ---------- SETTINGS ----------

st.sidebar.header("Scanner Settings")

symbols_input = st.sidebar.text_input(

    "Watchlist",

    "SPY, QQQ, AAPL, MSFT, NVDA, TSLA"

)

symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

auto_refresh = st.sidebar.checkbox("Auto Refresh Every 60s", False)

send_texts = st.sidebar.checkbox("Send SMS Alerts", True)

st.sidebar.subheader("Risk Settings")

account_size = st.sidebar.number_input("Account Size ($)", value=1000)

risk_percent = st.sidebar.slider("Risk Per Trade (%)", 0.5, 5.0, 1.0)

st.sidebar.subheader("Trade Plan")

entry_buffer_percent = st.sidebar.slider("Entry Buffer (%)", 0.05, 1.0, 0.15)

stop_percent = st.sidebar.slider("Stop Loss (%)", 0.5, 5.0, 1.0)

reward_ratio = st.sidebar.slider("Reward Ratio", 1.0, 5.0, 2.0)

st.sidebar.subheader("Alert Settings")

minimum_score = st.sidebar.slider("Minimum Alert Score", 20, 100, 30)

cooldown_minutes = st.sidebar.slider("Alert Cooldown Minutes", 5, 60, 15)

# ---------- SESSION STATE ----------

if "last_alerts" not in st.session_state:

    st.session_state.last_alerts = {}

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

        st.warning(f"SMS failed: {e}")

        return False

# ---------- DATA ----------

def get_data(symbol):

    try:

        data = yf.Ticker(symbol).history(period="1d", interval="5m")

        if data is None or len(data) < 6:

            return None

        return data

    except Exception:

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

    recent_high = highs.iloc[-5:].max()

    recent_low = lows.iloc[-5:].min()

    return {

        "price": float(price),

        "change": float(change),

        "pullback": bool(pullback),

        "recent_high": float(recent_high),

        "recent_low": float(recent_low),

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

# ---------- TRADE PLAN ----------

def build_trade_plan(symbol, price, signal, recent_high, recent_low, change, pullback, market):

    max_risk = account_size * (risk_percent / 100)

    if "BUY" in signal:

        entry = recent_high * (1 + entry_buffer_percent / 100)

        stop = price * (1 - stop_percent / 100)

        risk_per_share = entry - stop

        target = entry + (risk_per_share * reward_ratio)

    elif "SELL" in signal:

        entry = recent_low * (1 - entry_buffer_percent / 100)

        stop = price * (1 + stop_percent / 100)

        risk_per_share = stop - entry

        target = entry - (risk_per_share * reward_ratio)

    else:

        return None

    if risk_per_share <= 0:

        return None

    shares = int(max_risk // risk_per_share)

    score = abs(change) * 100

    if pullback:

        score += 10

    if "STRONG" in signal:

        score += 10

    if market == "BULLISH" and "BUY" in signal:

        score += 10

    if market == "BEARISH" and "SELL" in signal:

        score += 10

    if score >= 40:

        grade = "A+"

    elif score >= 30:

        grade = "A"

    elif score >= 20:

        grade = "B"

    else:

        grade = "C"

    return {

        "Grade": grade,

        "Score": round(score, 1),

        "Symbol": symbol,

        "Price": round(price, 2),

        "20m %": round(change, 3),

        "Signal": signal,

        "Entry": round(entry, 2),

        "Stop": round(stop, 2),

        "Target": round(target, 2),

        "Shares": shares,

        "Max Risk $": round(shares * risk_per_share, 2)

    }

# ---------- ALERT CONTROL ----------

def can_alert(symbol, signal):

    now = time.time()

    key = f"{symbol}-{signal}"

    last_time = st.session_state.last_alerts.get(key)

    if last_time is None:

        st.session_state.last_alerts[key] = now

        return True

    cooldown_seconds = cooldown_minutes * 60

    if now - last_time >= cooldown_seconds:

        st.session_state.last_alerts[key] = now

        return True

    return False

# ---------- SCAN ----------

def run_scan():

    spy = analyze("SPY")

    if spy is None:

        return None, None, pd.DataFrame()

    market = get_market(spy["change"])

    results = []

    for symbol in symbols:

        data = analyze(symbol)

        if data is None:

            continue

        signal = get_signal(

            data["change"],

            data["pullback"],

            market

        )

        if signal == "⚪ NO TRADE":

            continue

        plan = build_trade_plan(

            symbol,

            data["price"],

            signal,

            data["recent_high"],

            data["recent_low"],

            data["change"],

            data["pullback"],

            market

        )

        if plan is None:

            continue

        if plan["Score"] < minimum_score:

            continue

        results.append(plan)

    df = pd.DataFrame(results)

    if not df.empty:

        df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

        df.index = df.index + 1

    return spy, market, df

# ---------- DISPLAY ----------

def display_app():

    spy, market, df = run_scan()

    if spy is None:

        st.error("Could not load SPY data.")

        return

    st.subheader("Market Direction")

    c1, c2, c3 = st.columns(3)

    c1.metric("SPY Price", round(spy["price"], 2))

    c2.metric("SPY 20m %", round(spy["change"], 3))

    c3.metric("Market", market)

    st.subheader("🚨 Trade Alerts")

    if df.empty:

        st.info("No qualified setups right now. Sit out.")

    else:

        top = df.iloc[0]

        alert_message = (

            f"TRADE ALERT: {top['Symbol']} {top['Signal']} | "

            f"Grade {top['Grade']} | Score {top['Score']} | "

            f"Entry {top['Entry']} | Stop {top['Stop']} | "

            f"Target {top['Target']} | Shares {top['Shares']}"

        )

        st.error(f"Top Setup: {top['Symbol']} | {top['Grade']} | {top['Signal']}")

        st.success(

            f"Entry: {top['Entry']} | Stop: {top['Stop']} | "

            f"Target: {top['Target']} | Shares: {top['Shares']}"

        )

        if send_texts and can_alert(top["Symbol"], top["Signal"]):

            if send_sms(alert_message):

                st.success("SMS alert sent.")

        st.subheader("🎯 Ranked Setups")

        st.dataframe(df, use_container_width=True)

    st.subheader("Notes / Journal")

    st.text_area("Journal")

# ---------- RUN ----------

display_app()

if auto_refresh:

    time.sleep(60)

    st.rerun()
