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

st.set_page_config(page_title="539 AI V72 投資系統", layout="wide")

PERF_FILE = "perf_v72.json"
STATE_FILE = "state_v72.json"

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
def score_numbers(history):

    scores = {}
    freq = Counter([n for d in history[-30:] for n in d])

    for n in range(1,40):
        gap = next((i for i,d in enumerate(reversed(history)) if n in d),50)
        scores[n] = freq[n] + gap/10

    return scores

def pick_numbers(scores):
    nums = sorted(scores, key=scores.get, reverse=True)
    return sorted(nums[:5])

# ==============================
# 信心計算
# ==============================
def calc_confidence(perf):

    if len(perf) < 10:
        return 0.5

    last10 = perf[-10:]
    avg_hit = np.mean([p["hit"] for p in last10])

    # 轉換成信心值
    return min(avg_hit, 1.2)

# ==============================
# 下注策略
# ==============================
def decide_bet(conf, lose_streak):

    if lose_streak >= 5:
        return "STOP", 0

    if conf < 0.6:
        return "SKIP", 0
    elif conf < 0.7:
        return "OBSERVE", 0
    elif conf < 0.8:
        return "SMALL", 50
    elif conf < 1.0:
        return "NORMAL", 100
    else:
        return "AGGRESSIVE", 150

# ==============================
# 評估
# ==============================
def evaluate(pred, draw):
    return len(set(pred) & set(draw))

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V72（下注強度系統）")

history = load_history()

perf = load_json(PERF_FILE, [])
state = load_json(STATE_FILE, {"lose_streak":0})

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(map(str,d)))

# ==============================
# 信心
# ==============================
conf = calc_confidence(perf)

st.subheader("🧠 模型狀態")
st.metric("信心分數", f"{conf:.2f}")
st.write(f"連輸次數：{state['lose_streak']}")

mode, amount = decide_bet(conf, state["lose_streak"])

st.subheader("🎯 建議策略")

if mode == "STOP":
    st.error("❌ 停手（連輸過多）")
elif mode == "SKIP":
    st.warning("⚠️ 不下注")
elif mode == "OBSERVE":
    st.info("👀 觀察期")
elif mode == "SMALL":
    st.success("💰 小注 50 元")
elif mode == "NORMAL":
    st.success("💰 正常下注 100 元")
else:
    st.success("🚀 加碼 150 元")

# ==============================
# 預測
# ==============================
if st.button("🚀 產生號碼"):

    scores = score_numbers(history)

    bet1 = pick_numbers(scores)
    bet2 = sorted(random.sample(range(1,40),5))

    st.subheader("🎯 號碼")
    st.write("主注：", bet1)
    st.write("副注：", bet2)

    st.session_state["bets"] = [bet1, bet2]
    st.session_state["index"] = len(history)

# ==============================
# 驗證
# ==============================
if "bets" in st.session_state:

    idx = st.session_state["index"]

    if len(history) > idx:

        draw = history[idx]

        hits = []
        for b in st.session_state["bets"]:
            hits.append(evaluate(b, draw))

        # 存績效
        for h in hits:
            perf.append({"draw": draw, "hit": h})

        save_json(PERF_FILE, perf)

        # 更新連輸
        if max(hits) < 2:
            state["lose_streak"] += 1
        else:
            state["lose_streak"] = 0

        save_json(STATE_FILE, state)

        del st.session_state["bets"]

        st.success(f"✅ 命中：{hits}")

# ==============================
# 顯示績效
# ==============================
if perf:
    df = pd.DataFrame(perf)
    st.subheader("📊 績效")
    st.dataframe(df.tail(20))

    st.metric("平均命中", f"{df['hit'].mean():.2f}")

# 重抓
if st.button("🔄 重抓資料"):
    st.cache_data.clear()
    st.rerun()