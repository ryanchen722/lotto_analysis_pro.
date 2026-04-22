import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import os
from datetime import datetime

# =========================
# 📌 股票池（可自行擴充）
# =========================
UNIVERSE = [
    "2330.TW","2317.TW","2454.TW","2382.TW",
    "2412.TW","2881.TW","2882.TW",
    "2408.TW","3532.TW","2379.TW"
]

TRADE_FILE = "trades.csv"
SIGNAL_FILE = "signals.csv"

# =========================
# 📊 安全抓資料（重點🔥）
# =========================
def fetch_stock(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        df = df.reset_index()

        # 防 MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

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

    df["ma5"] = df["Close"].rolling(5).mean()
    df["ma20"] = df["Close"].rolling(20).mean()

    df["score"] = 50 + (df["ma5"] - df["ma20"]) / df["ma20"] * 100
    df["score"] = df["score"].replace([np.inf, -np.inf], np.nan).fillna(50)

    # 🔥 訊號（合理化）
    def signal(x):
        if x > 70:
            return "🟢 可考慮買進"
        elif x < 40:
            return "🔴 建議減碼/避開"
        else:
            return "🟡 無明確優勢"

    df["交易建議"] = df["score"].apply(signal)

    return df

# =========================
# 📊 選股排序
# =========================
def scan(df):
    latest = df.groupby("symbol").tail(1)
    return latest.sort_values("score", ascending=False)

# =========================
# 🚀 UI
# =========================
st.title("📊 V5-Stable 台股量化系統（完整版）")

# =========================
# 📈 市場掃描（上半部）
# =========================
st.header("🧠 市場掃描")

if st.button("開始掃描市場"):

    df = fetch_all()

    if df is None:
        st.error("❌ 無法取得資料")
        st.stop()

    df = calc_score(df)
    result = scan(df)

    st.success("掃描完成")

    show = result[[
        "symbol",
        "Close",
        "score",
        "交易建議"
    ]]

    st.subheader("🔥 TOP 選股")
    st.dataframe(show)

    # 存 signal
    show.to_csv(SIGNAL_FILE, index=False)

# =========================
# 💰 手動交易（永遠存在🔥）
# =========================
st.header("💰 手動交易紀錄")

symbol = st.text_input("股票代號", "2330.TW")
shares = st.number_input("股數", 1, 1000, 10)
entry = st.number_input("進場價格", 500.0)
stop = st.number_input("停損價格", 480.0)
tp = st.number_input("停利價格", 550.0)

if st.button("儲存交易"):

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
    st.success("已存入交易紀錄")

# =========================
# 📊 交易紀錄顯示
# =========================
if os.path.exists(TRADE_FILE):
    st.subheader("📊 交易紀錄")
    st.dataframe(pd.read_csv(TRADE_FILE))

# =========================
# 📊 Signal 歷史
# =========================
if os.path.exists(SIGNAL_FILE):
    st.subheader("📈 最近選股結果")
    st.dataframe(pd.read_csv(SIGNAL_FILE))