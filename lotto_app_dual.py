import random
import streamlit as st
import requests
import re
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(page_title="539 AI V64 自學習系統", layout="wide")

# ==============================
# 抓資料
# ==============================
@st.cache_data(ttl=10800)
def load_history():
    target = 1770
    headers = {"User-Agent": "Mozilla/5.0"}
    all_data = []
    page = 1

    while len(all_data) < target:
        url = f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={page}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = "big5"
            soup = BeautifulSoup(r.text, "lxml")
            rows = soup.find_all("tr")

            page_data = []
            for row in rows:
                nums = re.findall(r'\b\d{1,2}\b', row.text)
                nums = [int(x) for x in nums if 1 <= int(x) <= 39]
                if len(nums) >= 5:
                    page_data.append(sorted(nums[-5:]))

            if len(page_data) < 10:
                break

            all_data.extend(page_data)
            page += 1
        except:
            page += 1

    return all_data[:target][::-1]

# ==============================
# 策略
# ==============================
def strategy_trend(history):
    last30 = history[-30:]
    freq = Counter([n for d in last30 for n in d])
    return [n for n,_ in freq.most_common(5)]

def strategy_zone(history):
    last = history[-1]
    zones = {
        "small": [n for n in range(1,14)],
        "mid": [n for n in range(14,27)],
        "big": [n for n in range(27,40)]
    }

    picks = []
    for k,v in zones.items():
        if not any(n in v for n in last):
            picks += random.sample(v,2)

    while len(picks) < 5:
        picks.append(random.randint(1,39))

    return sorted(set(picks))[:5]

def strategy_cold(history):
    last50 = history[-50:]
    freq = Counter([n for d in last50 for n in d])
    cold = sorted(range(1,40), key=lambda x: freq[x])[:15]
    return random.sample(cold,5)

# ==============================
# 回測策略表現
# ==============================
def backtest_strategy(history, func, test_size=300):

    hits = []

    for i in range(len(history)-test_size, len(history)-1):
        train = history[:i]
        pred = func(train)
        actual = history[i]
        hits.append(len(set(pred)&set(actual)))

    return np.mean(hits)

# ==============================
# 融合推薦
# ==============================
def combine(s1, s2, s3, w1, w2, w3):

    score = Counter()

    for n in s1:
        score[n] += w1
    for n in s2:
        score[n] += w2
    for n in s3:
        score[n] += w3

    final = [n for n,_ in score.most_common(5)]
    return sorted(final)

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V64（自學習進化版）")

history = load_history()

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(map(str,d)))

# ==============================
# 執行
# ==============================
if st.button("🚀 啟動AI自學習預測"):

    with st.spinner("AI學習中..."):

        s1_score = backtest_strategy(history, strategy_trend)
        s2_score = backtest_strategy(history, strategy_zone)
        s3_score = backtest_strategy(history, strategy_cold)

        total = s1_score + s2_score + s3_score

        w1 = s1_score / total
        w2 = s2_score / total
        w3 = s3_score / total

        s1 = strategy_trend(history)
        s2 = strategy_zone(history)
        s3 = strategy_cold(history)

        final = combine(s1, s2, s3, w1, w2, w3)

    # 顯示策略表現
    st.subheader("📊 策略表現（回測）")

    df = pd.DataFrame({
        "策略": ["趨勢","區間","冷門"],
        "平均命中": [s1_score, s2_score, s3_score],
        "權重": [w1, w2, w3]
    })

    st.dataframe(df)

    # 顯示策略號碼
    st.subheader("🧠 各策略推薦")
    st.write("🏆 趨勢：", s1)
    st.write("⚖️ 區間：", s2)
    st.write("🎲 冷門：", s3)

    # 最終推薦
    st.subheader("💰 最終推薦號碼（AI融合）")
    st.success(" - ".join(f"{n:02d}" for n in final))

# 重抓
if st.button("🔄 重抓資料"):
    st.cache_data.clear()
    st.rerun()