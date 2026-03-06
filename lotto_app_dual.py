import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter

# ==========================================
# 核心計算引擎 (539 倒敘優化版)
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
    history[0] 為最新期
    """
    all_draws = [num for sublist in history for num in sublist]
    counts = Counter(all_draws)
    hot_numbers = [num for num, _ in counts.most_common(12)]
    
    # 正確抓取「最新 15 期」
    recent_15 = history[:15] 
    streak_count = sum(1 for d in recent_15 if any(d[i] == d[i-1] + 1 for i in range(1, 5)))
    
    # 趨勢補償：若最近連號開得少，則模擬中給予連號較高分
    streak_tendency = 2.5 if streak_count < 5 else 1.1
    return {"hot": hot_numbers, "streak_tendency": streak_tendency, "counts": counts, "latest": history[0]}

def get_god_score_batch(metrics_list, patterns):
    scores = []
    for m in metrics_list:
        base = m['ac'] * 28 
        if m['streak'] == 2:
            base += 40 * patterns['streak_tendency']
        elif m['streak'] >= 3:
            base -= 85
        if m['same_tail'] == 2:
            base += 35
        
        # 冷熱平衡：含有 1~2 顆熱門號最理想
        hot_in_combo = len(set(m['nums']).intersection(set(patterns['hot'])))
        if 1 <= hot_in_combo <= 2:
            base += 50
        
        # 奇偶平衡
        if m['odd'] == 2 or m['odd'] == 3:
            base += 30
            
        # 總和懲罰 (錨定 100)
        sum_penalty = abs(m['sum'] - 100) * 1.6
        entropy = random.uniform(0, 15)
        scores.append(round(base + entropy - sum_penalty, 3))
    return scores

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Master Pro V13 Fusion", page_icon="💎", layout="wide")
st.title("💎 Gauss Master Pro V13 倒敘優化版")
st.markdown("💡 **第一組為最新期** | 自動拆分儲存格 | 570,000 次暴力模擬")

uploaded_file = st.file_uploader("上傳 Excel (最新一期在第一列)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        
        for _, row in df.iterrows():
            row_numbers = []
            for cell in row:
                cell_str = str(cell).strip()
                # 抓取儲存格中所有數字
                nums_in_cell = re.findall(r'\d+', cell_str)
                for n in nums_in_cell:
                    row_numbers.append(int(n))
            
            # 過濾 539 範圍球號 (排除期數等雜訊)
            clean_nums = [n for n in row_numbers if 1 <= n <= 39]
            if len(clean_nums) >= 5:
                # 保持原序，不強制 sorted，直到分析前再整理
                history.append(clean_nums[:5])

        if history:
            # 整理歷史紀錄：每期內部的球號排序，以便計算規律
            history_sorted = [sorted(h) for h in history]
            patterns = analyze_full_history(history_sorted)
            
            st.success(f"✅ 成功掃描 {len(history)} 期數據！(最新期：{', '.join(map(str, history[0]))})")
            
            # --- 模擬計算 ---
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("🌡️ **數據分析結果**")
                st.write(f"最新一期：`{patterns['latest']}`")
                st.write(f"連號引導：`{patterns['streak_tendency']}x`")
                st.write(f"前三強熱號：`{patterns['hot'][:3]}`")

            with c2:
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
                        if score > 165: 
                            all_top_candidates.append({"combo": combo_meta['nums'], "score": score, "m": combo_meta})
                    
                    progress_bar.progress((i + batch_size) / total_sims)
                    status_text.text(f"天機運算中: {i + batch_size}...")

            # --- 結果 ---
            st.subheader("👑 V13 天機融合推薦 (基於最新趨勢)")
            final_pool = sorted(all_top_candidates, key=lambda x: x['score'], reverse=True)[:5]
            
            display_data = []
            for idx, item in enumerate(final_pool):
                c = item["combo"]
                m = item["m"]
                display_data.append({
                    "等級": "🔥 至尊選" if idx == 0 else f"精選 {idx+1}",
                    "推薦組合": ", ".join([f"{x:02d}" for x in c]),
                    "評分": item["score"],
                    "總和": m["sum"],
                    "奇偶": f"{m['odd']}:{m['even']}",
                    "AC值": m["ac"]
                })
            st.table(pd.DataFrame(display_data))
            st.balloons()
        else:
            st.error("❌ 無法偵測到球號，請確認檔案格式。")
    except Exception as e:
        st.error(f"錯誤: {e}")
else:
    st.info("👋 請上傳 Excel (最新一期在第一列，就算擠在同一格也沒問題)。")
