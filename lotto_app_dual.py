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

st.set_page_config(page_title="539 AI V71 投資版", layout="wide")

PERF_FILE = "perf_v71.json"
STATE_FILE = "state_v71.json"

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
def load_json(file, default):
    if os.path.exists(file):
        return json.load(open(file))
    return default

def save_json(file, data):
    json.dump(data, open(file,"w"), indent=2)

# ==============================
# 簡單模型
# ==============================
def get_scores(history):
    freq = Counter([n for d in history[-30:] for n in d])
    scores = {}

    for n in range(1,40):
        gap = next((i for i,d in enumerate(reversed(history)) if n in d),50)
        scores[n] = freq[n] + gap/10

    return scores

def pick_numbers(scores):
    nums = sorted(scores, key=scores.get, reverse=True)
    return sorted(nums[:5])

def pick_random():
    return sorted(random.sample(range(1,40),5))

# ==============================
# 投資策略
# ==============================
def should_bet(perf):

    if len(perf) < 10:
        return True

    last10 = perf[-10:]
    avg_hit = np.mean([np.mean(p["hit"]) for p in last10])

    return avg_hit > 0.6

def calculate_roi(perf):

    money = 0
    cost = 0

    for p in perf:
        for h in p["hit"]:
            if h == 2:
                money += 50
            elif h == 3:
                money += 500
            elif h >= 4:
                money += 20000
            cost += 50

    return money - cost

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V71（下注策略系統）")

history = load_history()
perf = load_json(PERF_FILE, [])
state = load_json(STATE_FILE, {"lose_streak":0})

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(map(str,d)))

# 顯示狀態
st.subheader("🧠 當前狀態")
st.write(f"連輸次數：{state['lose_streak']}")

if perf:
    avg_hit = np.mean([np.mean(p["hit"]) for p in perf])
    st.metric("平均命中", f"{avg_hit:.2f}")

    roi = calculate_roi(perf)
    st.metric("總收益", f"{roi} 元")

# ==============================
# 預測
# ==============================
if st.button("🚀 AI下注決策"):

    bet_flag = should_bet(perf)

    if state["lose_streak"] >= 5:
        st.error("❌ 連輸過多 → 停手")
        bet_flag = False

    if not bet_flag:
        st.warning("⚠️ 本期建議不下注")
    else:
        scores = get_scores(history)

        main = pick_numbers(scores)
        sub = pick_random()

        st.subheader("💰 投資組合（100元）")

        st.success(f"主注（70元）：{' - '.join(map(str,main))}")
        st.success(f"副注（30元）：{' - '.join(map(str,sub))}")

        save_json("last_bet.json", {
            "bets":[main,sub],
            "target": len(history)
        })

# ==============================
# 驗證
# ==============================
if os.path.exists("last_bet.json"):

    last = json.load(open("last_bet.json"))
    idx = last["target"]

    if len(history) > idx:

        draw = history[idx]

        hits = []
        for b in last["bets"]:
            hits.append(len(set(b)&set(draw)))

        perf.append({
            "draw": draw,
            "hit": hits
        })

        save_json(PERF_FILE, perf)

        # 更新連輸
        if max(hits) < 2:
            state["lose_streak"] += 1
        else:
            state["lose_streak"] = 0

        save_json(STATE_FILE, state)

        os.remove("last_bet.json")

        st.success(f"✅ 本期命中：{hits}")

# ==============================
# 重抓
# ==============================
if st.button("🔄 重抓資料"):
    st.cache_data.clear()
    st.rerun()