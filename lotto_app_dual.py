import random
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：六大物理維度分析系統
# ==========================================

def get_detailed_metrics(nums):
    """計算六大物理指標"""
    nums = sorted(nums)
    # 1. AC 值 (算術複雜度)
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
    same_tail_count = max(digit_counts.values()) # 最高重複次數
    
    # 5. 奇偶比 (Odd/Even)
    odds = len([n for n in nums if n % 2 != 0])
    
    # 6. 總和 (Sum)
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
    """分析最近 100 期的深度物理規律"""
    sample_size = min(len(history), 100)
    recent_data = history[:sample_size]
    
    spans = [(d[-1] - d[0]) for d in recent_data]
    avg_span = np.mean(spans)
    
    streaks = [get_detailed_metrics(d)['streak'] for d in recent_data]
    actual_streak_rate = len([s for s in streaks[:10] if s > 1]) / 10
    streak_tendency = 1.8 if actual_streak_rate < 0.4 else 1.0
    
    # 尾數規律：歷史中同尾現象的頻率
    tails = [get_detailed_metrics(d)['same_tail'] for d in recent_data]
    avg_tail_repeat = np.mean(tails) # 通常在 1.5 - 1.8 之間
    
    return {
        "avg_span": avg_span,
        "streak_tendency": streak_tendency,
        "avg_tail": avg_tail_repeat,
        "sample_size": sample_size,
        "history_spans": spans
    }

def get_ai_score(combo, patterns):
    """V6.9.2 AI 全維度評分邏輯"""
    m = get_detailed_metrics(combo)
    
    score = m['ac'] * 12 # AC基礎
    
    # 跨度權重
    score -= abs(m['span'] - patterns['avg_span']) * 4.5
    
    # 連號補償
    if m['streak'] == 2: score += (22 * patterns['streak_tendency'])
    elif m['streak'] >= 3: score -= 55
    
    # 總和平衡
    score -= abs(m['sum'] - 100) * 0.7
    
    # 尾數平衡 (理想是 1 組同尾，即 same_tail = 2)
    if m['same_tail'] == 2: score += 15
    elif m['same_tail'] >= 3: score -= 25 # 三同尾機率過低
    
    # 奇偶平衡 (理想是 2:3 或 3:2)
    if m['odds'] in [2, 3]: score += 15
    else: score -= 20 # 5:0 或 0:5 是大忌
    
    return round(score, 2)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Pro V6.9.2", page_icon="🧩", layout="wide")

st.title("🧩 Gauss Master Pro V6.9.2 (全維度精選版)")
st.markdown("本版本在 **1,000 次模擬** 中加入了 **奇偶平衡** 與 **尾數重複規律** 的深度檢索。")

with st.sidebar:
    st.header("📂 數據導入")
    uploaded_file = st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    st.divider()
    st.write("📊 **新增維度說明：**")
    st.info("🧬 **尾數重複**：偵測個位數相同規律。")
    st.info("⚖️ **奇偶平衡**：鎖定黃金比例 (2:3 / 3:2)。")
    st.write("✅ 模擬規模：1,000 組")
    st.write("🥇 錄取名額：前 3 名")

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
            
            # 看板數據
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("100期平均跨度", f"{patterns['avg_span']:.1f}")
            with c2:
                st.metric("尾數重複傾向", f"{patterns['avg_tail']:.2f}")
            with c3:
                st.write("物理跨度走勢：")
                st.line_chart(patterns['history_spans'][-30:])

            # 模擬計算
            all_candidates = []
            with st.spinner('AI 正在計算全維度權重 (1,000 次模擬)...'):
                for _ in range(1000):
                    combo = sorted(random.sample(range(1, 40), 5))
                    score = get_ai_score(combo, patterns)
                    m = get_detailed_metrics(combo)
                    
                    all_candidates.append({
                        "推薦組合": ", ".join([f"{x:02d}" for x in combo]),
                        "AI 綜合評分": score,
                        "跨度": m['span'],
                        "奇偶 (奇:偶)": f"{m['odds']}:{5-m['odds']}",
                        "連號": "無" if m['streak'] == 1 else f"{m['streak']}連",
                        "尾數重複": "有" if m['same_tail'] > 1 else "無",
                        "總和": m['sum']
                    })
            
            # 篩選 Top 3
            top_3 = pd.DataFrame(all_candidates).sort_values("AI 綜合評分", ascending=False).head(3)
            
            st.subheader("🥇 本次千次模擬 - 全維度精選 Top 3")
            st.table(top_3)
            
            st.success("✅ 分析完成！這三組號碼不僅符合跨度規律，更在奇偶與尾數分佈上達到了『數學平衡』。")

        else:
            st.error("數據格式錯誤，請檢查 Excel。")
    except Exception as e:
        st.error(f"系統錯誤: {e}")
else:
    st.info("👋 請上傳歷史數據，啟動全維度深度模擬分析。")

st.markdown("---")
st.caption("Gauss Master Pro v6.9.2 | Total Dimension Analytics | 1000-Sim Elite Selection")

