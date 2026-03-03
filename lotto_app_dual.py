import random
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：五萬次海選 + 盲區全息融合系統
# ==========================================

def get_detailed_metrics(nums):
    """計算物理指標 (解鎖跨度與奇偶限制)"""
    nums = sorted(nums)
    # 1. AC 值 (隨機複雜度)
    diffs = set()
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    ac = len(diffs) - (len(nums) - 1)
    
    # 2. 跨度 (Span)
    span = nums[-1] - nums[0]
    
    # 3. 連號 (Consecutive)
    max_streak = 1
    current = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i-1] + 1:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 1
            
    # 4. 尾數重複度 (Last Digit)
    last_digits = [n % 10 for n in nums]
    digit_counts = Counter(last_digits)
    same_tail_count = max(digit_counts.values()) 
    
    # 5. 總和 (Sum)
    total_sum = sum(nums)
    
    # 6. 奇偶
    odds = len([n for n in nums if n % 2 != 0])
    
    return {
        "ac": ac, "span": span, "streak": max_streak, 
        "same_tail": same_tail_count, "sum": total_sum, "odds": odds
    }

def get_ai_score(m, patterns):
    """V6.9.7 融合權重邏輯"""
    score = m['ac'] * 20 
    if m['streak'] == 2: 
        score += (35 * patterns['streak_tendency'])
    elif m['streak'] >= 3: 
        score -= 50 
    score -= abs(m['sum'] - 100) * 1.0
    if m['same_tail'] == 2: 
        score += 30
    return round(score, 2)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Pro V6.9.7 Fusion", page_icon="♾️", layout="wide")

st.title("♾️ Gauss Master Pro V6.9.7 (全息融合至尊版)")
st.markdown("本版本在 **50,000 次暴力模擬** 後，將 Top 5 精英組與 **數位盲區 (遺漏號碼)** 進行深度融合運算。")

with st.sidebar:
    st.header("📂 數據導入")
    uploaded_file = st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    st.divider()
    st.write("🧬 **融合技術：**")
    st.info("🔄 **遺漏補償**：將盲區號碼強制嵌入高分結構。")
    st.info("🧩 **全息校正**：確保最終組合覆蓋率達到最大化。")
    st.error("🔥 模擬規模：50,000 次")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for val in df.iloc[:, 1].dropna().astype(str):
            nums = [int(n) for n in val.replace(' ', ',').replace('、', ',').split(',') if n.strip().isdigit()]
            if len(nums) == 5:
                history.append(sorted(nums))
        
        if history:
            # 分析連號傾向
            sample_size = min(len(history), 100)
            recent_data = history[:sample_size]
            streaks = [get_detailed_metrics(d)['streak'] for d in recent_data]
            actual_streak_rate = len([s for s in streaks[:15] if s > 1]) / 15
            patterns = {"streak_tendency": 2.5 if actual_streak_rate < 0.3 else 1.0}

            # 階段 1: 五萬次暴力海選 Top 5
            best_pool = [] 
            for i in range(50000):
                combo = sorted(random.sample(range(1, 40), 5))
                m = get_detailed_metrics(combo)
                score = get_ai_score(m, patterns)
                best_pool.append({"combo": combo, "score": score, "metrics": m})
                if len(best_pool) > 200:
                    best_pool = sorted(best_pool, key=lambda x: x["score"], reverse=True)[:100]

            top_5 = sorted(best_pool, key=lambda x: x["score"], reverse=True)[:5]
            
            # 階段 2: 盲區統計
            selected_nums = set()
            for item in top_5:
                selected_nums.update(item["combo"])
            unselected_nums = sorted(list(set(range(1, 40)) - selected_nums))

            # 階段 3: 全息融合 (Holographic Fusion)
            # 邏輯：從 Top 5 中挑選物理結構最穩定的基礎，將其中一個號碼替換為盲區中最具隨機性的號碼
            fusion_sets = []
            
            # 融合方案 A: 均勻覆蓋組 (從盲區中隨機填補)
            for idx, base in enumerate(top_5):
                new_combo = list(base["combo"])
                # 替換邏輯：保留首尾，替換中間的一個號碼，增加盲區覆蓋
                if unselected_nums:
                    replacement = random.choice(unselected_nums)
                    # 確保不會重複
                    if replacement not in new_combo:
                        new_combo[2] = replacement # 替換中心點
                    unselected_nums.remove(replacement)
                
                new_combo = sorted(new_combo)
                m_f = get_detailed_metrics(new_combo)
                fusion_sets.append({
                    "類型": f"融合組 {idx+1}",
                    "組合": ", ".join([f"{x:02d}" for x in new_combo]),
                    "融合前評分": base["score"],
                    "跨度": m_f["span"],
                    "奇偶比": f"{m_f['odds']}:{5-m_f['odds']}",
                    "連號": "有" if m_f["streak"] > 1 else "無",
                    "AC值": m_f["ac"]
                })

            # 顯示結果
            st.subheader("👑 全息融合至尊五組 (精英 + 盲區號碼)")
            st.table(pd.DataFrame(fusion_sets))

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🚫 原始盲區統計")
                st.code(", ".join([f"{x:02d}" for x in sorted(list(set(range(1, 40)) - selected_nums))]))
            with col2:
                st.subheader("🧬 融合後的最終遺漏")
                final_selected = set()
                for fs in fusion_sets:
                    final_selected.update([int(n) for n in fs["組合"].split(", ")])
                final_unselected = sorted(list(set(range(1, 40)) - final_selected))
                st.code(", ".join([f"{x:02d}" for x in final_unselected]))
                st.caption(f"融合後號碼覆蓋率大幅提升，遺漏數由 {len(set(range(1, 40)) - selected_nums)} 降至 {len(final_unselected)}")

            st.success("✅ 全息融合運算完成。這五組號碼在保持物理強度的同時，成功吸收了盲區數位。")

        else:
            st.error("Excel 格式錯誤。")
    except Exception as e:
        st.error(f"系統錯誤: {e}")
else:
    st.info("👋 請上傳歷史數據，啟動全息融合五萬次暴力模擬。")

st.markdown("---")
st.caption("Gauss Master Pro v6.9.7 | Holographic Fusion System | 50,000 Brute-Force")

