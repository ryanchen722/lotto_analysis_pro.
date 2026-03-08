import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter

# ==========================================
# 核心計算引擎 (V15.9 多樣化優化版)
# ==========================================

def analyze_full_history(history):
    recent_15_draws = [num for sublist in history[:15] for num in sublist]
    missing_numbers = [n for n in range(1, 40) if n not in recent_15_draws]
    danger_numbers = set()
    if len(history) >= 2:
        danger_numbers = set(history[0]).intersection(set(history[1]))
    return {"missing": missing_numbers, "danger_numbers": danger_numbers}

def get_metrics_batch(combos):
    metrics_list = []
    for nums in combos:
        nums = sorted(list(nums))
        diffs = set()
        for i in range(len(nums)):
            for j in range(i+1, len(nums)):
                diffs.add(abs(nums[i] - nums[j]))
        ac = len(diffs) - (len(nums) - 1)
        total_sum = sum(nums)
        max_streak = 1
        current = 1
        for i in range(1, len(nums)):
            if nums[i] == nums[i-1] + 1:
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 1
        odd = sum(n % 2 for n in nums)
        metrics_list.append({"ac": ac, "streak": max_streak, "sum": total_sum, "odd": odd, "nums": nums})
    return metrics_list

def get_god_score_batch(metrics_list, patterns, trend_mode):
    scores = []
    for m in metrics_list:
        nums = m['nums']
        first_num = nums[0]
        s = m['sum']
        base = m['ac'] * 20 # 降低基礎權重，讓位給區間邏輯
        
        # --- 戰略約束 (區間內一律平等加分) ---
        if "強力回歸" in trend_mode:
            if 1 <= first_num <= 11: base += 200 # 只要在 06±5 內就拿高分
            else: base -= 5000 # 嚴格制裁
            target_sum, sum_margin = 90, 15
        else:
            if 10 <= first_num <= 20: base += 200 # 只要在 15±5 內就拿高分
            else: base -= 5000
            target_sum, sum_margin = 130, 15

        # --- 總和約束 ---
        if abs(s - target_sum) <= sum_margin: base += 100
        else: base -= 5000

        # --- 基礎過濾 ---
        if m['streak'] == 2: base += 30
        if m['odd'] in [2, 3]: base += 30
        
        # --- 歷史避險 ---
        danger_hits = len(set(nums).intersection(patterns['danger_numbers']))
        base -= (danger_hits * 300)

        # 提高熵值 (隨機性)，範圍加大到 100，確保組合不重複
        entropy = random.uniform(0, 100) 
        scores.append(round(base + entropy, 2))
    return scores

# ==========================================
# UI 介面
# ==========================================

st.set_page_config(page_title="Gauss Master V15.9", page_icon="🎯", layout="wide")
st.title("🎯 Gauss Master Pro V15.9 多樣化戰略版")

st.sidebar.header("🕹️ 指揮中心")
trend_mode = st.sidebar.radio("走勢預測：", ("強力回歸 (06±5, 總和 90±15)", "高位震盪 (15±5, 總和 130±15)"))

uploaded_file = st.file_uploader("上傳歷史 Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for _, row in df.iterrows():
            clean_nums = [int(n) for n in re.findall(r'\d+', str(row.values)) if 1 <= int(n) <= 39]
            if len(clean_nums) >= 5: history.append(clean_nums[:5])

        if history:
            patterns = analyze_full_history(history)
            if st.button("啟動 57 萬次多樣化模擬"):
                progress_bar = st.progress(0)
                all_candidates = []
                for i in range(38): # 570,000 / 15,000 = 38
                    raw = [random.sample(range(1, 40), 5) for _ in range(15000)]
                    metrics = get_metrics_batch(raw)
                    scores = get_god_score_batch(metrics, patterns, trend_mode)
                    for m, s in zip(metrics, scores):
                        if s > 0: # 只要是正分，代表完全符合你的區間
                            all_candidates.append({"combo": m['nums'], "score": s, "sum": m['sum']})
                    progress_bar.progress((i+1)/38)
                
                if all_candidates:
                    # 從合格池中隨機打亂，再選出最高分的
                    random.shuffle(all_candidates) 
                    final_top = sorted(all_candidates, key=lambda x: x['score'], reverse=True)[:5]
                    
                    res = []
                    for idx, item in enumerate(final_top):
                        res.append({"排名": f"Top {idx+1}", "推薦組合": ", ".join([f"{x:02d}" for x in item['combo']]), "總和": item['sum'], "首碼": item['combo'][0]})
                    st.table(pd.DataFrame(res))
                    st.balloons()
                else:
                    st.warning("找不到符合條件的組合。")
    except Exception as e: st.error(f"出錯: {e}")
