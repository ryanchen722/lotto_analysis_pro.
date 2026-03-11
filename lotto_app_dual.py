import random
import pandas as pd
import streamlit as st
import numpy as np
import itertools
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter


# =====================================
# 抓取539資料（雲端優化）
# =====================================

@st.cache_data(ttl=3600)
def fetch_539_history():

    url = "https://www.pilio.idv.tw/lto539/drawlist/drawlist.asp"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers)
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "lxml")

    rows = soup.find_all("tr")

    history = []

    for row in rows:

        nums = re.findall(r'\d{1,2}', row.text)

        if len(nums) >= 5:

            numbers = list(map(int, nums[-5:]))

            if all(1 <= n <= 39 for n in numbers):

                history.append(sorted(numbers))

    return history


# =====================================
# AC值
# =====================================

def calculate_ac(nums):

    return len(set(abs(a-b) for a,b in itertools.combinations(nums,2))) - 4


# =====================================
# 結構評分
# =====================================

def structure_score(nums,history):

    nums = sorted(nums)

    score = 0

    ac = calculate_ac(nums)

    if 4 <= ac <= 8:
        score += 120

    span = nums[-1] - nums[0]

    if 22 <= span <= 32:
        score += 150

    odd = sum(n % 2 for n in nums)

    if odd in [2,3]:
        score += 80

    consecutive = sum(1 for i in range(4) if nums[i+1] - nums[i] == 1)

    if consecutive == 1:
        score += 50

    tails = [n % 10 for n in nums]

    if len(set(tails)) <= 4:
        score += 40

    recent = [n for sub in history[:10] for n in sub]

    cold = [n for n in nums if n not in recent]

    score += len(cold) * 20

    return score


# =====================================
# Monte Carlo
# =====================================

def monte_carlo_pool(history, simulations=200000):

    pool = []

    history_set = set(tuple(sorted(x)) for x in history)

    for _ in range(simulations):

        nums = sorted(random.sample(range(1,40),5))

        if tuple(nums) in history_set:
            continue

        score = structure_score(nums,history)

        if score > 200:

            pool.extend(nums)

    counter = Counter(pool)

    strong_numbers = [n for n,_ in counter.most_common(15)]

    return strong_numbers


# =====================================
# 找三碼核心
# =====================================

def find_core_three(numbers):

    combos = list(itertools.combinations(numbers,3))

    return random.choice(combos)


# =====================================
# 五組覆蓋
# =====================================

def generate_five_sets(core,pool):

    final = []

    remaining = [n for n in pool if n not in core]

    for _ in range(5):

        extra = random.sample(remaining,2)

        combo = sorted(list(core)+extra)

        final.append(combo)

    return final


# =====================================
# Streamlit UI
# =====================================

st.set_page_config(page_title="Gauss 539 Cloud",page_icon="🎯")

st.title("🎯 Gauss 539 V26 Cloud")

if st.button("抓取最新資料並分析"):

    history = fetch_539_history()

    st.success(f"抓到 {len(history)} 期資料")

    st.write("最新一期：",history[0])

    st.write("Monte Carlo 模擬中...")

    pool = monte_carlo_pool(history)

    core = find_core_three(pool)

    results = generate_five_sets(core,pool)

    st.subheader("三碼核心")

    st.write(core)

    res = []

    for idx,nums in enumerate(results):

        res.append({

            "排名":f"Top {idx+1}",

            "推薦組合":", ".join([f"{x:02d}" for x in nums]),

            "和值":sum(nums),

            "跨度":nums[-1]-nums[0],

            "AC":calculate_ac(nums)

        })

    st.subheader("五組推薦")

    st.table(pd.DataFrame(res))

    st.subheader("強勢號碼池")

    st.write(pool)

    st.balloons()