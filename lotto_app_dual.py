import random
import pandas as pd
import streamlit as st
import numpy as np
import re
from collections import Counter
import itertools
import os

# ==========================================
# 核心函數
# ==========================================

def calculate_ac(nums):
    return len(set(abs(a-b) for a,b in itertools.combinations(nums,2))) - 4

def score_combo(nums, patterns, avg_first, tail_probs):
    first = nums[0]
    last = nums[-1]
    spread = last - first
    ac = calculate_ac(nums)
    
    base = 0
    base += ac * 35  # AC值
    base += 220 if 22 <= spread <= 32 else -abs(spread-27)*15
    base += 120 if last >= 30 else 0
    dist_first = abs(first-avg_first)
    base += 180-(dist_first*10) if dist_first<=6 else 0
    odd = sum(n%2 for n in nums)
    base += 140 if odd in [2,3] else -60
    s = sum(nums)
    base += 200 if 90<=s<=120 else -abs(s-105)*2
    tails = [n%10 for n in nums]
    base += 80 if len(set(tails))<=4 else 0
    missing_hits = len(set(nums).intersection(patterns['missing']))
    if 1<=missing_hits<=2: base += 120
    danger_hits = len(set(nums).intersection(patterns['danger']))
    base -= danger_hits*300
    for t in tails:
        base += tail_probs.get(t,0)*5
    entropy = random.uniform(0,15)
    return base + entropy

# ==========================================
# 馬可夫尾數矩陣
# ==========================================

def compute_tail_probs(history):
    tail_counts = [Counter() for _ in range(10)]
    for draw in history:
        tails = [n%10 for n in draw]
        for t in tails:
            tail_counts[t][t]+=1
    probs = {i:sum(tail_counts[i].values()) for i in range(10)}
    total = sum(probs.values())
    return {i:0 if total==0 else probs[i]/total for i in range(10)}

# ==========================================
# 分區抽樣 + 熱號強化
# ==========================================

def structured_random(hot_pool):
    nums = [
        random.choice(range(1,10)),
        random.choice(range(10,20)),
        random.choice(range(20,30)),
        random.choice(range(30,40)),
        random.choice(hot_pool) if hot_pool else random.randint(1,39)
    ]
    return sorted(list(set(nums))) if len(set(nums))==5 else structured_random(hot_pool)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Master V19+", page_icon="🚀", layout="wide")
st.title("🚀 Gauss Master V19+ 進階版")

uploaded_file = st.file_uploader("上傳539歷史Excel", type=["xlsx"])

TOP50_FILE = "v19_top50.csv"

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for _, row in df.iterrows():
            nums = [int(n) for n in re.findall(r'\d+', str(row.values)) if 1<=int(n)<=39]
            if len(nums)>=5:
                history.append(sorted(nums[:5]))
        
        if history:
            recent_context = history[:15]
            avg_first = np.mean([draw[0] for draw in recent_context])
            recent_all = [n for sub in history[:10] for n in sub]
            missing = [n for n in range(1,40) if n not in recent_all]
            danger = set(history[0]).intersection(set(history[1])) if len(history)>=2 else set()
            patterns = {"missing":missing, "danger":danger}
            tail_probs = compute_tail_probs(history)
            st.markdown(f"### 最新期：{', '.join([f'{x:02d}' for x in history[0]])}")
            
            if st.button("🚀 開始200k模擬"):
                progress = st.progress(0)
                candidates = []
                hot_pool = [n for n,_ in Counter(recent_all).most_common(20)]
                total = 200000
                for i in range(total):
                    nums = structured_random(hot_pool)
                    score = score_combo(nums, patterns, avg_first, tail_probs)
                    if score>500:
                        candidates.append((nums,score))
                    if i%5000==0:
                        progress.progress(i/total)
                progress.progress(1.0)
                
                if candidates:
                    candidates.sort(key=lambda x:x[1], reverse=True)
                    top10 = candidates[:10]
                    top5_next = top10[:5]  # 下一期建議
                    
                    # 顯示 Top10
                    res = []
                    for i,(c,s) in enumerate(top10):
                        res.append({
                            "排名":f"Top{i+1}",
                            "號碼":", ".join([f"{x:02d}" for x in c]),
                            "和值":sum(c),
                            "跨度":c[-1]-c[0],
                            "AC":calculate_ac(c),
                            "評分":round(s,2)
                        })
                    st.subheader("📊 模擬結果 Top 10")
                    st.table(pd.DataFrame(res))
                    
                    # 顯示下一期 Top5
                    st.subheader("👑 建議下一期 Top5 組合")
                    next5 = []
                    for i,(c,s) in enumerate(top5_next):
                        next5.append({"排名":f"Top{i+1}", "號碼":", ".join([f"{x:02d}" for x in c])})
                    st.table(pd.DataFrame(next5))
                    
                    # 熱號池
                    hot_nums = [n for combo,_ in candidates[:1000] for n in combo]
                    pool = [n for n,_ in Counter(hot_nums).most_common(20)]
                    st.markdown(f"🔥 強勢號碼池：{', '.join(map(str,pool))}")
                    st.balloons()
                    
                    # 儲存 Top50
                    top50 = candidates[:50]
                    top50_df = pd.DataFrame([{"號碼":", ".join([f"{x:02d}" for x in c]), "評分":s} for c,s in top50])
                    top50_df.to_csv(TOP50_FILE, index=False)
                    st.success(f"💾 已保存 Top50 組合到 {TOP50_FILE}")

            # 顯示上一次 Top50
            if os.path.exists(TOP50_FILE):
                st.subheader("📁 上一次 Top50 組合")
                last_top50 = pd.read_csv(TOP50_FILE)
                st.table(last_top50)
                
    except Exception as e:
        st.error(e)