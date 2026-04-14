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

st.set_page_config(page_title="539 AI V71.5 穩定版", layout="wide")

PERF_FILE = "perf_v71_5.json"

# ==============================
# 抓資料
# ==============================
@st.cache_data(ttl=10800)
def load_history():
    target = 600
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
# 工具
# ==============================
def load_json(file):
    if os.path.exists(file):
        return json.load(open(file))
    return []

def save_json(file, data):
    json.dump(data, open(file,"w"), indent=2)

# ==============================
# 🧠 市場判斷（核心）
# ==============================
def detect_mode(history):

    last20 = history[-20:]
    nums = [n for d in last20 for n in d]
    avg = np.mean(nums)

    if avg > 23:
        return "追冷"
    elif avg < 17:
        return "追熱"
    else:
        return "平衡"

# ==============================
# 🧠 核心評分（修正版🔥）
# ==============================
def score_numbers(history, mode):

    scores = {}
    freq = Counter([n for d in history[-30:] for n in d])

    for n in range(1,40):

        gap = next((i for i,d in enumerate(reversed(history)) if n in d),50)

        if mode == "追冷":
            score = gap * 1.2 - freq[n]*0.5

        elif mode == "追熱":
            score = freq[n]*1.2 - gap*0.5

        else:  # 平衡
            score = freq[n]*0.8 + gap*0.8

        scores[n] = max(0.1, score)

    return scores

# ==============================
# 選號（機率抽樣）
# ==============================
def pick_numbers(scores):

    nums = np.array(list(scores.keys()))
    vals = np.array(list(scores.values()))
    vals = vals / vals.sum()

    picks = set()

    while len(picks) < 5:
        picks.add(int(np.random.choice(nums, p=vals)))

    return sorted(picks)

# ==============================
# 是否下注（關鍵🔥）
# ==============================
def should_bet(perf):

    if len(perf) < 10:
        return False

    avg = np.mean([p["hit"] for p in perf[-10:]])

    return avg > 0.7

# ==============================
# 評估
# ==============================
def evaluate(pred, draw):
    return len(set(pred) & set(draw))

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V71.5（穩定策略版）")

history = load_history()
perf = load_json(PERF_FILE)

mode = detect_mode(history)

st.write(f"📊 當前模式：{mode}")

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(map(str,d)))

# ==============================
# 顯示績效
# ==============================
if perf:
    df = pd.DataFrame(perf)
    st.subheader("📊 績效")
    st.dataframe(df.tail(20))
    st.metric("平均命中", f"{df['hit'].mean():.2f}")

# ==============================
# 預測
# ==============================
if st.button("🚀 AI預測"):

    if not should_bet(perf):
        st.warning("⚠️ 模型狀態不佳 → 建議不下注")
    else:
        scores = score_numbers(history, mode)

        bet1 = pick_numbers(scores)
        bet2 = pick_numbers(scores)

        st.subheader("💰 投資組合")
        st.success(" - ".join(f"{n:02d}" for n in bet1))
        st.success(" - ".join(f"{n:02d}" for n in bet2))

        # 存等待驗證
        st.session_state["last_bets"] = [bet1, bet2]
        st.session_state["bet_index"] = len(history)

# ==============================
# 驗證（下一期）
# ==============================
if "last_bets" in st.session_state:

    idx = st.session_state["bet_index"]

    if len(history) > idx:

        draw = history[idx]

        hits = []
        for b in st.session_state["last_bets"]:
            hits.append(evaluate(b, draw))

        for h in hits:
            perf.append({"draw": draw, "hit": h})

        save_json(PERF_FILE, perf)

        del st.session_state["last_bets"]

        st.success(f"✅ 本期命中：{hits}")

# ==============================
# 重抓
# ==============================
if st.button("🔄 重抓資料"):
    st.cache_data.clear()
    st.rerun()