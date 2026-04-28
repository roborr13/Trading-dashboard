import streamlit as st

import yfinance as yf

import pandas as pd

import time

from twilio.rest import Client

st.set_page_config(page_title="Trading Scanner PRO", layout="wide")

st.title("📈 Trading Scanner PRO")

st.caption("Paper trading only — no real trades are placed.")

# ---------- TWILIO SAFE SETUP ----------

def send_sms(message):

    try:

        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]

        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]

        twilio_number = st.secrets["TWILIO_PHONE_NUMBER"]

        your_number = st.secrets["YOUR_PHONE_NUMBER"]

        client = Client(account_sid, auth_token)

        client.messages.create(

            body=message,

            from_=twilio_number,

            to=your_number

        )

        return True

    except Exception as e:

        st.warning(f"SMS not sent: {e}")

        return False

# ---------- SETTINGS ----------

st.sidebar.header("Settings")

symbols_input = st.sidebar.text_input(

    "Watchlist",

    "SPY, QQQ, AAPL, MSFT, NVDA, TSLA"

)

symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

mode = st.sidebar.selectbox("Mode", ["AUTO", "TREND", "CHOP"])

auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", True)

send_texts = st.sidebar.checkbox("Send SMS Alerts", False)

alert_grade = st.sidebar.selectbox("Alert Minimum Grade", ["A+", "A"])

st.sidebar.subheader("Risk")

account_size = st.sidebar.number_input("Account Size ($)", value=1000)

risk_percent = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

st.sidebar.subheader("Trade Plan")

entry_buffer_percent = st.sidebar.slider("Entry Buffer (%)", 0.05, 1.0, 0.15)

entry_trigger_buffer = st.sidebar.slider("Entry Trigger Distance (%)", 0.05, 1.0, 0.2)

stop_percent = st.sidebar.slider("Stop Loss (%)", 0.5, 5.0, 1.0)

reward_ratio = st.sidebar.slider("Reward Ratio", 1.0, 5.0, 2.0)

if "last_alert" not in st.session_state:

    st.session_state.last_alert = None

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

    return price, change, pullback, recent_high, recent_low

# ---------- MARKET ----------

def get_market(change):

    if change >= 0.05:

        return "BULLISH"

    elif change <= -0.05:

        return "BEARISH"

    return "CHOPPY"

# ---------- SIGNALS ----------

def trend_signal(change, pullback):

    if change >= 0.10 and pullback:

        return "🚀 STRONG BUY"

    elif change >= 0.05 and pullback:

        return "🟢 BUY"

    if change <= -0.10 and pullback:

        return "🔻 STRONG SELL"

    elif change <= -0.05 and pullback:

        return "🔴 SELL"

    return None

def chop_signal(change):

    if change >= 0.15:

        return "🔻 FADE SELL"

    elif change <= -0.15:

        return "🚀 FADE BUY"

    return None

# ---------- TRADE PLAN ----------

def build_plan(price, signal, high, low):

    max_risk = account_size * (risk_percent / 100)

    if "BUY" in signal:

        entry = high * (1 + entry_buffer_percent / 100)

        stop = price * (1 - stop_percent / 100)

        risk_per_share = entry - stop

        target = entry + (risk_per_share * reward_ratio)

    elif "SELL" in signal:

        entry = low * (1 - entry_buffer_percent / 100)

        stop = price * (1 + stop_percent / 100)

        risk_per_share = stop - entry

        target = entry - (risk_per_share * reward_ratio)

    else:

        return None

    if risk_per_share <= 0:

        return None

    shares = int(max_risk // risk_per_share)

    distance = abs(price - entry) / entry * 100

    ready = distance <= entry_trigger_buffer

    return entry, stop, target, shares, risk_per_share, ready, distance

# ---------- GRADING ----------

def grade_trade(change, pullback, market, signal):

    score = abs(change) * 100

    if pullback:

        score += 10

    if market == "BULLISH" and "BUY" in signal:

        score += 10

    if market == "BEARISH" and "SELL" in signal:

        score += 10

    if score >= 30:

        grade = "A+"

    elif score >= 20:

        grade = "A"

    elif score >= 10:

        grade = "B"

    else:

        grade = "C"

    return score, grade

def alert_allowed(grade):

    if alert_grade == "A+":

        return grade == "A+"

    return grade in ["A+", "A"]

# ---------- APP ----------

placeholder = st.empty()

while True:

    spy = analyze("SPY")

    if spy is None:

        st.error("SPY data failed. Try refreshing in a minute.")

        break

    spy_price, spy_change, _, _, _ = spy

    market = get_market(spy_change)

    results = []

    for symbol in symbols:

        data = analyze(symbol)

        if data is None:

            continue

        price, change, pullback, high, low = data

        active_mode = mode

        if mode == "AUTO":

            active_mode = "TREND" if market != "CHOPPY" else "CHOP"

        signal = None

        if active_mode == "TREND":

            signal = trend_signal(change, pullback)

            if market == "BULLISH" and signal and "BUY" not in signal:

                signal = None

            if market == "BEARISH" and signal and "SELL" not in signal:

                signal = None

        elif active_mode == "CHOP":

            signal = chop_signal(change)

        if not signal:

            continue

        plan = build_plan(price, signal, high, low)

        if not plan:

            continue

        entry, stop, target, shares, risk_ps, ready, distance = plan

        score, grade = grade_trade(change, pullback, market, signal)

        if grade not in ["A+", "A"]:

            continue

        results.append({

            "Grade": grade,

            "Score": round(score, 1),

            "Status": "🟢 READY" if ready else "⏳ WAIT",

            "Symbol": symbol,

            "Price": round(price, 2),

            "20m %": round(change, 3),

            "Signal": signal,

            "Entry": round(entry, 2),

            "Stop": round(stop, 2),

            "Target": round(target, 2),

            "Shares": shares,

            "Distance %": round(distance, 3)

        })

    df = pd.DataFrame(results)

    with placeholder.container():

        st.subheader("Market")

        c1, c2, c3 = st.columns(3)

        c1.metric("SPY", round(spy_price, 2))

        c2.metric("20m %", round(spy_change, 3))

        c3.metric("Market", market)

        st.subheader("🚨 Ready Alerts")

        if df.empty:

            st.warning("No A/A+ setups right now.")

        else:

            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            df.index += 1

            ready_df = df[df["Status"] == "🟢 READY"]

            if ready_df.empty:

                st.info("Setups found, but none are close enough to entry yet.")

            else:

                top = ready_df.iloc[0]

                alert_key = f"{top['Symbol']}-{top['Signal']}-{top['Entry']}"

                if alert_allowed(top["Grade"]):

                    if st.session_state.last_alert != alert_key:

                        st.session_state.last_alert = alert_key

                        alert_message = (

                            f"TRADE ALERT: {top['Symbol']} | {top['Grade']} | {top['Signal']} | "

                            f"Entry: {top['Entry']} | Stop: {top['Stop']} | "

                            f"Target: {top['Target']} | Shares: {top['Shares']}"

                        )

                        st.error(f"🚨 LIVE TRADE READY: {top['Symbol']} | {top['Grade']} | {top['Signal']}")

                        st.success(

                            f"Entry: {top['Entry']} | Stop: {top['Stop']} | "

                            f"Target: {top['Target']} | Shares: {top['Shares']}"

                        )

                        if send_texts:

                            sent = send_sms(alert_message)

                            if sent:

                                st.success("SMS alert sent.")

                    else:

                        st.info(

                            f"Active ready trade: {top['Symbol']} | {top['Signal']} | Entry {top['Entry']}"

                        )

            st.subheader("🎯 A/A+ Setups")

            st.dataframe(df, use_container_width=True)

    if not auto_refresh:

        break

    time.sleep(30)

    st.rerun()

st.subheader("Notes")

st.text_area("Journal")
