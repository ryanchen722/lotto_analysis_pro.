import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter

# ==========================================
# 核心計算引擎 (V15.6 彈性區間版)
# ==========================================

def analyze_full_history(history):
    """
    分析數據庫：找出熱門號與長期遺漏號
    """
    all_draws = [num for sublist in history for num in sublist]
    counts = Counter(all_draws)
    
    # 遺漏號分析 (最近 15 期未出的冷門黑馬)
    recent_15_draws = [num for sublist in history[:15] for num in sublist]
    missing_numbers = [n for n in range(1, 40) if n not in recent_15_draws]
    
    # 避險：連開兩期攔截 (防止連三開)
    danger_numbers = set()
    if len(history) >= 2:
        danger_numbers = set(history[0]).intersection(set(history[1]))
    
    return {
        "missing": missing_numbers,
        "latest": history[0],
        "danger_numbers": danger_numbers
    }

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
        metrics_list.append({
            "ac": ac, "streak": max_streak, "sum": total_sum,
            "odd": odd, "even": 5-odd, "nums": nums
        })
    return metrics_list

def get_god_score_batch(metrics_list, patterns, trend_mode):
    scores = []
    for m in metrics_list:
        nums = m['nums']
        base = m['ac'] * 35 
        first_num = nums[0]
        s = m['sum']
        
        # --- 1. 戰略模式：首碼正負 5 區間化 ---
        if "強力回歸" in trend_mode:
            # 中心 06, 區間 01-11
            dist_center = abs(first_num - 6)
            if dist_center <= 5: 
                base += 110 - (dist_center * 5)
            else:
                base -= (dist_center - 5) * 35
            target_sum = 90
            
        else: # 高位震盪模式
            # 中心 15, 區間 10-20
            dist_center = abs(first_num - 15)
            if dist_center <= 5: 
                base += 125 - (dist_center * 5)
            else:
                base -= (dist_center - 5) * 40
            target_sum = 130

        # --- 2. 總和正負 15 彈性緩衝 ---
        sum_dist = abs(s - target_sum)
        if sum_dist <= 15:
            # 區間內給予穩定獎勵，扣分極輕
            base += 35 - (sum_dist * 1.5)
        else:
            # 超出區間才開始重罰
            base -= (sum_dist - 15) * 5.0
        
        # --- 3. 歷史補償與避險 ---
        missing_hits = len(set(nums).intersection(patterns['missing']))
        base += (missing_hits * 18)
        
        danger_hits = len(set(nums).intersection(patterns['danger_numbers']))
        base -= (danger_hits * 160)

        # --- 4. 科學過濾 ---
        if m['streak'] == 2: base += 45
        elif m['streak'] >= 3: base -= 150
        if m['odd'] in [2, 3]: base += 40
            
        entropy = random.uniform(0, 50) 
        scores.append(round(base + entropy, 2))
    return scores

# ==========================================
# UI 介面
# ==========================================

st.set_page_config(page_title="Gauss Master V15.6", page_icon="💎", layout="wide")
st.title("💎 Gauss Master Pro V15.6 彈性戰略版")

st.sidebar.header("🕹️ 指揮控制中心")
trend_mode = st.sidebar.radio(
    "預測下一期走勢：",
    ("強力回歸 (首碼 06±5, 總和 90±15)", "高位震盪 (首碼 15±5, 總和 130±15)")
)

st.sidebar.markdown("---")
st.sidebar.write("**戰略參數：**")
if "回歸" in trend_mode:
    st.sidebar.info("🎯 首碼範圍：01 - 11\n\n⚖️ 總和範圍：75 - 105")
else:
    st.sidebar.warning("🔥 首碼範圍：10 - 20\n\n⚖️ 總和範圍：115 - 145")

uploaded_file = st.file_uploader("上傳 539 歷史 Excel (第一列需為最新一期)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for _, row in df.iterrows():
            row_numbers = []
            for cell in row:
                nums_in_cell = re.findall(r'\d+', str(cell))
                for n in nums_in_cell: row_numbers.append(int(n))
            clean_nums = [n for n in row_numbers if 1 <= n <= 39]
            if len(clean_nums) >= 5: history.append(clean_nums[:5])

        if history:
            patterns = analyze_full_history(history)
            st.success(f"✅ 資料載入成功！最新期開出：{history[0]}")
            
            if st.button("啟動 57 萬次彈性模擬"):
                progress_bar = st.progress(0)
                all_candidates = []
                batch_size = 15000
                total_sims = 570000
                
                for i in range(0, total_sims, batch_size):
                    raw_combos = [random.sample(range(1, 40), 5) for _ in range(batch_size)]
                    metrics = get_metrics_batch(raw_combos)
                    scores = get_god_score_batch(metrics, patterns, trend_mode)
                    
                    for m, s in zip(metrics, scores):
                        if s > 220: # 提高優選門檻
                            all_candidates.append({
                                "combo": m['nums'], 
                                "score": s, 
                                "sum": m['sum'], 
                                "odd": m['odd'],
                                "streak": m['streak']
                            })
                    progress_bar.progress((i + batch_size) / total_sims)
                
                final_top = sorted(all_candidates, key=lambda x: x['score'], reverse=True)[:5]
                st.subheader(f"👑 {trend_mode} - 精選建議")
                
                res_df = []
                for idx, item in enumerate(final_top):
                    c = item['combo']
                    res_df.append({
                        "排名": f"Top {idx+1}",
                        "推薦組合": ", ".join([f"{x:02d}" for x in c]),
                        "總和": item['sum'],
                        "首碼": c[0],
                        "奇偶比": f"{item['odd']}:{5-item['odd']}",
                        "連號": "有" if item['streak'] == 2 else "無",
                        "評分": item['score']
                    })
                st.table(pd.DataFrame(res_df))
                st.balloons()
    except Exception as e:
        st.error(f"執行出錯: {e}")
else:
    st.info("👋 請上傳 Excel 檔案以開始模擬。")
