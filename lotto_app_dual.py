import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter
import itertools

# ==========================================
# 核心引擎：V16.2 階梯式彈性評分邏輯
# ==========================================

def get_god_score_batch(metrics_list, patterns, trend_mode):
    scores = []
    for m in metrics_list:
        nums = m['nums']
        first_num = nums[0]
        s = m['sum']
        ac_val = m['ac']
        
        # --- 1. AC 值：階梯式加分 (優選 7 以上，但 5, 6 亦可接受) ---
        if ac_val >= 7:
            base = 250 + (ac_val * 15)
        elif ac_val >= 5:
            base = 100 + (ac_val * 10)
        else:
            base = ac_val * 5  # 規律號碼給予極低分

        # --- 2. 戰略約束：首碼區間 (06±5 或 15±5) ---
        if "強力回歸" in trend_mode:
            dist = abs(first_num - 6)
            if dist <= 5: # 01-11 號
                base += 350 - (dist * 15)
            else:
                base -= (dist - 5) * 60 # 區間外線性扣分
            target_sum = 90
        else:
            dist = abs(first_num - 15)
            if dist <= 5: # 10-20 號
                base += 350 - (dist * 15)
            else:
                base -= (dist - 5) * 60
            target_sum = 130

        # --- 3. 總和區間：目標 ± 15 ---
        sum_err = abs(s - target_sum)
        if sum_err <= 15:
            base += 250 - (sum_err * 8)
        else:
            base -= (sum_err - 15) * 20 # 超出範圍重罰

        # --- 4. 歷史避險 ---
        danger_hits = len(set(nums).intersection(patterns['danger_numbers']))
        base -= (danger_hits * 400)
        
        # 較高熵值：確保每次結果具備多樣性
        entropy = random.uniform(0, 80) 
        scores.append(round(base + entropy, 2))
    return scores

# ==========================================
# UI 介面與系統整合
# ==========================================

st.set_page_config(page_title="Gauss Master V16.2", page_icon="🧬", layout="wide")
st.title("🧬 Gauss Master Pro V16.2 彈性優化版")

st.sidebar.header("🕹️ 指揮中心")
trend_mode = st.sidebar.radio("走勢預測：", ("強力回歸 (06±5, 總和 90±15)", "高位震盪 (15±5, 總和 130±15)"))

st.sidebar.markdown("---")
st.sidebar.write("**🛡️ 系統狀態：**")
st.sidebar.success("✅ AC 值：優先鎖定 7-10")
st.sidebar.success("✅ 邏輯：二次精準重組")
st.sidebar.info("💡 若條件太嚴苛，系統將自動匹配次優組合")

uploaded_file = st.file_uploader("上傳 539 歷史 Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for _, row in df.iterrows():
            clean_nums = [int(n) for n in re.findall(r'\d+', str(row.values)) if 1 <= int(n) <= 39]
            if len(clean_nums) >= 5: history.append(sorted(clean_nums[:5]))

        if history:
            latest_draw = history[0]
            danger_numbers = set(history[0]).intersection(set(history[1])) if len(history)>=2 else set()
            patterns = {"danger_numbers": danger_numbers, "latest": latest_draw}
            
            st.markdown(f"### 📅 最新一期紀錄：`{', '.join([f'{x:02d}' for x in latest_draw])}`")
            st.divider()
            
            if st.button("🚀 執行 V16.2 彈性強化模擬"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # --- 第一階段：海選號碼池 ---
                hot_pool = []
                for i in range(38):
                    status_text.text(f"第一階段：海選強勢號碼... ({i+1}/38)")
                    raw = [random.sample(range(1, 40), 5) for _ in range(15000)]
                    metrics = []
                    for r in raw:
                        r.sort()
                        diffs = set(abs(a-b) for a,b in itertools.combinations(r, 2))
                        metrics.append({"nums": r, "sum": sum(r), "ac": len(diffs) - 4})
                    
                    scores = get_god_score_batch(metrics, patterns, trend_mode)
                    for m, s in zip(metrics, scores):
                        if s > 150: # 門檻設定在相對高分
                            hot_pool.extend(m['nums'])
                    progress_bar.progress((i+1)/50)

                # --- 第二階段：精準重組 ---
                status_text.text("第二階段：正在從強勢池進行二次配對...")
                if hot_pool:
                    # 統計頻率最高的前 18 個號碼
                    top_n_nums = [n for n, c in Counter(hot_pool).most_common(18)]
                    
                    # 使用這 18 顆號碼隨機生成 30,000 組
                    refined_raw = [random.sample(top_n_nums, 5) for _ in range(30000)]
                    refined_metrics = []
                    for r in refined_raw:
                        r.sort()
                        diffs = set(abs(a-b) for a,b in itertools.combinations(r, 2))
                        refined_metrics.append({"nums": r, "sum": sum(r), "ac": len(diffs) - 4})
                    
                    refined_scores = get_god_score_batch(refined_metrics, patterns, trend_mode)
                    
                    final_candidates = []
                    for m, s in zip(refined_metrics, refined_scores):
                        if s > 300: # 二次重組的組合分數會更高
                            final_candidates.append({"combo": m['nums'], "score": s, "sum": m['sum'], "ac": m['ac']})
                    
                    progress_bar.progress(1.0)
                    
                    if final_candidates:
                        status_text.success("✅ 模擬成功！已尋獲最優配置。")
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
                        st.warning("⚠️ 符合條件的組合較少，請再次點擊按鈕重試。")
                else:
                    st.error("海選階段失敗，請確認 Excel 格式或放寬戰略設定。")
                    
    except Exception as e:
        st.error(f"❌ 發生錯誤: {e}")
