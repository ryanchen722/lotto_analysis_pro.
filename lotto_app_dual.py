import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter
import itertools

# ==========================================
# 核心引擎：V16.3 動態重心評分邏輯
# ==========================================

def get_god_score_batch(metrics_list, patterns, auto_first_center, auto_sum_center):
    scores = []
    for m in metrics_list:
        nums = m['nums']
        first_num = nums[0]
        s = m['sum']
        ac_val = m['ac']
        
        # --- 1. AC 值：階梯式加分 (鎖定隨機分佈美感) ---
        if ac_val >= 7: 
            base = 300 + (ac_val * 15)
        elif ac_val >= 5: 
            base = 150 + (ac_val * 10)
        else: 
            base = ac_val * 5

        # --- 2. 動態首碼約束 (自動重心 ± 7 的彈性緩衝) ---
        dist_first = abs(first_num - auto_first_center)
        if dist_first <= 7: 
            base += 300 - (dist_first * 15)
        else:
            base -= (dist_first - 7) * 45 

        # --- 3. 動態總和約束 (自動總和重心 ± 20) ---
        sum_err = abs(s - auto_sum_center)
        if sum_err <= 20:
            base += 200 - (sum_err * 6)
        else:
            base -= (sum_err - 20) * 18

        # --- 4. 歷史避險 (過濾近期高機率連開號碼) ---
        danger_hits = len(set(nums).intersection(patterns['danger_numbers']))
        base -= (danger_hits * 400)
        
        # 增加熵值 (隨機擾動)，確保每次模擬結果都具有獨特性
        entropy = random.uniform(0, 100) 
        scores.append(round(base + entropy, 2))
    return scores

# ==========================================
# UI 介面與動態趨勢分析
# ==========================================

st.set_page_config(page_title="Gauss Master V16.3", page_icon="♾️", layout="wide")
st.title("♾️ Gauss Master Pro V16.3 動態重心版")

uploaded_file = st.file_uploader("請上傳 539 歷史 Excel 檔案 (xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for _, row in df.iterrows():
            clean_nums = [int(n) for n in re.findall(r'\d+', str(row.values)) if 1 <= int(n) <= 39]
            if len(clean_nums) >= 5: history.append(sorted(clean_nums[:5]))

        if history:
            # --- 自動趨勢掃描：分析最近 15 期重心 ---
            recent_context = history[:15]
            avg_first = np.mean([draw[0] for draw in recent_context])
            avg_sum = np.mean([sum(draw) for draw in recent_context])
            
            latest_draw = history[0]
            # 避險：找出最近兩期交集的號碼
            danger_numbers = set(history[0]).intersection(set(history[1])) if len(history)>=2 else set()
            patterns = {"danger_numbers": danger_numbers, "latest": latest_draw}
            
            # --- 頂部數據儀表板 ---
            st.markdown("### 📊 當前盤勢自動偵測")
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("最新一期開獎", ", ".join([f"{x:02d}" for x in latest_draw]))
            with col2: st.metric("動態首碼重心 (15期)", f"{avg_first:.1f}")
            with col3: st.metric("動態總和重心 (15期)", f"{int(avg_sum)}")
            st.divider()

            if st.button("🚀 啟動 57 萬次自動重心模擬"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                hot_pool = []
                
                # 第一階段：海選強勢號碼池
                for i in range(38):
                    status_text.text(f"第一階段：正在根據自動重心海選強勢號碼... ({i+1}/38)")
                    raw = [random.sample(range(1, 40), 5) for _ in range(15000)]
                    metrics = []
                    for r in raw:
                        r.sort()
                        diffs = set(abs(a-b) for a,b in itertools.combinations(r, 2))
                        # 計算 AC 值
                        metrics.append({"nums": r, "sum": sum(r), "ac": len(diffs) - 4})
                    
                    scores = get_god_score_batch(metrics, patterns, avg_first, avg_sum)
                    for m, s in zip(metrics, scores):
                        if s > 250: # 收集高分號碼
                            hot_pool.extend(m['nums'])
                    progress_bar.progress((i+1)/50)

                # 第二階段：精準二次重組
                status_text.text("第二階段：正在從強勢池重組最佳搭配組合...")
                if hot_pool:
                    # 統計頻率最高的前 20 名號碼
                    top_n_nums = [n for n, c in Counter(hot_pool).most_common(20)]
                    
                    # 使用這 20 顆強勢號碼隨機生成 30,000 組
                    refined_raw = [random.sample(top_n_nums, 5) for _ in range(30000)]
                    refined_metrics = []
                    for r in refined_raw:
                        r.sort()
                        diffs = set(abs(a-b) for a,b in itertools.combinations(r, 2))
                        refined_metrics.append({"nums": r, "sum": sum(r), "ac": len(diffs) - 4})
                    
                    refined_scores = get_god_score_batch(refined_metrics, patterns, avg_first, avg_sum)
                    
                    final_candidates = []
                    for m, s in zip(refined_metrics, refined_scores):
                        if s > 450: # 二次精配的高分門檻
                            final_candidates.append({"combo": m['nums'], "score": s, "sum": m['sum'], "ac": m['ac']})
                    
                    progress_bar.progress(1.0)
                    if final_candidates:
                        status_text.success("✅ 自動重心模擬完成！")
                        random.shuffle(final_candidates)
                        final_top = sorted(final_candidates, key=lambda x: x['score'], reverse=True)[:5]
                        
                        st.subheader("👑 本期推薦天選組合")
                        res_df = []
                        for idx, item in enumerate(final_top):
                            c = item['combo']
                            res_df.append({
                                "排名": f"Top {idx+1}", 
                                "推薦組合": ", ".join([f"{x:02d}" for x in c]), 
                                "總和": item['sum'], 
                                "首碼": f"{c[0]:02d}", 
                                "AC值": item['ac']
                            })
                        st.table(pd.DataFrame(res_df))
                        
                        st.markdown(f"📊 **動態核心強勢號碼池 (Top 20)**：\n`{', '.join([f'{x:02d}' for x in sorted(top_n_nums)])}`")
                        st.balloons()
                    else:
                        st.warning("⚠️ 模擬過程波動較大，請再次點擊按鈕獲取結果。")
                else:
                    st.error("海選失敗，請檢查 Excel 資料格式。")
                    
    except Exception as e:
        st.error(f"❌ 執行出錯: {e}")
else:
    st.info("👋 指揮官您好！請上傳 Excel 歷史資料，我將自動分析重心並啟動模擬。")
