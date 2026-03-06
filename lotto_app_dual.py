import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter

# ==========================================
# 核心計算引擎 (V13.3 避險強化版)
# ==========================================

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
        last_digits = [n % 10 for n in nums]
        same_tail_count = max(Counter(last_digits).values())
        odd = sum(n % 2 for n in nums)
        even = len(nums) - odd

        metrics_list.append({
            "ac": ac, "streak": max_streak,
            "same_tail": same_tail_count, "sum": total_sum,
            "odd": odd, "even": even, "nums": nums
        })
    return metrics_list

def analyze_full_history(history):
    """
    history[0] 為最新一期，history[1] 為前一期
    """
    all_draws = [num for sublist in history for num in sublist]
    counts = Counter(all_draws)
    hot_numbers = [num for num, _ in counts.most_common(12)]
    
    # --- 三連開避險邏輯 ---
    danger_numbers = set()
    if len(history) >= 2:
        latest = set(history[0])
        previous = set(history[1])
        # 找出連續兩期都出現的號碼
        danger_numbers = latest.intersection(previous)
    
    # 拖牌分析：抓取最新一期號碼的鄰居 (±1)
    latest_draw = set(history[0])
    drag_pool = set()
    for n in latest_draw:
        if n > 1: drag_pool.add(n-1)
        drag_pool.add(n) # 包含連莊加權
        if n < 39: drag_pool.add(n+1)
        
    return {
        "hot": hot_numbers, 
        "latest": history[0],
        "drag_pool": drag_pool,
        "danger_numbers": danger_numbers,
        "counts": counts
    }

def get_god_score_batch(metrics_list, patterns):
    scores = []
    for m in metrics_list:
        base = m['ac'] * 30 
        
        # 1. 連號邏輯 (2連號加分，3連號大扣分)
        if m['streak'] == 2:
            base += 40
        elif m['streak'] >= 3:
            base -= 90
            
        # 2. 尾數邏輯
        if m['same_tail'] == 2:
            base += 35
        
        # 3. 冷熱平衡
        hot_in_combo = len(set(m['nums']).intersection(set(patterns['hot'])))
        if 1 <= hot_in_combo <= 2:
            base += 50
            
        # 4. 拖牌與連莊加權
        drag_hits = len(set(m['nums']).intersection(patterns['drag_pool']))
        base += (drag_hits * 15)
        
        # 5. --- 避險：三連開強制冷卻 ---
        danger_hits = len(set(m['nums']).intersection(patterns['danger_numbers']))
        if danger_hits > 0:
            # 已經連開兩期的號碼，第三期出現機率極低，大幅扣分
            base -= (danger_hits * 120)
            
        # 6. 奇偶平衡 (2:3 或 3:2)
        if m['odd'] == 2 or m['odd'] == 3:
            base += 30
            
        # 7. 靈活總和邏輯 (75~125區間)
        s = m['sum']
        if 75 <= s <= 125:
            sum_penalty = 0
        else:
            sum_penalty = abs(s - 100) * 0.8
        
        # 隨機擾動
        entropy = random.uniform(0, 30)
        
        scores.append(round(base + entropy - sum_penalty, 3))
    return scores

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss V13.3 Pro", page_icon="💎", layout="wide")
st.title("💎 Gauss Master Pro V13.3 避險版")
st.markdown("💡 **第一組最新** | **靈活總和** | **自動攔截三連開號碼**")

uploaded_file = st.file_uploader("上傳 539 歷史 Excel (最新在第一列)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for _, row in df.iterrows():
            row_numbers = []
            for cell in row:
                nums_in_cell = re.findall(r'\d+', str(cell))
                for n in nums_in_cell:
                    row_numbers.append(int(n))
            
            clean_nums = [n for n in row_numbers if 1 <= n <= 39]
            if len(clean_nums) >= 5:
                history.append(clean_nums[:5])

        if history:
            history_sorted = [sorted(h) for h in history]
            patterns = analyze_full_history(history_sorted)
            
            st.success(f"✅ 資料載入成功！最新一期：{', '.join(map(str, history[0]))}")
            
            if patterns['danger_numbers']:
                st.warning(f"⚠️ 偵測到過熱號碼 (已連開兩期)：{', '.join(map(str, patterns['danger_numbers']))}。系統已自動調降其權重，避開三連開。")
            
            # --- 數據儀表板 ---
            cols = st.columns(4)
            cols[0].metric("最新期", f"{history[0][0]}, {history[0][1]}...")
            cols[1].metric("避險狀態", "連三開攔截中")
            cols[2].metric("總和策略", "靈活 (75-125)")
            cols[3].metric("運算規模", "570k")

            # --- 模擬計算 ---
            progress_bar = st.progress(0)
            status_text = st.empty()
            batch_size = 15000
            total_sims = 570000
            all_top_candidates = []

            for i in range(0, total_sims, batch_size):
                combos = [random.sample(range(1, 40), 5) for _ in range(batch_size)]
                metrics_list = get_metrics_batch(combos)
                scores = get_god_score_batch(metrics_list, patterns)
                
                for combo_meta, score in zip(metrics_list, scores):
                    if score > 185: 
                        all_top_candidates.append({"combo": combo_meta['nums'], "score": score, "m": combo_meta})
                
                progress_bar.progress((i + batch_size) / total_sims)
                status_text.text(f"天機演算法運算中... {i + batch_size}")

            # --- 結果顯示 ---
            final_pool = sorted(all_top_candidates, key=lambda x: x['score'], reverse=True)[:5]
            
            st.subheader("👑 天機融合最終精選 (V13.3)")
            
            display_data = []
            for idx, item in enumerate(final_pool):
                c = item["combo"]
                m = item["m"]
                display_data.append({
                    "推薦等級": "🔥 至尊首選" if idx == 0 else f"精選組合 {idx+1}",
                    "推薦組合": ", ".join([f"{x:02d}" for x in c]),
                    "綜合評分": item["score"],
                    "總和": m["sum"],
                    "奇偶": f"{m['odd']}:{m['even']}",
                    "AC值": m["ac"]
                })
            
            st.table(pd.DataFrame(display_data))
            st.balloons()
            
        else:
            st.error("未偵測到號碼紀錄。")
    except Exception as e:
        st.error(f"程式運行異常: {e}")
else:
    st.info("👋 上傳 Excel 啟動 V13.3 避險模擬。")
