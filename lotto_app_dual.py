import random
import pandas as pd
import streamlit as st
import numpy as np
from collections import Counter

# ==========================================
# 核心計算引擎 (539 適配)
# ==========================================

def get_metrics_batch(combos):
    """計算物理特徵：AC值、連號、尾數、奇偶、總和"""
    metrics_list = []
    for nums in combos:
        nums = sorted(list(nums))
        
        # 1. AC 值 (539 建議 4-6)
        diffs = set()
        for i in range(len(nums)):
            for j in range(i+1, len(nums)):
                diffs.add(abs(nums[i] - nums[j]))
        ac = len(diffs) - (len(nums) - 1)
        
        # 2. 總和
        total_sum = sum(nums)

        # 3. 連號判斷
        max_streak = 1
        current = 1
        for i in range(1, len(nums)):
            if nums[i] == nums[i-1] + 1:
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 1

        # 4. 尾碼與奇偶
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
    """分析歷史規律：自動偵測冷熱號與連號傾向"""
    all_draws = [num for sublist in history for num in sublist]
    counts = Counter(all_draws)
    hot_numbers = [num for num, _ in counts.most_common(12)]
    
    recent_15 = history[:15]
    streak_count = sum(1 for d in recent_15 if any(d[i] == d[i-1] + 1 for i in range(1, 5)))
    # 若近期連號少於 5 期，則拉高模擬中的連號權重
    streak_tendency = 2.5 if streak_count < 5 else 1.1
    return {"hot": hot_numbers, "streak_tendency": streak_tendency, "counts": counts}

def get_god_score_batch(metrics_list, patterns):
    """天機評分演算法：V9 統計特徵 + 總和錨定"""
    scores = []
    for m in metrics_list:
        # 基底分數：AC 值加權
        base = m['ac'] * 28 
        
        # 連號獎勵/懲罰
        if m['streak'] == 2:
            base += 40 * patterns['streak_tendency']
        elif m['streak'] >= 3:
            base -= 85
            
        # 尾數邏輯 (同尾 2 顆最優)
        if m['same_tail'] == 2:
            base += 35
        elif m['same_tail'] > 3:
            base -= 60

        # 冷熱平衡
        hot_in_combo = len(set(m['nums']).intersection(set(patterns['hot'])))
        if 1 <= hot_in_combo <= 2:
            base += 50
        elif hot_in_combo >= 4:
            base -= 40 # 避開極端過熱
            
        # 奇偶平衡加分
        if m['odd'] == 2 or m['odd'] == 3:
            base += 30
            
        # 核心：總和過濾 (539 理想期望值 100)
        # 總和偏離 100 越遠，扣分越重
        sum_penalty = abs(m['sum'] - 100) * 1.6
        
        # 隨機熵值 (避免每次結果完全一樣)
        entropy = random.uniform(0, 15)
        
        scores.append(round(base + entropy - sum_penalty, 3))
    return scores

# ==========================================
# Streamlit UI 介面
# ==========================================

st.set_page_config(page_title="Gauss Master Pro V13 Fusion", page_icon="💎", layout="wide")
st.title("💎 Gauss Master Pro V13 終極自動化版")
st.markdown("💡 **無須日期欄位** | 自動掃描 Excel | 570,000 次暴力模擬融合")

with st.sidebar:
    st.header("📂 數據核心")
    uploaded_file = st.file_uploader("上傳歷史 Excel (純號碼即可)", type=["xlsx"])
    st.divider()
    st.info("🧬 讀取技術：全列自動識別 (OCR-Logic)")
    st.info("🌡️ 評分模型：V9 統計融合")
    st.error("⏳ 模擬規模：570,000 次")

if uploaded_file:
    try:
        # 讀取 Excel 並啟動自動偵測
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        
        for _, row in df.iterrows():
            # 自動找尋該列中所有的數字，並過濾掉非數字內容
            clean_row = pd.to_numeric(row, errors='coerce').dropna().astype(int).tolist()
            # 539 每一期應該有 5 個號碼
            if len(clean_row) >= 5:
                history.append(sorted(clean_row[:5]))

        if history:
            st.success(f"✅ 成功掃描到 {len(history)} 期歷史開獎數據！")
            patterns = analyze_full_history(history)
            
            # --- 數據儀表板 ---
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("核心熱門號碼", f"{patterns['hot'][0]:02d}")
            with c2:
                st.metric("趨勢引導強度", f"{patterns['streak_tendency']:.1f}x")
            with c3:
                st.write("🔥 近期 Top 12 熱號：")
                st.caption(", ".join([f"{x:02d}" for x in patterns['hot']]))

            # --- 模擬計算過程 ---
            progress_bar = st.progress(0)
            status_text = st.empty()
            batch_size = 15000
            total_sims = 570000
            all_top_candidates = []

            for i in range(0, total_sims, batch_size):
                # 生成 539 組合 (1-39 選 5)
                combos = [random.sample(range(1, 40), 5) for _ in range(batch_size)]
                metrics_list = get_metrics_batch(combos)
                scores = get_god_score_batch(metrics_list, patterns)
                
                for combo_meta, score in zip(metrics_list, scores):
                    # 只收集高分潛力組合
                    if score > 160: 
                        all_top_candidates.append({"combo": combo_meta['nums'], "score": score, "m": combo_meta})
                
                progress_bar.progress((i + batch_size) / total_sims)
                status_text.text(f"正在進行第 {i + batch_size} 次天機演算...")

            # 從候選池中挑選最強 Top 100，再取前 5 名
            final_pool = sorted(all_top_candidates, key=lambda x: x['score'], reverse=True)[:100]
            final_top5 = final_pool[:5]

            # --- 結果呈現 ---
            st.subheader("👑 V13 天機融合最終精選 Top 5")
            
            display_data = []
            for idx, item in enumerate(final_top5):
                c = item["combo"]
                m = item["m"]
                display_data.append({
                    "推薦等級": "🔥 至尊首選" if idx == 0 else f"推薦組 {idx+1}",
                    "組合": ", ".join([f"{x:02d}" for x in c]),
                    "天機評分": item["score"],
                    "總和": m["sum"],
                    "奇偶比": f"{m['odd']}:{m['even']}",
                    "AC值": m["ac"]
                })

            st.table(pd.DataFrame(display_data))

            # --- 遺漏號碼統計 ---
            st.divider()
            selected_nums = set()
            for item in final_top5:
                selected_nums.update(item["combo"])
            missing_nums = sorted(list(set(range(1, 40)) - selected_nums))
            st.write("🧬 **本次運算未涵蓋號碼 (遺漏參考)**")
            st.code(", ".join([f"{x:02d}" for x in missing_nums]))

            st.balloons()
        else:
            st.error("無法從 Excel 中偵測到足夠的號碼組合。請確認檔案內有包含 5 個號碼的橫列。")
    except Exception as e:
        st.error(f"系統執行出錯: {e}")
else:
    st.info("👋 歡迎！請上傳刪除日期後的 539 歷史 Excel 檔案即可啟動。")

st.markdown("---")
st.caption("Gauss Master Pro V13 | Fusion Engine | No Date Field Required")
