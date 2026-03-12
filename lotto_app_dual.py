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
# 1. 數據抓取 (擴大至 3000 期)
# ==========================
@st.cache_data(ttl=3600)
def fetch_539_history():
    headers = {"User-Agent": "Mozilla/5.0"}
    history = []
    session = requests.Session() # 使用 Session 加速抓取
    
    # 抓取 150 頁，約可獲得 3000 期資料
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for page in range(1, 151):
        if page % 10 == 0:
            progress_bar.progress(page / 150)
            status_text.text(f"正在抓取第 {page}/150 頁資料...")
            
        url = f"https://www.pilio.idv.tw/lto539/drawlist/drawlist.asp?page={page}"
        try:
            r = session.get(url, headers=headers, timeout=10)
            r.encoding = 'big5'
            soup = BeautifulSoup(r.text, "lxml")
            rows = soup.find_all("tr")
            for row in rows:
                nums = re.findall(r'\d{1,2}', row.text)
                if len(nums) >= 5:
                    draw = [int(n) for n in nums[-5:]]
                    if all(1 <= n <= 39 for n in draw):
                        sorted_draw = sorted(draw)
                        if sorted_draw not in history:
                            history.append(sorted_draw)
        except:
            break
            
    progress_bar.empty()
    status_text.empty()
    return history[::-1] # 由舊到新

# ==========================
# 2. HMM 核心與雷達圖 (維持 V31 穩定版)
# ==========================
def calculate_ac(nums):
    return len(set(abs(a-b) for a, b in itertools.combinations(nums, 2))) - 4

def hmm_prediction(history_data, num_to_return=15):
    all_nums = [n for draw in history_data for n in draw]
    global_heat = Counter(all_nums)
    avg_freq = len(all_nums) / 39
    
    def get_state(num):
        count = global_heat.get(num, 0)
        if count < avg_freq * 0.8: return 0
        if count > avg_freq * 1.2: return 2
        return 1

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
            chosen = random.choice(Counter(pool_in_state).most_common(10))[0]
            pool.append(chosen)
    
    pool = list(set(pool))
    while len(pool) < num_to_return:
        extra = random.randint(1, 39)
        if extra not in pool: pool.append(extra)
    return sorted(pool[:num_to_return])

def draw_radar_chart(numbers):
    big_count = len([n for n in numbers if n >= 20]) / 5
    odd_count = len([n for n in numbers if n % 2 != 0]) / 5
    s_val = (sum(numbers) - 15) / (185 - 15)
    span = (numbers[-1] - numbers[0]) / 38
    ac = calculate_ac(numbers) / 8
    categories = ['大小比', '奇偶比', '和值感', '跨度感', '複雜度(AC)']
    values = [big_count, odd_count, s_val, span, ac]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='號碼體質'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False, height=300, margin=dict(l=30, r=30, t=20, b=20))
    return fig

# ==========================
# 3. Streamlit UI
# ==========================
st.set_page_config(page_title="Gauss 539 V32 BigData", layout="wide")
st.title("🎯 Gauss 539 V32 - 3000期大數據 + HMM")

if 'history_data' not in st.session_state:
    with st.spinner("正在加載 3000 期歷史數據..."):
        st.session_state.history_data = fetch_539_history()

history = st.session_state.history_data
st.success(f"目前資料庫共有 {len(history)} 期歷史開獎紀錄")

tab1, tab2 = st.tabs(["🔮 HMM 預測與雷達分析", "🕵️ 歷史重複性驗證"])

with tab1:
    if st.button("🚀 執行三千期大數據預測"):
        hmm_pool = hmm_prediction(history)
        
        # 轉換為集合以便檢查重複
        history_sets = [set(h) for h in history]
        
        recs = []
        for _ in range(5000):
            sample = sorted(random.sample(hmm_pool, 5))
            if 4 <= calculate_ac(sample) <= 8:
                if 20 <= (sample[-1] - sample[0]) <= 32:
                    # 關鍵功能：排除與歷史完全一樣的組合
                    if set(sample) not in history_sets:
                        if sample not in recs: recs.append(sample)
            if len(recs) >= 3: break

        st.subheader(f"💡 強勢號碼池: {', '.join([f'{x:02d}' for x in hmm_pool])}")
        
        cols = st.columns(3)
        for i, rec in enumerate(recs):
            with cols[i]:
                st.markdown(f"### 推薦組合 {i+1}")
                st.code("  ".join([f"{x:02d}" for x in rec]), language="")
                st.plotly_chart(draw_radar_chart(rec), use_container_width=True)
                st.success("✅ 通過歷史重複性校驗")

with tab2:
    st.subheader("🕵️ 推薦組合 vs 3000期歷史")
    st.write("此功能會驗證目前的預測是否曾出現在三千期歷史中。")
    st.info("根據統計，539 號碼組合重複出現的機率極低，排除重複號碼可提高科學性。")
    
    # 顯示最近五期數據作為參考
    st.markdown("#### 最新 5 期歷史紀錄")
    recent_df = pd.DataFrame(history[-5:][::-1], columns=['號1', '號2', '號3', '號4', '號5'])
    st.table(recent_df)

st.markdown("---")
st.caption("V32 版：已優化三千期抓取效能，並加入歷史重複性自動過濾機制。")
