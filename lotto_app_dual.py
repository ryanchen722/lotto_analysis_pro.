import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter

# ==========================================
# 核心計算引擎 (V15.9.1 旗艦動畫版)
# ==========================================

def analyze_full_history(history):
    recent_15_draws = [num for sublist in history[:15] for num in sublist]
    missing_numbers = [n for n in range(1, 40) if n not in recent_15_draws]
    danger_numbers = set()
    if len(history) >= 2:
        danger_numbers = set(history[0]).intersection(set(history[1]))
    return {"missing": missing_numbers, "danger_numbers": danger_numbers, "latest": history[0]}

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
        odd = sum(n % 2 for n in nums)
        metrics_list.append({"ac": ac, "streak": max_streak, "sum": total_sum, "odd": odd, "nums": nums})
    return metrics_list

def get_god_score_batch(metrics_list, patterns, trend_mode):
    scores = []
    for m in metrics_list:
        nums = m['nums']
        first_num = nums[0]
        s = m['sum']
        base = m['ac'] * 20 
        
        # --- 戰略約束 (區間內一律加分，區間外制裁) ---
        if "強力回歸" in trend_mode:
            if 1 <= first_num <= 11: base += 200 
            else: base -= 5000 
            target_sum, sum_margin = 90, 15
        else:
            if 10 <= first_num <= 20: base += 200 
            else: base -= 5000
            target_sum, sum_margin = 130, 15

        # --- 總和約束 ---
        if abs(s - target_sum) <= sum_margin: base += 120
        else: base -= 5000

        # --- 基礎過濾與避險 ---
        if m['streak'] == 2: base += 35
        if m['odd'] in [2, 3]: base += 35
        danger_hits = len(set(nums).intersection(patterns['danger_numbers']))
        base -= (danger_hits * 350)

        # 高熵值隨機性 (0-100)，解決結果重複的問題
        entropy = random.uniform(0, 100) 
        scores.append(round(base + entropy, 2))
    return scores

# ==========================================
# UI 介面
# ==========================================

st.set_page_config(page_title="Gauss Master V15.9.1", page_icon="🎯", layout="wide")
st.title("🎯 Gauss Master Pro V15.9.1 旗艦戰略版")

# 側邊欄控制
st.sidebar.header("🕹️ 指揮指揮中心")
trend_mode = st.sidebar.radio("走勢預測：", ("強力回歸 (06±5, 總和 90±15)", "高位震盪 (15±5, 總和 130±15)"))

st.sidebar.markdown("---")
if "回歸" in trend_mode:
    st.sidebar.info("🎯 **戰略鎖定**：小號反彈\n\n⚖️ **目標**：首碼 01-11 / 總和 75-105")
else:
    st.sidebar.warning("🔥 **戰略鎖定**：高位震盪\n\n⚖️ **目標**：首碼 10-20 / 總和 115-145")

uploaded_file = st.file_uploader("請上傳歷史 Excel 檔案 (xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for _, row in df.iterrows():
            clean_nums = [int(n) for n in re.findall(r'\d+', str(row.values)) if 1 <= int(n) <= 39]
            if len(clean_nums) >= 5: history.append(clean_nums[:5])

        if history:
            patterns = analyze_full_history(history)
            
            # --- 顯示最新一期資訊 ---
            st.markdown(f"### 📅 最新一期開獎紀錄：`{', '.join([f'{x:02d}' for x in patterns['latest']])}`")
            st.divider()
            
            if st.button("🚀 啟動 57 萬次多樣化戰略模擬"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                all_candidates = []
                
                for i in range(38):
                    status_text.text(f"正在進行第 {i+1}/38 批次深度計算...")
                    raw = [random.sample(range(1, 40), 5) for _ in range(15000)]
                    metrics = get_metrics_batch(raw)
                    scores = get_god_score_batch(metrics, patterns, trend_mode)
                    for m, s in zip(metrics, scores):
                        if s > 0: # 正分代表完全符合你的戰略要求
                            all_candidates.append({"combo": m['nums'], "score": s, "sum": m['sum']})
                    progress_bar.progress((i+1)/38)
                
                status_text.success("✅ 570,000 次模擬計算完成！")
                
                if all_candidates:
                    # 隨機打亂後排序，確保每次結果都不同
                    random.shuffle(all_candidates) 
                    final_top = sorted(all_candidates, key=lambda x: x['score'], reverse=True)[:5]
                    
                    st.subheader(f"👑 {trend_mode} - 推薦天選組合")
                    
                    res_display = []
                    for idx, item in enumerate(final_top):
                        res_display.append({
                            "排名": f"Top {idx+1}",
                            "推薦組合": ", ".join([f"{x:02d}" for x in item['combo']]),
                            "總和": item['sum'],
                            "首碼": f"{item['combo'][0]:02d}",
                            "綜合評分": item['score']
                        })
                    
                    st.table(pd.DataFrame(res_display))
                    st.balloons() # 勝利動畫
                else:
                    st.warning("⚠️ 在目前的嚴格約束下找不到符合條件的組合，請嘗試重新模擬。")
                    
    except Exception as e:
        st.error(f"❌ 程式執行出錯: {e}")
else:
    st.info("👋 歡迎指揮官！請先上傳 Excel 檔案以開啟分析。")
