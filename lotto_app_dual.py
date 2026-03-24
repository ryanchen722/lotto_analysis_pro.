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
st.set_page_config(page_title="539 AI V54.7 Pro", layout="wide")

# 嘗試匯入 Plotly
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ==============================
# 數據抓取
# ==============================
@st.cache_data(ttl=10800)
def load_history():
    target = 1770
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

# ==============================
# 運算邏輯
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

def get_health_label(combo):
    odd = sum(1 for n in combo if n % 2 != 0)
    big = sum(1 for n in combo if n >= 20)
    is_balanced = (2 <= odd <= 3) and (2 <= big <= 3)
    return f"奇偶{odd}:{5-odd} | 大小{big}:{5-big} " + ("✅平衡" if is_balanced else "⚠️偏激")

# ==============================
# UI 顯示介面
# ==============================
st.title("🎯 539 AI V54.7 投資最大化決策系統")

history = load_history()
biases = calculate_cross_weights(history)

# --- 最新五期資料 ---
st.subheader("📅 最新五期開獎紀錄")
draw_cols = st.columns(5)
latest_five = history[-5:][::-1]
for i, draw in enumerate(latest_five):
    with draw_cols[i]:
        st.markdown(f"**前 {i+1} 期**")
        st.code(" ".join(f"{x:02d}" for x in draw))

st.divider()

# --- 熱度與尾數分析 ---
col_charts = st.columns(2)
with col_charts[0]:
    st.subheader("📊 號碼熱度分析")
    short_term = Counter([n for d in history[-50:] for n in d])
    heat_df = pd.DataFrame([{"號碼": n, "出現次數": short_term[n], 
                             "狀態": "🔥 熱門" if short_term[n] > 8 else ("❄️ 冷門" if short_term[n] < 4 else "⚖️ 正常")} 
                            for n in range(1, 40)])
    if HAS_PLOTLY:
        fig_heat = px.bar(heat_df, x="號碼", y="出現次數", color="狀態",
                          color_discrete_map={"🔥 熱門": "#FF4B4B", "❄️ 冷門": "#1C83E1", "⚖️ 正常": "#00C496"})
        st.plotly_chart(fig_heat, use_container_width=True)

with col_charts[1]:
    st.subheader("🧬 尾數能量趨勢")
    recent_20 = history[-20:]
    tail_counts = Counter([n % 10 for d in recent_20 for n in d])
    tail_df = pd.DataFrame([{"尾數": str(t), "能量點": tail_counts[t]} for t in range(10)])
    if HAS_PLOTLY:
        fig_tail = px.line(tail_df, x="尾數", y="能量點", markers=True)
        st.plotly_chart(fig_tail, use_container_width=True)

# --- 預測區塊 (投資最大化) ---
st.divider()
if st.button("🚀 啟動 AI 混合策略預測", use_container_width=True):
    with st.spinner('正在精算能量共鳴與組合健康度...'):
        # 1. 原始三策略
        s1 = ai_recommend_prob(history, biases)[0]
        
        hot_list = heat_df[heat_df["狀態"] == "🔥 熱門"]["號碼"].tolist()
        cold_list = heat_df[heat_df["狀態"] == "❄️ 冷門"]["號碼"].tolist()
        s2_set = set()
        if len(hot_list) >= 2 and len(cold_list) >= 2:
            for n in random.sample(hot_list, 2): s2_set.add(n)
            for n in random.sample(cold_list, 2): s2_set.add(n)
            while len(s2_set) < 5: s2_set.add(random.randint(1, 39))
            s2 = sorted(list(s2_set))
        else: s2 = ai_recommend_prob(history, biases)[1]
            
        mid_zone = [n for n in range(10, 23)]
        s3_set = set(random.sample(mid_zone, 3))
        while len(s3_set) < 5: s3_set.add(random.randint(1, 39))
        s3 = sorted(list(s3_set))

        # --- 100 元最大化邏輯 (Consensus Strategy) ---
        all_picks = s1 + s2 + s3
        consensus_counts = Counter(all_picks)
        # 找出出現 2 次以上的號碼作為「主支核心」
        core_nums = [n for n, count in consensus_counts.items() if count >= 2]
        
        # 為了最大化利益，我們產出 2 組互補注碼
        # 第一注：主支 + 策略一高分號
        bet1_set = set(core_nums)
        for n in s1:
            if len(bet1_set) >= 5: break
            bet1_set.add(n)
        while len(bet1_set) < 5: bet1_set.add(random.randint(1,39))
        bet1 = sorted(list(bet1_set))

        # 第二注：主支 + 策略二/三平衡號
        bet2_set = set(core_nums)
        for n in (s2 + s3):
            if len(bet2_set) >= 5: break
            bet2_set.add(n)
        while len(bet2_set) < 5: bet2_set.add(random.randint(1,39))
        bet2 = sorted(list(bet2_set))

    # --- UI 顯示 ---
    st.subheader("💡 100 元黃金組合 (利益最大化推薦)")
    st.info("邏輯：提取三種 AI 策略的「共鳴號碼」作為主支，並分散在兩組投注中，降低號碼分散風險。")
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.success(f"### 第 1 注：{' - '.join(f'{x:02d}' for x in bet1)}")
        st.caption(get_health_label(bet1))
    with b_col2:
        st.success(f"### 第 2 注：{' - '.join(f'{x:02d}' for x in bet2)}")
        st.caption(get_health_label(bet2))

    st.divider()
    st.subheader("🎯 原始 AI 策略參考")
    res_cols = st.columns(3)
    strategies = [s1, s2, s3]
    titles = ["🏆 機率權重", "⚖️ 能量平衡", "🛠 區間修正"]
    for i, combo in enumerate(strategies):
        with res_cols[i]:
            st.markdown(f"#### {titles[i]}")
            st.code(f"{' - '.join(f'{x:02d}' for x in combo)}")
            st.progress([0.95, 0.88, 0.82][i])

if st.button("🔄 同步歷史資料"):
    st.cache_data.clear()
    st.rerun()
