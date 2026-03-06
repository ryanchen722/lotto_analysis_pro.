import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter

# ==========================================
# 核心計算引擎 (V13.2 靈活總和 + 拖牌強化)
# ==========================================

def get_metrics_batch(combos):
    metrics_list = []
    for nums in combos:
        nums = sorted(list(nums))
        diffs = set()
        for i in range(len(nums)):
            for j in range(i+1, len(nums)):
                diffs.add(abs(nums[i] - nums[j]))
        ac = len(diffs) - (len(nums) - 1)
        total_sum = sum(nums)
        max_streak = 1
        current = 1
        for i in range(1, len(nums)):
            if nums[i] == nums[i-1] + 1:
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 1
        last_digits = [n % 10 for n in nums]
        same_tail_count = max(Counter(last_digits).values())
        odd = sum(n % 2 for n in nums)
        even = len(nums) - odd

        metrics_list.append({
            "ac": ac, "streak": max_streak,
            "same_tail": same_tail_count, "sum": total_sum,
            "odd": odd, "even": even, "nums": nums
        })
    return metrics_list

def analyze_full_history(history):
    """
    history[0] 為最新一期
    """
    all_draws = [num for sublist in history for num in sublist]
    counts = Counter(all_draws)
    hot_numbers = [num for num, _ in counts.most_common(12)]
    
    # 抓取「最新 15 期」
    recent_15 = history[:15] 
    streak_count = sum(1 for d in recent_15 if any(d[i] == d[i-1] + 1 for i in range(1, 5)))
    
    # 趨勢補償
    streak_tendency = 2.5 if streak_count < 5 else 1.1
    
    # 拖牌分析：抓取最新一期的數字及其鄰居 (±1)
    latest_draw = set(history[0])
    drag_numbers = set()
    for n in latest_draw:
        if n > 1: drag_numbers.add(n-1)
        drag_numbers.add(n) # 連莊可能
        if n < 39: drag_numbers.add(n+1)
        
    return {
        "hot": hot_numbers, 
        "streak_tendency": streak_tendency, 
        "counts": counts, 
        "latest": history[0],
        "drag_pool": drag_numbers
    }

def get_god_score_batch(metrics_list, patterns):
    scores = []
    for m in metrics_list:
        base = m['ac'] * 30 
        
        # 連號邏輯
        if m['streak'] == 2:
            base += 45 * patterns['streak_tendency']
        elif m['streak'] >= 3:
            base -= 90
            
        # 尾數
        if m['same_tail'] == 2:
            base += 35
        
        # 冷熱平衡 (1-3 顆熱號)
        hot_in_combo = len(set(m['nums']).intersection(set(patterns['hot'])))
        if 1 <= hot_in_combo <= 3:
            base += 55
            
        # 拖牌與連莊加權 (命中最新一期鄰近號碼)
        drag_hits = len(set(m['nums']).intersection(patterns['drag_pool']))
        base += (drag_hits * 15)
        
        # 奇偶平衡
        if m['odd'] == 2 or m['odd'] == 3:
            base += 30
            
        # --- 靈活總和邏輯 (不再死守 100) ---
        s = m['sum']
        if 75 <= s <= 125:
            # 黃金寬鬆區間：完全不扣分
            sum_penalty = 0
        else:
            # 極端區間：溫和扣分
            sum_penalty = abs(s - 100) * 0.7
        
        # 增加隨機擾動範圍
        entropy = random.uniform(0, 30)
        
        scores.append(round(base + entropy - sum_penalty, 3))
    return scores

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss V13.2 Fusion", page_icon="🔮", layout="wide")
st.title("🔮 Gauss Master Pro V13.2 靈活進階版")
st.markdown("💡 **第一組最新** | **靈活總和 (75-125)** | **拖牌加強機制**")

uploaded_file = st.file_uploader("上傳 539 歷史資料 (最新在第一列)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for _, row in df.iterrows():
            row_numbers = []
            for cell in row:
                nums_in_cell = re.findall(r'\d+', str(cell))
                for n in nums_in_cell:
                    row_numbers.append(int(n))
            
            clean_nums = [n for n in row_numbers if 1 <= n <= 39]
            if len(clean_nums) >= 5:
                history.append(clean_nums[:5])

        if history:
            history_sorted = [sorted(h) for h in history]
            patterns = analyze_full_history(history_sorted)
            
            st.success(f"✅ 資料載入成功！最新一期：{', '.join(map(str, history[0]))}")
            
            # --- 數據儀表板 ---
            cols = st.columns(4)
            cols[0].metric("核心熱號", f"{patterns['hot'][0]}")
            cols[1].metric("總和策略", "靈活區間")
            cols[2].metric("拖牌強度", f"{len(patterns['drag_pool'])} 碼")
            cols[3].metric("運算規模", "570k")

            # --- 模擬計算 ---
            progress_bar = st.progress(0)
            status_text = st.empty()
            batch_size = 15000
            total_sims = 570000
            all_top_candidates = []

            for i in range(0, total_sims, batch_size):
                combos = [random.sample(range(1, 40), 5) for _ in range(batch_size)]
                metrics_list = get_metrics_batch(combos)
                scores = get_god_score_batch(metrics_list, patterns)
                
                for combo_meta, score in zip(metrics_list, scores):
                    if score > 180: # 稍微提高門檻篩選精銳
                        all_top_candidates.append({"combo": combo_meta['nums'], "score": score, "m": combo_meta})
                
                progress_bar.progress((i + batch_size) / total_sims)
                status_text.text(f"數據融合中: {i + batch_size} / {total_sims}")

            # --- 最終結果 ---
            final_pool = sorted(all_top_candidates, key=lambda x: x['score'], reverse=True)[:5]
            
            st.subheader("👑 天機融合最終精選 (V13.2)")
            
            display_data = []
            for idx, item in enumerate(final_pool):
                c = item["combo"]
                m = item["m"]
                display_data.append({
                    "推薦等級": "🔥 旗艦首選" if idx == 0 else f"精選組 {idx+1}",
                    "推薦組合": ", ".join([f"{x:02d}" for x in c]),
                    "評分": item["score"],
                    "總和": m["sum"],
                    "奇偶": f"{m['odd']}:{m['even']}",
                    "AC值": m["ac"]
                })
            
            st.table(pd.DataFrame(display_data))
            st.info("💡 註：V13.2 已放寬總和限制，現在的組合會更具隨機起伏，並強化了最新一期的拖牌聯繫。")
            st.balloons()
            
        else:
            st.error("未能識別號碼。請確認 Excel 內容。")
    except Exception as e:
        st.error(f"執行錯誤: {e}")
else:
    st.info("請上傳您的 539 歷史 Excel（最新一期在最上方）。")
