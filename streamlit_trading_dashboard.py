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
st.caption("Stable Auto Watch Mode + Trend Scanner v1")

LOG_FILE = Path("paper_trade_log.csv")

symbols_input = st.sidebar.text_input(
    "Watchlist",
    "SPY, QQQ, AAPL, MSFT, NVDA, TSLA, AMD, META, AMZN, GOOGL, XOM"
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

st.sidebar.subheader("Volume Filter")
min_volume_ratio = st.sidebar.slider("Minimum Volume Strength", 1.0, 3.0, 1.2)

minimum_score = 40
cooldown_minutes = 15

if "last_alerts" not in st.session_state:
    st.session_state.last_alerts = {}


def time_status():
    now = datetime.now(ZoneInfo("America/New_York"))

    weekday = now.weekday() < 5
    active = weekday and dtime(9, 20) <= now.time() <= dtime(17, 40)
    market_open = weekday and dtime(9, 30) <= now.time() <= dtime(16, 0)

    return now, active, market_open


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
        st.warning(f"SMS error: {e}")
        return False


def get_data(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1d", interval="5m")
        if data is None or len(data) < 10:
            return None
        return data
    except Exception:
        return None


def get_daily_data(symbol):
    try:
        data = yf.Ticker(symbol).history(period="3mo", interval="1d")
        if data is None or len(data) < 30:
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
    volumes = data["Volume"]

    price = float(closes.iloc[-1])
    start = float(closes.iloc[-5])
    prev = float(closes.iloc[-2])

    change = ((price - start) / start) * 100
    pullback = price < prev

    vol_now = float(volumes.iloc[-1])
    vol_avg = float(volumes.iloc[-10:-1].mean())
    volume_ratio = vol_now / vol_avg if vol_avg > 0 else 0

    return {
        "price": price,
        "change": change,
        "pullback": pullback,
        "recent_high": float(highs.iloc[-5:].max()),
        "recent_low": float(lows.iloc[-5:].min()),
        "volume_ratio": volume_ratio,
        "volume_ok": volume_ratio >= min_volume_ratio
    }


def get_current_price(symbol):
    data = get_data(symbol)
    if data is None:
        return None
    return float(data["Close"].iloc[-1])


def get_market(change):
    if change >= 0.05:
        return "BULLISH"
    elif change <= -0.05:
        return "BEARISH"
    return "CHOPPY"


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

    return "⚪ NO TRADE"


def build_trade(symbol, data, signal, market):
    if not data["volume_ok"]:
        return None

    price = data["price"]

    if "BUY" in signal:
        direction = "BUY"
        entry = data["recent_high"] * (1 + entry_buffer_percent / 100)
        stop = price * (1 - stop_percent / 100)
        risk = entry - stop
        target = entry + (risk * reward_ratio)

    elif "SELL" in signal:
        direction = "SELL"
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
    if data["volume_ok"]:
        score += 10

    if score < minimum_score:
        return None

    grade = "A+" if score >= 40 else "A"

    return {
        "Symbol": symbol,
        "Direction": direction,
        "Signal": signal,
        "Grade": grade,
        "Score": round(score, 1),
        "Entry": round(entry, 2),
        "Stop": round(stop, 2),
        "Target": round(target, 2),
        "Shares": shares,
        "Volume Strength": round(data["volume_ratio"], 2)
    }


def analyze_trend(symbol):
    data = get_daily_data(symbol)
    if data is None:
        return None

    close = data["Close"]
    high = data["High"]
    volume = data["Volume"]

    price = float(close.iloc[-1])
    sma20 = float(close.rolling(20).mean().iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else sma20
    high20 = float(high.iloc[-20:].max())

    five_day_change = ((price - close.iloc[-6]) / close.iloc[-6]) * 100
    one_month_change = ((price - close.iloc[-21]) / close.iloc[-21]) * 100

    avg_volume = volume.iloc[-20:-1].mean()
    current_volume = volume.iloc[-1]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

    score = 0
    reasons = []

    if price > sma20:
        score += 20
        reasons.append("Above 20D")

    if price > sma50:
        score += 15
        reasons.append("Above 50D")

    if five_day_change >= 4:
        score += 20
        reasons.append("Strong 5D")

    if one_month_change >= 8:
        score += 20
        reasons.append("Strong 1M")

    if price >= high20 * 0.97:
        score += 15
        reasons.append("Near highs")

    if volume_ratio >= 1.0:
        score += 10
        reasons.append("Volume OK")

    if score < 65:
        return None

    stop = sma20
    risk = price - stop

    if risk <= 0:
        return None

    target = price + (risk * reward_ratio)
    shares = int((account_size * (risk_percent / 100)) // risk)

    if score >= 80:
        grade = "A+"
    elif score >= 65:
        grade = "A"
    else:
        grade = "B"

    return {
        "Symbol": symbol,
        "Direction": "BUY",
        "Signal": "📈 TREND BUY",
        "Grade": grade,
        "Score": round(score, 1),
        "Entry": round(price, 2),
        "Stop": round(stop, 2),
        "Target": round(target, 2),
        "Shares": shares,
        "5D %": round(five_day_change, 2),
        "1M %": round(one_month_change, 2),
        "Volume Strength": round(volume_ratio, 2),
        "Reasons": ", ".join(reasons)
    }
    def can_alert(symbol, signal):
        key = f"{symbol}-{signal}"
        now = time.time()
        last = st.session_state.last_alerts.get(key)

    if last is None or now - last > cooldown_minutes * 60:
        st.session_state.last_alerts[key] = now
        return True

    return False


def load_log():
    if LOG_FILE.exists():
        return pd.read_csv(LOG_FILE)

    return pd.DataFrame(columns=[
        "Opened", "Closed", "Symbol", "Direction", "Signal", "Grade", "Score",
        "Entry", "Stop", "Target", "Shares", "Status",
        "Exit Price", "Result", "Paper P/L"
    ])


def save_log(df):
    df.to_csv(LOG_FILE, index=False)


def add_paper_trade(trade):
    log = load_log()

    if not log.empty:
        existing = log[
            (log["Symbol"] == trade["Symbol"]) &
            (log["Signal"] == trade["Signal"]) &
            (log["Status"] == "OPEN")
        ]

        if not existing.empty:
            return

    new_trade = {
        "Opened": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Closed": "",
        "Symbol": trade["Symbol"],
        "Direction": trade["Direction"],
        "Signal": trade["Signal"],
        "Grade": trade["Grade"],
        "Score": trade["Score"],
        "Entry": trade["Entry"],
        "Stop": trade["Stop"],
        "Target": trade["Target"],
        "Shares": trade["Shares"],
        "Status": "OPEN",
        "Exit Price": "",
        "Result": "",
        "Paper P/L": ""
    }

    log = pd.concat([log, pd.DataFrame([new_trade])], ignore_index=True)
    save_log(log)


def update_open_trades():
    log = load_log()

    if log.empty:
        return log

    for i, row in log.iterrows():

        if row["Status"] != "OPEN":
            continue

        price = get_current_price(row["Symbol"])

        if price is None:
            continue

        try:
            entry = float(row["Entry"])
            stop = float(row["Stop"])
            target = float(row["Target"])
            shares = int(float(row["Shares"]))
        except Exception:
            continue

        direction = row["Direction"]

        result = None
        exit_price = None

        if direction == "BUY":

            if price <= stop:
                result = "LOSS"
                exit_price = stop

            elif price >= target:
                result = "WIN"
                exit_price = target

        elif direction == "SELL":

            if price >= stop:
                result = "LOSS"
                exit_price = stop

            elif price <= target:
                result = "WIN"
                exit_price = target

        if result:

            pnl = (
                (exit_price - entry) * shares
                if direction == "BUY"
                else (entry - exit_price) * shares
            )

            log.at[i, "Closed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.at[i, "Status"] = "CLOSED"
            log.at[i, "Exit Price"] = round(exit_price, 2)
            log.at[i, "Result"] = result
            log.at[i, "Paper P/L"] = round(pnl, 2)

            send_sms(
                f"PAPER TRADE {result}: "
                f"{row['Symbol']} | "
                f"Exit {round(exit_price,2)} | "
                f"P/L ${round(pnl,2)}"
            )

    save_log(log)
    return log


def show_performance(log):

    closed = log[log["Status"] == "CLOSED"]

    if closed.empty:
        st.info("No closed paper trades yet.")
        return

    wins = closed[closed["Result"] == "WIN"]
    losses = closed[closed["Result"] == "LOSS"]

    total = len(closed)

    win_rate = round((len(wins) / total) * 100, 1)

    pnl = pd.to_numeric(
        closed["Paper P/L"],
        errors="coerce"
    ).fillna(0).sum()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Closed Trades", total)
    c2.metric("Wins", len(wins))
    c3.metric("Losses", len(losses))
    c4.metric("Win Rate", f"{win_rate}%")

    st.metric("Net Paper P/L", f"${round(pnl, 2)}")


def run():

    now, active, market_open = time_status()

    st.subheader("System Status")

    c1, c2, c3 = st.columns(3)

    c1.metric("Current ET Time", now.strftime("%I:%M:%S %p"))
    c2.metric("Watch Mode", "ACTIVE" if active else "SLEEP")
    c3.metric("Market", "OPEN" if market_open else "CLOSED")

    if not active:
        st.warning(
            "Sleep mode. Active scanning runs Monday–Friday, "
            "9:20 AM to 5:40 PM ET."
        )
        return

    if market_open:
        st.success("Market open — SMS alerts enabled.")
    else:
        st.info("Pre/after-market monitoring only — trade SMS blocked.")

    update_open_trades()

    spy = analyze("SPY")

    if spy is None:
        st.error("SPY failed")
        return

    market = get_market(spy["change"])

    st.subheader("Market Direction")

    c1, c2 = st.columns(2)

    c1.metric("SPY 20m %", round(spy["change"], 3))
    c2.metric("Market", market)

    setups = []

    for symbol in symbols:

        data = analyze(symbol)

        if data is None:
            continue

        signal = get_signal(
            data["change"],
            data["pullback"],
            market
        )

        trade = build_trade(
            symbol,
            data,
            signal,
            market
        )

        if trade:
            setups.append(trade)

    if setups:

        df = pd.DataFrame(setups).sort_values(
            "Score",
            ascending=False
        )

        top = df.iloc[0]

        st.subheader("🚨 Intraday Top Setup")

        st.error(
            f"{top['Symbol']} | "
            f"{top['Grade']} | "
            f"{top['Signal']}"
        )

        st.success(
            f"Entry {top['Entry']} | "
            f"Stop {top['Stop']} | "
            f"Target {top['Target']} | "
            f"Volume {top['Volume Strength']}x"
        )

        if (
            market_open
            and "STRONG" in top["Signal"]
            and send_texts
        ):

            msg = (
                f"{top['Symbol']} {top['Signal']} | "
                f"Entry {top['Entry']} "
                f"Stop {top['Stop']} "
                f"Target {top['Target']} | "
                f"Volume {top['Volume Strength']}x"
            )

            if send_sms(msg):
                st.success("SMS sent")

            add_paper_trade(top)

        st.subheader("Ranked Intraday Setups")
        st.dataframe(df, use_container_width=True)

    else:
        st.info("No intraday setups")

    st.subheader("📈 Trend Scanner v1")

    trend_setups = []

    for symbol in symbols:

        trend = analyze_trend(symbol)

        if trend:
            trend_setups.append(trend)

    if trend_setups:

        trend_df = pd.DataFrame(trend_setups).sort_values(
            "Score",
            ascending=False
        )

        top_trend = trend_df.iloc[0]

        st.error(
            f"Top Trend: {top_trend['Symbol']} | "
            f"{top_trend['Grade']} | "
            f"{top_trend['Signal']}"
        )

        st.success(
            f"Entry {top_trend['Entry']} | "
            f"Stop {top_trend['Stop']} | "
            f"Target {top_trend['Target']} | "
            f"5D {top_trend['5D %']}% | "
            f"1M {top_trend['1M %']}%"
        )

        if (
            market_open
            and send_texts
        ):

            msg = (
                f"TREND ALERT: {top_trend['Symbol']} | "
                f"Grade {top_trend['Grade']} | "
                f"Entry {top_trend['Entry']} "
                f"Stop {top_trend['Stop']} "
                f"Target {top_trend['Target']}"
            )

            if send_sms(msg):
                st.success("Trend SMS sent")

            add_paper_trade(top_trend)

        st.dataframe(trend_df, use_container_width=True)

    else:
        st.info("No trend setups")

    st.subheader("Paper Trade Performance")

    log = load_log()

    show_performance(log)

    st.subheader("Paper Trade Log")

    st.dataframe(log.tail(20), use_container_width=True)


run()

now, active, market_open = time_status()

if active:
    time.sleep(30)
else:
    time.sleep(600)

st.rerun()
