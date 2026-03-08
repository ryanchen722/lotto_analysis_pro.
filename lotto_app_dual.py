import random
import pd as pd
import streamlit as st
import numpy as np
import re
from collections import Counter

# ==========================================
# 核心計算引擎 (V15.7 嚴格區間版)
# ==========================================

def analyze_full_history(history):
    # 遺漏號分析 (最近 15 期未出的冷門黑馬)
    recent_15_draws = [num for sublist in history[:15] for num in sublist]
    missing_numbers = [n for n in range(1, 40) if n not in recent_15_draws]
    
    # 避險：連開兩期攔截 (防止連三開)
    danger_numbers = set()
    if len(history) >= 2:
        danger_numbers = set(history[0]).intersection(set(history[1]))
    
    return {
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
        
        # --- 1. 戰略模式：首碼區間 (嚴格鎖定) ---
        if "強力回歸" in trend_mode:
            # 中心 06, 區間 [01 - 11]
            if 1 <= first_num <= 11:
                dist_06 = abs(first_num - 6)
                base += 150 - (dist_06 * 5)
            else:
                base -= 1000 # 絕對淘汰
            target_sum = 90
            
        else: # 高位震盪模式 (咖啡震盪)
            # 中心 15, 區間 [10 - 20]
            if 10 <= first_num <= 20:
                dist_15 = abs(first_num - 15)
                base += 150 - (dist_15 * 5)
            else:
                base -= 1000 # 絕對淘汰
            target_sum = 130

        # --- 2. 總和區間 [目標 ± 15] 彈性緩衝 ---
        sum_dist = abs(s - target_sum)
        if sum_dist <= 15:
            base += 50 - (sum_dist * 2)
        else:
            base -= (sum_dist - 15) * 20.0 # 區間外強力扣分
        
        # --- 3. 歷史補償與避險 ---
        missing_hits = len(set(nums).intersection(patterns['missing']))
        base += (missing_hits * 15)
        danger_hits = len(set(nums).intersection(patterns['danger_numbers']))
        base -= (danger_hits * 250)

        # --- 4. 科學過濾 ---
        if m['streak'] == 2: base += 45
        elif m['streak'] >= 3: base -= 250
        if m['odd'] in [2, 3]: base += 40
            
        # 保持極低熵值，讓規則主導結果
        entropy = random.uniform(0, 15) 
        scores.append(round(base + entropy, 2))
    return scores

# ==========================================
# UI 介面
# ==========================================

import pandas as pd
st.set_page_config(page_title="Gauss Master V15.7", page_icon="🎯", layout="wide")
st.title("🎯 Gauss Master Pro V15.7 嚴格戰略版")

st.sidebar.header("🕹️ 指揮控制中心")
trend_mode = st.sidebar.radio(
    "預測下一期走勢：",
    ("強力回歸 (首碼 06±5, 總和 90±15)", "高位震盪 (首碼 15±5, 總和 130±15)")
)

st.sidebar.markdown("---")
st.sidebar.write("**⚠️ 嚴格約束中：**")
if "回歸" in trend_mode:
    st.sidebar.info("🎯 首碼必須：01 - 11\n\n⚖️ 總和必須：75 - 105")
else:
    st.sidebar.warning("🔥 首碼必須：10 - 20\n\n⚖️ 總和必須：115 - 145")

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
            st.success(f"✅ 資料載入成功！最新開獎：{history[0]}")
            
            if st.button("啟動 57 萬次嚴格模擬"):
                progress_bar = st.progress(0)
                all_candidates = []
                batch_size = 15000
                total_sims = 570000
                
                for i in range(0, total_sims, batch_size):
                    raw_combos = [random.sample(range(1, 40), 5) for _ in range(batch_size)]
                    metrics = get_metrics_batch(raw_combos)
                    scores = get_god_score_batch(metrics, patterns, trend_mode)
                    
                    for m, s in zip(metrics, scores):
                        if s > 150: # 嚴格邏輯下基礎分較穩定
                            all_candidates.append({
                                "combo": m['nums'], 
                                "score": s, 
                                "sum": m['sum'], 
                                "odd": m['odd']
                            })
                    progress_bar.progress((i + batch_size) / total_sims)
                
                if all_candidates:
                    final_top = sorted(all_candidates, key=lambda x: x['score'], reverse=True)[:5]
                    st.subheader(f"👑 {trend_mode} - 精選天選組合")
                    
                    res_df = []
                    for idx, item in enumerate(final_top):
                        c = item['combo']
                        res_df.append({
                            "排名": f"Top {idx+1}",
                            "推薦組合": ", ".join([f"{x:02d}" for x in c]),
                            "總和": item['sum'],
                            "首碼": c[0],
                            "奇偶比": f"{item['odd']}:{5-item['odd']}",
                            "評分": item['score']
                        })
                    st.table(pd.DataFrame(res_df))
                    st.balloons()
                else:
                    st.error("此嚴格條件下未能在 57 萬次模擬中找到符合規定的組合，請重新啟動模擬。")
    except Exception as e:
        st.error(f"程式執行出錯: {e}")
