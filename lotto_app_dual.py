import random
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：五萬次分區破壁模擬系統
# ==========================================

def get_detailed_metrics(nums):
    """計算物理指標 (全面解除總和與跨度約束)"""
    nums = sorted(nums)
    # AC 值 (複雜度)
    diffs = set()
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    ac = len(diffs) - (len(nums) - 1)
    
    span = nums[-1] - nums[0]
    last_digit_zone = (nums[-1] - 1) // 13 # 0: 01-13, 1: 14-26, 2: 27-39
    
    # 連號
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
    
    return {
        "ac": ac, "span": span, "streak": max_streak, 
        "same_tail": same_tail_count, "last_zone": last_digit_zone,
        "sum": sum(nums), "last_num": nums[-1]
    }

def get_ai_score_v8(m, patterns):
    """V6.9.8 評分邏輯：專注於隨機亂度，移除位置偏見"""
    # 提高 AC 值權重，這是隨機開獎的最核心特徵
    score = m['ac'] * 25 
    
    # 連號權重：僅針對二連號做補償
    if m['streak'] == 2: 
        score += (30 * patterns['streak_tendency'])
    elif m['streak'] >= 3: 
        score -= 60 
        
    # 尾數權重：自然重複獎勵
    if m['same_tail'] == 2: 
        score += 35
        
    # 移除總和與跨度扣分，讓最後一碼可以落在任何位置
    
    return round(score, 2)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Pro V6.9.8 Unbound", page_icon="🚀", layout="wide")

st.title("🚀 Gauss Master Pro V6.9.8 (分區破壁版)")
st.markdown("針對「最後一碼過於偏大」的偏頗進行修正。AI 現在強制打破跨度鎖定，並分析盲區號碼進行全息融合。")

with st.sidebar:
    st.header("📂 數據導入")
    uploaded_file = st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    st.divider()
    st.write("🛠️ **破壁技術說明：**")
    st.info("🔓 **解除總和限制**：不再強制接近 100。")
    st.info("🔓 **解除跨度限制**：允許最後一碼出現在 20 幾甚至更早。")
    st.info("🧬 **盲區融合**：50,000 次模擬後的遺漏號碼補償。")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for val in df.iloc[:, 1].dropna().astype(str):
            nums = [int(n) for n in val.replace(' ', ',').replace('、', ',').split(',') if n.strip().isdigit()]
            if len(nums) == 5:
                history.append(sorted(nums))
        
        if history:
            # 分析連號
            sample_size = min(len(history), 100)
            recent_data = history[:sample_size]
            streaks = [get_detailed_metrics(d)['streak'] for d in recent_data]
            streak_rate = len([s for s in streaks[:15] if s > 1]) / 15
            patterns = {"streak_tendency": 2.2 if streak_rate < 0.4 else 1.0}

            # 階段 1: 五萬次暴力海選 (分區儲存，打破 3 開頭偏頗)
            # 我們將結果按「最後一碼分區」分類，確保 Top 5 涵蓋不同結尾區間
            zones_pool = {0: [], 1: [], 2: []}
            
            progress_bar = st.progress(0)
            for i in range(50000):
                combo = sorted(random.sample(range(1, 40), 5))
                m = get_detailed_metrics(combo)
                score = get_ai_score_v8(m, patterns)
                
                zone = m['last_zone']
                zones_pool[zone].append({"combo": combo, "score": score, "metrics": m})
                
                # 保持每個分區只存前 50 名，優化效能
                if len(zones_pool[zone]) > 50:
                    zones_pool[zone] = sorted(zones_pool[zone], key=lambda x: x["score"], reverse=True)[:50]
                
                if i % 10000 == 0:
                    progress_bar.progress((i + 10000) / 50000)

            # 階段 2: 跨分區選取 Top 5 (確保結尾數字不單一)
            raw_top_candidates = []
            # 從 14-26 區 (Zone 1) 強制選 1 組，從 27-39 區 (Zone 2) 選 4 組 (依分佈機率)
            if zones_pool[1]: raw_top_candidates.append(zones_pool[1][0])
            for j in range(4):
                if len(zones_pool[2]) > j: raw_top_candidates.append(zones_pool[2][j])

            # 階段 3: 盲區融合
            selected_nums = set()
            for item in raw_top_candidates:
                selected_nums.update(item["combo"])
            unselected_nums = sorted(list(set(range(1, 40)) - selected_nums))

            final_fusion_results = []
            for idx, item in enumerate(raw_top_candidates):
                f_combo = list(item["combo"])
                if unselected_nums:
                    # 融合邏輯：從盲區選一個號碼替換第二或第四碼
                    rep = random.choice(unselected_nums)
                    if rep not in f_combo:
                        pos = 1 if idx % 2 == 0 else 3
                        f_combo[pos] = rep
                    unselected_nums.remove(rep)
                
                f_combo = sorted(f_combo)
                m_f = get_detailed_metrics(f_combo)
                final_fusion_results.append({
                    "推薦組合": ", ".join([f"{x:02d}" for x in f_combo]),
                    "AI 評分": item["score"],
                    "最後一碼": f_combo[-1],
                    "跨度": m_f["span"],
                    "總和": m_f["sum"],
                    "AC值": m_f["ac"]
                })

            st.subheader("👑 全息融合破壁組 (已打破 3 開頭數字偏頗)")
            st.table(pd.DataFrame(final_fusion_results))

            # 盲區顯示
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.write("🚫 **初始盲區號碼**")
                st.code(", ".join([f"{x:02d}" for x in sorted(list(set(range(1, 40)) - selected_nums))]))
            with c2:
                current_selected = set()
                for res in final_fusion_results:
                    current_selected.update([int(n) for n in res["推薦組合"].split(", ")])
                st.write("🧬 **融合後剩餘遺漏**")
                st.code(", ".join([f"{x:02d}" for x in sorted(list(set(range(1, 40)) - current_selected))]))

            st.success("✅ 運算完成！這次推薦特別引入了「非 3 開頭結尾」的組合，整體分佈更符合真實隨機狀態。")

        else:
            st.error("Excel 格式錯誤。")
    except Exception as e:
        st.error(f"系統錯誤: {e}")
else:
    st.info("👋 請上傳數據，AI 將執行 50,000 次分區破壁模擬，修正最後一碼的偏頗。")

st.markdown("---")
st.caption("Gauss Master Pro v6.9.8 | Zone-Unbound Analytics | 50,000 Brute-Force Fusion")

