import random
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：五萬次全維度暴力模擬系統
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
    
    # 連號傾向分析 (最近 15 期)
    streaks = [get_detailed_metrics(d)['streak'] for d in recent_data]
    recent_15_streaks = streaks[:15]
    actual_streak_rate = len([s for s in recent_15_streaks if s > 1]) / 15
    # 若近期連號出現頻率極低，大幅提高連號回歸獎勵
    streak_tendency = 2.2 if actual_streak_rate < 0.35 else 1.0
    
    return {
        "avg_span": avg_span,
        "streak_tendency": streak_tendency,
        "sample_size": sample_size,
        "history_spans": spans
    }

def get_ai_score(m, patterns):
    """V6.9.4 AI 全維度評分邏輯 (50,000次專用)"""
    # 基礎權重：AC值 (確保隨機度)
    score = m['ac'] * 12 
    
    # 1. 跨度精準權重 (極致鎖定)
    score -= abs(m['span'] - patterns['avg_span']) * 5.5
    
    # 2. 連號回歸權重
    if m['streak'] == 2: 
        score += (28 * patterns['streak_tendency'])
    elif m['streak'] >= 3: 
        score -= 65 # 暴力排除低機率三連號
    
    # 3. 總和平衡權重 (理想中心 100)
    score -= abs(m['sum'] - 100) * 0.9
    
    # 4. 尾數平衡權重 (理想為「一組同尾」)
    if m['same_tail'] == 2: 
        score += 25
    elif m['same_tail'] >= 3: 
        score -= 35 
    
    # 5. 奇偶平衡權重 (極限鎖定 3奇2偶 或 2奇3偶)
    if m['odds'] in [2, 3]: 
        score += 25
    else: 
        score -= 30
    
    return round(score, 2)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Pro V6.9.4 50K-Sim", page_icon="🧬", layout="wide")

st.title("🧬 Gauss Master Pro V6.9.4 (五萬次暴力模擬版)")
st.markdown("本版本採取 **50,000 次深度海選抽樣**，運算規模提升至最高級別，只為篩選出物理結構最完美的 **Top 3**。")

with st.sidebar:
    st.header("📂 數據導入")
    uploaded_file = st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    st.divider()
    st.write("📊 **核心執行策略：**")
    st.error("🔥 **模擬規模：50,000 次**")
    st.info("🏆 **錄取名額：Top 3 超精英**")
    st.write("✅ 基準：最近 100 期大數據慣性")
    st.write("✅ 指標：AC/跨度/連號/總和/奇偶/尾數")

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
                st.caption("AI 邊界鎖定基準")
            with c2:
                st.metric("連號缺失補償", f"{patterns['streak_tendency']}x")
                st.caption("越高則 AI 越傾向推薦二連號")
            with c3:
                st.write("歷史跨度走勢 (最近 30 期)：")
                st.line_chart(patterns['history_spans'][-30:])

            # 3. 執行 50,000 次模擬抽樣
            st.subheader(f"🤖 AI 正在進行 50,000 次暴力模擬運算...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            best_candidates = [] # 僅存儲得分前 50 的種子組合，避免記憶體溢出
            
            # 模擬計算
            for i in range(50000):
                combo = sorted(random.sample(range(1, 40), 5))
                m = get_detailed_metrics(combo)
                score = get_ai_score(m, patterns)
                
                # 簡單的排序維持邏輯，只留分數最高的組合
                best_candidates.append({
                    "推薦組合": ", ".join([f"{x:02d}" for x in combo]),
                    "AI 綜合評分": score,
                    "跨度": m['span'],
                    "奇偶比 (奇:偶)": f"{m['odds']}:{5-m['odds']}",
                    "連號狀況": "無" if m['streak'] == 1 else f"{m['streak']}連",
                    "尾數同尾": "是" if m['same_tail'] > 1 else "否",
                    "組合總和": m['sum'],
                    "AC值": m['ac']
                })
                
                # 每 5000 次清理一次列表，只保留 Top 50，提升效能
                if len(best_candidates) > 200:
                    best_candidates = sorted(best_candidates, key=lambda x: x["AI 綜合評分"], reverse=True)[:50]
                
                # 更新進度條 (每 5000 次更新一次)
                if i % 5000 == 0:
                    progress_bar.progress((i + 5000) / 50000)
                    status_text.text(f"已完成 {i+5000} / 50000 次運算...")
            
            # 4. 最終篩選 Top 3
            top_3 = pd.DataFrame(best_candidates).sort_values("AI 綜合評分", ascending=False).head(3)
            
            st.subheader("👑 五萬次模擬決選 - Top 3 全維度精英")
            st.table(top_3)
            
            st.success(f"✅ 暴力模擬完成！從五萬個隨機組合中脫穎而出，這三組是結構最穩定、最符合歷史物理慣性的頂級推薦。")
            
            # 5. 下載區
            csv = top_3.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 下載決選戰略報告", csv, "Gauss_V694_Top3_50K.csv", "text/csv")

        else:
            st.error("數據格式錯誤，請檢查 Excel 第二欄。")
    except Exception as e:
        st.error(f"系統錯誤: {e}")
else:
    st.info("👋 請上傳歷史數據。AI 將啟動 50,000 次暴力模擬運算，尋找物理結構最強的三組精華。")

st.markdown("---")
st.caption("Gauss Master Pro v6.9.4 | 50,000-Sim Brute Force Selection | Hexa-Dimensional Analysis")

