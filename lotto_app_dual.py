import streamlit as st
import pandas as pd
import yfinance as yf
import os
from datetime import datetime

# =========================
# 📌 股票池
# =========================
UNIVERSE = [
    "2330.TW","2317.TW","2454.TW","2382.TW",
    "2412.TW","2881.TW","2882.TW"
]

TRADE_FILE = "trades.csv"

# =========================
# 📊 抓資料
# =========================
def fetch(symbol):
    df = yf.download(symbol, period="3mo", interval="1d")
    df = df.reset_index()
    df["symbol"] = symbol
    return df

def fetch_all():
    all_df = []
    for s in UNIVERSE:
        try:
            all_df.append(fetch(s))
        except:
            continue
    return pd.concat(all_df, ignore_index=True)

# =========================
# 🧠 Score 模型
# =========================
def calc_score(df):
    df = df.copy()

    df["ma5"] = df["Close"].rolling(5).mean()
    df["ma20"] = df["Close"].rolling(20).mean()

    df["score"] = 50 + (df["ma5"] - df["ma20"]) / df["ma20"] * 100
    df["score"] = df["score"].fillna(50)

    df["signal"] = df["score"].apply(
        lambda x: "BUY" if x > 70 else ("SELL" if x < 40 else "PASS")
    )

    return df

# =========================
# 📈 選股
# =========================
def scan(df):
    latest = df.groupby("symbol").tail(1)
    return latest.sort_values("score", ascending=False)

# =========================
# 🚀 UI
# =========================
st.title("📊 V5 實戰交易系統（Live Signal + 手動下單）")

# =========================
# 📊 上半部：市場掃描
# =========================
st.header("🧠 台股即時掃描")

if st.button("開始掃描市場"):

    df = fetch_all()
    df = calc_score(df)

    result = scan(df)

    st.success("掃描完成")

    st.subheader("🔥 TOP 選股")

    st.dataframe(result)

    st.subheader("📢 交易訊號")

    st.dataframe(result[["symbol","Close","score","signal"]])

# =========================
# 💰 下半部：手動交易
# =========================
st.header("💰 手動建立交易")

symbol = st.text_input("股票代號", "2330.TW")
shares = st.number_input("買幾股", 1, 1000, 10)
entry = st.number_input("進場價格", 500.0)
stop = st.number_input("停損", 480.0)
tp = st.number_input("停利", 550.0)

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
# 📊 顯示交易紀錄
# =========================
st.subheader("📊 交易紀錄")

if os.path.exists(TRADE_FILE):
    st.dataframe(pd.read_csv(TRADE_FILE))