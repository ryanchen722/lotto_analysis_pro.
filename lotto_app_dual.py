import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="股票 AI 分析系統", layout="wide")

# ==============================
# 股票池（你可以自己改）
# ==============================
stocks = [
    "AAPL","MSFT","NVDA","TSLA","META",
    "GOOGL","AMZN","AMD","NFLX","INTC"
]

# ==============================
# 抓資料
# ==============================
@st.cache_data(ttl=3600)
def load_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d")
    return df

# ==============================
# 核心評分
# ==============================
def calc_score(df):

    df = df.copy()

    # 近期漲幅（動量）
    ret_5 = df["Close"].pct_change(5).iloc[-1]
    ret_20 = df["Close"].pct_change(20).iloc[-1]

    # 波動（風險）
    vol = df["Close"].pct_change().std()

    # 成交量變化
    vol_change = df["Volume"].pct_change(5).iloc[-1]

    # score（你可以調整）
    score = (
        ret_5 * 2 +
        ret_20 * 1.5 +
        vol_change * 0.5 -
        vol * 1
    )

    return score, ret_5, ret_20

# ==============================
# UI
# ==============================
st.title("📈 股票 AI 分析系統（簡化實戰版）")

results = []

for s in stocks:
    df = load_data(s)

    if len(df) < 30:
        continue

    score, r5, r20 = calc_score(df)

    results.append({
        "股票": s,
        "Score": score,
        "5日漲幅": r5,
        "20日漲幅": r20
    })

df_res = pd.DataFrame(results)

# 排序
df_res = df_res.sort_values("Score", ascending=False)

# ==============================
# 顯示
# ==============================
st.subheader("🏆 強勢股票排名")

st.dataframe(df_res)

# Top 3
top3 = df_res.head(3)

st.subheader("🔥 推薦標的（Top 3）")

for i, row in top3.iterrows():
    st.success(f"{row['股票']} | Score: {row['Score']:.3f}")

# ==============================
# 單一股票分析
# ==============================
st.subheader("🔍 個股分析")

pick = st.selectbox("選一檔股票", stocks)

df = load_data(pick)

st.line_chart(df["Close"])