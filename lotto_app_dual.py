import streamlit as st
import twstock
import pandas as pd
import numpy as np

st.set_page_config(page_title="股票 AI V3 買賣點版", layout="wide")

stocks = ["2330","2317","2454","2303","2881","2603"]

# ==============================
# 抓資料
# ==============================
@st.cache_data(ttl=3600)
def load_data(code):
    stock = twstock.Stock(code)
    data = stock.fetch_from(2023,1)

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    df["Close"] = df["close"]

    return df

# ==============================
# RSI
# ==============================
def calc_rsi(series, period=14):
    delta = series.diff()

    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

# ==============================
# 訊號判斷
# ==============================
def generate_signal(df):

    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["RSI"] = calc_rsi(df["Close"])

    last = df.iloc[-1]

    # 買
    if last["MA5"] > last["MA20"] and last["RSI"] < 70:
        return "BUY"

    # 賣
    elif last["RSI"] > 70 or last["MA5"] < last["MA20"]:
        return "SELL"

    else:
        return "HOLD"

# ==============================
# 回測（核心🔥）
# ==============================
def backtest(df):

    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["RSI"] = calc_rsi(df["Close"])

    position = 0
    entry_price = 0
    returns = []

    for i in range(20, len(df)):

        row = df.iloc[i]

        if position == 0:
            if row["MA5"] > row["MA20"] and row["RSI"] < 70:
                position = 1
                entry_price = row["Close"]

        elif position == 1:
            if row["RSI"] > 70 or row["MA5"] < row["MA20"]:
                ret = row["Close"] / entry_price - 1
                returns.append(ret)
                position = 0

    if len(returns) == 0:
        return 0, 0

    avg = np.mean(returns)
    win = sum([1 for r in returns if r > 0]) / len(returns)

    return avg, win

# ==============================
# UI
# ==============================
st.title("📈 股票 AI V3（買賣點版）")

results = []

for s in stocks:

    df = load_data(s)

    if len(df) < 50:
        continue

    signal = generate_signal(df)
    avg, win = backtest(df)

    results.append({
        "股票": s,
        "訊號": signal,
        "平均報酬": avg,
        "勝率": win
    })

df_res = pd.DataFrame(results)

st.subheader("📊 策略結果")
st.dataframe(df_res)

# 推薦買
st.subheader("🔥 建議進場")

buy_list = df_res[df_res["訊號"]=="BUY"]

if len(buy_list) == 0:
    st.warning("目前沒有明確進場點")
else:
    for i,row in buy_list.iterrows():
        st.success(f"{row['股票']} | 勝率:{row['勝率']:.2f}")

# 個股圖
st.subheader("📈 個股分析")

pick = st.selectbox("選股票", stocks)
df = load_data(pick)

df["MA5"] = df["Close"].rolling(5).mean()
df["MA20"] = df["Close"].rolling(20).mean()

st.line_chart(df[["Close","MA5","MA20"]])