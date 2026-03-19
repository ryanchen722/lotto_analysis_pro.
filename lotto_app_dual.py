import random
import streamlit as st
import requests
import re
import os
import json
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from collections import Counter

# --- 必須是 Streamlit 的第一個指令 ---
st.set_page_config(page_title="539 AI V54.2 Pro", layout="wide")

# 嘗試匯入 Plotly
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ==============================
# 數據抓取
# ==============================
def fetch_all_history(target=1770):
    headers = {"User-Agent": "Mozilla/5.0"}
    all_data = []
    page = 1
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    while len(all_data) < target:
        status_text.text(f"正在抓取第 {page} 頁歷史資料...")
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
            
            if not page_data: break
            all_data.extend(page_data)
            page += 1
            progress_bar.progress(min(len(all_data) / target, 1.0))
        except: break

    status_text.empty()
    progress_bar.empty()
    return all_data[:target][::-1]

@st.cache_data(ttl=10800)
def load_history():
    return fetch_all_history()

# ==============================
# 核心運算邏輯 (同前版本)
# ==============================
def cond_extreme(d): return min(d) >= 21
def cond_big(d): return min(d) >= 20
def cond_tail_heavy(d):
    tails = [n % 10 for n in d]
    return max(Counter(tails).values()) >= 3

def calculate_cross_weights(history):
    biases = {k: {i: 0.0 for i in range(1, 40)} for k in ["extreme", "big", "tail"]}
    counts = {"extreme": 0, "big": 0, "tail": 0}
    for i in range(len(history) - 1):
        curr, nxt = history[i], history[i+1]
        if cond_extreme(curr):
            counts["extreme"] += 1
            for n in nxt: biases["extreme"][n] += 1
        if cond_big(curr):
            counts["big"] += 1
            for n in nxt: biases["big"][n] += 1
        if cond_tail_heavy(curr):
            counts["tail"] += 1
            for n in nxt: biases["tail"][n] += 1
            
    avg_prob = 5 / 39
    for k in biases:
        if counts[k] > 0:
            for n in range(1, 40):
                biases[k][n] = (biases[k][n] / counts[k]) - avg_prob
    return biases

def get_number_scores(history, biases):
    last_draw = history[-1]
    signals = {"extreme": cond_extreme(last_draw), "big": cond_big(last_draw), "tail": cond_tail_heavy(last_draw)}
    short_freq = Counter([n for d in history[-30:] for n in d])
    scores = {}
    for n in range(1, 40):
        base = short_freq[n] * 0.8
        gap = next((i for i, d in enumerate(reversed(history)) if n in d), 50)
        cross_bonus = sum(biases[sig][n] * 15 for sig, active in signals.items() if active)
        scores[n] = max(0.1, base + (gap / 15) + cross_bonus + random.uniform(0, 0.5))
    return scores

def ai_recommend_prob(history, biases):
    scores_dict = get_number_scores(history, biases)
    nums = np.array(list(scores_dict.keys()))
    scores = np.array(list(scores_dict.values()))
    probs = scores / scores.sum()
    recs = []
    for _ in range(1000):
        combo = sorted([int(x) for x in np.random.choice(nums, 5, replace=False, p=probs)])
        if combo not in recs:
            recs.append(combo)
            if len(recs) >= 3: break
    return recs

# ==============================
# UI 顯示介面
# ==============================
st.title("🎯 539 AI V54.2 智能熱區預測")

history = load_history()
biases = calculate_cross_weights(history)

# --- 新增：最新五期資料 ---
st.subheader("📅 最新五期開獎紀錄")
draw_cols = st.columns(5)
# 取最後五期並反轉，讓最新的一期排在最左邊
latest_five = history[-5:][::-1]
for i, draw in enumerate(latest_five):
    with draw_cols[i]:
        st.markdown(f"**前 {i+1} 期**")
        # 05, 23, 25, 30, 37 這種格式
        st.code(" ".join(f"{x:02d}" for x in draw))

st.divider()

# --- 熱度分析圖表 ---
st.subheader("📊 號碼熱度分析 (近 50 期)")
short_term = Counter([n for d in history[-50:] for n in d])
heat_df = pd.DataFrame([{"號碼": n, "出現次數": short_term[n], 
                         "狀態": "🔥 熱門" if short_term[n] > 8 else ("❄️ 冷門" if short_term[n] < 4 else "⚖️ 正常")} 
                        for n in range(1, 40)])

if HAS_PLOTLY:
    fig = px.bar(heat_df, x="號碼", y="出現次數", color="狀態",
                 color_discrete_map={"🔥 熱門": "#FF4B4B", "❄️ 冷門": "#1C83E1", "⚖️ 正常": "#00C496"})
    st.plotly_chart(fig, use_container_width=True)

# --- 預測區塊 ---
st.divider()
if st.button("🚀 啟動 AI 混合策略預測", use_container_width=True):
    with st.spinner('正在分析數據規律...'):
        strategy_1 = ai_recommend_prob(history, biases)[0]
        
        # 策略 2: 熱冷混合
        hot_list = heat_df[heat_df["狀態"] == "🔥 熱門"]["號碼"].tolist()
        cold_list = heat_df[heat_df["狀態"] == "❄️ 冷門"]["號碼"].tolist()
        if len(hot_list) >= 2 and len(cold_list) >= 2:
            s2 = sorted(random.sample(hot_list, 2) + random.sample(cold_list, 2) + [random.randint(1,39)])
        else:
            s2 = ai_recommend_prob(history, biases)[1]
            
        # 策略 3: 基於上一期 05,23,25,30,37 的區間修正
        # 針對 10-22 這個大空檔進行補償
        mid_zone = [n for n in range(10, 23)]
        s3 = sorted(random.sample(mid_zone, 3) + random.sample(range(1, 40), 2))

    st.subheader("🎯 AI 推薦組合")
    res_cols = st.columns(3)
    labels = ["機率權重最佳化", "熱冷混合平衡", "中段區間修正"]
    for i, r in enumerate([strategy_1, s2, s3]):
        res_cols[i].markdown(f"**{labels[i]}**")
        res_cols[i].success(f"### {' - '.join(f'{x:02d}' for x in r)}")

if st.button("🔄 重整並同步歷史資料"):
    st.cache_data.clear()
    st.rerun()
