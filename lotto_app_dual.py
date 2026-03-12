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
# 1. 精準數據抓取 (鎖定 1000 期)
# ==========================
@st.cache_data(ttl=3600)
def fetch_539_history(max_pages=50):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"}
    history = []
    session = requests.Session()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for page in range(1, max_pages + 1):
        url = f"https://www.pilio.idv.tw/lto539/drawlist/drawlist.asp?page={page}"
        try:
            r = session.get(url, headers=headers, timeout=10)
            r.encoding = 'big5'
            soup = BeautifulSoup(r.text, "lxml")
            rows = soup.find_all("tr")
            
            for row in rows:
                cells = row.find_all("td")
                # 精準抓取：只拿 td 內 1-39 的純數字
                row_nums = [int(val) for val in [c.get_text(strip=True) for c in cells] if val.isdigit() and 1 <= int(val) <= 39]
                
                # 539 標準規格：每行必須剛好 5 碼
                if len(row_nums) == 5:
                    sorted_draw = sorted(row_nums)
                    if sorted_draw not in history:
                        history.append(sorted_draw)
            
            if page % 5 == 0:
                progress_bar.progress(page / max_pages)
                status_text.text(f"已同步數據：{len(history)} 期...")
        except:
            break
            
    progress_bar.empty()
    status_text.empty()
    return history[::-1] # 由舊到新

# ==========================
# 2. HMM 隱藏狀態預測邏輯
# ==========================
def hmm_analysis(history_data):
    if not history_data: return sorted(random.sample(range(1, 40), 15))
    
    all_nums = [n for d in history_data for n in d]
    heat = Counter(all_nums)
    avg = len(all_nums) / 39
    
    # 定義狀態：0-冷, 1-溫, 2-熱
    def get_s(n):
        return 0 if heat[n] < avg*0.8 else (2 if heat[n] > avg*1.2 else 1)

    # 建立狀態序列與遷移矩陣
    states = [tuple(sorted([get_s(n) for n in d])) for d in history_data]
    trans = defaultdict(lambda: defaultdict(int))
    for i in range(len(states)-1):
        trans[states[i]][states[i+1]] += 1

    # 預測下一期可能狀態
    curr_s = states[-1]
    next_s = max(trans[curr_s], key=trans[curr_s].get) if trans[curr_s] else (2, 2, 1, 1, 0)

    # 根據預測狀態池抽樣
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
    # 計算體質指標
    ac = (len(set(abs(a-b) for a,b in itertools.combinations(nums,2)))-4)/8
    metrics = [
        len([n for n in nums if n >= 20])/5, # 大小
        len([n for n in nums if n % 2 != 0])/5, # 奇偶
        (sum(nums)-15)/170, # 和值
        (nums[-1]-nums[0])/38, # 跨度
        ac # 複雜度
    ]
    fig = go.Figure(data=go.Scatterpolar(r=metrics, theta=['大','奇','和','跨','AC'], fill='toself', line_color='#FF4B4B'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 1])), showlegend=False, height=220, margin=dict(l=30,r=30,t=20,b=20))
    return fig

# ==========================
# 4. Streamlit UI 主程式
# ==========================
st.set_page_config(page_title="Gauss 539 HMM Pro", layout="wide")

if 'history' not in st.session_state:
    st.session_state.history = fetch_539_history(50) # 預設抓 1000 期

history = st.session_state.history

if not history:
    st.error("🚨 無法取得歷史數據，請確認網路連線。")
    st.stop()

# --- 頂部：最新五期連顯 ---
st.title("🎯 Gauss 539 AI V33.5 - HMM 旗艦版")
st.subheader("📅 近五期開獎數據")
cols_top = st.columns(5)
last_5 = history[-5:][::-1]
for i, d in enumerate(last_5):
    with cols_top[i]:
        st.metric(label="最新期" if i==0 else f"前 {i} 期", value="-".join([f"{x:02d}" for x in d]))
        st.caption(f"和值: {sum(d)} | 跨度: {d[-1]-d[0]}")

st.markdown("---")

tab1, tab2 = st.tabs(["🚀 HMM 智慧分析", "📊 千期數據回測"])

with tab1:
    if st.button("✨ 啟動 HMM 狀態轉移預測"):
        strong_pool = hmm_analysis(history)
        history_sets = [set(h) for h in history]
        
        recs = []
        # 進行一萬次模擬，確保 AC 合格且史上未出現過
        for _ in range(10000):
            sample = sorted(random.sample(strong_pool, 5))
            ac = len(set(abs(a-b) for a,b in itertools.combinations(sample,2)))-4
            if 4 <= ac <= 8 and 20 <= (sample[-1]-sample[0]) <= 32:
                if set(sample) not in history_sets:
                    if sample not in recs: recs.append(sample)
            if len(recs) >= 3: break

        st.info(f"💡 HMM 強勢號碼池 (下一期預計狀態)： {', '.join([f'{x:02d}' for x in strong_pool])}")
        
        cols_rec = st.columns(3)
        for i, r in enumerate(recs):
            with cols_rec[i]:
                st.success(f"推薦組合 {i+1}")
                st.markdown(f"## `{'  '.join([f'{x:02d}' for x in r])}`")
                st.plotly_chart(draw_radar(r), use_container_width=True)
                st.caption("✅ 已排除千期內所有重複號碼")

with tab2:
    st.subheader(f"📊 1000 期歷史總庫 (已載入 {len(history)} 期)")
    df_history = pd.DataFrame(history[::-1], columns=['號1','號2','號3','號4','號5'])
    st.dataframe(df_history, height=450, use_container_width=True)

st.markdown("---")
st.caption("本系統基於 HMM 隱藏狀態遷移演算法，所有推薦組合皆通過歷史重複性檢查。")
