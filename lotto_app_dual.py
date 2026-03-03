import random
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：五萬次全維度暴力模擬 (解鎖跨度與奇偶)
# ==========================================

def get_detailed_metrics(nums):
    """計算物理指標 (解鎖跨度與奇偶限制)"""
    nums = sorted(nums)
    # 1. AC 值 (算術複雜度) - 這是隨機性的靈魂，保留
    diffs = set()
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    ac = len(diffs) - (len(nums) - 1)
    
    # 2. 跨度 (Span) - 僅記錄，不參與扣分
    span = nums[-1] - nums[0]
    
    # 3. 連號 (Consecutive) - 根據歷史慣性保留
    max_streak = 1
    current = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i-1] + 1:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 1
            
    # 4. 尾數重複度 (Last Digit) - 保留自然規律
    last_digits = [n % 10 for n in nums]
    digit_counts = Counter(last_digits)
    same_tail_count = max(digit_counts.values()) 
    
    # 5. 奇偶比 (Odd/Even) - 僅記錄，不參與扣分
    odds = len([n for n in nums if n % 2 != 0])
    
    # 6. 總和 (Sum) - 保留常態分佈回歸
    total_sum = sum(nums)
    
    return {
        "ac": ac,
        "span": span,
        "streak": max_streak,
        "same_tail": same_tail_count,
        "odds": odds,
        "sum": total_sum
    }

def analyze_patterns_100(history):
    """分析最近 100 期的連號回歸傾向"""
    sample_size = min(len(history), 100)
    recent_data = history[:sample_size]
    
    # 僅分析連號傾向，不再計算平均跨度
    streaks = [get_detailed_metrics(d)['streak'] for d in recent_data]
    recent_15_streaks = streaks[:15]
    actual_streak_rate = len([s for s in recent_15_streaks if s > 1]) / 15
    streak_tendency = 2.5 if actual_streak_rate < 0.3 else 1.0
    
    return {
        "streak_tendency": streak_tendency,
        "sample_size": sample_size
    }

def get_ai_score(m, patterns):
    """V6.9.6 AI 物理評分邏輯 (解鎖版)"""
    # 核心權重：AC值 (確保數字之間沒有簡單的算術規律)
    score = m['ac'] * 20 
    
    # 1. 連號回歸權重 (這是目前唯一的物理慣性引導)
    if m['streak'] == 2: 
        score += (35 * patterns['streak_tendency'])
    elif m['streak'] >= 3: 
        score -= 50 # 極端連號依然稍微控制
    
    # 2. 總和平衡權重 (確保組合不至於全部太小或全部太大)
    score -= abs(m['sum'] - 100) * 1.0
    
    # 3. 尾數平衡權重 (一組同尾是自然現象，予以獎勵)
    if m['same_tail'] == 2: 
        score += 30
    elif m['same_tail'] >= 3: 
        score -= 40 
    
    # 注意：跨度 (Span) 與 奇偶比 (Odds) 的扣分項已移除
    
    return round(score, 2)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Pro V6.9.6 Unlocked", page_icon="🔓", layout="wide")

st.title("🔓 Gauss Master Pro V6.9.6 (跨度與奇偶解鎖版)")
st.markdown("本版本已**移除跨度限制與奇偶平衡限制**。AI 現在完全根據 **AC 值、連號回歸與尾數規律** 進行五萬次暴力篩選。")

with st.sidebar:
    st.header("📂 數據導入")
    uploaded_file = st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    st.divider()
    st.write("📊 **解鎖狀態：**")
    st.success("🔓 **跨度鎖定：已解除**")
    st.success("🔓 **奇偶鎖定：已解除**")
    st.error("🔥 **模擬規模：50,000 次**")
    st.info("🏆 **錄取名額：Top 5 精英組**")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for val in df.iloc[:, 1].dropna().astype(str):
            nums = [int(n) for n in val.replace(' ', ',').replace('、', ',').split(',') if n.strip().isdigit()]
            if len(nums) == 5:
                history.append(sorted(nums))
        
        if history:
            patterns = analyze_patterns_100(history)
            
            # 執行五萬次模擬
            st.subheader(f"🤖 AI 正在進行 50,000 次「解鎖限制」暴力篩選...")
            progress_bar = st.progress(0)
            
            best_pool = [] 
            
            for i in range(50000):
                combo = sorted(random.sample(range(1, 40), 5))
                m = get_detailed_metrics(combo)
                score = get_ai_score(m, patterns)
                
                best_pool.append({
                    "combo_list": combo,
                    "推薦組合": ", ".join([f"{x:02d}" for x in combo]),
                    "AI 綜合評分": score,
                    "跨度": m['span'],
                    "奇偶比": f"{m['odds']}:{5-m['odds']}",
                    "連號": "無" if m['streak'] == 1 else f"{m['streak']}連",
                    "尾數同尾": "是" if m['same_tail'] > 1 else "否",
                    "組合總和": m['sum']
                })
                
                if len(best_pool) > 500:
                    best_pool = sorted(best_pool, key=lambda x: x["AI 綜合評分"], reverse=True)[:100]
                
                if i % 5000 == 0:
                    progress_bar.progress((i + 5000) / 50000)
            
            # 取得 Top 5
            top_5_results = sorted(best_pool, key=lambda x: x["AI 綜合評分"], reverse=True)[:5]
            top_5_df = pd.DataFrame(top_5_results).drop(columns=["combo_list"])
            
            st.subheader("👑 五萬次模擬決選 - 解鎖版 Top 5")
            st.table(top_5_df)
            
            # 統計未選中的數字
            selected_nums = set()
            for r in top_5_results:
                selected_nums.update(r["combo_list"])
            
            all_nums = set(range(1, 40))
            unselected_nums = sorted(list(all_nums - selected_nums))
            
            st.divider()
            st.subheader("🚫 數位盲區 (以上五組中未出現的號碼)")
            st.write(f"共有 **{len(unselected_nums)}** 個號碼未被選中：")
            st.code(", ".join([f"{x:02d}" for x in unselected_nums]))
            
            st.success("✅ 解鎖版全維度暴力篩選完成！觀察看看這些不受限號碼的規律。")

        else:
            st.error("Excel 格式錯誤。")
    except Exception as e:
        st.error(f"系統錯誤: {e}")
else:
    st.info("👋 請上傳歷史數據，啟動「不鎖定跨度與奇偶」的五萬次暴力模擬。")

st.markdown("---")
st.caption("Gauss Master Pro v6.9.6 | Unlocked Physical Constraints | 50,000 Brute-Force")

