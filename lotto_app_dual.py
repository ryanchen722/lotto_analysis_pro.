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

st.set_page_config(page_title="539 AI V68 正確預測版", layout="wide")

PERF_FILE = "performance.json"
PRED_FILE = "prediction.json"

# ==============================
# 抓資料
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

    return all_data[:target][::-1]

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

def strategy_random():
    return sorted(random.sample(range(1,40),5))

# ==============================
# 融合
# ==============================
def combine(s1, s2, s3):
    score = Counter()

    for n in s1: score[n] += 1.2
    for n in s2: score[n] += 1.0
    for n in s3: score[n] += 0.8

    return sorted([n for n,_ in score.most_common(5)])

# ==============================
# 檔案操作
# ==============================
def load_json(file):
    if os.path.exists(file):
        return json.load(open(file))
    return None

def save_json(file, data):
    json.dump(data, open(file,"w"))

# ==============================
# 命中計算
# ==============================
def evaluate(bets, draw):
    res = []
    for b in bets:
        hit = len(set(b) & set(draw))
        res.append(hit)
    return res

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V68（正確預測系統）")

history = load_history()

# 顯示最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(f"{x:02d}" for x in d))

# ==============================
# ⭐ 先做「上一期預測驗證」
# ==============================
last_pred = load_json(PRED_FILE)
perf = load_json(PERF_FILE) or []

if last_pred:
    target_index = last_pred["target_index"]

    if len(history) > target_index:
        draw = history[target_index]

        hits = evaluate(last_pred["bets"], draw)

        perf.append({
            "期數": target_index,
            "開獎": draw,
            "命中": hits
        })

        save_json(PERF_FILE, perf)
        os.remove(PRED_FILE)

        st.success(f"✅ 已驗證上一期 → 命中 {hits}")

# ==============================
# 顯示績效
# ==============================
if perf:
    df = pd.DataFrame(perf)

    st.subheader("📊 歷史績效")
    st.dataframe(df.tail(20))

    avg_hit = np.mean([np.mean(x) for x in df["命中"]])
    st.metric("平均命中", f"{avg_hit:.2f}")

# ==============================
# AI預測
# ==============================
if st.button("🚀 AI預測下一期"):

    s1 = strategy_trend(history)
    s2 = strategy_cold(history)
    s3 = strategy_random()

    final = combine(s1, s2, s3)

    bet1 = final
    bet2 = sorted(random.sample(range(1,40),5))

    st.subheader("💰 投資組合（下一期）")
    st.success(" - ".join(f"{n:02d}" for n in bet1))
    st.success(" - ".join(f"{n:02d}" for n in bet2))

    # ⭐ 存預測（重點）
    save_json(PRED_FILE, {
        "bets": [bet1, bet2],
        "target_index": len(history)   # 下一期
    })

    st.info("📌 已記錄預測，等下一期開獎自動驗證")

# ==============================
# 重抓
# ==============================
if st.button("🔄 重抓資料"):
    st.cache_data.clear()
    st.rerun()