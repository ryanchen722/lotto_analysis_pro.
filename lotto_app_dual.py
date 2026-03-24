import random
import streamlit as st
import requests
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(page_title="539 AI V55 Ultimate", layout="wide")

# ==============================
# 🔥 穩定抓資料（最終版）
# ==============================
@st.cache_data(ttl=10800)
def load_history():
    target = 1770
    headers = {"User-Agent": "Mozilla/5.0"}
    all_data = []
    page = 1

    progress = st.progress(0)
    txt = st.empty()

    while len(all_data) < target:

        txt.text(f"抓第 {page} 頁...")
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

            progress.progress(min(len(all_data)/target,1.0))

        except:
            page += 1
            continue

    progress.empty()
    txt.empty()

    return all_data[:target][::-1]


# ==============================
# 🧠 條件
# ==============================
def cond_extreme(d): return min(d) >= 21
def cond_big(d): return min(d) >= 20
def cond_tail(d):
    tails = [n % 10 for n in d]
    return max(Counter(tails).values()) >= 3


# ==============================
# 🔥 V55 核心（時間權重 + cross）
# ==============================
def calculate_cross_weights_v55(history):

    biases = {k: {i: 0.0 for i in range(1,40)} for k in ["extreme","big","tail"]}
    counts = {"extreme":0,"big":0,"tail":0}

    total = len(history)

    for i in range(len(history)-1):

        curr = history[i]
        nxt = history[i+1]

        # 🔥 時間衰減（越近越強）
        decay = (i / total) ** 2   # 核心🔥

        if cond_extreme(curr):
            counts["extreme"] += decay
            for n in nxt:
                biases["extreme"][n] += decay

        if cond_big(curr):
            counts["big"] += decay
            for n in nxt:
                biases["big"][n] += decay

        if cond_tail(curr):
            counts["tail"] += decay
            for n in nxt:
                biases["tail"][n] += decay

    avg = 5 / 39

    for k in biases:
        if counts[k] > 0:
            for n in range(1,40):
                biases[k][n] = (biases[k][n] / counts[k]) - avg

    return biases


# ==============================
# 🔥 評分（時間+冷熱+AI）
# ==============================
def get_scores_v55(history, biases):

    last = history[-1]

    signals = {
        "extreme": cond_extreme(last),
        "big": cond_big(last),
        "tail": cond_tail(last)
    }

    short = Counter([n for d in history[-30:] for n in d])
    mid = Counter([n for d in history[-100:] for n in d])

    scores = {}

    for n in range(1,40):

        base = short[n]*0.6 + mid[n]*0.4

        # 冷號
        gap = next((i for i,d in enumerate(reversed(history)) if n in d),50)
        cold = gap / 20

        # AI影響
        ai = sum(biases[s][n]*20 for s,v in signals.items() if v)

        noise = random.uniform(0,0.3)

        scores[n] = max(0.1, base + cold + ai + noise)

    return scores


# ==============================
# 🎯 AI推薦
# ==============================
def ai_pick_v55(history, biases):

    scores = get_scores_v55(history, biases)

    nums = np.array(list(scores.keys()))
    vals = np.array(list(scores.values()))
    probs = vals / vals.sum()

    res = []

    for _ in range(1000):
        c = sorted([int(x) for x in np.random.choice(nums,5,replace=False,p=probs)])
        if c not in res:
            res.append(c)
        if len(res) >= 3:
            break

    return res


# ==============================
# 🧠 健康度
# ==============================
def health(combo):
    odd = sum(n%2 for n in combo)
    big = sum(n>=20 for n in combo)
    ok = (2<=odd<=3) and (2<=big<=3)
    return f"奇偶{odd}:{5-odd} | 大小{big}:{5-big} " + ("✅" if ok else "⚠️")


# ==============================
# UI
# ==============================
st.title("🔥 539 AI V55（時間學習最終版）")

history = load_history()

st.write("📊 期數:", len(history))

if len(history) < 1000:
    st.error("⚠️ 資料不完整，請重抓")

biases = calculate_cross_weights_v55(history)

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)

for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(f"{x:02d}" for x in d))


# 熱度
st.subheader("📊 熱度")
short = Counter([n for d in history[-50:] for n in d])
df = pd.DataFrame([{"號碼":n,"次數":short[n]} for n in range(1,40)])
st.bar_chart(df.set_index("號碼"))


# 預測
if st.button("🚀 AI預測"):

    s1,s2,s3 = ai_pick_v55(history, biases)

    # 共識
    all_nums = s1 + s2 + s3
    cnt = Counter(all_nums)
    core = [n for n,c in cnt.items() if c>=2]

    def build(base):
        s = set(core)
        for n in base:
            if len(s)>=5: break
            s.add(n)
        while len(s)<5:
            s.add(random.randint(1,39))
        return sorted(s)

    bet1 = build(s1)
    bet2 = build(s2)

    st.subheader("💰 投資組合")

    c1,c2 = st.columns(2)

    c1.success(" ".join(f"{x:02d}" for x in bet1))
    c1.caption(health(bet1))

    c2.success(" ".join(f"{x:02d}" for x in bet2))
    c2.caption(health(bet2))

    st.subheader("🎯 原始策略")

    for s in [s1,s2,s3]:
        st.code(" ".join(f"{x:02d}" for x in s))


# 重抓
if st.button("🔄 重抓"):
    st.cache_data.clear()
    st.rerun()