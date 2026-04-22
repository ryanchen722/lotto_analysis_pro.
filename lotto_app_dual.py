import streamlit as st
import pandas as pd
import os
import numpy as np
from datetime import datetime

TRADE_FILE = "trades.csv"

st.title("📊 V5 量化回測引擎（Equity + Risk）")

# =========================
# 💰 交易輸入
# =========================
st.header("💰 新增交易")

symbol = st.text_input("股票", "2330.TW")
shares = st.number_input("股數", 1, 1000, 10)
entry = st.number_input("進場價", 500.0)
exit_price = st.number_input("出場價", 550.0)
score = st.slider("Score", 0, 100, 70)

if st.button("存入交易"):

    pnl = (exit_price - entry) * shares

    trade = {
        "time": datetime.now(),
        "symbol": symbol,
        "shares": shares,
        "entry": entry,
        "exit": exit_price,
        "score": score,
        "pnl": pnl
    }

    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        df = pd.concat([df, pd.DataFrame([trade])], ignore_index=True)
    else:
        df = pd.DataFrame([trade])

    df.to_csv(TRADE_FILE, index=False)
    st.success("已存入")

# =========================
# 📊 回測核心
# =========================
st.header("📊 回測分析（V5核心）")

if os.path.exists(TRADE_FILE):

    df = pd.read_csv(TRADE_FILE)

    # =========================
    # 📈 Equity Curve
    # =========================
    df["equity"] = df["pnl"].cumsum() + 100000  # 初始資金10萬

    st.subheader("📈 資金曲線")
    st.line_chart(df["equity"])

    # =========================
    # 📉 最大回撤
    # =========================
    df["peak"] = df["equity"].cummax()
    df["drawdown"] = df["equity"] - df["peak"]

    max_dd = df["drawdown"].min()

    st.write("📉 最大回撤：", round(max_dd, 2))

    # =========================
    # 📊 勝率
    # =========================
    win_rate = (df["pnl"] > 0).mean()

    st.write("📊 勝率：", round(win_rate * 100, 2), "%")
    st.write("💰 總損益：", round(df["pnl"].sum(), 2))

    # =========================
    # 📊 Score 分析
    # =========================
    st.subheader("🧠 Score vs 報酬")

    st.scatter_chart(df[["score", "pnl"]])

    st.dataframe(df)

else:
    st.info("尚無交易資料")