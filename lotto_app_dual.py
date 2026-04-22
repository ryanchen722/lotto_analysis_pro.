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
# 📊 抓資料
# =========================
def fetch(symbol):
    df = yf.download(symbol, period="3mo", interval="1d", progress=False)
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

    df["Close"] = df["Close"].astype(float)

    df["ma5"] = df["Close"].rolling(5).mean()
    df["ma20"] = df["Close"].rolling(20).mean()

    df["score"] = 50 + (df["ma5"] - df["ma20"]) / df["ma20"] * 100
    df["score"] = df["score"].fillna(50)

    return df

# =========================
# 📊 TOP10 選股
# =========================
def get_top10(df):
    latest = df.groupby("symbol").tail(1)
    latest = latest.sort_values("score", ascending=False)
    return latest.head(10)

# =========================
# 🚀 UI
# =========================
st.title("📊 V6 交易儀表板（TOP10 + 下單 + 損益）")

# =========================
# 📈 ① TOP10 選股
# =========================
st.header("🔥 TOP10 選股")

df = fetch_all()
df = calc_score(df)

top10 = get_top10(df)

top10_display = top10[["symbol","Close","score"]].copy()
top10_display.rename(columns={
    "symbol":"股票代號",
    "Close":"現價",
    "score":"評分"
}, inplace=True)

st.dataframe(top10_display)

# =========================
# 💰 ② 下單區（重點🔥）
# =========================
st.header("💰 下單區（從 TOP10 選）")

symbol_list = top10["symbol"].tolist()

selected = st.selectbox("選擇股票", symbol_list)

# 自動帶入價格
current_price = float(top10[top10["symbol"] == selected]["Close"].values[0])

st.write(f"📌 當前價格：{current_price}")

shares = st.number_input("投入股數", 1, 10000, 10)

stop = st.number_input("停損", value=current_price * 0.95)
tp = st.number_input("停利", value=current_price * 1.1)

if st.button("存入交易"):

    trade = {
        "time": datetime.now(),
        "symbol": selected,
        "shares": shares,
        "entry": current_price,
        "stop": stop,
        "tp": tp
    }

    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        df = pd.concat([df, pd.DataFrame([trade])], ignore_index=True)
    else:
        df = pd.DataFrame([trade])

    df.to_csv(TRADE_FILE, index=False)
    st.success("已存入交易")

# =========================
# 📊 ③ 損益追蹤（即時）
# =========================
st.header("📊 損益追蹤")

if os.path.exists(TRADE_FILE):

    trades = pd.read_csv(TRADE_FILE)

    def get_live_price(symbol):
        try:
            return yf.Ticker(symbol).history(period="1d")["Close"].iloc[-1]
        except:
            return None

    pnl_list = []

    for _, row in trades.iterrows():

        live_price = get_live_price(row["symbol"])

        if live_price is None:
            pnl = 0
        else:
            pnl = (live_price - row["entry"]) * row["shares"]

        pnl_list.append(pnl)

    trades["即時損益"] = pnl_list

    st.dataframe(trades)

    st.write("💰 總損益：", round(sum(pnl_list), 2))

else:
    st.info("尚無交易紀錄")