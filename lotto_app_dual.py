import random
import streamlit as st
import itertools
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter
import plotly.graph_objects as go
import pandas as pd

# ==============================
# 抓取歷史資料 (鎖定 1000 期 / 12小時更新一次)
# ==============================
@st.cache_data(ttl=43200) # 12小時 = 12 * 3600 秒
def fetch_history(max_pages=50):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
    history = []
    session = requests.Session()
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    for page in range(1, max_pages + 1):
        url = f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={page}"
        try:
            r = session.get(url, headers=headers, timeout=10)
            r.encoding = "big5"
            soup = BeautifulSoup(r.text, "lxml")
            rows = soup.find_all("tr")

            for row in rows:
                nums = re.findall(r'\b\d{1,2}\b', row.text)
                if len(nums) >= 5:
                    n = list(map(int, nums[-5:]))
                    n = [x for x in n if 1 <= x <= 39]
                    if len(n) == 5:
                        draw = sorted(n)
                        if draw not in history:
                            history.append(draw)
            
            if page % 10 == 0:
                progress_bar.progress(page / max_pages)
                status_text.text(f"已同步大數據：{len(history)} 期...")
        except:
            break

    progress_bar.empty()
    status_text.empty()
    return history[::-1] # 由舊到新

# ==============================
# Score 模型 (權重計算)
# ==============================
def score_numbers(history):
    freq120 = Counter([n for d in history[-120:] for n in d])
    freq30 = Counter([n for d in history[-30:] for n in d])
    
    score = {}
    for n in range(1, 40):
        hot = freq120[n] / 120
        trend = freq30[n] / 30
        last_seen = 0
        for i, d in enumerate(reversed(history)):
            if n in d:
                last_seen = i
                break
        cold = min(last_seen / 40, 1)
        score[n] = 0.4 * hot + 0.3 * trend + 0.3 * cold
    return score

# ==============================
# AI 推薦引擎 (動態核心輪替)
# ==============================
def ai_recommend(history):
    score = score_numbers(history)
    sorted_nums = sorted(score.items(), key=lambda x: x[1], reverse=True)
    
    # 強勢池 18 碼
    pool = [n for n, s in sorted_nums[:18]]
    # 核心候選 5 碼 (解決號碼不動的關鍵)
    potential_cores = [n for n, s in sorted_nums[:5]]
    
    odd_list = [len([n for n in d if n % 2]) for d in history[-200:]]
    span_list = [max(d) - min(d) for d in history[-200:]]
    odd_target = Counter(odd_list).most_common(1)[0][0]
    span_target = int(sum(span_list) / len(span_list))

    history_sets = [set(d) for d in history]
    combos = set()

    # 模擬 80,000 次，尋找不重號組合
    for _ in range(80000):
        # 關鍵：每次核心球都從前五強中隨機挑選 2 碼，增加組合活性
        c = set(random.sample(potential_cores, 2))
        while len(c) < 5:
            c.add(random.choice(pool))
        
        sorted_c = tuple(sorted(list(c)))
        
        if set(sorted_c) in history_sets:
            continue
            
        odd = len([n for n in sorted_c if n % 2])
        span = sorted_c[-1] - sorted_c[0]
        
        # 符合體質條件
        if abs(odd - odd_target) <= 1 and abs(span - span_target) <= 6:
            combos.add(sorted_c)
            if len(combos) >= 20: break

    # 評分排序，並加入 2% 的隨機擾動，讓接近的組合能輪替出現
    scored_combos = sorted(
        [(list(c), sum(score[n] for n in c) * random.uniform(0.98, 1.02)) for c in combos], 
        key=lambda x: x[1], 
        reverse=True
    )
    
    top10 = [c for c, s in scored_combos[:10]]
    return pool, potential_cores, top10[:3], top10

# ==============================
# 雷達圖功能
# ==============================
def radar(nums):
    ac = len(set(abs(a-b) for a, b in itertools.combinations(nums, 2))) - 4
    metrics = [
        len([n for n in nums if n >= 20]) / 5,
        len([n for n in nums if n % 2]) / 5,
        (sum(nums) - 15) / 170,
        (nums[-1] - nums[0]) / 38,
        ac / 8
    ]
    fig = go.Figure(data=go.Scatterpolar(r=metrics, theta=['大', '奇', '和值', '跨度', 'AC'], fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 1])), showlegend=False, height=200, margin=dict(l=30, r=30, t=20, b=20))
    return fig

# ==============================
# UI 配置
# ==============================
st.set_page_config(page_title="539 AI 預測 V33.9", layout="wide")
st.title("🎯 539 AI 預測系統 (動態核心版)")

# 載入 1000 期 (緩存 12 小時)
if 'history' not in st.session_state:
    st.session_state.history = fetch_history(50)

history = st.session_state.history

# 頂部：最新五期
st.header("📅 最新五期開獎紀錄")
cols = st.columns(5)
for i, d in enumerate(history[-5:][::-1]):
    with cols[i]:
        st.metric(label="最新期" if i==0 else f"前 {i} 期", value=" ".join([f"{x:02d}" for x in d]))

st.divider()

if st.button("🚀 執行 AI 深度預測"):
    pool, cores, top3, top10 = ai_recommend(history)
    
    st.header("✨ AI 核心推薦組合")
    st.caption(f"本輪預測核心種子球：{', '.join([f'{x:02d}' for x in cores])}")
    
    rec_cols = st.columns(3)
    for i, r in enumerate(top3):
        with rec_cols[i]:
            st.success(f"推薦組合 {i+1}")
            st.markdown(f"## `{' - '.join([f'{x:02d}' for x in r])}`")
            st.plotly_chart(radar(r), use_container_width=True)
            st.caption("✅ 已過濾 1000 期不重號校驗")

    with st.expander("📋 查看更多推薦 (Top 10)"):
        df_top10 = pd.DataFrame([{"排名": f"第 {i+1} 名", "推薦號碼": " ".join([f"{x:02d}" for x in r])} for i, r in enumerate(top10)])
        st.table(df_top10)

    st.balloons()
else:
    st.info("點擊上方按鈕開始模擬。數據每 12 小時自動更新。")

st.sidebar.subheader("📊 數據統計")
st.sidebar.write(f"當前載入期數：{len(history)}")
st.sidebar.write("分析引擎：動態核心輪替 (Dynamic Core)")
