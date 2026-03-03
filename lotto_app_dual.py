import random
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：100 期物理規律與高分過濾系統
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
    if len(history) < 10:
        return None
    
    # 擴展分析範圍至 100 期
    sample_size = min(len(history), 100)
    recent_data = history[:sample_size]
    
    # 1. 跨度數據走勢
    spans = [(d[-1] - d[0]) for d in recent_data]
    avg_span = np.mean(spans)
    span_std = np.std(spans)
    
    # 2. 連號數據分析
    streaks = [get_metrics(d)[2] for d in recent_data]
    streak_counts = Counter(streaks)
    
    # 3. 趨勢傾向 (觀察最近 10 期是否有連號缺失)
    recent_10_streaks = streaks[:10]
    # 若連號頻率低於平均(539二連號機率約40-50%)，則增加連號權重補償
    actual_streak_rate = len([s for s in recent_10_streaks if s > 1]) / 10
    streak_tendency = 1.6 if actual_streak_rate < 0.4 else 1.0
    
    return {
        "avg_span": avg_span,
        "span_std": span_std,
        "span_history": spans,
        "streak_counts": streak_counts,
        "streak_tendency": streak_tendency,
        "sample_size": sample_size
    }

def get_ai_score(combo, patterns):
    """V6.9.0 AI 物理評分：純數據驅動"""
    ac, span, streak = get_metrics(combo)
    
    # A. AC值權重 (基礎穩定性)
    score = ac * 15 
    
    # B. 跨度匹配分 (邊界凝聚力)
    # 距離 100 期平均跨度越近分越高
    span_diff = abs(span - patterns['avg_span'])
    score -= span_diff * 4.0
    
    # C. 連號策略分
    if streak == 2:
        score += (20 * patterns['streak_tendency'])
    elif streak >= 3:
        score -= 50 # 極端規律仍予以扣分，保持隨機美感
        
    # D. 總和回歸分 (539 理想中位數 100)
    score -= abs(sum(combo) - 100) * 0.6
    
    return round(score, 2)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Pro V6.9.0", page_icon="💎", layout="wide")

st.title("💎 Gauss Master Pro V6.9.0 (100期物理高分版)")
st.markdown("本版本針對 **最近 100 期** 數據進行跨度與連號建模，且 **AI 評分僅推薦 80 分以上** 之極品組合。")

with st.sidebar:
    st.header("📂 數據導入")
    uploaded_file = st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    num_sets = st.slider("推薦組數", 1, 10, 5)
    st.divider()
    st.write("📋 **當前篩選標準：**")
    st.info("🎯 **AI 分數下限：80.0**")
    st.write("✅ 樣本範圍：最近 100 期")
    st.write("✅ 移除所有號碼過濾器")

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
            
            # 2. 顯示數據報告
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"最近 {patterns['sample_size']} 期平均跨度", f"{patterns['avg_span']:.2f}")
                st.write(f"跨度波動率 (Std): {patterns['span_std']:.2f}")
            with col2:
                st.write("連號歷史分佈 (100期)")
                st.bar_chart(pd.DataFrame.from_dict(patterns['streak_counts'], orient='index'))
            with col3:
                # 簡單計算近期強勢區
                recent_all = [n for d in history[:20] for n in d]
                top_3 = [f"{k:02d}" for k, v in Counter(recent_all).most_common(3)]
                st.write("近期活躍號碼參考：")
                st.code(", ".join(top_3))
                st.write("AI 評分門檻：80.0")

            # 3. 跨度走勢分析 (100期)
            st.subheader("📈 歷史跨度 (Span) 走勢分析 (100期)")
            st.line_chart(patterns['span_history'])

            # 4. 生成 AI 推薦 (嚴格 80 分篩選)
            st.subheader(f"🤖 AI 物理規律推薦 (僅顯示 80 分以上組合)")
            recommendations = []
            max_attempts = 20000 # 增加嘗試次數以達成高標篩選
            attempts = 0
            
            with st.spinner('AI 正在進行高強度運算與結構篩選...'):
                while len(recommendations) < num_sets and attempts < max_attempts:
                    attempts += 1
                    combo = sorted(random.sample(range(1, 40), 5))
                    score = get_ai_score(combo, patterns)
                    
                    # 嚴格過濾：必須大於等於 80 分
                    if score >= 80:
                        ac, span, streak = get_metrics(combo)
                        recommendations.append({
                            "推薦組合": ", ".join([f"{x:02d}" for x in combo]),
                            "AI 綜合評分": score,
                            "跨度 (Span)": span,
                            "連號狀況": "無連號" if streak == 1 else f"{streak}連號",
                            "組合總和": sum(combo),
                            "AC值": ac
                        })
            
            if recommendations:
                rec_df = pd.DataFrame(recommendations).sort_values("AI 綜合評分", ascending=False)
                st.table(rec_df)
                st.success(f"✅ 成功從 {attempts} 次隨機模擬中篩選出 {len(recommendations)} 組 80 分以上的精英組合。")
            else:
                st.warning("⚠️ 在兩萬次模擬中未找到 80 分以上的組合，建議降低組數或重新上傳數據。")

        else:
            st.error("數據解析失敗，請確保號碼位於 Excel 第二欄。")
    except Exception as e:
        st.error(f"執行錯誤: {e}")
else:
    st.info("👋 請上傳歷史數據。AI 將分析最近 100 期的物理規律並進行高標篩選。")

st.markdown("---")
st.caption("Gauss Master Pro v6.9.0 | 100-Period Deep Analytics | High-Threshold Scoring")

