import random
import streamlit as st
import requests
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from collections import Counter, defaultdict

st.set_page_config(page_title="539 AI V61 真分析版", layout="wide")

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
# 🧠 盤勢分類
# ==============================
def classify(draw):
    avg = np.mean(draw)
    tails = [n % 10 for n in draw]
    tail_concentration = max(Counter(tails).values())

    if avg < 18:
        return "冷盤"
    elif avg > 23:
        return "熱盤"
    elif tail_concentration >= 3:
        return "爆發盤"
    else:
        return "均衡盤"

# ==============================
# 🧠 建立轉移模型
# ==============================
def build_transition(history):

    transition = {
        "冷盤": Counter(),
        "熱盤": Counter(),
        "均衡盤": Counter(),
        "爆發盤": Counter()
    }

    count = Counter()

    for i in range(len(history)-1):

        state = classify(history[i])
        next_draw = history[i+1]

        count[state] += 1

        for n in next_draw:
            transition[state][n] += 1

    # 轉機率
    probs = {}

    for state in transition:
        total = sum(transition[state].values())
        if total == 0:
            continue
        probs[state] = {n: transition[state][n]/total for n in range(1,40)}

    return probs

# ==============================
# 🧠 區間補償
# ==============================
def zone_boost(last_draw):

    zones = {
        "small": sum(1 for n in last_draw if n <= 13),
        "mid": sum(1 for n in last_draw if 14 <= n <= 26),
        "big": sum(1 for n in last_draw if n >= 27),
    }

    boost = {"small":1.0,"mid":1.0,"big":1.0}

    for z in zones:
        if zones[z] == 0:
            boost[z] = 1.3
        elif zones[z] >= 3:
            boost[z] = 0.8

    return boost

# ==============================
# 🧠 產生預測
# ==============================
def predict(history, probs):

    last = history[-1]
    state = classify(last)

    base_prob = probs.get(state, {n:1/39 for n in range(1,40)})

    boost = zone_boost(last)

    final_scores = {}

    for n in range(1,40):

        score = base_prob.get(n, 0.01)

        if n <= 13:
            score *= boost["small"]
        elif n <= 26:
            score *= boost["mid"]
        else:
            score *= boost["big"]

        final_scores[n] = score

    # normalize
    nums = np.array(list(final_scores.keys()))
    vals = np.array(list(final_scores.values()))
    probs = vals / vals.sum()

    picks = []
    for _ in range(1000):
        c = sorted(np.random.choice(nums,5,replace=False,p=probs))
        c = [int(x) for x in c]
        if c not in picks:
            picks.append(c)
        if len(picks) >= 3:
            break

    return picks, state

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V61（真正分析版）")

history = load_history()
probs = build_transition(history)

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(map(str,d)))

# 顯示盤勢
current_state = classify(history[-1])
st.info(f"📊 當前盤勢：{current_state}")

# 預測
if st.button("🚀 AI分析預測"):

    picks, state = predict(history, probs)

    st.subheader("🎯 AI 推薦（基於盤勢轉移）")

    for i,p in enumerate(picks):
        st.success(f"策略 {i+1}：{' - '.join(map(str,p))}")

    st.caption(f"推理依據：目前為「{state}」，使用歷史轉移機率生成")