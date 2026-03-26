import random
import streamlit as st
import requests
import re
import pandas as pd
import numpy as np
import json
import os
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(page_title="539 AI V59 自學習版", layout="wide")

PERF_FILE = "performance.json"
BET_FILE = "last_bet.json"
WEIGHT_FILE = "weights.json"

# ==============================
# 初始化權重
# ==============================
def load_weights():
    if os.path.exists(WEIGHT_FILE):
        return json.load(open(WEIGHT_FILE))
    return {
        "hot": 1.0,
        "cold": 1.0,
        "big": 1.0,
        "tail": 1.0
    }

def save_weights(w):
    json.dump(w, open(WEIGHT_FILE,"w"), indent=2)

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
            continue

    return all_data[:target][::-1]

# ==============================
# 工具
# ==============================
def load_json(file):
    if os.path.exists(file):
        return json.load(open(file))
    return []

def save_json(file,data):
    json.dump(data, open(file,"w"), indent=2)

# ==============================
# 特徵分析
# ==============================
def analyze_features(history):

    last30 = history[-30:]
    freq = Counter([n for d in last30 for n in d])

    hot = set([n for n,c in freq.items() if c >= 6])
    cold = set(range(1,40)) - set(freq.keys())

    return hot, cold

# ==============================
# 評分（核心）
# ==============================
def score_numbers(history, weights):

    hot, cold = analyze_features(history)

    scores = {}

    for n in range(1,40):

        score = 1.0

        # 熱號
        if n in hot:
            score *= weights["hot"]

        # 冷號
        if n in cold:
            score *= weights["cold"]

        # 大號
        if n >= 20:
            score *= weights["big"]

        # gap
        gap = next((i for i,d in enumerate(reversed(history)) if n in d),50)
        score += gap / 20

        scores[n] = score + random.uniform(0,0.2)

    return scores

# ==============================
# 選號
# ==============================
def pick_numbers(scores):

    nums = np.array(list(scores.keys()))
    vals = np.array(list(scores.values()))
    probs = vals / vals.sum()

    picks = []

    for _ in range(1000):
        c = sorted([int(x) for x in np.random.choice(nums,5,replace=False,p=probs)])
        if c not in picks:
            picks.append(c)
        if len(picks) >= 3:
            break

    return picks

# ==============================
# 投資組合
# ==============================
def build_bets(picks):

    all_nums = sum(picks, [])
    cnt = Counter(all_nums)
    core = [n for n,c in cnt.items() if c>=2]

    def build(base):
        s=set(core)
        for n in base:
            if len(s)>=5: break
            s.add(n)
        while len(s)<5:
            s.add(random.randint(1,39))
        return sorted(s)

    return build(picks[0]), build(picks[1])

# ==============================
# 評估
# ==============================
def evaluate(bets, draw):
    res = []
    for b in bets:
        hit = len(set(b) & set(draw))
        res.append({"下注":b,"開獎":draw,"命中":hit})
    return res

# ==============================
# 🔥 自學習（核心）
# ==============================
def learn(weights, results):

    avg_hit = np.mean([r["命中"] for r in results])

    # 命中高 → 強化策略
    if avg_hit >= 2:
        weights["hot"] *= 1.05
        weights["big"] *= 1.02
    else:
        weights["cold"] *= 1.05

    return weights

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V59（自學習進化版）")

history = load_history()
weights = load_weights()

st.write("📦 目前權重", weights)

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(map(str,d)))

# 預測
if st.button("🚀 預測"):

    scores = score_numbers(history, weights)
    picks = pick_numbers(scores)
    bet1, bet2 = build_bets(picks)

    st.success(bet1)
    st.success(bet2)

    save_json(BET_FILE, {
        "bets":[bet1,bet2],
        "index": len(history)
    })

# 驗證 + 學習
if os.path.exists(BET_FILE):

    bet_data = load_json(BET_FILE)

    if len(history) > bet_data["index"]:

        draw = history[bet_data["index"]]

        results = evaluate(bet_data["bets"], draw)

        perf = load_json(PERF_FILE)
        perf.extend(results)
        save_json(PERF_FILE, perf)

        # 🔥 學習
        weights = learn(weights, results)
        save_weights(weights)

        os.remove(BET_FILE)

        st.success("✅ 已學習並更新權重")

# 績效
perf = load_json(PERF_FILE)
if perf:
    df = pd.DataFrame(perf)
    st.dataframe(df.tail(20))
    st.metric("平均命中", f"{df['命中'].mean():.2f}")

# 重抓
if st.button("🔄 重抓"):
    st.cache_data.clear()
    st.rerun()