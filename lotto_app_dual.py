import random
import streamlit as st
import requests
import re
import os
import json
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter
from itertools import combinations

CSV_PATH = "539_history.csv"
WEIGHT_PATH = "weights.json"
MAX_HISTORY = 1770


# ==============================
# 抓資料（保持你原本方式🔥）
# ==============================
def fetch_all_history(target=1770):

    headers = {"User-Agent": "Mozilla/5.0"}
    all_data = []
    page = 1

    while len(all_data) < target:

        url = f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={page}"
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

        if not page_data:
            break

        all_data.extend(page_data)
        page += 1

    return all_data[:target][::-1]  # 🔥順序修正


# ==============================
# 快取
# ==============================
@st.cache_data(ttl=10800)
def load_history():
    data = fetch_all_history(MAX_HISTORY)
    pd.DataFrame(data).to_csv(CSV_PATH, index=False)
    return data


# ==============================
# 事件條件
# ==============================
def cond_extreme(d): return min(d) >= 21
def cond_big(d): return min(d) >= 20

def cond_consecutive(d):
    d = sorted(d)
    return any(d[i]+1==d[i+1] and d[i]+2==d[i+2] for i in range(3))

def cond_tail(d):
    tails = [n % 10 for n in d]
    return max(Counter(tails).values()) >= 3


# ==============================
# 回測
# ==============================
def backtest_event(history, trigger_func, result_func):

    success = 0
    total = 0

    for i in range(len(history)-1):
        if trigger_func(history[i]):
            total += 1
            if result_func(history[i+1]):
                success += 1

    return success/total if total else 0


# ==============================
# 🔥 權重系統（自學習）
# ==============================
def calculate_weights(history):

    weights = {}

    def calc(trigger):
        rate = backtest_event(history, trigger, trigger)
        return (rate - 0.5) * 2

    weights["extreme"] = calc(cond_extreme)
    weights["big"] = calc(cond_big)
    weights["tail"] = calc(cond_tail)

    return weights


def load_weights(history):

    if os.path.exists(WEIGHT_PATH):
        with open(WEIGHT_PATH, "r") as f:
            return json.load(f)

    weights = calculate_weights(history)

    with open(WEIGHT_PATH, "w") as f:
        json.dump(weights, f)

    return weights


def update_weights(history):

    weights = calculate_weights(history)

    with open(WEIGHT_PATH, "w") as f:
        json.dump(weights, f)

    return weights


# ==============================
# 評分模型（AI核心🔥）
# ==============================
def score_numbers(history, signals, weights):

    short = Counter([n for d in history[-30:] for n in d])
    mid = Counter([n for d in history[-100:] for n in d])
    long = Counter([n for d in history[-500:] for n in d])

    score = {}

    for n in range(1, 40):

        base = short[n]*0.5 + mid[n]*0.3 + long[n]*0.2

        last_seen = 100
        for i, d in enumerate(reversed(history)):
            if n in d:
                last_seen = i
                break

        cold = min(last_seen/50, 1)

        bonus = 0

        if signals["extreme"]:
            bonus += weights["extreme"] * (1 if n >= 21 else -0.3)

        if signals["big"]:
            bonus += weights["big"] * (1 if n >= 20 else -0.3)

        if signals["tail"]:
            bonus += weights["tail"] * (1 if n % 10 in [0,1,2,3] else -0.2)

        noise = random.uniform(0, 0.3)

        score[n] = base + cold + bonus + noise

    return score


# ==============================
# AI推薦
# ==============================
def valid_combo(c):

    if not (80 <= sum(c) <= 140):
        return False

    if sum(n % 2 for n in c) not in [2, 3]:
        return False

    return True


def ai_recommend(history, signals, weights):

    score = score_numbers(history, signals, weights)

    combos = set()

    for _ in range(80000):
        c = random.sample(range(1, 40), 5)

        if valid_combo(c):
            combos.add(tuple(sorted(c)))

    combos = list(combos)

    scored = [(c, sum(score[n] for n in c)) for c in combos]
    scored.sort(key=lambda x: x[1], reverse=True)

    picks = random.sample(scored[:25], 3)

    return [list(c) for c, _ in picks]


# ==============================
# UI
# ==============================
st.set_page_config(layout="wide")
st.title("🔥 539 AI V53（自我學習系統）")

# 🔄 重抓資料
if st.button("🔄 重抓1770期"):
    st.cache_data.clear()
    if os.path.exists(CSV_PATH):
        os.remove(CSV_PATH)
    st.rerun()

history = load_history()
weights = load_weights(history)

st.write("📊 期數:", len(history))


# ==============================
# 事件狀態
# ==============================
signals = {
    "extreme": cond_extreme(history[-1]),
    "big": cond_big(history[-1]),
    "tail": cond_tail(history[-1])
}

st.markdown("## 🧠 AI權重（自動學習）")

c1, c2, c3 = st.columns(3)
c1.metric("極端權重", f"{weights['extreme']:.2f}")
c2.metric("全大權重", f"{weights['big']:.2f}")
c3.metric("尾數權重", f"{weights['tail']:.2f}")


# 更新權重
if st.button("🧠 重新學習權重"):
    weights = update_weights(history)
    st.success("已更新AI權重")


# 最新五期
st.markdown("### 📅 最新五期")
cols = st.columns(5)

for i, d in enumerate(history[-5:][::-1]):
    cols[i].metric(f"{i+1}", " ".join(f"{x:02d}" for x in d))


# AI預測
if st.button("🚀 AI預測"):

    recs = ai_recommend(history, signals, weights)

    st.markdown("## 🎯 AI推薦")

    for r in recs:
        st.success(" ".join(f"{x:02d}" for x in r))