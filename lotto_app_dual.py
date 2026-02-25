import random
import pandas as pd
import streamlit as st
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：連號偵測與 AI 評分優化
# ==========================================

def get_consecutive_info(nums):
    """偵測連號狀況"""
    nums = sorted(nums)
    consecutive_count = 0
    max_streak = 1
    current_streak = 1
    
    for i in range(1, len(nums)):
        if nums[i] == nums[i-1] + 1:
            current_streak += 1
            consecutive_count += 1
        else:
            max_streak = max(max_streak, current_streak)
            current_streak = 1
    max_streak = max(max_streak, current_streak)
    return consecutive_count, max_streak

def analyze_trend(history, max_num=39):
    """分析最近 30 期的盤勢體質與連號頻率"""
    if len(history) < 10:
        return "數據不足", "建議維持標準策略", 1.0, 0.5
    
    recent_30 = history[:30]
    
    # 連號頻率分析
    consecutive_history = [get_consecutive_info(d)[0] for d in recent_30]
    avg_consecutive = sum(consecutive_history) / len(consecutive_history)
    
    all_nums = [n for draw in recent_30 for n in draw]
    counts = Counter(all_nums)
    unique_covered = len(counts.keys())
    coverage_rate = unique_covered / max_num
    
    if avg_consecutive > 0.8:
        return "連號密集期", "近期連號頻繁出現，AI 已調高『二連號』生成機率。", 1.2, 0.7
    elif coverage_rate > 0.85:
        return "均勻分佈期", "號碼極度分散，AI 將優先選擇『無連號』組合。", 1.1, 0.3
    else:
        return "標準隨機", "盤勢平穩，維持 50/50 連號配比策略。", 1.0, 0.5

def calculate_ac(nums):
    """計算算術複雜度 (AC值)"""
    if not nums: return 0
    diffs = set()
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    return len(diffs) - (len(nums) - 1)

def get_ai_score(combo, trend_weight):
    """V6.8.6 AI 綜合評分 (導入連號權重)"""
    ac = calculate_ac(combo)
    c_count, m_streak = get_consecutive_info(combo)
    
    # 基礎分
    score = ac * 10 
    
    # 連號獎懲邏輯
    if m_streak == 2: score += 15  # 獎勵二連號 (符合大眾心理與實際機率平衡)
    if m_streak >= 3: score -= 30  # 懲罰三連號以上 (低機率組合)
    if m_streak == 1: score += 5   # 無連號為基準
    
    # 總和回歸 (539中位數約100)
    score -= abs(sum(combo) - 100) * 0.4
    
    return round(score * trend_weight, 2)

# ==========================================
# UI 介面
# ==========================================

st.set_page_config(page_title="Gauss Master Pro V6.8.6", page_icon="🧬", layout="wide")

st.title("🧬 Gauss Master Pro V6.8.6 (連號規律強化版)")
st.markdown("當前版本已整合 **連號頻率偵測** 與 **動態空間權重系統**。")

with st.sidebar:
    st.header("📊 數據中心")
    uploaded_file = st.file_uploader("上傳 Excel 歷史數據", type=["xlsx"])
    st.divider()
    num_sets = st.slider("推薦組數", 1, 10, 5)
    st.info("💡 專業建議：在 5 組推薦中，通常會包含 2 組二連號與 3 組無連號。")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for val in df.iloc[:, 1].dropna().astype(str):
            nums = [int(n) for n in val.replace(' ', ',').replace('、', ',').split(',') if n.strip().isdigit()]
            if len(nums) == 5: # 專注 539 邏輯
                history.append(nums)
        
        if history:
            trend_name, advice, t_weight, cons_prob = analyze_trend(history)
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("盤勢體質", trend_name)
                st.write(f"🔮 **策略導向**：\n{advice}")
            
            with col2:
                # 顯示連號分佈統計
                c_data = [get_consecutive_info(d)[0] for d in history[:30]]
                c_counts = Counter(c_data)
                st.write("最近 30 期連號組數分佈 (0=無連號, 1=二連號...)")
                st.bar_chart(pd.DataFrame.from_dict(c_counts, orient='index'))

            st.subheader("🤖 AI 戰略推薦 (已優化連號配比)")
            recommendations = []
            while len(recommendations) < num_sets:
                # 根據趨勢決定是否強制生成連號
                force_consecutive = random.random() < cons_prob
                combo = sorted(random.sample(range(1, 40), 5))
                c_count, m_streak = get_consecutive_info(combo)
                
                if force_consecutive and m_streak < 2: continue
                if not force_consecutive and m_streak > 1: continue
                
                # 基礎過濾：至少一個大號碼
                if not any(n > 31 for n in combo): continue
                
                score = get_ai_score(combo, t_weight)
                recommendations.append({
                    "組合": ", ".join(map(str, combo)),
                    "AI 評分": score,
                    "連號狀況": "無" if m_streak == 1 else f"{m_streak}連號",
                    "AC值": calculate_ac(combo),
                    "總和": sum(combo)
                })
            
            rec_df = pd.DataFrame(recommendations).sort_values("AI 評分", ascending=False)
            st.table(rec_df)
            
        else:
            st.error("數據格式不符，請確保號碼在第二欄。")
    except Exception as e:
        st.error(f"執行錯誤: {e}")
else:
    st.info("請上傳歷史數據以啟動 AI 連號平衡邏輯。")

st.markdown("---")
st.caption("Gauss Master Pro v6.8.6 | 空間機率學實驗室 | 僅供數據研究參考")

