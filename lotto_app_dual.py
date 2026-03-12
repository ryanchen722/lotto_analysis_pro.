import random
import pandas as pd
import streamlit as st
import numpy as np
import itertools
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter, defaultdict

# ==========================
# 1. 數據抓取 (嚴格過濾版)
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
    # 確保由舊到新排序，方便時間序列分析
    return history[::-1] 

# ==========================
# 2. HMM 核心邏輯
# ==========================
def hmm_prediction(history):
    # 定義狀態：0=冷(低頻), 1=溫(中頻), 2=熱(高頻)
    all_nums = [n for draw in history for n in draw]
    global_heat = Counter(all_nums)
    
    def get_state(num):
        count = global_heat[num]
        avg = len(all_nums) / 39
        if count < avg * 0.8: return 0  # 冷
        if count > avg * 1.2: return 2  # 熱
        return 1 # 溫

    # 遷移矩陣：紀錄狀態轉換 (冷->熱, 熱->熱 等)
    transitions = defaultdict(lambda: defaultdict(int))
    state_to_nums = defaultdict(list)
    
    # 建立歷史狀態序列
    last_states = None
    for draw in history:
        current_states = tuple(sorted([get_state(n) for n in draw]))
        for n in draw:
            state_to_nums[get_state(n)].append(n)
        
        if last_states:
            transitions[last_states][current_states] += 1
        last_states = current_states

    # 預測下一期最可能的狀態組合
    latest_draw_state = tuple(sorted([get_state(n) for n in history[-1]]))
    next_state_candidates = transitions[latest_draw_state]
    
    if not next_state_candidates:
        # 若無歷史匹配，預設為「2熱 2溫 1冷」的經典組合
        predicted_states = [2, 2, 1, 1, 0]
    else:
        # 取出現次數最多的狀態轉換
        predicted_states = max(next_state_candidates, key=next_state_candidates.get)

    # 從預測狀態中抽取號碼
    final_pool = []
    for s in predicted_states:
        pool_in_state = state_to_nums[s]
        if pool_in_state:
            # 加入加權抽樣邏輯
            chosen = random.choice(Counter(pool_in_state).most_common(10))[0]
            final_pool.append(chosen)
    
    # 確保號碼不重複且為 5 個
    final_pool = list(set(final_pool))
    while len(final_pool) < 15:
        extra = random.randint(1, 39)
        if extra not in final_pool:
            final_pool.append(extra)
            
    return sorted(final_pool[:15])

# ==========================
# 3. 輔助分析
# ==========================
def calculate_ac(nums):
    return len(set(abs(a-b) for a, b in itertools.combinations(nums, 2))) - 4

# ==========================
# 4. Streamlit UI
# ==========================
st.set_page_config(page_title="Gauss 539 V30 HMM", page_icon="🧠")
st.title("🧠 Gauss 539 V30 - HMM 隱藏狀態預測版")
st.write("利用馬可夫遷移矩陣 (Transition Matrix) 分析開獎狀態轉換機率")

if st.button("執行 HMM 模型預測"):
    with st.spinner("正在計算遷移矩陣..."):
        history = fetch_539_history()
        if not history:
            st.error("無法取得數據")
            st.stop()

        # 執行 HMM 預測
        hmm_pool = hmm_prediction(history)
        
        # 從 HMM 池中生成推薦組合 (過濾 AC 與 跨度)
        recommendations = []
        for _ in range(1000): # 內部模擬 1000 次尋找最佳組合
            sample = sorted(random.sample(hmm_pool, 5))
            if 4 <= calculate_ac(sample) <= 8:
                span = sample[-1] - sample[0]
                if 20 <= span <= 32:
                    if sample not in recommendations:
                        recommendations.append(sample)
            if len(recommendations) >= 5:
                break

        # 顯示結果
        st.success(f"已根據 {len(history)} 期數據完成狀態轉移建模")
        
        st.subheader("🔮 HMM 強勢預測池 (前15碼)")
        st.write(f"這 15 碼是根據下一期預計跳轉的「隱藏狀態」篩選而出：")
        st.info(", ".join([f"{x:02d}" for x in hmm_pool]))

        st.subheader("📋 模型推薦組合")
        res_df = []
        for i, rec in enumerate(recommendations):
            res_df.append({
                "組別": f"HMM 推薦 {i+1}",
                "號碼": " - ".join([f"{x:02d}" for x in rec]),
                "AC值": calculate_ac(rec),
                "跨度": rec[-1] - rec[0]
            })
        st.table(pd.DataFrame(res_df))

        st.balloons()

st.caption("註：HMM 模型假設開獎規律存在狀態轉換，此工具僅供統計參考。")
