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

# ====== 可選 AI（填入你的 API KEY）======
USE_AI = False
OPENAI_API_KEY = ""

# ========================================
st.set_page_config(page_title="539 AI V57 Hybrid", layout="wide")

PERF_FILE = "performance.json"

# ==============================
# 抓資料（穩定）
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
# 條件
# ==============================
def cond_extreme(d): return min(d) >= 21
def cond_big(d): return min(d) >= 20
def cond_tail(d):
    tails = [n % 10 for n in d]
    return max(Counter(tails).values()) >= 3


# ==============================
# 🔥 AI盤勢判斷（可接LLM）
# ==============================
def ai_market_state(history):

    last10 = history[-10:]
    nums = [n for d in last10 for n in d]

    avg = np.mean(nums)

    if avg > 23:
        return "熱盤"
    elif avg < 17:
        return "冷盤"
    else:
        return "均衡盤"


# ==============================
# 🔥 權重計算（時間衰減）
# ==============================
def calc_weights(history):

    bias = {k:{i:0 for i in range(1,40)} for k in ["extreme","big","tail"]}
    count = {"extreme":0,"big":0,"tail":0}

    total = len(history)

    for i in range(len(history)-1):

        decay = (i/total)**2
        curr = history[i]
        nxt = history[i+1]

        if cond_extreme(curr):
            count["extreme"] += decay
            for n in nxt: bias["extreme"][n] += decay

        if cond_big(curr):
            count["big"] += decay
            for n in nxt: bias["big"][n] += decay

        if cond_tail(curr):
            count["tail"] += decay
            for n in nxt: bias["tail"][n] += decay

    avg = 5/39

    for k in bias:
        if count[k] > 0:
            for n in range(1,40):
                bias[k][n] = (bias[k][n]/count[k]) - avg

    return bias


# ==============================
# 🔥 評分（AI調整版）
# ==============================
def score_numbers(history, bias, market):

    short = Counter([n for d in history[-30:] for n in d])

    scores = {}

    for n in range(1,40):

        base = short[n]

        gap = next((i for i,d in enumerate(reversed(history)) if n in d),50)

        ai = sum(bias[k][n]*20 for k in bias)

        # 🔥 AI市場調整
        if market == "熱盤":
            base *= 0.8
            gap *= 1.2
        elif market == "冷盤":
            base *= 1.2

        scores[n] = max(0.1, base + gap/20 + ai + random.uniform(0,0.3))

    return scores


# ==============================
# 選號
# ==============================
def pick_numbers(history, bias, market):

    scores = score_numbers(history, bias, market)

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
# 投資績效
# ==============================
def load_perf():
    if os.path.exists(PERF_FILE):
        return json.load(open(PERF_FILE))
    return []

def save_perf(data):
    json.dump(data, open(PERF_FILE,"w"))

def evaluate(bets, draw):
    res = []
    for b in bets:
        hit = len(set(b) & set(draw))
        res.append({"bet":b,"draw":draw,"hit":hit,"error":5-hit})
    return res


# ==============================
# UI
# ==============================
st.title("🔥 539 AI V57（AI混合最終版）")

history = load_history()
bias = calc_weights(history)

market = ai_market_state(history)

st.write(f"📊 市場狀態：{market}")

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(f"{x:02d}" for x in d))


# 績效
perf = load_perf()
if perf:
    df = pd.DataFrame(perf)
    st.subheader("📊 投資績效")
    st.dataframe(df.tail(20))
    st.metric("平均命中", f"{df['hit'].mean():.2f}")


# AI預測
if st.button("🚀 AI預測"):

    s1,s2,s3 = pick_numbers(history, bias, market)

    all_nums = s1+s2+s3
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

    bet1 = build(s1)
    bet2 = build(s2)

    st.subheader("💰 投資組合")
    st.success(" ".join(map(str,bet1)))
    st.success(" ".join(map(str,bet2)))

    st.session_state["last_bets"] = [bet1,bet2]


# 自動比對
if "last_bets" in st.session_state:

    draw = history[-1]

    res = evaluate(st.session_state["last_bets"], draw)

    perf = load_perf()
    perf.extend(res)
    save_perf(perf)

    del st.session_state["last_bets"]

    st.success("✅ 已更新績效")


# 重抓
if st.button("🔄 重抓資料"):
    st.cache_data.clear()
    st.rerun()