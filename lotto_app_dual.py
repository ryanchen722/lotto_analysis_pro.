import random
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：五萬次全維度暴力模擬與盲區統計
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
    
    spans = [(d[-1] - d[0]) for d in recent_data]
    avg_span = np.mean(spans)
    
    streaks = [get_detailed_metrics(d)['streak'] for d in recent_data]
    recent_15_streaks = streaks[:15]
    actual_streak_rate = len([s for s in recent_15_streaks if s > 1]) / 15
    streak_tendency = 2.2 if actual_streak_rate < 0.35 else 1.0
    
    return {
        "avg_span": avg_span,
        "streak_tendency": streak_tendency,
        "sample_size": sample_size,
        "history_spans": spans
    }

def get_ai_score(m, patterns):
    """V6.9.5 AI 全維度評分邏輯 (50,000次海選專用)"""
    score = m['ac'] * 12 
    score -= abs(m['span'] - patterns['avg_span']) * 5.5
    
    if m['streak'] == 2: 
        score += (30 * patterns['streak_tendency'])
    elif m['streak'] >= 3: 
        score -= 70 
    
    score -= abs(m['sum'] - 100) * 0.9
    
    if m['same_tail'] == 2: score += 25
    elif m['same_tail'] >= 3: score -= 40 
    
    if m['odds'] in [2, 3]: score += 25
    else: score -= 35
    
    return round(score, 2)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Pro V6.9.5 50K", page_icon="🔱", layout="wide")

st.title("🔱 Gauss Master Pro V6.9.5 (五萬次暴力精選版)")
st.markdown("本版本採取 **50,000 次暴力模擬**，精選 **Top 5** 超精英組合，並同步解析**數位盲區**。")

with st.sidebar:
    st.header("📂 數據導入")
    uploaded_file = st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    st.divider()
    st.write("📊 **核心執行策略：**")
    st.error("🔥 **模擬規模：50,000 次**")
    st.info("🏆 **錄取名額：Top 5 精英組**")
    st.write("✅ 指標：AC/跨度/連號/總和/奇偶/尾數")
    st.write("✅ 功能：自動統計未選中數位")

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
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(f"最近 {patterns['sample_size']} 期平均跨度", f"{patterns['avg_span']:.1f}")
            with c2:
                st.metric("二連號強化係數", f"{patterns['streak_tendency']}x")
            with c3:
                st.write("跨度波動走勢 (最近 30 期)：")
                st.line_chart(patterns['history_spans'][-30:])

            # 執行 50,000 次模擬
            st.subheader(f"🤖 AI 正在進行 50,000 次暴力模擬篩選...")
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
                    "總和": m['sum']
                })
                
                # 每 5000 次優化一次列表
                if len(best_pool) > 500:
                    best_pool = sorted(best_pool, key=lambda x: x["AI 綜合評分"], reverse=True)[:100]
                
                if i % 5000 == 0:
                    progress_bar.progress((i + 5000) / 50000)
            
            # 取得 Top 5
            top_5_results = sorted(best_pool, key=lambda x: x["AI 綜合評分"], reverse=True)[:5]
            top_5_df = pd.DataFrame(top_5_results).drop(columns=["combo_list"])
            
            st.subheader("👑 五萬次模擬決選 - Top 5 超精英組合")
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
            st.caption("💡 提示：若盲區中包含你強烈看好的熱號，可考慮自行替換一組中的某個數字。")

            st.success("✅ 全維度暴力篩選完成！")

        else:
            st.error("Excel 格式錯誤。")
    except Exception as e:
        st.error(f"系統錯誤: {e}")
else:
    st.info("👋 請上傳數據以啟動 50,000 次海選與盲區解析。")

st.markdown("---")
st.caption("Gauss Master Pro v6.9.5 | 50,000 Brute-Force Selection | Exclusion Mapping")

