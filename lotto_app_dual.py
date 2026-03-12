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
# 1. 數據抓取 (加強防護與保底)
# ==========================
@st.cache_data(ttl=3600)
def fetch_539_history(max_pages=50):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    history = []
    session = requests.Session()
    
    status_placeholder = st.empty()
    
    for page in range(1, max_pages + 1):
        url = f"https://www.pilio.idv.tw/lto539/drawlist/drawlist.asp?page={page}"
        try:
            r = session.get(url, headers=headers, timeout=10)
            if r.status_code != 200:
                st.warning(f"第 {page} 頁連線失敗，錯誤碼：{r.status_code}")
                break
            
            r.encoding = 'big5'
            soup = BeautifulSoup(r.text, "lxml")
            rows = soup.find_all("tr")
            
            page_data_count = 0
            for row in rows:
                cells = row.find_all("td")
                row_nums = [int(val) for val in [c.get_text(strip=True) for c in cells] if val.isdigit() and 1 <= int(val) <= 39]
                
                if len(row_nums) == 5:
                    sorted_draw = sorted(row_nums)
                    if sorted_draw not in history:
                        history.append(sorted_draw)
                        page_data_count += 1
            
            if page % 10 == 0:
                status_placeholder.text(f"📊 數據加載中... 已取得 {len(history)} 期")
                
            if page_data_count == 0 and page > 1: # 沒抓到資料就停
                break
        except Exception as e:
            st.error(f"抓取發生異常: {e}")
            break
            
    status_placeholder.empty()
    # 歷史由新到舊排
    return history[::-1]

# ==========================
# 2. HMM 預測邏輯 (加入保底號碼)
# ==========================
def hmm_prediction(history_data):
    if len(history_data) < 5:
        return sorted(random.sample(range(1, 40), 15)) # 資料不夠時回傳隨機
    
    all_nums = [n for draw in history_data for n in draw]
    global_heat = Counter(all_nums)
    avg_f = len(all_nums) / 39
    
    def get_state(n):
        c = global_heat.get(n, 0)
        return 0 if c < avg_f * 0.8 else (2 if c > avg_f * 1.2 else 1)

    state_seq = [tuple(sorted([get_state(n) for n in d])) for d in history_data]
    transitions = defaultdict(lambda: defaultdict(int))
    for i in range(len(state_seq)-1):
        transitions[state_seq[i]][state_seq[i+1]] += 1

    latest_s = state_seq[-1]
    predicted_s = max(transitions[latest_s], key=transitions[latest_s].get) if transitions.get(latest_s) else (2, 2, 1, 1, 0)

    state_map = defaultdict(list)
    for n in range(1, 40): state_map[get_state(n)].append(n)

    pool = []
    for s in predicted_s:
        if state_map[s]: pool.append(random.choice(state_map[s]))
    
    while len(set(pool)) < 15:
        extra = random.randint(1, 39)
        if extra not in pool: pool.append(extra)
    return sorted(list(set(pool))[:15])

# ==========================
# 3. UI 顯示邏輯
# ==========================
st.set_page_config(page_title="Gauss 539 AI Pro", layout="wide")

if 'history' not in st.session_state:
    with st.spinner("🚀 正在啟動 AI 引擎並抓取千期大數據..."):
        st.session_state.history = fetch_539_history(50)

# --- 重要：保底機制，如果真的抓不到資料，放一組虛擬數據避免崩潰 ---
if not st.session_state.history:
    st.error("⚠️ 數據源暫時無法連線，請稍後再試。目前顯示範例數據。")
    history = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15], [16, 17, 18, 19, 20], [21, 22, 23, 24, 25]]
else:
    history = st.session_state.history

# 顯示標題
st.title("🎯 Gauss 539 V33.4 - HMM 終極穩定版")

# 顯示最新五期
st.subheader("📅 最新五期開獎紀錄")
last_5 = history[-5:][::-1]
cols = st.columns(len(last_5))
for i, draw in enumerate(last_5):
    with cols[i]:
        st.info(f"最新第 {i+1} 期" if i==0 else f"前 {i} 期")
        st.markdown(f"### `{' '.join([f'{x:02d}' for x in draw])}`")

st.markdown("---")

tab1, tab2 = st.tabs(["🚀 智慧預測分析", "📊 千期大數據庫"])

with tab1:
    if st.button("✨ 執行 HMM 狀態轉移預測"):
        pool = hmm_prediction(history)
        history_sets = [set(h) for h in history]
        
        recs = []
        for _ in range(5000):
            sample = sorted(random.sample(pool, 5))
            ac = len(set(abs(a-b) for a, b in itertools.combinations(sample, 2))) - 4
            if 4 <= ac <= 8 and 20 <= (sample[-1]-sample[0]) <= 32:
                if set(sample) not in history_sets:
                    recs.append(sample)
            if len(recs) >= 3: break
        
        if not recs: # 如果模擬不出組合，給保底推薦
            recs = [sorted(random.sample(pool, 5)) for _ in range(3)]

        st.info(f"💡 強勢號碼池： {', '.join([f'{x:02d}' for x in pool])}")
        
        rec_cols = st.columns(3)
        for i, r in enumerate(recs):
            with rec_cols[i]:
                st.success(f"推薦組合 {i+1}")
                st.markdown(f"## {' - '.join([f'{x:02d}' for x in r])}")
                # 簡單雷達圖輔助
                metrics = [len([n for n in r if n>=20])/5, len([n for n in r if n%2!=0])/5, (sum(r)-15)/170, (r[-1]-r[0])/38, 0.7]
                fig = go.Figure(data=go.Scatterpolar(r=metrics, theta=['大','奇','和','跨','AC'], fill='toself'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 1])), showlegend=False, height=200, margin=dict(l=20,r=20,t=20,b=20))
                st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader(f"📊 數據庫概覽 (載入期數: {len(history)})")
    st.dataframe(pd.DataFrame(history[::-1], columns=['號1','號2','號3','號4','號5']), height=400, use_container_width=True)

st.markdown("---")
st.caption("穩定版：內建自動恢復機制與防當機邏輯。")
