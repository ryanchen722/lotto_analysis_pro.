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
# 🧠 安全抓資料（核心🔥）
# =========================
def fetch_stock(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        df = df.reset_index()

        # 🔥 修正 MultiIndex / Close 問題
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 🔥 強制轉 Series
        if "Close" not in df.columns:
            return None

        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")

        df["symbol"] = symbol
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
# 🧠 Score 模型（穩定版）
# =========================
def calc_score(df):
    df = df.copy()

    df["Close"] = df["Close"].astype(float)

    df["ma5"] = df["Close"].rolling(5).mean()
    df["ma20"] = df["Close"].rolling(20).mean()

    # 防止除 0 / NaN
    df["ma20"] = df["ma20"].replace(0, np.nan)

    df["score"] = 50 + (df["ma5"] - df["ma20"]) / df["ma20"] * 100
    df["score"] = df["score"].replace([np.inf, -np.inf], np.nan)
    df["score"] = df["score"].fillna(50)

    df["signal"] = df["score"].apply(
        lambda x: "BUY" if x > 70 else ("SELL" if x < 40 else "PASS")
    )

    return df

# =========================
# 📊 選股
# =========================
def scan(df):
    latest = df.groupby("symbol").tail(1)
    return latest.sort_values("score", ascending=False)

# =========================
# 🚀 UI
# =========================
st.title("📊 V5-Stable 台股量化系統（穩定版）")

mode = st.sidebar.selectbox(
    "模式",
    ["市場掃描", "交易紀錄"]
)

# =========================
# 📊 市場掃描
# =========================
if mode == "市場掃描":

    st.header("🧠 台股掃描（穩定版）")

    if st.button("開始掃描"):

        df = fetch_all()

        if df is None:
            st.error("❌ 無法取得資料")
            st.stop()

        df = calc_score(df)
        result = scan(df)

        st.success("掃描完成")

        st.subheader("🔥 TOP 選股")
        st.dataframe(result)

        st.subheader("📢 BUY / SELL 訊號")
        st.dataframe(result[["symbol","Close","score","signal"]])

# =========================
# 💰 交易紀錄
# =========================
if mode == "交易紀錄":

    st.header("💰 交易紀錄")

    symbol = st.text_input("股票", "2330.TW")
    shares = st.number_input("股數", 1, 1000, 10)
    entry = st.number_input("進場", 500.0)
    stop = st.number_input("停損", 480.0)
    tp = st.number_input("停利", 550.0)

    if st.button("存入交易"):

        trade = {
            "time": datetime.now(),
            "symbol": symbol,
            "shares": shares,
            "entry": entry,
            "stop": stop,
            "tp": tp
        }

        if os.path.exists(TRADE_FILE):
            df = pd.read_csv(TRADE_FILE)
            df = pd.concat([df, pd.DataFrame([trade])], ignore_index=True)
        else:
            df = pd.DataFrame([trade])

        df.to_csv(TRADE_FILE, index=False)
        st.success("已存入")

    if os.path.exists(TRADE_FILE):
        st.dataframe(pd.read_csv(TRADE_FILE))