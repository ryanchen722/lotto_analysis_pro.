import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter
import itertools

# ==========================================
# 核心引擎：V16.1 AC值與區間邏輯
# ==========================================

def get_god_score_batch(metrics_list, patterns, trend_mode):
    scores = []
    for m in metrics_list:
        nums = m['nums']
        first_num = nums[0]
        s = m['sum']
        ac_val = m['ac']
        
        # --- 基礎分數由 AC 值決定 (AC < 7 直接墊底) ---
        if ac_val >= 7:
            base = ac_val * 40  # AC越高，分佈越隨機，機率越高
        else:
            base = -1000 # 排除規律號碼

        # --- 戰略約束 (首碼區間) ---
        if "強力回歸" in trend_mode:
            if 1 <= first_num <= 11: base += 250 
            else: base -= 5000 
            target_sum, sum_margin = 90, 15
        else:
            if 10 <= first_num <= 20: base += 250 
            else: base -= 5000
            target_sum, sum_margin = 130, 15

        # --- 總和約束 ---
        if abs(s - target_sum) <= sum_margin:
            base += 150
        else:
            base -= 5000

        # --- 避險：連開兩期攔截 ---
        danger_hits = len(set(nums).intersection(patterns['danger_numbers']))
        base -= (danger_hits * 400)
        
        # 微量隨機熵值
        entropy = random.uniform(0, 30) 
        scores.append(round(base + entropy, 2))
    return scores

# ==========================================
# UI 介面與邏輯整合
# ==========================================

st.set_page_config(page_title="Gauss Master V16.1", page_icon="🧬", layout="wide")
st.title("🧬 Gauss Master Pro V16.1 核心強勢版")

st.sidebar.header("🕹️ 指揮中心")
trend_mode = st.sidebar.radio("走勢預測：", ("強力回歸 (06±5, 總和 90±15)", "高位震盪 (15±5, 總和 130±15)"))

st.sidebar.markdown("---")
st.sidebar.write("**🧬 科學過濾：**")
st.sidebar.success("✅ AC 值 >= 7 (排除規律號)")
st.sidebar.success("✅ 二次重組強勢號碼池")

uploaded_file = st.file_uploader("上傳歷史 Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for _, row in df.iterrows():
            clean_nums = [int(n) for n in re.findall(r'\d+', str(row.values)) if 1 <= int(n) <= 39]
            if len(clean_nums) >= 5: history.append(sorted(clean_nums[:5]))

        if history:
            latest_draw = history[0]
            # 避險：找出最近兩期都出的號碼
            danger_numbers = set(history[0]).intersection(set(history[1])) if len(history)>=2 else set()
            patterns = {"danger_numbers": danger_numbers, "latest": latest_draw}
            
            st.markdown(f"### 📅 最新一期紀錄：`{', '.join([f'{x:02d}' for x in latest_draw])}`")
            st.divider()
            
            if st.button("🚀 執行 V16.1 深度 AC 模擬"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # --- 第一階段：海選強勢號碼池 (57萬次) ---
                hot_pool = []
                for i in range(38):
                    status_text.text(f"第一階段：海選符合 AC >= 7 的強勢號碼... ({i+1}/38)")
                    raw = [random.sample(range(1, 40), 5) for _ in range(15000)]
                    metrics = []
                    for r in raw:
                        r.sort()
                        # 計算 AC 值
                        diffs = set(abs(a-b) for a,b in itertools.combinations(r, 2))
                        ac_val = len(diffs) - 4
                        metrics.append({"nums": r, "sum": sum(r), "ac": ac_val})
                    
                    scores = get_god_score_batch(metrics, patterns, trend_mode)
                    for m, s in zip(metrics, scores):
                        if s > 0: # 收集高分組合中的號碼
                            hot_pool.extend(m['nums'])
                    progress_bar.progress((i+1)/50)

                # --- 第二階段：強勢號碼精準組號 ---
                status_text.text("第二階段：正在從強勢號碼池進行二次配對...")
                if hot_pool:
                    # 抓取出現頻率最高的前 18 名號碼
                    top_n_nums = [n for n, c in Counter(hot_pool).most_common(18)]
                    
                    # 從這 18 顆號碼隨機生成 30,000 組進行精選
                    refined_raw = [random.sample(top_n_nums, 5) for _ in range(30000)]
                    refined_metrics = []
                    for r in refined_raw:
                        r.sort()
                        diffs = set(abs(a-b) for a,b in itertools.combinations(r, 2))
                        refined_metrics.append({"nums": r, "sum": sum(r), "ac": len(diffs) - 4})
                    
                    refined_scores = get_god_score_batch(refined_metrics, patterns, trend_mode)
                    
                    final_candidates = []
                    for m, s in zip(refined_metrics, refined_scores):
                        if s > 150:
                            final_candidates.append({"combo": m['nums'], "score": s, "sum": m['sum'], "ac": m['ac']})
                    
                    progress_bar.progress(1.0)
                    status_text.success("✅ 深度模擬完成！")
                    
                    if final_candidates:
                        random.shuffle(final_candidates)
                        final_top = sorted(final_candidates, key=lambda x: x['score'], reverse=True)[:5]
                        
                        res = []
                        for idx, item in enumerate(final_top):
                            res.append({
                                "排名": f"Top {idx+1}", 
                                "推薦組合": ", ".join([f"{x:02d}" for x in item['combo']]), 
                                "總和": item['sum'], 
                                "首碼": f"{item['combo'][0]:02d}",
                                "AC值": item['ac']
                            })
                        st.table(pd.DataFrame(res))
                        
                        st.markdown(f"📊 **本次強勢號碼池 (頻率最高 18 碼)**：\n`{', '.join([f'{x:02d}' for x in sorted(top_n_nums)])}`")
                        st.balloons()
                    else:
                        st.warning("⚠️ 符合 AC >= 7 的條件過於嚴苛，請嘗試再次點擊運行。")
                else:
                    st.error("海選階段未找到符合區間的號碼。")
                    
    except Exception as e:
        st.error(f"❌ 錯誤: {e}")
