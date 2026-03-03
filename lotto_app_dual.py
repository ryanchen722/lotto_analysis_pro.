import random
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：100 期物理規律與千次模擬系統
# ==========================================

def get_metrics(nums):
    """計算物理指標：AC值、跨度、連號"""
    nums = sorted(nums)
    # AC 值 (算術複雜度)
    diffs = set()
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    ac = len(diffs) - (len(nums) - 1)
    # 跨度 (Span)
    span = nums[-1] - nums[0]
    # 連號 (Consecutive)
    max_streak = 1
    current = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i-1] + 1:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 1
    return ac, span, max_streak

def analyze_patterns_100(history):
    """分析最近 100 期的物理規律"""
    sample_size = min(len(history), 100)
    recent_data = history[:sample_size]
    
    # 1. 跨度數據走勢
    spans = [(d[-1] - d[0]) for d in recent_data]
    avg_span = np.mean(spans)
    
    # 2. 連號數據分析
    streaks = [get_metrics(d)[2] for d in recent_data]
    streak_counts = Counter(streaks)
    
    # 3. 趨勢傾向 (觀察最近 10 期是否有連號缺失)
    recent_10_streaks = streaks[:10]
    actual_streak_rate = len([s for s in recent_10_streaks if s > 1]) / 10
    # 若近期連號偏低，則大幅補償二連號
    streak_tendency = 1.8 if actual_streak_rate < 0.4 else 1.0
    
    return {
        "avg_span": avg_span,
        "span_history": spans,
        "streak_counts": streak_counts,
        "streak_tendency": streak_tendency,
        "sample_size": sample_size
    }

def get_ai_score(combo, patterns):
    """V6.9.1 AI 物理評分：純數據驅動"""
    ac, span, streak = get_metrics(combo)
    
    # A. AC值權重 (越高越散越好)
    score = ac * 15 
    
    # B. 跨度匹配分 (接近 100 期平均)
    span_diff = abs(span - patterns['avg_span'])
    score -= span_diff * 4.5
    
    # C. 連號策略分
    if streak == 2:
        score += (22 * patterns['streak_tendency'])
    elif streak >= 3:
        score -= 55 
        
    # D. 總和回歸分 (539 理想中位數 100)
    score -= abs(sum(combo) - 100) * 0.7
    
    return round(score, 2)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Pro V6.9.1", page_icon="🏆", layout="wide")

st.title("🏆 Gauss Master Pro V6.9.1 (千次模擬精選版)")
st.markdown("本版本採取 **1000 次深度模擬抽樣**，並從中精選出 AI 評分最高的 **Top 3** 物理均衡組合。")

with st.sidebar:
    st.header("📂 數據導入")
    uploaded_file = st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    st.divider()
    st.write("📋 **當前執行策略：**")
    st.info("🔄 **模擬規模：1,000 組**")
    st.info("🥇 **錄取名額：前 3 名**")
    st.write("✅ 基準：最近 100 期跨度慣性")
    st.write("✅ 移除所有人工篩選偏見")

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
            col1, col2 = st.columns(2)
            with col1:
                st.metric(f"最近 {patterns['sample_size']} 期平均跨度", f"{patterns['avg_span']:.2f}")
                st.write("📈 **歷史跨度走勢：**")
                st.line_chart(patterns['span_history'])
            with col2:
                st.write("📊 **100期連號分佈狀況：**")
                st.bar_chart(pd.DataFrame.from_dict(patterns['streak_counts'], orient='index'))
                st.info(f"💡 連號趨勢權重：{patterns['streak_tendency']} (高於 1 代表近期連號缺失，AI 將強化二連號)")

            # 3. 執行 1000 次模擬抽樣
            st.subheader("🤖 AI 正在進行 1,000 次模擬運算...")
            
            all_candidates = []
            with st.spinner('正在分析千組結構...'):
                for _ in range(1000):
                    combo = sorted(random.sample(range(1, 40), 5))
                    score = get_ai_score(combo, patterns)
                    ac, span, streak = get_metrics(combo)
                    
                    all_candidates.append({
                        "推薦組合": ", ".join([f"{x:02d}" for x in combo]),
                        "AI 綜合評分": score,
                        "跨度 (Span)": span,
                        "連號狀況": "無連號" if streak == 1 else f"{streak}連號",
                        "組合總和": sum(combo),
                        "AC值": ac
                    })
            
            # 4. 篩選 Top 3
            top_3 = pd.DataFrame(all_candidates).sort_values("AI 綜合評分", ascending=False).head(3)
            
            st.subheader("🥇 本次模擬精選 Top 3 組合")
            st.table(top_3)
            
            st.success(f"✅ 模擬完成！這三組號碼是從 1000 次隨機事件中，最符合最近 100 期物理規律的佼佼者。")
            
            # 5. 下載區
            csv = top_3.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 下載 Top 3 戰略報告", csv, "Gauss_V691_Top3.csv", "text/csv")

        else:
            st.error("數據格式錯誤，請確保號碼在第二欄。")
    except Exception as e:
        st.error(f"執行錯誤: {e}")
else:
    st.info("👋 請上傳 Excel 歷史數據，啟動 1,000 次深度模擬與 Top 3 篩選。")

st.markdown("---")
st.caption("Gauss Master Pro v6.9.1 | 1000-Sim Elite Selection | No Bias Physical Analytics")

