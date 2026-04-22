import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import os
from datetime import datetime

# =========================
# 📌 股票池
# =========================
UNIVERSE = [
    "2330.TW","2317.TW","2454.TW","2382.TW",
    "2412.TW","2881.TW","2882.TW",
    "2408.TW","3532.TW","2379.TW"
]

TRADE_FILE = "trades.csv"

# =========================
# 📊 抓資料（穩定版）
# =========================
def fetch_stock(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        df = df.reset_index()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df["收盤價"] = pd.to_numeric(df["Close"], errors="coerce")
        df["股票代號"] = symbol

        df = df.dropna()

        return df

    except:
        return None

def fetch_all():
    all_df = []

    for s in UNIVERSE:
        df = fetch_stock(s)
        if df is not None:
            all_df.append(df)

    if len(all_df) == 0:
        return None

    return pd.concat(all_df, ignore_index=True)

# =========================
# 🧠 計算模型（中文欄位）
# =========================
def calc_score(df):
    df = df.copy()

    df["均線5日"] = df["收盤價"].rolling(5).mean()
    df["均線20日"] = df["收盤價"].rolling(20).mean()

    df["評分"] = 50 + (df["均線5日"] - df["均線20日"]) / df["均線20日"] * 100
    df["評分"] = df["評分"].replace([np.inf, -np.inf], np.nan).fillna(50)

    # 👉 訊號中文化（重點🔥）
    def signal(x):
        if x > 70:
            return "🟢 建議買進"
        elif x < 40:
            return "🔴 建議賣出"
        else:
            return "🟡 觀望（不交易）"

    df["交易建議"] = df["評分"].apply(signal)

    return df

# =========================
# 📊 選股排序
# =========================
def scan(df):
    latest = df.groupby("股票代號").tail(1)
    return latest.sort_values("評分", ascending=False)

# =========================
# 🚀 UI
# =========================
st.title("📊 V5-Stable 台股量化系統（中文完整版）")

mode = st.sidebar.selectbox(
    "功能選單",
    ["📈 市場掃描", "💰 手動交易紀錄"]
)

# =========================
# 📈 市場掃描
# =========================
if mode == "📈 市場掃描":

    st.header("🧠 台股掃描（中文化）")

    if st.button("開始掃描"):

        df = fetch_all()

        if df is None:
            st.error("❌ 無法取得資料")
            st.stop()

        df = calc_score(df)
        result = scan(df)

        st.success("掃描完成")

        # 👉 中文欄位顯示
        show = result[[
            "股票代號",
            "收盤價",
            "評分",
            "交易建議"
        ]]

        st.subheader("🔥 排行榜")
        st.dataframe(show)

        st.subheader("📢 建議操作")
        st.dataframe(show)

# =========================
# 💰 手動交易（你要的功能保留🔥）
# =========================
if mode == "💰 手動交易紀錄":

    st.header("💰 手動建立交易")

    股票 = st.text_input("股票代號", "2330.TW")
    股數 = st.number_input("買幾股", 1, 1000, 10)
    進場價 = st.number_input("進場價格", 500.0)
    停損 = st.number_input("停損價格", 480.0)
    停利 = st.number_input("停利價格", 550.0)

    if st.button("儲存交易"):

        trade = {
            "時間": datetime.now(),
            "股票代號": 股票,
            "股數": 股數,
            "進場價": 進場價,
            "停損": 停損,
            "停利": 停利
        }

        if os.path.exists(TRADE_FILE):
            df = pd.read_csv(TRADE_FILE)
            df = pd.concat([df, pd.DataFrame([trade])], ignore_index=True)
        else:
            df = pd.DataFrame([trade])

        df.to_csv(TRADE_FILE, index=False)
        st.success("已存入交易紀錄")

    # 👉 顯示紀錄（保留！）
    if os.path.exists(TRADE_FILE):
        st.subheader("📊 交易紀錄")
        st.dataframe(pd.read_csv(TRADE_FILE))