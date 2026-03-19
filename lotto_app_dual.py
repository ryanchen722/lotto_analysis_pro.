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

# --- MUST BE THE VERY FIRST STREAMLIT COMMAND ---
st.set_page_config(page_title="539 AI V54.1 Pro", layout="wide")

# Try to import plotly, handle if missing
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ==============================
# Configuration & Paths
# ==============================
CSV_PATH = "539_history.csv"
MAX_HISTORY = 1770

# ==============================
# Data Fetching
# ==============================
def fetch_all_history(target=MAX_HISTORY):
    headers = {"User-Agent": "Mozilla/5.0"}
    all_data = []
    page = 1
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    while len(all_data) < target:
        status_text.text(f"正在爬取第 {page} 頁資料...")
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
    data = fetch_all_history(MAX_HISTORY)
    return data

# ==============================
# Logic & Analysis
# ==============================
def cond_extreme(d): return min(d) >= 21
def cond_big(d): return min(d) >= 20
def cond_tail_heavy(d):
    tails = [n % 10 for n in d]
    return max(Counter(tails).values()) >= 3

def calculate_cross_weights(history):
    biases = {k: {i: 0.0 for i in range(1, 40)} for k in ["extreme", "big", "tail"]}
    counts = {"extreme": 0, "big": 0, "tail": 0}
    avg_prob = 5 / 39
    
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

def valid_combo(c):
    s = sum(c)
    odd_count = sum(1 for n in c if n % 2 != 0)
    return (75 <= s <= 145) and (1 <= odd_count <= 4)

def ai_recommend_prob(history, biases):
    scores_dict = get_number_scores(history, biases)
    nums, scores = np.array(list(scores_dict.keys())), np.array(list(scores_dict.values()))
    probs = scores / scores.sum()
    
    recs = []
    for _ in range(2000):
        combo = sorted([int(x) for x in np.random.choice(nums, 5, replace=False, p=probs)])
        if valid_combo(combo) and combo not in recs:
            recs.append(combo)
            if len(recs) >= 3: break
    return recs

# ==============================
# UI Rendering
# ==============================
st.title("🎯 539 AI V54.1 (熱區與冷區強化版)")

history = load_history()
biases = calculate_cross_weights(history)

# --- Heat Map ---
st.subheader("📊 號碼熱度分析 (近 50 期)")
short_term = Counter([n for d in history[-50:] for n in d])
heat_data = [{"Number": n, "Count": short_term[n], 
              "Status": "🔥 Hot" if short_term[n] > 8 else ("❄️ Cold" if short_term[n] < 4 else "⚖️ Normal")} 
             for n in range(1, 40)]
heat_df = pd.DataFrame(heat_data)

if HAS_PLOTLY:
    fig = px.bar(heat_df, x="Number", y="Count", color="Status",
                 color_discrete_map={"🔥 Hot": "#ef553b", "❄️ Cold": "#636efa", "⚖️ Normal": "#00cc96"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.table(heat_df.T)

# --- Zones ---
c1, c2 = st.columns(2)
hot_list = heat_df[heat_df["Status"] == "🔥 Hot"]["Number"].tolist()
cold_list = heat_df[heat_df["Status"] == "❄️ Cold"]["Number"].tolist()
c1.error(f"🔥 熱門區: {', '.join(f'{x:02d}' for x in hot_list)}")
c2.info(f"❄️ 冷門區: {', '.join(f'{x:02d}' for x in cold_list)}")

# --- Prediction ---
st.divider()
if st.button("🚀 啟動 AI 混合策略預測", use_container_width=True):
    with st.spinner('計算中...'):
        strategy_1 = ai_recommend_prob(history, biases)[0]
        
        # Strategy 2: Hot/Cold Mix
        if len(hot_list) >= 2 and len(cold_list) >= 2:
            s2 = sorted(random.sample(hot_list, 2) + random.sample(cold_list, 2) + [random.randint(1,39)])
        else:
            s2 = ai_recommend_prob(history, biases)[1]
            
        # Strategy 3: Correction (Focus on 10-22 zone missing from 05,23,25,30,37)
        mid_zone = [n for n in range(10, 23) if n not in history[-1]]
        s3 = sorted(random.sample(mid_zone, 3) + random.sample(range(1, 40), 2))

    res_cols = st.columns(3)
    labels = ["機率最佳化", "熱冷混合平衡", "區間校正 (10-22)"]
    for i, r in enumerate([strategy_1, s2, s3]):
        res_cols[i].markdown(f"**{labels[i]}**")
        res_cols[i].success(f"### {' - '.join(f'{x:02d}' for x in r)}")

if st.button("🔄 同步歷史資料"):
    st.cache_data.clear()
    st.rerun()
