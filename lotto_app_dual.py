import random
import streamlit as st
import requests
import re
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(page_title="539 AI V63 回測驗證版", layout="wide")

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
# 盤勢分類
# ==============================
def classify(draw):
    avg = np.mean(draw)
    if avg < 18:
        return "冷盤"
    elif avg > 23:
        return "熱盤"
    else:
        return "均衡盤"

# ==============================
# 建立轉移機率
# ==============================
def build_transition(history):
    trans = {"冷盤":Counter(),"熱盤":Counter(),"均衡盤":Counter()}
    for i in range(len(history)-1):
        state = classify(history[i])
        for n in history[i+1]:
            trans[state][n] += 1

    probs = {}
    for s in trans:
        total = sum(trans[s].values())
        if total == 0: continue
        probs[s] = {n:trans[s][n]/total for n in range(1,40)}
    return probs

# ==============================
# 預測
# ==============================
def predict_one(history):
    probs = build_transition(history)
    state = classify(history[-1])

    base = probs.get(state, {n:1/39 for n in range(1,40)})

    nums = np.array(list(base.keys()))
    vals = np.array(list(base.values()))
    p = vals / vals.sum()

    return sorted(np.random.choice(nums,5,replace=False,p=p))

# ==============================
# 回測
# ==============================
def backtest(history, test_size=500):

    hits = []

    for i in range(len(history)-test_size, len(history)-1):

        train = history[:i]
        pred = predict_one(train)
        actual = history[i]

        hit = len(set(pred) & set(actual))
        hits.append(hit)

    return hits

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V63（回測驗證系統）")

history = load_history()

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(map(str,d)))

# 回測按鈕
if st.button("🚀 開始回測模型（500期）"):

    with st.spinner("正在回測中..."):
        hits = backtest(history, test_size=500)

    df = pd.DataFrame({"命中數": hits})

    avg_hit = np.mean(hits)

    st.subheader("📊 回測結果")

    st.metric("平均命中", f"{avg_hit:.3f}")

    # 分布
    dist = Counter(hits)
    dist_df = pd.DataFrame({
        "命中數": list(dist.keys()),
        "次數": list(dist.values())
    }).sort_values("命中數")

    st.bar_chart(dist_df.set_index("命中數"))

    # baseline
    st.info("🎯 隨機 baseline ≈ 0.64")

    if avg_hit > 0.8:
        st.success("🔥 模型有優勢")
    elif avg_hit > 0.65:
        st.warning("⚠️ 略高於隨機，但不穩")
    else:
        st.error("❌ 沒有優勢（接近隨機）")