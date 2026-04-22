import streamlit as st
import pandas as pd
import os
from datetime import datetime

TRADE_FILE = "trades.csv"
SIGNAL_FILE = "signals.csv"

st.title("📊 台股 V4-C（資料庫 + 回測系統）")

# =========================
# 🧠 1. 台股 Signal（模型輸入）
# =========================
st.header("🧠 輸入台股模型資料")

symbol = st.text_input("股票代號", "2330")
close = st.number_input("收盤價", value=500.0)
score = st.slider("模型 Score", 0, 100, 75)

signal = "BUY" if score > 70 else "PASS"

if st.button("存入 Signal"):

    new_signal = {
        "date": datetime.now(),
        "symbol": symbol,
        "close": close,
        "score": score,
        "signal": signal
    }

    if os.path.exists(SIGNAL_FILE):
        df = pd.read_csv(SIGNAL_FILE)
        df = pd.concat([df, pd.DataFrame([new_signal])], ignore_index=True)
    else:
        df = pd.DataFrame([new_signal])

    df.to_csv(SIGNAL_FILE, index=False)
    st.success("✅ Signal 已存入")

st.write("📢 建議：", signal)

# =========================
# 💰 2. 交易紀錄
# =========================
st.header("💰 手動交易紀錄")

shares = st.number_input("股數", min_value=1, value=10)
entry = st.number_input("進場價", value=500.0)
stop = st.number_input("停損", value=480.0)
tp = st.number_input("停利", value=550.0)

if st.button("存入交易"):

    trade = {
        "time": datetime.now(),
        "symbol": symbol,
        "shares": shares,
        "entry": entry,
        "stop": stop,
        "tp": tp,
        "score": score,
        "status": "OPEN"
    }

    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        df = pd.concat([df, pd.DataFrame([trade])], ignore_index=True)
    else:
        df = pd.DataFrame([trade])

    df.to_csv(TRADE_FILE, index=False)
    st.success("✅ 交易已存")

# =========================
# 📊 3. 資料庫查看
# =========================
st.header("📊 Signal 資料庫")

if os.path.exists(SIGNAL_FILE):
    df = pd.read_csv(SIGNAL_FILE)
    st.dataframe(df)

    st.subheader("Score 分布")
    st.bar_chart(df["score"])

# =========================
# 🔥 4. 回測（核心）
# =========================
st.header("🔥 簡易回測")

if os.path.exists(TRADE_FILE):
    df = pd.read_csv(TRADE_FILE)

    df["pnl"] = (df["tp"] - df["entry"]) * df["shares"]
    df["win"] = df["pnl"] > 0

    st.write("交易數量：", len(df))
    st.write("勝率：", round(df["win"].mean() * 100, 2), "%")
    st.write("總損益：", round(df["pnl"].sum(), 2))

    st.subheader("P/L 分布")
    st.bar_chart(df["pnl"])

else:
    st.info("尚無交易資料")