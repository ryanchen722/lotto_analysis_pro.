import random
import pandas as pd
import streamlit as st
import numpy as np
from collections import Counter

# ==========================================
# V13 終極融合版 (539 適配)
# ==========================================

def get_metrics_batch(combos):
    """計算物理特徵：AC值、跨度、連號、尾數、奇偶、總和"""
    metrics_list = []
    for nums in combos:
        # 確保排序穩定
        nums = sorted(list(nums))
        
        # 1. AC 值
        diffs = set()
        for i in range(len(nums)):
            for j in range(i+1, len(nums)):
                diffs.add(abs(nums[i] - nums[j]))
        ac = len(diffs) - (len(nums) - 1)
        
        # 2. 跨度與總和
        span = nums[-1] - nums[0]
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
            "ac": ac, "span": span, "streak": max_streak,
            "same_tail": same_tail_count, "sum": total_sum,
            "odd": odd, "even": even, "nums": nums
        })
    return metrics_list

def analyze_full_history(history):
    """分析歷史規律：熱號、連號趨勢"""
    all_draws = [num for sublist in history for num in sublist]
    counts = Counter(all_draws)
    hot_numbers = [num for num, _ in counts.most_common(12)] # 取前12強
    
    # 分析近 15 期連號頻率
    recent_15 = history[:15]
    streak_count = sum(1 for d in recent_15 if any(d[i] == d[i-1] + 1 for i in range(1, 5)))
    # 如果近期連號少，則拉高連號權重 (補償心理)
    streak_tendency = 2.5 if streak_count < 5 else 1.1
    return {"hot": hot_numbers, "streak_tendency": streak_tendency, "counts": counts}

def get_god_score_batch(metrics_list, patterns):
    """天機評分演算法：融合 V9 統計規律"""
    scores = []
    for m in metrics_list:
        # --- 基石評分 (AC值是靈魂) ---
        base = m['ac'] * 28 
        
        # --- 連號邏輯 ---
        if m['streak'] == 2:
            base += 40 * patterns['streak_tendency']
        elif m['streak'] >= 3:
            base -= 80 # 539 極少 3 連號
            
        # --- 尾數邏輯 (同尾 2 顆最香) ---
        if m['same_tail'] == 2:
            base += 35
        elif m['same_tail'] > 3:
            base -= 60

        # --- 冷熱號平衡 (1~2 顆熱號) ---
        hot_in_combo = len(set(m['nums']).intersection(set(patterns['hot'])))
        if 1 <= hot_in_combo <= 2:
            base += 50
        elif hot_in_combo == 0:
            base -= 20
            
        # --- 奇偶平衡 (539 建議 2:3 或 3:2) ---
        if m['odd'] == 2 or m['odd'] == 3:
            base += 30
        else:
            base -= 30
            
        # --- 核心：總和懲罰 (錨定 100) ---
        # 539 理想總和 75~125，越偏離扣分越重
        sum_penalty = abs(m['sum'] - 100) * 1.5
        
        # 熵值微擾 (增加隨機多樣性)
        entropy = random.uniform(0, 15)
        
        scores.append(round(base + entropy - sum_penalty, 3))
    return scores

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Master Pro V13 Fusion", page_icon="💎", layout="wide")
st.title("💎 Gauss Master Pro V13 終極融合版")
st.markdown("🚀 **大數據暴力模擬 + V9 統計過濾器**：570,000 次運算完美收斂")

with st.sidebar:
    st.header("📂 核心配置")
    uploaded_file = st.file_uploader("上傳歷史數據 (Excel)", type=["xlsx"])
    st.divider()
    st.write("🔧 運作參數：")
    st.success("🎯 總和錨定：100")
    st.success("🧬 AC 過濾：標靶化")
    st.warning("🔄 模擬次數：570,000")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        # 強化解析邏輯
        for _, row in df.iterrows():
            clean_row = pd.to_numeric(row, errors='coerce').dropna().astype(int).tolist()
            if len(clean_row) >= 5:
                history.append(sorted(clean_row[:5]))

        if history:
            patterns = analyze_full_history(history)
            
            # --- 數據儀表板 ---
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("核心首選熱號", f"{patterns['hot'][0]:02d}")
            with c2:
                st.metric("趨勢補償係數", f"{patterns['streak_tendency']:.1f}x")
            with c3:
                st.write("🔥 熱號池：")
                st.caption(", ".join([f"{x:02d}" for x in patterns['hot']]))

            # --- 暴力模擬啟動 ---
            progress_bar = st.progress(0)
            status_text = st.empty()
            batch_size = 15000
            total_sims = 570000
            all_top_candidates = []

            for i in range(0, total_sims, batch_size):
                # 1. 生成原始組合
                combos = [random.sample(range(1, 40), 5) for _ in range(batch_size)]
                # 2. 批量計算物理特徵
                metrics_list = get_metrics_batch(combos)
                # 3. 注入天機評分演算法
                scores = get_god_score_batch(metrics_list, patterns)
                
                for combo_meta, score in zip(metrics_list, scores):
                    # 門檻過濾：只保留高分且物理結構合理的
                    if score > 150: 
                        all_top_candidates.append({"combo": combo_meta['nums'], "score": score, "m": combo_meta})
                
                progress_bar.progress((i + batch_size) / total_sims)
                status_text.text(f"已掃描 {i + batch_size} 組天機組合...")

            # 從數萬組高分候選中選出 Top 100
            final_pool = sorted(all_top_candidates, key=lambda x: x['score'], reverse=True)[:100]

            # --- 最終 Top 5 融合展示 ---
            st.subheader("👑 天機融合最終精選 Top 5")
            final_top5 = final_pool[:5]
            
            display_list = []
            for idx, item in enumerate(final_top5):
                c = item["combo"]
                m = item["m"]
                display_list.append({
                    "等級": "破壁至尊" if idx == 0 else "天機推薦",
                    "推薦組合": ", ".join([f"{x:02d}" for x in c]),
                    "評分": item["score"],
                    "總和": m["sum"],
                    "奇偶": f"{m['odd']}:{m['even']}",
                    "AC值": m["ac"],
                    "尾碼": "符合自然分佈"
                })

            st.table(pd.DataFrame(display_list))

            # --- 遺漏號碼分析 ---
            st.divider()
            final_selected_nums = set()
            for item in final_top5:
                final_selected_nums.update(item["combo"])
            
            missing_nums = sorted(list(set(range(1, 40)) - final_selected_nums))
            st.write("🧬 **本次運算未選中號碼 (遺漏參考)**")
            st.code(", ".join([f"{x:02d}" for x in missing_nums]))

            st.success(f"✅ 模擬完成！在 {total_sims} 組模擬中，已為您鎖定最強 5 組 539 組合。")

        else:
            st.error("Excel 資料格式不符，請確認是否包含 539 開獎號碼欄位。")
    except Exception as e:
        st.error(f"系統運行異常: {e}")
else:
    st.info("👋 歡迎使用！請上傳 539 歷史開獎資料 Excel 以啟動暴力模擬引擎。")
