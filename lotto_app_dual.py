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

st.set_page_config(page_title="539 AI V70 進化版", layout="wide")

PERF_FILE = "performance.json"
PRED_FILE = "prediction.json"
WEIGHT_FILE = "weights.json"

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
# 市場判斷
# ==============================
def detect_market(history):
    last20 = history[-20:]
    nums = [n for d in last20 for n in d]
    avg = np.mean(nums)

    if avg > 23:
        return "熱盤"
    elif avg < 17:
        return "冷盤"
    else:
        return "均衡"

# ==============================
# 策略
# ==============================
def strategy_trend(history):
    last30 = history[-30:]
    freq = Counter([n for d in last30 for n in d])
    return [n for n,_ in freq.most_common(5)]

def strategy_cold(history):
    last50 = history[-50:]
    freq = Counter([n for d in last50 for n in d])
    cold = sorted(range(1,40), key=lambda x: freq[x])[:15]
    return random.sample(cold,5)

def strategy_mutation(history):
    pool = list(range(1,40))
    return sorted(random.sample(pool,5))

# ==============================
# 權重
# ==============================
def load_weights():
    if os.path.exists(WEIGHT_FILE):
        return json.load(open(WEIGHT_FILE))
    return {"trend":1.0,"cold":1.0,"mutate":1.0}

def save_weights(w):
    json.dump(w, open(WEIGHT_FILE,"w"))

# ==============================
# 融合（市場適應）
# ==============================
def combine(s1,s2,s3,w,market):
    score = Counter()

    # 市場影響
    if market == "熱盤":
        w["cold"] *= 1.2
        w["trend"] *= 0.9
    elif market == "冷盤":
        w["trend"] *= 1.2

    for n in s1: score[n]+=w["trend"]
    for n in s2: score[n]+=w["cold"]
    for n in s3: score[n]+=w["mutate"]

    return sorted([n for n,_ in score.most_common(5)])

# ==============================
# 評估
# ==============================
def evaluate(pred, draw):
    return len(set(pred)&set(draw))

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V70（策略進化系統）")

history = load_history()
weights = load_weights()
market = detect_market(history)

st.write(f"📊 市場狀態：{market}")
st.write("⚙️ 權重：", weights)

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(f"{x:02d}" for x in d))

# ==============================
# 驗證
# ==============================
if os.path.exists(PRED_FILE):
    last = json.load(open(PRED_FILE))

    idx = last.get("target", last.get("target_index"))

    if len(history) > idx:

        draw = history[idx]

        hit_t = evaluate(last["trend"], draw)
        hit_c = evaluate(last["cold"], draw)
        hit_m = evaluate(last["mutate"], draw)

        # 🔥 指數學習
        weights["trend"] *= (1 + (hit_t-1)*0.15)
        weights["cold"] *= (1 + (hit_c-1)*0.15)
        weights["mutate"] *= (1 + (hit_m-1)*0.15)

        # 淘汰機制
        for k in weights:
            if weights[k] < 0.3:
                weights[k] = 0.5  # 重生

        save_weights(weights)
        os.remove(PRED_FILE)

        st.success(f"命中 → 趨勢:{hit_t} 冷門:{hit_c} 變異:{hit_m}")

# ==============================
# 預測
# ==============================
if st.button("🚀 AI進化預測"):

    s1 = strategy_trend(history)
    s2 = strategy_cold(history)
    s3 = strategy_mutation(history)

    final = combine(s1,s2,s3,weights.copy(),market)

    st.subheader("💰 推薦號碼")
    st.success(" - ".join(f"{n:02d}" for n in final))

    json.dump({
        "trend":s1,
        "cold":s2,
        "mutate":s3,
        "target":len(history)
    }, open(PRED_FILE,"w"))

    st.info("📌 已進入下一期學習")

# 重抓
if st.button("🔄 重抓資料"):
    st.cache_data.clear()
    st.rerun()