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

st.set_page_config(page_title="539 AI V60 進化版", layout="wide")

PERF_FILE = "performance_v60.json"
BET_FILE = "last_bet_v60.json"
WEIGHT_FILE = "weights_v60.json"
NUM_STAT_FILE = "number_stats.json"

# ==============================
# 初始化
# ==============================
def load_json(file, default):
    if os.path.exists(file):
        return json.load(open(file))
    return default

def save_json(file, data):
    json.dump(data, open(file,"w"), indent=2)

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
# 特徵分析
# ==============================
def analyze(history):
    last30 = history[-30:]
    freq = Counter([n for d in last30 for n in d])
    hot = set([n for n,c in freq.items() if c >= 6])
    cold = set(range(1,40)) - set(freq.keys())
    return hot, cold

# ==============================
# 評分
# ==============================
def score_numbers(history, weights, num_stats):

    hot, cold = analyze(history)
    scores = {}

    for n in range(1,40):

        score = 1.0

        if n in hot:
            score *= weights["hot"]

        if n in cold:
            score *= weights["cold"]

        if n >= 20:
            score *= weights["big"]

        # gap
        gap = next((i for i,d in enumerate(reversed(history)) if n in d),50)
        score += gap/20

        # 🔥 個別命中率學習
        stat = num_stats.get(str(n), {"hit":1,"total":5})
        rate = stat["hit"] / stat["total"]
        score *= (0.5 + rate)

        scores[n] = score + random.uniform(0,0.2)

    return scores

# ==============================
# 選號 + 信心
# ==============================
def pick(scores):

    nums = np.array(list(scores.keys()))
    vals = np.array(list(scores.values()))
    probs = vals / vals.sum()

    combos = []
    combo_scores = []

    for _ in range(1000):
        c = sorted([int(x) for x in np.random.choice(nums,5,replace=False,p=probs)])
        if c not in combos:
            combos.append(c)
            combo_scores.append(sum(scores[x] for x in c))
        if len(combos) >= 3:
            break

    # 信心分數
    max_score = max(combo_scores)
    confidences = [round(s/max_score*100,1) for s in combo_scores]

    return combos, confidences

# ==============================
# 投資組合
# ==============================
def build(picks):
    all_nums = sum(picks,[])
    cnt = Counter(all_nums)
    core = [n for n,c in cnt.items() if c>=2]

    def make(base):
        s=set(core)
        for n in base:
            if len(s)>=5: break
            s.add(n)
        while len(s)<5:
            s.add(random.randint(1,39))
        return sorted(s)

    return make(picks[0]), make(picks[1])

# ==============================
# 評估 + 誤差
# ==============================
def evaluate(bets, draw):
    res = []
    for b in bets:
        hit = len(set(b)&set(draw))
        error = 5-hit
        res.append({
            "下注":b,
            "開獎":draw,
            "命中":hit,
            "誤差":error
        })
    return res

# ==============================
# 自學習
# ==============================
def learn(weights, num_stats, results):

    for r in results:
        for n in r["下注"]:
            stat = num_stats.setdefault(str(n), {"hit":0,"total":0})
            stat["total"] += 1
            if n in r["開獎"]:
                stat["hit"] += 1

    avg_hit = np.mean([r["命中"] for r in results])

    if avg_hit >= 2:
        weights["hot"] *= 1.05
        weights["big"] *= 1.02
    else:
        weights["cold"] *= 1.05

    return weights, num_stats

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V60（自學習 + 誤差分析）")

history = load_history()

weights = load_json(WEIGHT_FILE, {"hot":1,"cold":1,"big":1})
num_stats = load_json(NUM_STAT_FILE, {})

st.write("📦 權重", weights)

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(map(str,d)))

# 預測
if st.button("🚀 AI預測"):

    scores = score_numbers(history, weights, num_stats)
    picks, conf = pick(scores)
    b1,b2 = build(picks)

    st.subheader("💰 投資組合")
    st.success(f"{b1} ｜信心 {conf[0]}%")
    st.success(f"{b2} ｜信心 {conf[1]}%")

    save_json(BET_FILE,{
        "bets":[b1,b2],
        "index":len(history)
    })

# 驗證
if os.path.exists(BET_FILE):

    bet_data = load_json(BET_FILE, {})
    if len(history) > bet_data["index"]:

        draw = history[bet_data["index"]]
        results = evaluate(bet_data["bets"], draw)

        perf = load_json(PERF_FILE, [])
        perf.extend(results)
        save_json(PERF_FILE, perf)

        weights, num_stats = learn(weights, num_stats, results)
        save_json(WEIGHT_FILE, weights)
        save_json(NUM_STAT_FILE, num_stats)

        os.remove(BET_FILE)

        st.success("✅ 已學習（含誤差分析）")

# 績效
perf = load_json(PERF_FILE, [])
if perf:
    df = pd.DataFrame(perf)
    st.subheader("📊 績效分析")
    st.dataframe(df.tail(20))

    st.metric("平均命中", f"{df['命中'].mean():.2f}")
    st.metric("平均誤差", f"{df['誤差'].mean():.2f}")