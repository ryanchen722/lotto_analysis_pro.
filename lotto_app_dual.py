import random
import streamlit as st
import requests
import re
import os
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter
from itertools import combinations

CSV_PATH = "539_history.csv"
MAX_HISTORY = 1770


# ==============================
# 抓資料（自動翻頁）
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

    return all_data[:target]


# ==============================
# 快取
# ==============================
@st.cache_data(ttl=10800)
def load_history():
    data = fetch_all_history(MAX_HISTORY)
    pd.DataFrame(data).to_csv(CSV_PATH, index=False)
    return data


# ==============================
# 🔥 多事件分析
# ==============================
def analyze_event(history, check_func):

    events = []
    gaps = []
    last = None

    for i, d in enumerate(history):
        if check_func(d):

            events.append(i)

            if last is not None:
                gaps.append(i - last)

            last = i

    prob = len(events)/len(history) if history else 0
    avg_gap = sum(gaps)/len(gaps) if gaps else 0
    current_gap = len(history)-1-last if last is not None else 0

    return prob, avg_gap, current_gap


# 各種事件
def cond_extreme(d): return min(d) >= 21
def cond_big(d): return min(d) >= 20
def cond_consecutive(d):
    d = sorted(d)
    return any(d[i]+1==d[i+1] and d[i]+2==d[i+2] for i in range(3))
def cond_tail(d):
    tails = [n%10 for n in d]
    return max(Counter(tails).values()) >= 3


# ==============================
# 評分模型（多事件🔥）
# ==============================
def score_numbers(history, signals):

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

        # 🔥 根據事件加權
        if signals["extreme"] and n >= 21:
            bonus += 1.5

        if signals["big"] and n >= 20:
            bonus += 1.0

        if signals["tail"] and n % 10 in [0,1,2,3]:
            bonus += 0.8

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


def ai_recommend(history, signals):

    score = score_numbers(history, signals)

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
st.title("🔥 539 AI V51（多事件判斷系統）")

# 重抓
if st.button("🔄 重新抓1770期"):
    st.cache_data.clear()
    st.rerun()

history = load_history()

st.write("📊 期數:", len(history))


# ==============================
# 事件分析顯示
# ==============================
events = {
    "極端小號消失": cond_extreme,
    "全大號": cond_big,
    "連號爆發": cond_consecutive,
    "尾數集中": cond_tail
}

signals = {}

st.markdown("## 🧠 市場狀態")

cols = st.columns(4)

for i, (name, func) in enumerate(events.items()):

    prob, avg_gap, current = analyze_event(history, func)

    with cols[i]:
        st.metric(name, f"{prob*100:.1f}%")

        if avg_gap > 0 and current >= avg_gap * 0.9:
            st.error("🔥 可能爆發")
            signals[name.split("號")[0]] = True
        else:
            st.success("正常")
            signals[name.split("號")[0]] = False


# 統一key
signals = {
    "extreme": signals.get("極端小", False),
    "big": signals.get("全大", False),
    "tail": signals.get("尾數", False)
}


# 最新五期
st.markdown("### 📅 最新五期")
cols = st.columns(5)
for i, d in enumerate(history[-5:][::-1]):
    cols[i].metric(f"{i+1}", " ".join(f"{x:02d}" for x in d))


# 預測
if st.button("🚀 AI預測"):

    recs = ai_recommend(history, signals)

    st.markdown("## 🎯 AI推薦")

    for r in recs:
        st.success(" ".join(f"{x:02d}" for x in r))