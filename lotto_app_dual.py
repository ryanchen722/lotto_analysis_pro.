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
# 1. 數據抓取 (還原 V28 邏輯並優化)
# ==========================
@st.cache_data(ttl=3600)
def fetch_539_history():
    headers = {"User-Agent": "Mozilla/5.0"}
    history = []
    
    # 執行 V28 的 150 頁抓取邏輯
    for page in range(1, 150):
        url = f"https://www.pilio.idv.tw/lto539/drawlist/drawlist.asp?page={page}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            # 修正編碼問題
            r.encoding = 'big5' 
            soup = BeautifulSoup(r.text, "lxml")
            rows = soup.find_all("tr")

            for row in rows:
                # --- 這是你 V28 的核心抓取代碼 ---
                nums = re.findall(r'\d{1,2}', row.text)
                if len(nums) >= 5:
                    # 取最後 5 個數字
                    numbers = list(map(int, nums[-5:]))
                    # 嚴格過濾確保是 539 號碼範圍
                    if all(1 <= n <= 39 for n in numbers):
                        sorted_draw = sorted(numbers)
                        # 避免重複加入
                        if sorted_draw not in history:
                            history.append(sorted_draw)
        except:
            break
            
    # 返回由舊到新的順序 (V28 抓到的是由新到舊)
    return history[::-1]

# ==========================
# 2. HMM 隱藏狀態預測
# ==========================
def hmm_analysis(history_data):
    if len(history_data) < 10: return sorted(random.sample(range(1, 40), 15))
    
    all_nums = [n for d in history_data for n in d]
    heat = Counter(all_nums)
    avg = len(all_nums) / 39
    
    def get_s(n):
        return 0 if heat[n] < avg*0.8 else (2 if heat[n] > avg*1.2 else 1)

    states = [tuple(sorted([get_s(n) for n in d])) for d in history_data]
    trans = defaultdict(lambda: defaultdict(int))
    for i in range(len(states)-1):
        trans[states[i]][states[i+1]] += 1

    curr_s = states[-1]
    next_s = max(trans[curr_s], key=trans[curr_s].get) if trans[curr_s] else (2, 2, 1, 1, 0)

    s_map = defaultdict(list)
    for n in range(1, 40): s_map[get_s(n)].append(n)
    
    pool = []
    for s in next_s:
        if s_map[s]: pool.append(random.choice(s_map[s]))
    while len(set(pool)) < 15:
        n = random.randint(1, 39)
        if n not in pool: pool.append(n)
    return sorted(list(set(pool))[:15])

# ==========================
# 3. 雷達圖分析
# ==========================
def draw_radar(nums):
    # AC 值計算
    ac_val = len(set(abs(a-b) for a,b in itertools.combinations(nums,2)))-4
    metrics = [
        len([n for n in nums if n >= 20])/5, # 大小
        len([n for n in nums if n % 2 != 0])/5, # 奇偶
        (sum(nums)-15)/170, # 和值
        (nums[-1]-nums[0])/38, # 跨度
        ac_val / 8 # 複雜度
    ]
    fig = go.Figure(data=go.Scatterpolar(r=metrics, theta=['大','奇','和','跨','AC'], fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 1])), showlegend=False, height=220, margin=dict(l=30,r=30,t=20,b=20))
    return fig

# ==========================
# 4. Streamlit UI
# ==========================
st.set_page_config(page_title="Gauss 539 V33.6", layout="wide")

if 'history' not in st.session_state:
    with st.spinner("正在以 V28 模式加載歷史數據..."):
        st.session_state.history = fetch_539_history()

history = st.session_state.history

if not history:
    st.error("🚨 無法取得數據，請檢查連線。")
    st.stop()

# --- 顯示最新五期 ---
st.title("🎯 Gauss 539 V33.6 - HMM 旗艦版")
st.subheader("📅 最新五期開獎 (V28 抓取引擎)")
cols_top = st.columns(5)
last_5 = history[-5:][::-1]
for i, d in enumerate(last_5):
    with cols_top[i]:
        st.metric(label="最新期" if i==0 else f"前 {i} 期", value="-".join([f"{x:02d}" for x in d]))
        st.caption(f"和值: {sum(d)} | AC: {len(set(abs(a-b) for a,b in itertools.combinations(d,2)))-4}")

st.markdown("---")

tab1, tab2 = st.tabs(["🚀 HMM 智慧預測", "📊 歷史數據總庫"])

with tab1:
    if st.button("✨ 執行 HMM 狀態預測"):
        pool = hmm_analysis(history)
        history_sets = [set(h) for h in history]
        
        recs = []
        for _ in range(10000):
            sample = sorted(random.sample(pool, 5))
            ac = len(set(abs(a-b) for a,b in itertools.combinations(sample,2)))-4
            span = sample[-1] - sample[0]
            if 4 <= ac <= 8 and 20 <= span <= 32:
                if set(sample) not in history_sets:
                    if sample not in recs: recs.append(sample)
            if len(recs) >= 3: break

        st.info(f"💡 HMM 強勢號碼池： {', '.join([f'{x:02d}' for x in pool])}")
        
        cols_rec = st.columns(3)
        for i, r in enumerate(recs):
            with cols_rec[i]:
                st.success(f"推薦組合 {i+1}")
                st.markdown(f"### `{'  '.join([f'{x:02d}' for x in r])}`")
                st.plotly_chart(draw_radar(r), use_container_width=True)
                st.caption("✅ 已過濾 AC 值與歷史重複組合")

with tab2:
    st.subheader(f"📊 歷史數據庫 (已載入 {len(history)} 期)")
    df_history = pd.DataFrame(history[::-1], columns=['號1','號2','號3','號4','號5'])
    st.dataframe(df_history, height=450, use_container_width=True)

st.markdown("---")
st.caption("V33.6 版：採用 V28 正則表達式抓取引擎，結合 HMM 隱藏狀態預測模型。")
