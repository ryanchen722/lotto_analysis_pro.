import random
import streamlit as st
import requests
import re
import numpy as np
import pandas as pd
import json
import os
from bs4 import BeautifulSoup
from collections import Counter
import plotly.express as px

# 設定
st.set_page_config(page_title="539 AI V71 專業投資版", layout="wide")

PERF_FILE = "perf_v71.json"
STATE_FILE = "state_v71.json"
BET_HISTORY_FILE = "bet_history_v71.json"

# ==============================
# 資料抓取與解析 (加入期號抓取)
# ==============================
@st.cache_data(ttl=10800)
def load_data():
    target_count = 600
    headers = {"User-Agent": "Mozilla/5.0"}
    all_data = []
    page = 1

    while len(all_data) < target_count:
        url = f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={page}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = "big5"
            soup = BeautifulSoup(r.text, "lxml")
            
            # 抓取表格行
            rows = soup.find_all("tr")
            for row in rows:
                txt = row.text.replace('\xa0', ' ')
                # 匹配期號 (例如: 113000123) 與 號碼
                draw_id = re.search(r'\b\d{8,9}\b', txt)
                nums = re.findall(r'\b\d{1,2}\b', txt)
                
                # 過濾出 5 個號碼
                clean_nums = [int(x) for x in nums if 1 <= int(x) <= 39]
                if draw_id and len(clean_nums) >= 5:
                    all_data.append({
                        "id": draw_id.group(),
                        "draw": sorted(clean_nums[-5:])
                    })
            
            if page > 30: break # 防止無限迴圈
            page += 1
        except Exception as e:
            st.error(f"連線錯誤: {e}")
            break

    # 轉為 DataFrame 方便處理，由舊到新排序
    df = pd.DataFrame(all_data).drop_duplicates(subset='id')
    df = df.sort_values('id').reset_index(drop=True)
    return df

# ==============================
# 工具函數
# ==============================
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ==============================
# AI 核心演算法
# ==============================
def get_ai_scores(df_history):
    # 取最近 60 期做分析
    recent = df_history.tail(60)
    all_nums = [n for sublist in recent['draw'] for n in sublist]
    freq = Counter(all_nums)
    
    scores = {}
    last_draws = df_history['draw'].tolist()
    
    for n in range(1, 40):
        # 1. 頻率分 (0-10分)
        f_score = freq.get(n, 0) / 60 * 100
        
        # 2. 遺漏分 (Gap)
        gap = 0
        for i, draw in enumerate(reversed(last_draws)):
            if n in draw:
                gap = i
                break
            gap = len(last_draws)
        
        # 綜合計分：熱度(頻率) + 適度冷感(遺漏補償)
        scores[n] = f_score + (gap * 0.5)
        
    return scores

def generate_prediction(scores):
    sorted_nums = sorted(scores, key=scores.get, reverse=True)
    main = sorted(sorted_nums[:5])
    sub = sorted(random.sample(range(1, 40), 5))
    return main, sub

# ==============================
# 損益計算邏輯
# ==============================
def calculate_metrics(perf):
    if not perf:
        return 0, 0, 0
    
    total_cost = 0
    total_win = 0
    
    for p in perf:
        for hit in p["hits"]:
            total_cost += 50
            if hit == 2: total_win += 50
            elif hit == 3: total_win += 500
            elif hit >= 4: total_win += 20000
            
    return total_win - total_cost, total_win, total_cost

# ==============================
# UI 介面
# ==============================
df_history = load_data()
perf = load_json(PERF_FILE, [])
state = load_json(STATE_FILE, {"lose_streak": 0, "last_processed_id": ""})
bet_queue = load_json(BET_HISTORY_FILE, []) # 儲存待驗證的下注

st.title("🔥 539 AI V71 投資決策系統")

# 側邊欄狀態
with st.sidebar:
    st.header("📊 帳戶概況")
    profit, wins, costs = calculate_metrics(perf)
    st.metric("累計盈虧 (ROI)", f"{profit} 元", delta=f"{profit}")
    st.write(f"總投入: {costs} 元")
    st.write(f"總回報: {wins} 元")
    st.divider()
    if st.button("🗑️ 清除所有紀錄"):
        if os.path.exists(PERF_FILE): os.remove(PERF_FILE)
        if os.path.exists(BET_HISTORY_FILE): os.remove(BET_HISTORY_FILE)
        save_json(STATE_FILE, {"lose_streak": 0, "last_processed_id": ""})
        st.rerun()

# 數據驗證邏輯：檢查是否有下注待開獎
current_last_id = df_history.iloc[-1]['id']
if bet_queue:
    new_bets = []
    for bet in bet_queue:
        # 在歷史紀錄中找尋該期號是否已開獎
        match = df_history[df_history['id'] == bet['target_id']]
        if not match.empty:
            draw_result = match.iloc[0]['draw']
            hits = [len(set(b) & set(draw_result)) for b in bet['bets']]
            
            perf.append({
                "id": bet['target_id'],
                "draw": draw_result,
                "hits": hits,
                "time": bet['time']
            })
            
            # 更新連輸狀態
            if max(hits) < 2:
                state["lose_streak"] += 1
            else:
                state["lose_streak"] = 0
            
            st.balloons()
            st.success(f"🎊 期號 {bet['target_id']} 已開獎！命中數: {hits}")
        else:
            new_bets.append(bet)
    
    save_json(PERF_FILE, perf)
    save_json(STATE_FILE, state)
    save_json(BET_HISTORY_FILE, new_bets)

# 主畫面展示
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📅 近期開獎走勢")
    st.dataframe(df_history.tail(10)[::-1], use_container_width=True)
    
    # 損益圖表
    if perf:
        p_df = pd.DataFrame([{"期號": p["id"], "盈虧": (sum([50 if h==2 else 500 if h==3 else 20000 if h>=4 else 0 for h in p["hits"]]) - 100)} for p in perf])
        p_df['累計損益'] = p_df['盈虧'].cumsum()
        fig = px.line(p_df, x="期號", y="累計損益", title="投資回報曲線")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🤖 AI 決策中心")
    
    # 預測邏輯
    avg_hit = np.mean([np.mean(p["hits"]) for p in perf]) if perf else 0
    st.info(f"當前連輸：{state['lose_streak']} 期 | 近期平均命中：{avg_hit:.2f}")
    
    # 計算下一期的期號 (簡單遞增)
    next_id = str(int(current_last_id) + 1)
    
    # 檢查是否已經針對下一期下注過
    already_bet = any(b['target_id'] == next_id for b in bet_queue)
    
    if st.button("🚀 執行期號 " + next_id + " 預測", disabled=already_bet):
        if state['lose_streak'] >= 5:
            st.error("⚠️ 觸發止損機制：連輸 5 期，建議休息。")
        else:
            scores = get_ai_scores(df_history)
            main, sub = generate_prediction(scores)
            
            # 儲存到待驗證隊列
            bet_queue.append({
                "target_id": next_id,
                "bets": [main, sub],
                "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
            })
            save_json(BET_HISTORY_FILE, bet_queue)
            st.rerun()

    if bet_queue:
        st.warning(f"⏳ 等待 {bet_queue[0]['target_id']} 期開獎中...")
        for i, b in enumerate(bet_queue[0]['bets']):
            st.code(f"組合 {i+1}: {' '.join(map(str, b))}")

# 底部統計
st.divider()
if not df_history.empty:
    st.subheader("🔢 號碼冷熱圖 (近60期)")
    flat_list = [n for sub in df_history.tail(60)['draw'] for n in sub]
    counts = Counter(flat_list)
    count_df = pd.DataFrame([{"號碼": i, "次數": counts.get(i, 0)} for i in range(1, 40)])
    fig2 = px.bar(count_df, x="號碼", y="次數", color="次數")
    st.plotly_chart(fig2, use_container_width=True)

if st.button("🔄 強制刷新數據"):
    st.cache_data.clear()
    st.rerun()
