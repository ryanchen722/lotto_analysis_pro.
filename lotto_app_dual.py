import random
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：純物理規律分析 (跨度與連號)
# ==========================================

def get_metrics(nums):
    """計算物理指標：AC值、跨度、連號"""
    nums = sorted(nums)
    # AC 值 (複雜度)
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

def analyze_patterns(history):
    """分析歷史數據中的跨度與連號規律"""
    if len(history) < 10:
        return None
    
    recent_30 = history[:30]
    
    # 1. 跨度數據
    spans = [(d[-1] - d[0]) for d in recent_30]
    avg_span = np.mean(spans)
    span_std = np.std(spans) # 跨度標準差，看波動大不大
    
    # 2. 連號數據
    streaks = [get_metrics(d)[2] for d in recent_30]
    streak_counts = Counter(streaks)
    # 判斷下一期出現連號的「機率傾向」
    # 如果最近 5 期都沒連號，理論上回歸機率增加
    recent_5_streaks = streaks[:5]
    streak_tendency = 1.0 if any(s > 1 for s in recent_5_streaks) else 1.5
    
    return {
        "avg_span": avg_span,
        "span_std": span_std,
        "span_history": spans,
        "streak_counts": streak_counts,
        "streak_tendency": streak_tendency,
        "all_nums": [n for d in recent_30 for n in d]
    }

def get_ai_score(combo, patterns):
    """V6.8.9 AI 物理評分邏輯 (移除人為過濾)"""
    ac, span, streak = get_metrics(combo)
    
    # 基礎分：AC 值 (越高代表分佈越均勻)
    score = ac * 12
    
    # 跨度匹配分：越接近歷史平均跨度分數越高
    span_diff = abs(span - patterns['avg_span'])
    score -= span_diff * 3.0
    
    # 連號匹配分：根據近期連號缺失狀況進行補償
    if streak == 2:
        score += (15 * patterns['streak_tendency'])
    elif streak >= 3:
        score -= 40 # 三連號依然屬於極低機率事件，予以扣分
        
    # 總和回歸分 (539 中位數 100)
    score -= abs(sum(combo) - 100) * 0.5
    
    return round(score, 2)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Master Pro V6.8.9", page_icon="🧬", layout="wide")

st.title("🧬 Gauss Master Pro V6.8.9 (物理規律強化版)")
st.markdown("本版本已**移除所有人工過濾器**，完全基於歷史**跨度走勢**與**連號頻率**進行預測。")

with st.sidebar:
    st.header("📂 數據導入")
    uploaded_file = st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    num_sets = st.slider("推薦組數", 1, 15, 5)
    st.divider()
    st.caption("版本說明：已取消 1-31 生日限制，完全開放所有號碼組合。")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for val in df.iloc[:, 1].dropna().astype(str):
            nums = [int(n) for n in val.replace(' ', ',').replace('、', ',').split(',') if n.strip().isdigit()]
            if len(nums) == 5:
                history.append(sorted(nums))
        
        if history:
            # 1. 規律分析
            patterns = analyze_patterns(history)
            
            # 2. 顯示數據報告
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("30期平均跨度", f"{patterns['avg_span']:.2f}")
                st.write(f"波動程度 (標準差): {patterns['span_std']:.2f}")
            with col2:
                st.write("連號出現次數 (1=無連號, 2=二連號)")
                st.bar_chart(pd.DataFrame.from_dict(patterns['streak_counts'], orient='index'))
            with col3:
                recent_span_trend = "縮小中" if patterns['span_history'][0] < patterns['avg_span'] else "擴大中"
                st.metric("當前跨度趨勢", recent_span_trend)
                st.write("AI 將優先匹配接近平均跨度的組合。")

            # 3. 跨度走勢圖
            st.subheader("📈 最近 30 期跨度 (Span) 走勢")
            st.line_chart(patterns['span_history'])

            # 4. 生成 AI 推薦
            st.subheader("🤖 AI 物理規律推薦組合")
            recommendations = []
            attempts = 0
            while len(recommendations) < num_sets and attempts < 5000:
                attempts += 1
                # 完全隨機取樣 1-39，無人為限制
                combo = sorted(random.sample(range(1, 40), 5))
                score = get_ai_score(combo, patterns)
                
                # 過濾極低分組合
                if score > 40:
                    ac, span, streak = get_metrics(combo)
                    recommendations.append({
                        "推薦組合": ", ".join([f"{x:02d}" for x in combo]),
                        "AI 綜合評分": score,
                        "跨度 (Span)": span,
                        "連號狀況": "無" if streak == 1 else f"{streak}連號",
                        "總和": sum(combo),
                        "AC值": ac
                    })
            
            rec_df = pd.DataFrame(recommendations).sort_values("AI 綜合評分", ascending=False)
            st.dataframe(rec_df, use_container_width=True, hide_index=True)
            
            st.success("✅ 物理規律分析完成。系統已根據歷史跨度與連號慣性優化推薦組合。")

        else:
            st.error("無法解析號碼，請確認號碼位在 Excel 第二欄。")
    except Exception as e:
        st.error(f"執行錯誤: {e}")
else:
    st.info("👋 請上傳歷史數據。系統將專注於分析跨度（首尾距離）與連號規律，不再進行人為過濾。")

st.markdown("---")
st.caption("Gauss Master Pro v6.8.9 | 物理結構分析引擎 | 移除人為過濾器")

