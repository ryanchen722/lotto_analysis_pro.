import random
import pandas as pd
import streamlit as st
import numpy as np
import itertools
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter

# ==========================
# 抓539資料 (精準版)
# ==========================

@st.cache_data(ttl=3600)
def fetch_539_history():
    headers = {"User-Agent": "Mozilla/5.0"}
    history = []
    
    # 抓取前 100 頁足矣，避免網頁讀取過久
    for page in range(1, 100):
        url = f"https://www.pilio.idv.tw/lto539/drawlist/drawlist.asp?page={page}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            # 該網站編碼通常為 Big5，需指定以避免亂碼
            r.encoding = 'big5' 
            soup = BeautifulSoup(r.text, "lxml")
            
            # 針對 Pilio 網頁結構，號碼通常在 td 標籤中
            rows = soup.find_all("tr")
            for row in rows:
                # 抓取所有 1-2 位數字
                nums = re.findall(r'\d{1,2}', row.text)
                
                # 539 核心邏輯：取最後 5 個數字，並嚴格檢查範圍 1-39
                if len(nums) >= 5:
                    draw = [int(n) for n in nums[-5:]]
                    if all(1 <= n <= 39 for n in draw):
                        # 排序並加入歷史，確保不重複抓取
                        sorted_draw = sorted(draw)
                        if sorted_draw not in history:
                            history.append(sorted_draw)
        except:
            break
    return history

# ==========================
# 核心演算法
# ==========================

def calculate_ac(nums):
    """計算 AC 值 (算術複雜度)"""
    return len(set(abs(a-b) for a, b in itertools.combinations(nums, 2))) - 4

def pair_matrix(history):
    """共現矩陣：計算號碼兩兩同時出現的次數"""
    pair_count = Counter()
    for draw in history:
        for pair in itertools.combinations(draw, 2):
            pair_count[tuple(sorted(pair))] += 1
    return pair_count

def number_heat(history):
    """號碼熱度：計算每個號碼出現的頻率"""
    nums = []
    for draw in history:
        nums.extend(draw)
    return Counter(nums)

def tail_analysis(history):
    """尾數分析：計算 0-9 尾數的出現次數"""
    tails = [n % 10 for draw in history for n in draw]
    return Counter(tails)

# ==========================
# Monte Carlo 模擬與過濾
# ==========================

def monte_carlo_pool(history, simulations=100000):
    pool = []
    history_set = set(tuple(x) for x in history)

    for _ in range(simulations):
        nums = sorted(random.sample(range(1, 40), 5))
        
        # 排除歷史已開出號碼
        if tuple(nums) in history_set:
            continue

        ac = calculate_ac(nums)
        # 篩選條件：AC值 4-8, 跨度 20-32
        if 4 <= ac <= 8:
            span = nums[-1] - nums[0]
            if 20 <= span <= 32:
                pool.extend(nums)

    # 防呆：如果 pool 為空，改用純熱度號碼
    if not pool:
        return [n for n, _ in number_heat(history).most_common(15)]

    # 提取前 15 名強勢號碼，並確保範圍 (排除 0)
    counter = Counter(pool)
    strong = [n for n, _ in counter.most_common(15) if 1 <= n <= 39]
    return strong

# ==========================
# AI 決策核心
# ==========================

def find_core_three(pool, pair_count, heat, tail):
    # 確保池子夠大
    if len(pool) < 3:
        return [1, 2, 3] # 極端情況下的預設值
        
    combos = list(itertools.combinations(pool, 3))
    best = None
    best_score = -1

    for combo in combos:
        score = 0
        # 考慮兩兩共現機率
        for p in itertools.combinations(combo, 2):
            score += pair_count.get(tuple(sorted(p)), 0)
        # 考慮單碼熱度與尾數權重
        for n in combo:
            score += heat.get(n, 0)
            score += tail.get(n % 10, 0)

        if score > best_score:
            best_score = score
            best = combo
    return best

# ==========================
# Streamlit UI
# ==========================

st.set_page_config(page_title="Gauss 539 V28.1", page_icon="🎯")
st.title("🎯 Gauss 539 V28.1 精準版")
st.markdown("---")

if st.button("🚀 開始智慧分析"):
    with st.spinner("正在爬取歷史數據並執行 Monte Carlo 模擬..."):
        history = fetch_539_history()

        if not history:
            st.error("無法連線至數據源，請檢查網路。")
            st.stop()

        st.success(f"成功抓取 {len(history)} 期歷史開獎資料")
        st.info(f"最新一期號碼：{', '.join([f'{x:02d}' for x in history[0]])}")

        # 核心運算
        pair_cnt = pair_matrix(history)
        heat_map = number_heat(history)
        tail_map = tail_analysis(history)
        
        # 模擬池
        strong_pool = monte_carlo_pool(history)
        
        # 尋找黃金三碼核心
        core = find_core_three(strong_pool, pair_cnt, heat_map, tail_map)
        
        # 生成五組推薦 (Wheeling System)
        results = []
        remain = [n for n in strong_pool if n not in core]
        
        for i in range(5):
            extra = random.sample(remain, 2)
            combo = sorted(list(core) + extra)
            results.append({
                "排名": f"推薦第 {i+1} 組",
                "建議號碼": " - ".join([f"{x:02d}" for x in combo]),
                "和值": sum(combo),
                "跨度": combo[-1] - combo[0],
                "AC值": calculate_ac(combo)
            })

        # 顯示結果
        st.subheader("💎 AI 核心三碼")
        st.write(f"### {', '.join([f'{x:02d}' for x in core])}")

        st.subheader("📋 推薦組合")
        st.table(pd.DataFrame(results))

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔥 強勢號碼池")
            st.write(strong_pool)
        with col2:
            st.subheader("📊 熱門尾數排行")
            st.write(dict(tail_map.most_common(5)))

        st.balloons()

st.markdown("---")
st.caption("本工具僅供統計學術分析與 Streamlit 實作練習，不保證獲利，請理性參與。")
