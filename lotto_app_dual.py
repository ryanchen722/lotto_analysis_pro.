import random
import streamlit as st
import requests
import re
import numpy as np
import pandas as pd
import json
import os
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(page_title="539 AI V67.5 實戰版", layout="wide")

PERF_FILE = "perf.json"
WEIGHT_FILE = "weights.json"

# ==============================
# 抓資料
# ==============================
@st.cache_data(ttl=10800)
def load_history():
    target = 800
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
# 權重讀寫
# ==============================
def load_weights():
    if os.path.exists(WEIGHT_FILE):
        return json.load(open(WEIGHT_FILE))
    return {"freq":1.2, "gap":0.3, "decay":2.0}

def save_weights(w):
    json.dump(w, open(WEIGHT_FILE,"w"))

# ==============================
# 核心評分
# ==============================
def score_numbers(history, weights):

    scores = {}
    recent = history[-30:]
    freq = Counter([n for d in recent for n in d])

    for n in range(1,40):

        gap = next((i for i,d in enumerate(reversed(history)) if n in d),50)

        decay = 0
        for i,d in enumerate(reversed(history[-50:])):
            if n in d:
                decay += 1/(i+1)

        score = (
            freq[n]*weights["freq"] +
            gap*weights["gap"] +
            decay*weights["decay"]
        )

        scores[n] = score

    return scores

# ==============================
# 選號（不隨機🔥）
# ==============================
def pick_numbers(scores):

    nums = sorted(scores, key=scores.get, reverse=True)

    combos = []
    i = 0

    while len(combos) < 2:
        c = sorted(nums[i:i+5])

        odd = sum(n%2 for n in c)
        big = sum(n>=20 for n in c)

        if 2 <= odd <= 3 and 2 <= big <= 3:
            combos.append(c)

        i += 1

    return combos

# ==============================
# 績效
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
        hit = len(set(b)&set(draw))
        res.append(hit)
    return res

# ==============================
# 自動學習（關鍵🔥）
# ==============================
def update_weights(weights, hits):

    avg = np.mean(hits)

    # 如果表現差 → 調整
    if avg < 1:
        weights["gap"] *= 1.1
        weights["freq"] *= 0.9

    elif avg > 2:
        weights["freq"] *= 1.1

    return weights

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V67.5（會進化版）")

history = load_history()
weights = load_weights()

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(map(str,d)))

# 顯示權重
st.subheader("⚙️ 當前權重")
st.write(weights)

# ==============================
# 預測
# ==============================
if st.button("🚀 AI預測"):

    scores = score_numbers(history, weights)
    bets = pick_numbers(scores)

    st.subheader("💰 投資組合")
    for b in bets:
        st.success(" - ".join(f"{n:02d}" for n in b))

    st.session_state["last_bets"] = bets

# ==============================
# 自動比對（下一期）
# ==============================
if "last_bets" in st.session_state:

    last_draw = history[-1]

    hits = evaluate(st.session_state["last_bets"], last_draw)

    perf = load_perf()
    perf.append({
        "draw": last_draw,
        "hits": hits
    })
    save_perf(perf)

    # 🔥 自動調整
    weights = update_weights(weights, hits)
    save_weights(weights)

    del st.session_state["last_bets"]

    st.success(f"✅ 已更新命中：{hits}")

# ==============================
# 顯示績效
# ==============================
perf = load_perf()
if perf:
    df = pd.DataFrame(perf)
    st.subheader("📊 歷史績效")
    st.dataframe(df.tail(20))

    avg = np.mean([np.mean(x) for x in df["hits"]])
    st.metric("平均命中", f"{avg:.2f}")

# 重抓
if st.button("🔄 重抓資料"):
    st.cache_data.clear()
    st.rerun()