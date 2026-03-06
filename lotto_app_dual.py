import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter

# ==========================================
# 核心計算引擎 (539 適配)
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
    all_draws = [num for sublist in history for num in sublist]
    counts = Counter(all_draws)
    hot_numbers = [num for num, _ in counts.most_common(12)]
    recent_15 = history[:15]
    streak_count = sum(1 for d in recent_15 if any(d[i] == d[i-1] + 1 for i in range(1, 5)))
    streak_tendency = 2.5 if streak_count < 5 else 1.1
    return {"hot": hot_numbers, "streak_tendency": streak_tendency, "counts": counts}

def get_god_score_batch(metrics_list, patterns):
    scores = []
    for m in metrics_list:
        base = m['ac'] * 28 
        if m['streak'] == 2:
            base += 40 * patterns['streak_tendency']
        elif m['streak'] >= 3:
            base -= 85
        if m['same_tail'] == 2:
            base += 35
        hot_in_combo = len(set(m['nums']).intersection(set(patterns['hot'])))
        if 1 <= hot_in_combo <= 2:
            base += 50
        if m['odd'] == 2 or m['odd'] == 3:
            base += 30
        sum_penalty = abs(m['sum'] - 100) * 1.6
        entropy = random.uniform(0, 15)
        scores.append(round(base + entropy - sum_penalty, 3))
    return scores

# ==========================================
# Streamlit UI 介面
# ==========================================

st.set_page_config(page_title="Gauss Master Pro V13 Fusion", page_icon="💎", layout="wide")
st.title("💎 Gauss Master Pro V13 終極自動化版")
st.markdown("💡 **支援「號碼擠在同一格」** | 自動拆分文字 | 570,000 次暴力模擬")

with st.sidebar:
    st.header("📂 數據核心")
    uploaded_file = st.file_uploader("上傳 Excel (支援同一格多號)", type=["xlsx"])
    st.divider()
    st.info("🧬 讀取技術：智能文字拆分 (Regex-Logic)")
    st.info("🌡️ 評分模型：V9 統計融合")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        
        for _, row in df.iterrows():
            row_numbers = []
            for cell in row:
                cell_str = str(cell).strip()
                # 使用正規表達式抓取所有數字 (支援逗號、空格、頓號分割)
                nums_in_cell = re.findall(r'\d+', cell_str)
                for n in nums_in_cell:
                    row_numbers.append(int(n))
            
            # 只要這一列總共抓到 5 個或以上的數字，就視為一期紀錄
            if len(row_numbers) >= 5:
                # 過濾掉可能不屬於 539 的異常數字 (例如期數)
                clean_nums = [n for n in row_numbers if 1 <= n <= 39]
                if len(clean_nums) >= 5:
                    history.append(sorted(clean_nums[:5]))

        if history:
            st.success(f"✅ 成功掃描到 {len(history)} 期歷史開獎數據！")
            patterns = analyze_full_history(history)
            
            # --- 模擬計算過程 ---
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
                    if score > 160: 
                        all_top_candidates.append({"combo": combo_meta['nums'], "score": score, "m": combo_meta})
                
                progress_bar.progress((i + batch_size) / total_sims)
                status_text.text(f"正在進行第 {i + batch_size} 次天機演算...")

            final_pool = sorted(all_top_candidates, key=lambda x: x['score'], reverse=True)[:100]
            final_top5 = final_pool[:5]

            # --- 結果呈現 ---
            st.subheader("👑 V13 天機融合最終精選 Top 5")
            display_data = []
            for idx, item in enumerate(final_top5):
                c = item["combo"]
                m = item["m"]
                display_data.append({
                    "等級": "至尊首選" if idx == 0 else f"推薦 {idx+1}",
                    "組合": ", ".join([f"{x:02d}" for x in c]),
                    "評分": item["score"],
                    "總和": m["sum"],
                    "奇偶": f"{m['odd']}:{m['even']}",
                    "AC值": m["ac"]
                })
            st.table(pd.DataFrame(display_data))
            st.balloons()
        else:
            st.error("❌ 依舊偵測不到數字。請確認 Excel 中儲存格內容，例如：'01 05 12 23 35' 或 '01,05,12,23,35'")
    except Exception as e:
        st.error(f"系統執行出錯: {e}")
else:
    st.info("👋 請上傳你的 539 歷史 Excel。就算號碼全部擠在同一格也沒問題！")
