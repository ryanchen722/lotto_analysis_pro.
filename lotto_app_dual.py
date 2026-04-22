import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
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
# 📊 穩定抓資料（V6-Pro）
# =========================
def fetch_stock(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        df = df.reset_index()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if "Close" not in df.columns:
            return None

        df = df[["Date","Close"]].copy()
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df["symbol"] = symbol

        return df.dropna()

    except:
        return None

def fetch_all():
    all_df = []

    for s in UNIVERSE:
        df = fetch_stock(s)
        if df is not None and len(df) > 20:
            all_df.append(df)

    if len(all_df) == 0:
        return None

    return pd.concat(all_df, ignore_index=True)

# =========================
# 🧠 V7 多策略模型
# =========================
def calc_features(df):
    df = df.copy()
    close = df["Close"]

    # 📈 趨勢策略
    df["ma5"] = close.rolling(5).mean()
    df["ma20"] = close.rolling(20).mean()

    trend_score = (df["ma5"] - df["ma20"]) / df["ma20"]

    # 🔁 均值回歸
    std = close.rolling(20).std()
    mean = close.rolling(20).mean()
    reversion_score = (close - mean) / std

    df["trend_score"] = trend_score
    df["reversion_score"] = -reversion_score  # 反向

    # 🧠 合成 score
    df["score"] = (
        0.6 * df["trend_score"] +
        0.4 * df["reversion_score"]
    ) * 100

    df["score"] = df["score"].replace([np.inf, -np.inf], np.nan).fillna(50)

    return df

# =========================
# 📊 TOP10
# =========================
def get_top10(df):
    latest = df.groupby("symbol").tail(1)
    return latest.sort_values("score", ascending=False).head(10)

# =========================
# 💰 模擬交易（核心🔥）
# =========================
def simulate_trades(df):
    trades = []

    for symbol in df["symbol"].unique():

        data = df[df["symbol"] == symbol].copy()
        data = data.sort_values("Date")

        position = False
        entry = 0

        for _, row in data.iterrows():

            if row["score"] > 70 and not position:
                position = True
                entry = row["Close"]

            elif row["score"] < 40 and position:
                exit_price = row["Close"]
                pnl = exit_price - entry

                trades.append({
                    "symbol": symbol,
                    "entry": entry,
                    "exit": exit_price,
                    "pnl": pnl
                })

                position = False

    return pd.DataFrame(trades)

# =========================
# 📊 equity curve
# =========================
def equity_curve(trades):
    if trades.empty:
        return None

    trades["cum_pnl"] = trades["pnl"].cumsum() + 100000
    return trades

# =========================
# 🚀 UI
# =========================
st.title("📊 V7 量化核心系統（策略 + 回測 + 資金曲線）")

# =========================
# 📈 ① 選股
# =========================
st.header("🔥 TOP10 選股")

df = fetch_all()

if df is None:
    st.error("無資料")
    st.stop()

df = calc_features(df)
top10 = get_top10(df)

st.dataframe(top10[["symbol","Close","score"]])

# =========================
# 💰 ② 模擬回測
# =========================
st.header("📊 策略回測（自動模擬）")

trades = simulate_trades(df)

if trades.empty:
    st.warning("沒有交易訊號")
else:
    st.dataframe(trades)

    # =========================
    # 📈 equity curve
    # =========================
    eq = equity_curve(trades)

    if eq is not None:
        st.subheader("📈 資金曲線")
        st.line_chart(eq["cum_pnl"])

        # 📉 回撤
        eq["peak"] = eq["cum_pnl"].cummax()
        eq["drawdown"] = eq["cum_pnl"] - eq["peak"]

        st.write("📉 最大回撤：", round(eq["drawdown"].min(), 2))

        st.write("💰 總損益：", round(eq["pnl"].sum(), 2))

# =========================
# 💾 ③ 存交易紀錄
# =========================
st.header("💰 手動交易紀錄")

symbol = st.text_input("股票", "2330.TW")
shares = st.number_input("股數", 1, 1000, 10)
entry = st.number_input("進場價", 500.0)

if st.button("存交易"):

    trade = {
        "time": datetime.now(),
        "symbol": symbol,
        "shares": shares,
        "entry": entry
    }

    if os.path.exists(TRADE_FILE):
        df_old = pd.read_csv(TRADE_FILE)
        df_old = pd.concat([df_old, pd.DataFrame([trade])], ignore_index=True)
    else:
        df_old = pd.DataFrame([trade])

    df_old.to_csv(TRADE_FILE, index=False)
    st.success("已存入")

if os.path.exists(TRADE_FILE):
    st.subheader("📋 交易紀錄")
    st.dataframe(pd.read_csv(TRADE_FILE))