import random
import streamlit as st
import requests
import re
import numpy as np
import json
import os
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(page_title="539 AI 實用版", layout="wide")

WEIGHT_FILE = "weights_clean.json"
PRED_FILE = "pred_clean.json"

# ==============================
# 抓資料
# ==============================
@st.cache_data(ttl=10800)
def load_history():
    target = 600
    headers = {"User-Agent": "Mozilla/5.0"}
    data = []
    page = 1

    while len(data) < target:
        url = f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={page}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = "big5"
            soup = BeautifulSoup(r.text, "lxml")

            rows = soup.find_all("tr")

            for row in rows:
                nums = re.findall(r'\b\d{1,2}\b', row.text)
                nums = [int(x) for x in nums if 1 <= int(x) <= 39]

                if len(nums) >= 5:
                    data.append(sorted(nums[-5:]))

            page += 1
        except:
            page += 1

    return data[:target][::-1]

# ==============================
# 權重
# ==============================
def load_weights():
    if os.path.exists(WEIGHT_FILE):
        return json.load(open(WEIGHT_FILE))
    return {"freq":1.0, "gap":1.0, "decay":1.0}

def save_weights(w):
    json.dump(w, open(WEIGHT_FILE,"w"))

# ==============================
# 分數（核心）
# ==============================
def score_numbers(history, w):

    freq = Counter([n for d in history[-30:] for n in d])
    scores = {}

    for n in range(1,40):

        gap = next((i for i,d in enumerate(reversed(history)) if n in d),50)

        decay = 0
        for i,d in enumerate(reversed(history[-50:])):
            if n in d:
                decay += 1/(i+1)

        score = (
            freq[n]*w["freq"] +
            gap*w["gap"] +
            decay*w["decay"]
        )

        scores[n] = score

    return scores

# ==============================
# 選號（不固定🔥）
# ==============================
def pick_numbers(scores):

    nums = list(scores.keys())
    vals = np.array(list(scores.values()))

    # 防止全部一樣
    vals = vals + np.random.rand(len(vals))*0.01

    probs = vals / vals.sum()

    picks = set()

    while len(picks) < 5:
        picks.add(int(np.random.choice(nums, p=probs)))

    return sorted(picks)

# ==============================
# 學習
# ==============================
def learn(weights, hits):

    avg = np.mean(hits)

    if avg < 1:
        weights["gap"] *= 1.1
    else:
        weights["freq"] *= 1.05

    return weights

# ==============================
# UI
# ==============================
st.title("🔥 539 AI（實用進化版）")

history = load_history()
weights = load_weights()

st.write("📊 權重：", weights)

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(map(str,d)))

# ==============================
# 預測
# ==============================
if st.button("🚀 AI選號"):

    scores = score_numbers(history, weights)

    b1 = pick_numbers(scores)
    b2 = pick_numbers(scores)

    st.subheader("💰 推薦號碼")
    st.success(" - ".join(f"{n:02d}" for n in b1))
    st.success(" - ".join(f"{n:02d}" for n in b2))

    st.session_state["bets"] = [b1, b2]
    st.session_state["idx"] = len(history)

# ==============================
# 學習（下一期）
# ==============================
if "bets" in st.session_state:

    if len(history) > st.session_state["idx"]:

        draw = history[st.session_state["idx"]]

        hits = [len(set(b)&set(draw)) for b in st.session_state["bets"]]

        weights = learn(weights, hits)
        save_weights(weights)

        del st.session_state["bets"]

        st.success(f"✅ 命中：{hits}")