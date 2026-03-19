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

# ==============================
# Configuration & Paths
# ==============================
CSV_PATH = "539_history.csv"
WEIGHT_PATH = "v54_weights.json"
MAX_HISTORY = 1770

# ==============================
# Data Fetching (Stable Method)
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
            
            if not page_data:
                break
            all_data.extend(page_data)
            page += 1
            
            progress = min(len(all_data) / target, 1.0)
            progress_bar.progress(progress)
            
        except Exception as e:
            st.error(f"連線中斷: {e}")
            break

    status_text.empty()
    progress_bar.empty()
    return all_data[:target][::-1]

@st.cache_data(ttl=10800)
def load_history():
    data = fetch_all_history(MAX_HISTORY)
    pd.DataFrame(data).to_csv(CSV_PATH, index=False)
    return data

# ==============================
# Trigger Conditions
# ==============================
def cond_extreme(d): return min(d) >= 21
def cond_big(d): return min(d) >= 20
def cond_tail_heavy(d):
    tails = [n % 10 for n in d]
    return max(Counter(tails).values()) >= 3

# ==============================
# Advanced Cross-Weight Logic
# ==============================
def calculate_cross_weights(history):
    """分析特定事件發生後，下一期哪些號碼機率顯著提高"""
    biases = {
        "extreme": {i: 0.0 for i in range(1, 40)},
        "big": {i: 0.0 for i in range(1, 40)},
        "tail": {i: 0.0 for i in range(1, 40)}
    }
    
    counts = {"extreme": 0, "big": 0, "tail": 0}
    
    avg_prob = 5 / 39  # 理論平均出現率
    
    for i in range(len(history) - 1):
        curr, nxt = history[i], history[i+1]
        
        # 1. 極端大號後
        if cond_extreme(curr):
            counts["extreme"] += 1
            for n in nxt: biases["extreme"][n] += 1
            
        # 2. 全大號後
        if cond_big(curr):
            counts["big"] += 1
            for n in nxt: biases["big"][n] += 1
            
        # 3. 尾數集中後
        if cond_tail_heavy(curr):
            counts["tail"] += 1
            for n in nxt: biases["tail"][n] += 1
            
    # 標準化偏好值 (實際率 - 理論率)
    for key in biases:
        if counts[key] > 0:
            for n in range(1, 40):
                actual_rate = biases[key][n] / counts[key]
                biases[key][n] = actual_rate - avg_prob
                
    return biases

# ==============================
# Scoring Model
# ==============================
def get_number_scores(history, biases):
    # 最新狀態
    last_draw = history[-1]
    active_signals = {
        "extreme": cond_extreme(last_draw),
        "big": cond_big(last_draw),
        "tail": cond_tail_heavy(last_draw)
    }
    
    # 基礎機率 (短/中/長期頻率)
    short_freq = Counter([n for d in history[-30:] for n in d])
    mid_freq = Counter([n for d in history[-100:] for n in d])
    
    scores = {}
    for n in range(1, 40):
        # 基礎分數: 頻率權重
        base = (short_freq[n] * 0.6) + (mid_freq[n] * 0.4)
        
        # 間隔分數: 遺漏值 (冷熱號平衡)
        gap = 0
        for i, d in enumerate(reversed(history)):
            if n in d:
                gap = i
                break
        cold_bonus = min(gap / 20, 1.5) # 遺漏越久分數微增
        
        # 事件偏好補償 (Cross-Weight Logic)
        cross_bonus = 0
        for signal, active in active_signals.items():
            if active:
                cross_bonus += biases[signal][n] * 10 # 放大權重影響
        
        # 隨機擾動
        noise = random.uniform(0, 0.5)
        
        scores[n] = max(0.1, base + cold_bonus + cross_bonus + noise)
        
    return scores

# ==============================
# AI Recommendation Engine
# ==============================
def valid_combo(c):
    s = sum(c)
    # 539 常見總和區間 80-140
    if not (75 <= s <= 145): return False
    # 奇偶比儘量不為全奇或全偶
    odd_count = sum(1 for n in c if n % 2 != 0)
    if odd_count == 0 or odd_count == 5: return False
    return True

def ai_recommend(history, biases):
    scores_dict = get_number_scores(history, biases)
    
    nums = np.array(list(scores_dict.keys()))
    scores = np.array(list(scores_dict.values()))
    
    # 將分數轉為機率分布 (Probability Distribution)
    probs = scores / scores.sum()
    
    recommendations = []
    attempts = 0
    while len(recommendations) < 3 and attempts < 2000:
        # 根據機率分佈抽取不重複的5個號碼
        combo = np.random.choice(nums, 5, replace=False, p=probs)
        combo = sorted([int(x) for x in combo])
        
        if valid_combo(combo) and combo not in recommendations:
            recommendations.append(combo)
        attempts += 1
        
    return recommendations

# ==============================
# Streamlit UI
# ==============================
st.set_page_config(page_title="539 AI V54 Professional", layout="wide")

st.title("🎯 539 AI V54 專業預測系統")
st.caption("基於 Cross-Event 關聯權重與機率分佈模型")

if st.button("🔄 同步最新歷史資料"):
    st.cache_data.clear()
    if os.path.exists(CSV_PATH): os.remove(CSV_PATH)
    st.rerun()

history = load_history()
biases = calculate_cross_weights(history)

# 顯示目前狀態
st.divider()
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("📈 數據概況")
    st.metric("已載入期數", len(history))
    st.write("目前觸發事件:")
    if cond_extreme(history[-1]): st.warning("⚠️ 觸發: 極端大號區")
    if cond_big(history[-1]): st.warning("⚠️ 觸發: 全大趨勢")
    if cond_tail_heavy(history[-1]): st.warning("⚠️ 觸發: 尾數高度集中")
    else: st.info("ℹ️ 當前為常規分布")

with col2:
    st.subheader("📅 最新開獎記錄")
    cols = st.columns(5)
    for i, d in enumerate(history[-5:][::-1]):
        cols[i].metric(f"前 {i+1} 期", " ".join(f"{x:02d}" for x in d))

# 執行預測
st.divider()
if st.button("🚀 啟動 AI 權重模擬預測", use_container_width=True):
    with st.spinner('正在分析機率矩陣...'):
        recs = ai_recommend(history, biases)
        
    st.subheader("🎯 AI 推薦組合 (經由機率權重篩選)")
    res_cols = st.columns(3)
    for i, r in enumerate(recs):
        res_cols[i].success(f"### {' - '.join(f'{x:02d}' for x in r)}")
    
    st.info("💡 提示：本模型使用加權機率抽取，每次點擊結果可能不同。")

st.divider()
with st.expander("🛠 系統說明"):
    st.write("""
    - **Cross-Event 邏輯**: 系統不只看單號頻率，還會計算如「上一期開大號時，下一期各號碼的偏移率」。
    - **加權抽取**: 捨棄純隨機，改用機率分布(Softmax-like)進行抽樣，分數越高的號碼被選中機會越高。
    - **過濾器**: 自動過濾掉總和小於75或大於145，以及全奇數/全偶數的不合理組合。
    """)

