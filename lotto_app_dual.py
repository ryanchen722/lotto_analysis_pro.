import streamlit as st
import pandas as pd
from datetime import datetime
import os

FILE = "trades.csv"

st.title("📊 V4 交易紀錄系統")

# =========================
# 📥 輸入區
# =========================
st.header("➕ 新增交易")

symbol = st.text_input("股票代號", "AAPL")
shares = st.number_input("股數", min_value=1, value=10)
entry_price = st.number_input("進場價格", value=100.0)
stop_loss = st.number_input("停損價格", value=95.0)
take_profit = st.number_input("停利價格", value=110.0)
score = st.slider("策略分數", 0, 100, 70)

if st.button("存入交易"):
    new_trade = {
        "time": datetime.now(),
        "symbol": symbol,
        "shares": shares,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "score": score,
        "status": "OPEN"
    }

    if os.path.exists(FILE):
        df = pd.read_csv(FILE)
        df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
    else:
        df = pd.DataFrame([new_trade])

    df.to_csv(FILE, index=False)
    st.success("✅ 已存檔")

# =========================
# 📊 讀取資料
# =========================
st.header("📊 交易紀錄")

if os.path.exists(FILE):
    df = pd.read_csv(FILE)
    st.dataframe(df)

    # =========================
    # 📈 分析
    # =========================
    st.subheader("📈 基本分析")

    st.write("交易數量：", len(df))
    st.write("平均 Score：", round(df["score"].mean(), 2))

    open_trades = df[df["status"] == "OPEN"]
    st.write("未平倉：", len(open_trades))

    # Score 分布
    st.subheader("📊 Score 分布")
    st.bar_chart(df["score"])

else:
    st.info("還沒有交易資料")