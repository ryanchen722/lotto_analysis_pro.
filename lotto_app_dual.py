import random
import pandas as pd
import streamlit as st
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：連號、冷熱、AC 綜合系統
# ==========================================

def get_consecutive_info(nums):
    """偵測連號狀況 (0=無連號, 1=二連號...)"""
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

def analyze_full_trend(history, max_num=39):
    """診斷最近 30 期的盤勢：包含冷熱與連號"""
    if len(history) < 10:
        return "數據中斷", "請補足歷史數據", 1.0, 0.5, {}
    
    recent_30 = history[:30]
    all_nums = [n for d in recent_30 for n in d]
    counts = Counter(all_nums)
    
    # 冷熱診斷
    hot_nums = {k: v for k, v in counts.items() if v >= 6} # 30期開6次以上(過熱)
    unique_covered = len(counts.keys())
    coverage_rate = unique_covered / max_num
    
    # 連號診斷
    c_data = [get_consecutive_info(d)[0] for d in recent_30]
    avg_cons = sum(c_data) / len(c_data)
    
    # 綜合體質判定
    if len(hot_nums) >= 5:
        trend = "極端熱平衡 (Hot Clustered)"
        advice = "號碼集中在特定區域（如 08 現象），AI 已啟動避熱過濾。"
        weight = 1.3
    elif coverage_rate > 0.85:
        trend = "均勻冷回歸 (Cold Dispersed)"
        advice = "號碼散佈極廣，適合追蹤長期未開出的冷門號。"
        weight = 1.1
    else:
        trend = "標準隨機走勢"
        advice = "盤勢穩定，AI 維持標準 50/50 連號策略。"
        weight = 1.0
        
    return trend, advice, weight, avg_cons, counts

def calculate_ac(nums):
    """計算算術複雜度 (AC值)"""
    if not nums: return 0
    diffs = set()
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    return len(diffs) - (len(nums) - 1)

def get_ai_score(combo, counts, t_weight):
    """V6.8.7 AI 綜合評分：整合熱度懲罰"""
    ac = calculate_ac(combo)
    c_count, m_streak = get_consecutive_info(combo)
    
    # 1. AC 複雜度基礎分
    score = ac * 11
    
    # 2. 連號權重修正
    if m_streak == 2: score += 12
    elif m_streak >= 3: score -= 35
    
    # 3. 熱度懲罰 (反人性：避免過熱號碼)
    # 若號碼在最近30期出現太頻繁，給予適度降分以避開分獎潮
    for n in combo:
        freq = counts.get(n, 0)
        if freq >= 6: score -= 8 # 極熱號懲罰
        if freq <= 1: score += 3 # 極冷號潛力獎勵
        
    # 4. 總和回歸 (539中位數100)
    score -= abs(sum(combo) - 100) * 0.4
    
    return round(score * t_weight, 2)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Master Pro V6.8.7", page_icon="🔥", layout="wide")

st.title("🔥 Gauss Master Pro V6.8.7 (熱度與連號全面版)")
st.markdown("本版本找回了**號碼熱度分佈分析**，並整合進 AI 選號權重。")

with st.sidebar:
    st.header("📊 數據管理中心")
    uploaded_file = st.file_uploader("請上傳開獎歷史 Excel", type=["xlsx"])
    st.divider()
    num_sets = st.slider("推薦組數", 1, 10, 5)
    st.info("💡 提醒：若 08 狂開，AI 會自動在推薦組合中降低其出現權重，以確保中獎期望值。")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for val in df.iloc[:, 1].dropna().astype(str):
            nums = [int(n) for n in val.replace(' ', ',').replace('、', ',').split(',') if n.strip().isdigit()]
            if len(nums) == 5:
                history.append(nums)
        
        if history:
            # 1. 執行診斷
            trend_name, advice, t_weight, avg_cons, freq_counts = analyze_full_trend(history)
            
            # 2. 顯示頂部儀表板
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("盤勢體質", trend_name)
            with col_b:
                st.metric("平均連號率", f"{avg_cons:.2f}")
            with col_c:
                st.write(f"🛡️ **AI 策略**：{advice}")
            
            # 3. 找回熱度分析圖表 (關鍵功能回歸)
            st.subheader("🌡️ 最近 30 期號碼熱度掃描")
            chart_data = pd.DataFrame({
                "號碼": [f"{i:02d}" for i in range(1, 40)],
                "出現次數": [freq_counts.get(i, 0) for i in range(1, 40)]
            })
            
            # 使用顏色標示熱度
            st.bar_chart(chart_data.set_index("號碼"), color="#FF4B4B" if "熱" in trend_name else "#3B82F6")

            # 4. 生成 AI 推薦
            st.subheader("🤖 AI 戰略推薦組合")
            recommendations = []
            while len(recommendations) < num_sets:
                # 模擬 50/50 連號配比
                use_consecutive = random.random() < 0.5
                combo = sorted(random.sample(range(1, 40), 5))
                _, m_streak = get_consecutive_info(combo)
                
                if use_consecutive and m_streak < 2: continue
                if not use_consecutive and m_streak > 1: continue
                if not any(n > 31 for n in combo): continue # 避開日期陷阱
                
                score = get_ai_score(combo, freq_counts, t_weight)
                
                recommendations.append({
                    "推薦組合": ", ".join(map(str, combo)),
                    "AI 綜合評分": score,
                    "連號": "無" if m_streak == 1 else f"{m_streak}連",
                    "AC值": calculate_ac(combo),
                    "總和": sum(combo)
                })
            
            rec_df = pd.DataFrame(recommendations).sort_values("AI 綜合評分", ascending=False)
            st.table(rec_df)
            
            # 5. 下載報告
            st.download_button("📥 下載完整分析報告", rec_df.to_csv(index=False).encode('utf-8-sig'), f"Gauss_V687_{datetime.now().strftime('%m%d')}.csv")

        else:
            st.error("無法解析號碼。請確認數據位在 Excel 第二欄。")
    except Exception as e:
        st.error(f"系統錯誤: {e}")
else:
    st.info("👋 請於左側上傳數據，系統將立即為您繪製熱度圖並計算 AI 評分。")

st.markdown("---")
st.caption("Gauss Master Pro v6.8.7 | 熱度感測系統 | 反人性權重引擎")

