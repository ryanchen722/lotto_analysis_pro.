import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter
import itertools

# ==========================================
# 核心引擎：V17.0 結構化評分邏輯 (去總和化)
# ==========================================

def get_god_score_batch(metrics_list, patterns, avg_first_context):
    scores = []
    for m in metrics_list:
        nums = m['nums']
        gaps = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
        tails = [n % 10 for n in nums]
        
        # --- 1. AC 值 (基礎複雜度) ---
        base = m['ac'] * 40 

        # --- 2. 間距平衡加分 (取代總和) ---
        # 理想的平均間距在 6~9 之間
        avg_gap = np.mean(gaps)
        if 6 <= avg_gap <= 9:
            base += 200
        else:
            base -= abs(avg_gap - 7.5) * 30

        # --- 3. 同尾連動 (Tail Logic) ---
        # 如果有同尾數 (如 12, 22)，通常是強勢盤的徵兆
        tail_counts = Counter(tails)
        if any(count >= 2 for count in tail_counts.values()):
            base += 100 # 鼓勵出現同尾數組合

        # --- 4. 首碼重心緩衝 ---
        dist_first = abs(nums[0] - avg_first_context)
        if dist_first <= 6:
            base += 250 - (dist_first * 15)
        else:
            base -= (dist_first - 6) * 50

        # --- 5. 歷史避險與冷熱過濾 ---
        # 避開最近兩期的重複交叉號
        danger_hits = len(set(nums).intersection(patterns['danger_numbers']))
        base -= (danger_hits * 450)
        
        # 鼓勵包含 1-2 顆長期遺漏號 (冷熱平衡)
        missing_hits = len(set(nums).intersection(patterns['missing']))
        if 1 <= missing_hits <= 2:
            base += 120

        entropy = random.uniform(0, 100) 
        scores.append(round(base + entropy, 2))
    return scores

# ==========================================
# UI 介面
# ==========================================

st.set_page_config(page_title="Gauss Master V17.0", page_icon="🧬", layout="wide")
st.title("🧬 Gauss Master Pro V17.0 結構平衡版")

uploaded_file = st.file_uploader("上傳 539 歷史 Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for _, row in df.iterrows():
            clean_nums = [int(n) for n in re.findall(r'\d+', str(row.values)) if 1 <= int(n) <= 39]
            if len(clean_nums) >= 5: history.append(sorted(clean_nums[:5]))

        if history:
            # 分析最近 15 期
            recent_context = history[:15]
            avg_first = np.mean([draw[0] for draw in recent_context])
            
            # 獲取遺漏號與避險號
            recent_all = [n for sub in history[:10] for n in sub]
            missing = [n for n in range(1, 40) if n not in recent_all]
            danger = set(history[0]).intersection(set(history[1])) if len(history)>=2 else set()
            patterns = {"danger_numbers": danger, "missing": missing}
            
            st.markdown(f"### 📊 盤勢分析：最新期 `{', '.join([f'{x:02d}' for x in history[0]])}`")
            st.info(f"💡 目前策略：放棄死板總和，改以「間距平衡(Gap)」與「同尾連動」為核心。")
            st.divider()

            if st.button("🚀 啟動 V17.0 結構化模擬"):
                progress_bar = st.progress(0)
                hot_pool = []
                
                # 第一階段：海選強勢結構
                for i in range(38):
                    raw = [random.sample(range(1, 40), 5) for _ in range(15000)]
                    metrics = []
                    for r in raw:
                        r.sort()
                        diffs = set(abs(a-b) for a,b in itertools.combinations(r, 2))
                        metrics.append({"nums": r, "ac": len(diffs) - 4})
                    
                    scores = get_god_score_batch(metrics, patterns, avg_first)
                    for m, s in zip(metrics, scores):
                        if s > 300: hot_pool.extend(m['nums'])
                    progress_bar.progress((i+1)/50)

                # 第二階段：重組
                if hot_pool:
                    top_n_nums = [n for n, c in Counter(hot_pool).most_common(20)]
                    refined_raw = [random.sample(top_n_nums, 5) for _ in range(30000)]
                    refined_metrics = [{"nums": sorted(r), "ac": len(set(abs(a-b) for a,b in itertools.combinations(sorted(r), 2))) - 4} for r in refined_raw]
                    
                    refined_scores = get_god_score_batch(refined_metrics, patterns, avg_first)
                    final_candidates = [{"combo": m['nums'], "score": s} for m, s in zip(refined_metrics, refined_scores) if s > 500]
                    
                    progress_bar.progress(1.0)
                    if final_candidates:
                        random.shuffle(final_candidates)
                        final_top = sorted(final_candidates, key=lambda x: x['score'], reverse=True)[:5]
                        
                        st.subheader("👑 結構化推薦組合 (去總和化)")
                        res = []
                        for idx, item in enumerate(final_top):
                            c = item['combo']
                            res.append({"排名": f"Top {idx+1}", "推薦組合": ", ".join([f"{x:02d}" for x in c]), 
                                        "平均間距": f"{np.mean([c[i+1]-c[i] for i in range(4)]):.1f}", 
                                        "首碼": f"{c[0]:02d}", "總和 (參考)": sum(c)})
                        st.table(pd.DataFrame(res))
                        st.markdown(f"📊 **本次核心強勢池**：\n`{', '.join([f'{x:02d}' for x in sorted(top_n_nums)])}`")
                        st.balloons()
    except Exception as e: st.error(f"錯誤: {e}")
