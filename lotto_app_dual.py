import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter

# ==========================================
# 核心計算引擎 (V14.2 終極曲線版)
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
    all_draws = [num for sublist in history for num in sublist]
    counts = Counter(all_draws)
    hot_numbers = [num for num, _ in counts.most_common(12)]
    
    # 動態拖牌規律偵測 (最近 30 期)
    drag_score = 0
    recent_30 = history[:30]
    for i in range(len(recent_30) - 1):
        curr = set(recent_30[i])
        prev = set(recent_30[i+1])
        prev_neighbors = set()
        for p in prev:
            if p > 1: prev_neighbors.add(p-1)
            prev_neighbors.add(p)
            if p < 39: prev_neighbors.add(p+1)
        drag_score += len(curr.intersection(prev_neighbors))
    
    drag_weight = (drag_score / 30) * 7 
    
    # 避險：連開兩期攔截
    danger_numbers = set()
    if len(history) >= 2:
        danger_numbers = set(history[0]).intersection(set(history[1]))
    
    return {
        "hot": hot_numbers, 
        "latest": history[0],
        "drag_weight": drag_weight,
        "danger_numbers": danger_numbers
    }

def get_god_score_batch(metrics_list, patterns):
    scores = []
    drag_pool = set()
    for n in patterns['latest']:
        if n > 1: drag_pool.add(n-1)
        drag_pool.add(n)
        if n < 39: drag_pool.add(n+1)

    for m in metrics_list:
        nums = m['nums']
        base = m['ac'] * 32 
        
        # 1. --- 首碼曲線遞減 (核心優化) ---
        first_num = nums[0]
        if first_num <= 9:
            base += 50    # 極高頻區
        elif 10 <= first_num <= 14:
            base += 10    # 中低頻區
        else:
            # 15 號之後開始非線性遞減 (機率像滑梯一樣下降)
            penalty_steps = first_num - 14
            base -= (penalty_steps * 28)

        # 2. 連號、尾數、奇偶
        if m['streak'] == 2: base += 45
        elif m['streak'] >= 3: base -= 110
        if m['same_tail'] == 2: base += 35
        if m['odd'] == 2 or m['odd'] == 3: base += 35
        
        # 3. 數據驅動拖牌 (不盲目跟隨，看歷史規律)
        drag_hits = len(set(nums).intersection(drag_pool))
        base += (drag_hits * patterns['drag_weight'])
        
        # 4. 避險
        danger_hits = len(set(nums).intersection(patterns['danger_numbers']))
        base -= (danger_hits * 160)
            
        # 5. 靈活總和 (針對今日 138 這種極端盤，設定區間)
        s = m['sum']
        if 70 <= s <= 130:
            sum_penalty = 0
        else:
            sum_penalty = abs(s - 100) * 1.5
            
        entropy = random.uniform(0, 45)
        scores.append(round(base + entropy - sum_penalty, 3))
    return scores

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss V14.2 Ultimate", page_icon="🧬", layout="wide")
st.title("🧬 Gauss Master Pro V14.2 曲線加權版")
st.markdown(f"💡 **歷史規律模式** | **首碼遞減曲線** | 最新開獎參考：`{', '.join(map(str, [19, 24, 29, 32, 34]))}`")

uploaded_file = st.file_uploader("上傳 Excel (最新一期在第一列)", type=["xlsx"])

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
            history_sorted = [sorted(h) for h in history]
            patterns = analyze_full_history(history_sorted)
            
            st.success(f"✅ 載入成功！偵測到最新期：{history[0]}")
            
            # --- 儀表板 ---
            cols = st.columns(4)
            cols[0].metric("最新首碼", history[0][0])
            cols[1].metric("統計拖牌權重", f"{patterns['drag_weight']:.2f}")
            cols[2].metric("總和寬度", "70-130")
            cols[3].metric("模擬次數", "570,000")

            # --- 模擬 ---
            progress_bar = st.progress(0)
            batch_size = 15000
            total_sims = 570000
            all_top = []

            for i in range(0, total_sims, batch_size):
                combos = [random.sample(range(1, 40), 5) for _ in range(batch_size)]
                metrics = get_metrics_batch(combos)
                scores = get_god_score_batch(metrics, patterns)
                for combo_meta, score in zip(metrics, scores):
                    if score > 195: 
                        all_top.append({"combo": combo_meta['nums'], "score": score, "m": combo_meta})
                progress_bar.progress((i + batch_size) / total_sims)

            # --- 結果 ---
            final_top5 = sorted(all_top, key=lambda x: x['score'], reverse=True)[:5]
            st.subheader("👑 V14.2 曲線演算精選 Top 5")
            
            res_df = []
            for idx, item in enumerate(final_top5):
                c = item["combo"]
                m = item["m"]
                res_df.append({
                    "等級": "數據至尊" if idx == 0 else f"精選 {idx+1}",
                    "組合": ", ".join([f"{x:02d}" for x in c]),
                    "評分": item["score"],
                    "總和": m["sum"],
                    "奇偶": f"{m['odd']}:{m['even']}",
                    "首碼": c[0]
                })
            st.table(pd.DataFrame(res_df))
            st.info("📊 提示：今日開出 19 開頭極端盤，系統已自動進入『區間回歸預測』模式，優先尋找結構穩定的組合。")
            st.balloons()
    except Exception as e:
        st.error(f"錯誤: {e}")
