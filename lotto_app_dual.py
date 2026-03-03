import random
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：五千次全維度深度抽樣系統
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
    same_tail_count = max(digit_counts.values()) 
    
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
    
    # 跨度分析
    spans = [(d[-1] - d[0]) for d in recent_data]
    avg_span = np.mean(spans)
    
    # 連號傾向分析 (最近10期)
    streaks = [get_detailed_metrics(d)['streak'] for d in recent_data]
    recent_10_streaks = streaks[:10]
    actual_streak_rate = len([s for s in recent_10_streaks if s > 1]) / 10
    # 若近期二連號出現頻率低於 40%，提高連號權重獎勵
    streak_tendency = 2.0 if actual_streak_rate < 0.4 else 1.0
    
    return {
        "avg_span": avg_span,
        "streak_tendency": streak_tendency,
        "sample_size": sample_size,
        "history_spans": spans
    }

def get_ai_score(combo, patterns):
    """V6.9.3 AI 全維度評分邏輯 (5,000次模擬專用)"""
    m = get_detailed_metrics(combo)
    
    # 基礎權重：AC值 (確保數字分佈具備足夠的隨機複雜度)
    score = m['ac'] * 12 
    
    # 1. 跨度精準權重 (邊界控制)
    score -= abs(m['span'] - patterns['avg_span']) * 5.0
    
    # 2. 連號回歸權重
    if m['streak'] == 2: 
        score += (25 * patterns['streak_tendency'])
    elif m['streak'] >= 3: 
        score -= 60 # 排除低機率三連號
    
    # 3. 總和平衡權重 (常態分佈回歸)
    score -= abs(m['sum'] - 100) * 0.8
    
    # 4. 尾數平衡權重 (理想為「一組同尾」)
    if m['same_tail'] == 2: 
        score += 20
    elif m['same_tail'] >= 3: 
        score -= 30 
    
    # 5. 奇偶平衡權重 (黃金比例 3:2 或 2:3)
    if m['odds'] in [2, 3]: 
        score += 20
    else: 
        score -= 25
    
    return round(score, 2)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Pro V6.9.3 5K-Sim", page_icon="🧬", layout="wide")

st.title("🧬 Gauss Master Pro V6.9.3 (5,000次模擬精選版)")
st.markdown("本版本採取 **5,000 次深度模擬抽樣**，對每一組號碼進行 **六維度權重運算**。")

with st.sidebar:
    st.header("📂 數據導入")
    uploaded_file = st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    st.divider()
    st.write("📊 **核心執行策略：**")
    st.info("🔥 **模擬規模：5,000 次**")
    st.info("🏆 **錄取名額：Top 3 精英**")
    st.write("✅ 基準：最近 100 期物理慣性")
    st.write("✅ 維度：跨度/連號/AC/總和/奇偶/尾數")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for val in df.iloc[:, 1].dropna().astype(str):
            nums = [int(n) for n in val.replace(' ', ',').replace('、', ',').split(',') if n.strip().isdigit()]
            if len(nums) == 5:
                history.append(sorted(nums))
        
        if history:
            # 1. 深度規律分析 (100期)
            patterns = analyze_patterns_100(history)
            
            # 2. 數據看板
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(f"最近 {patterns['sample_size']} 期平均跨度", f"{patterns['avg_span']:.1f}")
                st.caption("AI 將鎖定此距離來配置首尾號碼")
            with c2:
                st.metric("連號權重補償", f"{patterns['streak_tendency']}x")
                st.caption("係數越高代表近期連號越缺失")
            with c3:
                st.write("歷史跨度波動 (最近30期)：")
                st.line_chart(patterns['history_spans'][-30:])

            # 3. 執行 5,000 次模擬抽樣
            st.subheader(f"🤖 AI 正在進行 5,000 次深度模擬運算...")
            progress_bar = st.progress(0)
            
            all_candidates = []
            
            # 模擬計算
            for i in range(5000):
                combo = sorted(random.sample(range(1, 40), 5))
                score = get_ai_score(combo, patterns)
                m = get_detailed_metrics(combo)
                
                all_candidates.append({
                    "推薦組合": ", ".join([f"{x:02d}" for x in combo]),
                    "AI 綜合評分": score,
                    "跨度": m['span'],
                    "奇偶比 (奇:偶)": f"{m['odds']}:{5-m['odds']}",
                    "連號狀況": "無" if m['streak'] == 1 else f"{m['streak']}連",
                    "尾數同尾": "是" if m['same_tail'] > 1 else "否",
                    "組合總和": m['sum'],
                    "AC值": m['ac']
                })
                
                # 更新進度條 (每 500 次更新一次)
                if i % 500 == 0:
                    progress_bar.progress((i + 500) / 5000)
            
            # 4. 篩選 Top 3
            top_3 = pd.DataFrame(all_candidates).sort_values("AI 綜合評分", ascending=False).head(3)
            
            st.subheader("🥇 本次 5,000 次模擬 - 最優選 Top 3")
            st.table(top_3)
            
            st.success(f"✅ 深度運算完成。這三組號碼是從五千個隨機樣本中，結構完整性最高、最符合歷史慣性的組合。")
            
            # 5. 下載區
            csv = top_3.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 下載 Top 3 精選報告", csv, "Gauss_V693_Top3.csv", "text/csv")

        else:
            st.error("數據格式錯誤，請檢查 Excel 第二欄。")
    except Exception as e:
        st.error(f"系統錯誤: {e}")
else:
    st.info("👋 請上傳歷史數據。AI 將在背景進行 5,000 次模擬運算並篩選出物理結構最強的三組號碼。")

st.markdown("---")
st.caption("Gauss Master Pro v6.9.3 | 5000-Sim Elite Selection | Hexa-Dimensional Analysis")

