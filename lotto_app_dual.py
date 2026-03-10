import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter
import itertools

# ==========================================
# 核心引擎：V17.3 終極平衡評分邏輯
# ==========================================

def get_god_score_batch(metrics_list, patterns):
    scores = []
    for m in metrics_list:
        nums = m['nums']
        first, last = nums[0], nums[-1]
        
        # --- 1. AC 值 (基礎複雜度) ---
        # 確保號碼足夠亂，这是 539 的核心開獎邏輯
        base = m['ac'] * 50 

        # --- 2. 首碼平衡 (範圍：01-10 均有機會) ---
        if 1 <= first <= 5:
            base += 200 # 小號補償
        elif 6 <= first <= 10:
            base += 200 # 中小號加權
        elif first > 15:
            base -= 400 # 首碼太大則重罰

        # --- 3. 尾碼與跨度平衡 (跨度優於絕對數值) ---
        # 不再硬性要求 31 以上，只要跨度 (最後碼-第一碼) 在 20-33 之間就給分
        spread = last - first
        if 20 <= spread <= 33:
            base += 300 
        else:
            base -= abs(spread - 26) * 20

        # --- 4. 尾碼合理區間 (25-39 均可) ---
        if 25 <= last <= 39:
            base += 150
        else:
            base -= 500 # 尾碼太小 (低於25) 或太誇張才扣分

        # --- 5. 結構特徵 (同尾 & 避險) ---
        tails = [n % 10 for n in nums]
        if len(set(tails)) <= 4: 
            base += 100 # 鼓勵出現同尾數組合
        
        danger_hits = len(set(nums).intersection(patterns['danger_numbers']))
        base -= (danger_hits * 500)

        # 隨機熵值，確保每次結果都不同
        entropy = random.uniform(0, 100) 
        scores.append(round(base + entropy, 2))
    return scores

# ==========================================
# UI 介面
# ==========================================

st.set_page_config(page_title="Gauss Master V17.3", page_icon="🎯", layout="wide")
st.title("🎯 Gauss Master Pro V17.3 終極平衡版")

uploaded_file = st.file_uploader("請上傳歷史 Excel (xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for _, row in df.iterrows():
            clean_nums = [int(n) for n in re.findall(r'\d+', str(row.values)) if 1 <= int(n) <= 39]
            if len(clean_nums) >= 5: history.append(sorted(clean_nums[:5]))

        if history:
            # 避險號碼 (最近兩期重複出現的)
            danger = set(history[0]).intersection(set(history[1])) if len(history)>=2 else set()
            patterns = {"danger_numbers": danger}
            
            st.success(f"✅ 資料載入成功。最新開獎：{', '.join([f'{x:02d}' for x in history[0]])}")
            
            if st.button("🚀 啟動 V17.3 全域平衡模擬"):
                progress_bar = st.progress(0)
                hot_pool = []
                
                # 第一階段：57 萬次大規模海選
                for i in range(38):
                    raw = [random.sample(range(1, 40), 5) for _ in range(15000)]
                    metrics = [{"nums": sorted(r), "ac": len(set(abs(a-b) for a,b in itertools.combinations(sorted(r), 2))) - 4} for r in raw]
                    scores = get_god_score_batch(metrics, patterns)
                    for m, s in zip(metrics, scores):
                        if s > 350: 
                            hot_pool.extend(m['nums'])
                    progress_bar.progress((i+1)/50)

                # 第二階段：核心池二次精準配對
                if hot_pool:
                    # 統計出最強勢的 22 顆號碼
                    top_n_nums = [n for n, c in Counter(hot_pool).most_common(22)]
                    refined_raw = [random.sample(top_n_nums, 5) for _ in range(50000)]
                    refined_metrics = [{"nums": sorted(r), "ac": len(set(abs(a-b) for a,b in itertools.combinations(sorted(r), 2))) - 4} for r in refined_raw]
                    
                    refined_scores = get_god_score_batch(refined_metrics, patterns)
                    final_candidates = [{"combo": m['nums'], "score": s} for m, s in zip(refined_metrics, refined_scores) if s > 500]
                    
                    progress_bar.progress(1.0)
                    if final_candidates:
                        random.shuffle(final_candidates)
                        final_top = sorted(final_candidates, key=lambda x: x['score'], reverse=True)[:5]
                        
                        st.subheader("👑 本期精選 Top 5 (全域平衡)")
                        res = []
                        for idx, item in enumerate(final_top):
                            c = item['combo']
                            res.append({
                                "排名": f"Top {idx+1}", 
                                "推薦號碼": ", ".join([f"{x:02d}" for x in c]), 
                                "首碼": f"{c[0]:02d}",
                                "尾碼": f"{c[-1]:02d}",
                                "跨度": c[-1] - c[0],
                                "總和": sum(c)
                            })
                        st.table(pd.DataFrame(res))
                        
                        st.markdown(f"📊 **動態強勢號碼池 (含小、中、大號)**：\n`{', '.join([f'{x:02d}' for x in sorted(top_n_nums)])}`")
                        st.balloons()
                    else:
                        st.warning("⚠️ 模擬未命中理想組合，請點擊重試。")
    except Exception as e: st.error(f"錯誤: {e}")
