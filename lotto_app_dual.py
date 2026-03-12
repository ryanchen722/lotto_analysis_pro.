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
# 1. 數據抓取 (設定 1000 期)
# ==========================
@st.cache_data(ttl=3600)
def fetch_539_history(max_pages=50): # 50 頁約等於 1000 期
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    history = []
    session = requests.Session()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for page in range(1, max_pages + 1):
        url = f"https://www.pilio.idv.tw/lto539/drawlist/drawlist.asp?page={page}"
        try:
            # 增加 timeout 防止卡死
            r = session.get(url, headers=headers, timeout=10)
            r.encoding = 'big5'
            soup = BeautifulSoup(r.text, "lxml")
            rows = soup.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                row_nums = []
                for cell in cells:
                    val = cell.get_text(strip=True)
                    if val.isdigit():
                        num = int(val)
                        if 1 <= num <= 39:
                            row_nums.append(num)
                # 嚴格篩選開獎欄位 (539 固定 5 碼)
                if len(row_nums) == 5:
                    sorted_draw = sorted(row_nums)
                    if sorted_draw not in history:
                        history.append(sorted_draw)
            
            if page % 5 == 0:
                progress_bar.progress(page / max_pages)
                status_text.text(f"已同步數據：{page}/{max_pages} 頁...")
        except:
            break
            
    progress_bar.empty()
    status_text.empty()
    # 網頁資料是由新到舊，回傳時轉為由舊到新方便分析
    return history[::-1]

# ==========================
# 2. HMM 預測邏輯
# ==========================
def hmm_prediction(history_data, num_to_return=15):
    if len(history_data) < 10: return list(range(1, 16))
    
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
    predicted_s = max(transitions[latest_s], key=transitions[latest_s].get) if transitions[latest_s] else (2, 2, 1, 1, 0)

    state_map = defaultdict(list)
    for n in range(1, 40): state_map[get_state(n)].append(n)

    pool = []
    for s in predicted_s:
        if state_map[s]: pool.append(random.choice(state_map[s]))
    while len(set(pool)) < num_to_return:
        extra = random.randint(1, 39)
        if extra not in pool: pool.append(extra)
    return sorted(list(set(pool))[:num_to_return])

def draw_radar(nums):
    metrics = [
        len([n for n in nums if n >= 20]) / 5,
        len([n for n in nums if n % 2 != 0]) / 5,
        (sum(nums)-15)/170,
        (nums[-1]-nums[0])/38,
        (len(set(abs(a-b) for a,b in itertools.combinations(nums,2)))-4)/8
    ]
    fig = go.Figure(data=go.Scatterpolar(r=metrics, theta=['大小','奇偶','和值','跨度','AC值'], fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 1])), showlegend=False, height=220, margin=dict(l=30,r=30,t=20,b=20))
    return fig

# ==========================
# 3. Streamlit UI
# ==========================
st.set_page_config(page_title="Gauss 539 AI V33.3", layout="wide")

if 'history' not in st.session_state:
    # 抓取 50 頁 (約 1000 期)
    st.session_state.history = fetch_539_history(50)

history = st.session_state.history

# --- 防錯檢查 ---
if not history:
    st.error("❌ 數據抓取失敗，請確認網路或 Pilio 網站狀態。")
    st.stop()

# --- 頂部顯示：最新五期紀錄 ---
st.title("🎯 Gauss 539 V33.3 - 千期大數據分析")
st.subheader("📅 最新五期開獎紀錄")
cols_latest = st.columns(5)
# 取最後五期 (history 尾端是最新的)
last_5 = history[-5:][::-1] 
for i, draw in enumerate(last_5):
    with cols_latest[i]:
        st.info(f"第 {i+1} 期 (最新)")
        st.markdown(f"### `{' '.join([f'{x:02d}' for x in draw])}`")

st.markdown("---")

# --- 功能分區 ---
tab1, tab2 = st.tabs(["🚀 AI HMM 智慧預測", "🕵️ 千期數據庫一覽"])

with tab1:
    if st.button("✨ 啟動千期模型預測"):
        pool = hmm_prediction(history)
        history_sets = [set(h) for h in history]
        
        recs = []
        # 進行一萬次模擬過濾，確保與歷史不重複
        for _ in range(10000):
            sample = sorted(random.sample(pool, 5))
            ac = len(set(abs(a-b) for a,b in itertools.combinations(sample,2)))-4
            if 4 <= ac <= 8:
                if 20 <= (sample[-1]-sample[0]) <= 32:
                    if set(sample) not in history_sets:
                        recs.append(sample)
            if len(recs) >= 3: break

        st.info(f"💡 HMM 強勢號碼池 (基於狀態遷移)： {', '.join([f'{x:02d}' for x in pool])}")
        
        cols_rec = st.columns(3)
        for i, r in enumerate(recs):
            with cols_rec[i]:
                st.success(f"推薦組合 {i+1}")
                st.markdown(f"## {' - '.join([f'{x:02d}' for x in r])}")
                st.plotly_chart(draw_radar(r), use_container_width=True)
                st.caption("✅ 已排除千期內所有重複號碼")

with tab2:
    st.subheader(f"📊 歷史數據總庫 (目前已載入 {len(history)} 期)")
    # 顯示更多期數供參考
    history_display = pd.DataFrame(history[::-1], columns=['一', '二', '三', '四', '五'])
    st.dataframe(history_display, height=400, use_container_width=True)

st.markdown("---")
st.caption("V33.3 版：已鎖定 1000 期分析樣本，並自動剔除歷史重複組合。")
