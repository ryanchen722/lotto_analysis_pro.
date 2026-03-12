import random
import pandas as pd
import streamlit as st
import numpy as np
import itertools
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
import plotly.graph_objects as go

# ==========================
# 1. 數據抓取
# ==========================
@st.cache_data(ttl=3600)
def fetch_539_history():
    headers = {"User-Agent": "Mozilla/5.0"}
    history = []
    for page in range(1, 100):
        url = f"https://www.pilio.idv.tw/lto539/drawlist/drawlist.asp?page={page}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = 'big5'
            soup = BeautifulSoup(r.text, "lxml")
            rows = soup.find_all("tr")
            for row in rows:
                nums = re.findall(r'\d{1,2}', row.text)
                if len(nums) >= 5:
                    draw = [int(n) for n in nums[-5:]]
                    if all(1 <= n <= 39 for n in draw):
                        history.append(sorted(draw))
        except:
            break
    return history[::-1] # 回傳由舊到新

# ==========================
# 2. HMM 核心邏輯
# ==========================
def hmm_prediction(history_data, num_to_return=15):
    all_nums = [n for draw in history_data for n in draw]
    global_heat = Counter(all_nums)
    avg_freq = len(all_nums) / 39
    
    def get_state(num):
        count = global_heat.get(num, 0)
        if count < avg_freq * 0.8: return 0  # 冷
        if count > avg_freq * 1.2: return 2  # 熱
        return 1 # 溫

    transitions = defaultdict(lambda: defaultdict(int))
    state_to_nums = defaultdict(list)
    
    last_states = None
    for draw in history_data:
        current_states = tuple(sorted([get_state(n) for n in draw]))
        for n in draw:
            state_to_nums[get_state(n)].append(n)
        if last_states:
            transitions[last_states][current_states] += 1
        last_states = current_states

    latest_state = tuple(sorted([get_state(n) for n in history_data[-1]]))
    candidates = transitions[latest_state]
    predicted_states = max(candidates, key=candidates.get) if candidates else (2, 2, 1, 1, 0)

    pool = []
    for s in predicted_states:
        pool_in_state = state_to_nums[s]
        if pool_in_state:
            # 取該狀態下最熱門的10個號碼隨機抽樣
            chosen = random.choice(Counter(pool_in_state).most_common(10))[0]
            pool.append(chosen)
    
    pool = list(set(pool))
    while len(pool) < num_to_return:
        extra = random.randint(1, 39)
        if extra not in pool: pool.append(extra)
            
    return sorted(pool[:num_to_return])

def calculate_ac(nums):
    return len(set(abs(a-b) for a, b in itertools.combinations(nums, 2))) - 4

# ==========================
# 3. 雷達圖工具
# ==========================
def draw_radar_chart(numbers):
    # 標準化各項指標 (0-1)
    # 大小比 (20以上為大)
    big_count = len([n for n in numbers if n >= 20]) / 5
    # 奇偶比
    odd_count = len([n for n in numbers if n % 2 != 0]) / 5
    # 和值 (正常範圍 60-140, 標準化)
    s_val = (sum(numbers) - 15) / (185 - 15)
    # 跨度 (正常範圍 20-32)
    span = (numbers[-1] - numbers[0]) / 38
    # AC值 (0-8)
    ac = calculate_ac(numbers) / 8

    categories = ['大小比', '奇偶比', '和值感', '跨度感', '複雜度(AC)']
    values = [big_count, odd_count, s_val, span, ac]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='號碼體質'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False, height=350, margin=dict(l=40, r=40, t=20, b=20))
    return fig

# ==========================
# 4. Streamlit UI
# ==========================
st.set_page_config(page_title="Gauss 539 V31 HMM Pro", layout="wide")
st.title("🧠 Gauss 539 V31 - HMM 驗證視覺化版")

history = fetch_539_history()

tab1, tab2 = st.tabs(["🎯 智慧預測", "🧪 模型驗證 (Backtest)"])

with tab1:
    if st.button("🚀 執行 HMM 深度預測"):
        hmm_pool = hmm_prediction(history)
        
        recs = []
        for _ in range(2000):
            sample = sorted(random.sample(hmm_pool, 5))
            if 4 <= calculate_ac(sample) <= 8:
                if 20 <= (sample[-1] - sample[0]) <= 32:
                    if sample not in recs: recs.append(sample)
            if len(recs) >= 3: break

        st.subheader(f"🔮 預測號碼池: {', '.join([f'{x:02d}' for x in hmm_pool])}")
        
        cols = st.columns(3)
        for i, rec in enumerate(recs):
            with cols[i]:
                st.markdown(f"### 推薦組合 {i+1}")
                st.code("  ".join([f"{x:02d}" for x in rec]), language="")
                st.plotly_chart(draw_radar_chart(rec), use_container_width=True)

with tab2:
    st.subheader("🧪 過去 10 期模擬回測")
    if st.button("開始回測"):
        results = []
        # 回測最近 10 期
        for i in range(10, 0, -1):
            target_idx = len(history) - i
            train_data = history[:target_idx]
            real_draw = set(history[target_idx])
            
            # 模擬預測
            test_pool = hmm_prediction(train_data, num_to_return=15)
            hits = real_draw.intersection(set(test_pool))
            
            results.append({
                "期數索引": f"倒數第 {i} 期",
                "實際開獎": ", ".join([f"{x:02d}" for x in sorted(list(real_draw))]),
                "預測池命中": len(hits),
                "命中號碼": ", ".join([f"{x:02d}" for x in sorted(list(hits))]) if hits else "無"
            })
        
        df_test = pd.DataFrame(results)
        st.table(df_test)
        avg_hit = df_test["預測池命中"].mean()
        st.metric("15碼預測池平均命中", f"{avg_hit:.1f} 碼")
        st.caption("註：此驗證僅針對 '15碼強勢池' 是否包含開獎號碼。")

st.markdown("---")
st.caption("本系統採用輕量化 HMM 遷移矩陣演算法。僅供數據分析參考，投注請理性。")
