import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter

# ==========================================
# 核心計算引擎 (V15.5 終極戰略版)
# ==========================================

def analyze_full_history(history):
    all_draws = [num for sublist in history for num in sublist]
    counts = Counter(all_draws)
    hot_numbers = [num for num, _ in counts.most_common(10)]
    
    # 遺漏號分析 (最近 15 期未出的冷門黑馬)
    recent_15_draws = [num for sublist in history[:15] for num in sublist]
    missing_numbers = [n for n in range(1, 40) if n not in recent_15_draws]
    
    # 避險：連開兩期攔截 (防止連三開)
    danger_numbers = set()
    if len(history) >= 2:
        danger_numbers = set(history[0]).intersection(set(history[1]))
    
    return {
        "hot": hot_numbers, 
        "missing": missing_numbers,
        "latest": history[0],
        "danger_numbers": danger_numbers
    }

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
        metrics_list.append({
            "ac": ac, "streak": max_streak, "sum": total_sum,
            "odd": odd, "even": 5-odd, "nums": nums
        })
    return metrics_list

def get_god_score_batch(metrics_list, patterns, trend_mode):
    scores = []
    for m in metrics_list:
        nums = m['nums']
        base = m['ac'] * 35 
        first_num = nums[0]
        s = m['sum']
        
        # --- 1. 戰略模式：正負 5 區間權重 ---
        if trend_mode == "強力回歸 (首碼區間 06±5, 總和~90)":
            dist_06 = abs(first_num - 6)
            if dist_06 <= 5: # 區間 01-11
                base += 110 - (dist_06 * 8)
            else:
                base -= (dist_06 - 5) * 35
            target_sum = 90
            sum_weight = 2.0
            
        else: # 高位震盪模式 (咖啡震盪)
            dist_15 = abs(first_num - 15)
            if dist_15 <= 5: # 區間 10-20
                base += 125 - (dist_15 * 8)
            else:
                base -= (dist_15 - 5) * 40
            target_sum = 130
            sum_weight = 2.5 

        # --- 2. 總和與歷史聯動 ---
        base -= abs(s - target_sum) * sum_weight
        
        # 遺漏號補償
        missing_hits = len(set(nums).intersection(patterns['missing']))
        base += (missing_hits * 15)
        
        # 避險攔截
        danger_hits = len(set(nums).intersection(patterns['danger_numbers']))
        base -= (danger_hits * 160)

        # --- 3. 科學過濾 ---
        if m['streak'] == 2: base += 45
        elif m['streak'] >= 3: base -= 150
        if m['odd'] in [2, 3]: base += 40
            
        entropy = random.uniform(0, 45)
        scores.append(round(base + entropy, 2))
    return scores

# ==========================================
# UI 介面
# ==========================================

st.set_page_config(page_title="Gauss Master V15.5", page_icon="💎", layout="wide")
st.title("💎 Gauss Master Pro V15.5 戰略區間版")

st.sidebar.header("🕹️ 指揮控制中心")
trend_mode = st.sidebar.radio(
    "預測下一期走勢：",
    ("強力回歸 (首碼區間 06±5, 總和~90)", "高位震盪 (首碼區間 15±5, 總和~130)")
)

uploaded_file = st.file_uploader("上傳 539 歷史 Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for _, row in df.iterrows():
            row_numbers = []
            for cell in row:
                nums_in_cell = re.findall(r'\d+', str(cell))
                for n in nums_in_cell: row_numbers.append(int(n))
            clean_nums = [n for n in row_numbers if 1 <= n <= 39]
            if len(clean_nums) >= 5: history.append(clean_nums[:5])

        if history:
            patterns = analyze_full_history(history)
            st.success(f"✅ 資料載入成功！最新期號：{history[0]}")
            
            if st.button("啟動 57 萬次戰略模擬"):
                progress_bar = st.progress(0)
                all_candidates = []
                batch_size = 15000
                total_sims = 570000
                
                for i in range(0, total_sims, batch_size):
                    raw_combos = [random.sample(range(1, 40), 5) for _ in range(batch_size)]
                    metrics = get_metrics_batch(raw_combos)
                    scores = get_god_score_batch(metrics, patterns, trend_mode)
                    
                    for m, s in zip(metrics, scores):
                        if s > 215: 
                            all_candidates.append({"combo": m['nums'], "score": s, "sum": m['sum'], "odd": m['odd']})
                    progress_bar.progress((i + batch_size) / total_sims)
                
                final_top = sorted(all_candidates, key=lambda x: x['score'], reverse=True)[:5]
                st.subheader(f"👑 {trend_mode} - 天選精選")
                
                res_df = []
                for idx, item in enumerate(final_top):
                    c = item['combo']
                    res_df.append({
                        "排名": f"Top {idx+1}",
                        "推薦組合": ", ".join([f"{x:02d}" for x in c]),
                        "總和": item['sum'],
                        "首碼": c[0],
                        "奇偶比": f"{item['odd']}:{5-item['odd']}",
                        "綜合評分": item['score']
                    })
                st.table(pd.DataFrame(res_df))
                st.balloons()
    except Exception as e:
        st.error(f"錯誤: {e}")
