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
# 抓539歷史資料
# ==========================

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


# ==========================
# AC值
# ==========================

def calculate_ac(nums):

    return len(set(abs(a-b) for a,b in itertools.combinations(nums,2))) - 4


# ==========================
# 共現矩陣
# ==========================

def pair_matrix(history):

    pair_count = Counter()

    for draw in history:

        for pair in itertools.combinations(draw,2):

            pair_count[tuple(sorted(pair))] += 1

    return pair_count


# ==========================
# Monte Carlo
# ==========================

def monte_carlo_pool(history, simulations=200000):

    pool = []

    history_set = set(tuple(sorted(x)) for x in history)

    for _ in range(simulations):

        nums = sorted(random.sample(range(1,40),5))

        if tuple(nums) in history_set:
            continue

        ac = calculate_ac(nums)

        if 4 <= ac <= 8:

            span = nums[-1] - nums[0]

            if 20 <= span <= 32:

                pool.extend(nums)

    counter = Counter(pool)

    strong = [n for n,_ in counter.most_common(15)]

    return strong


# ==========================
# 找三碼核心
# ==========================

def find_core_three(pool, pair_count):

    combos = list(itertools.combinations(pool,3))

    best_combo = None
    best_score = -1

    for combo in combos:

        score = 0

        pairs = list(itertools.combinations(combo,2))

        for p in pairs:

            score += pair_count.get(tuple(sorted(p)),0)

        if score > best_score:

            best_score = score
            best_combo = combo

    return best_combo


# ==========================
# 五組覆蓋
# ==========================

def generate_sets(core,pool):

    results = []

    remaining = [n for n in pool if n not in core]

    for _ in range(5):

        extra = random.sample(remaining,2)

        combo = sorted(list(core)+extra)

        results.append(combo)

    return results


# ==========================
# 回測
# ==========================

def backtest(history):

    hit2 = 0
    hit3 = 0

    for i in range(50,len(history)-1):

        train = history[i:]

        target = history[i-1]

        pair_count = pair_matrix(train)

        pool = monte_carlo_pool(train,50000)

        core = find_core_three(pool,pair_count)

        sets = generate_sets(core,pool)

        for s in sets:

            match = len(set(s) & set(target))

            if match >= 3:

                hit3 += 1

                break

            elif match == 2:

                hit2 += 1

    return hit2,hit3


# ==========================
# Streamlit UI
# ==========================

st.set_page_config(page_title="Gauss 539 V27",page_icon="🎯")

st.title("🎯 Gauss 539 V27 Stable")

if st.button("抓取資料並分析"):

    history = fetch_539_history()

    st.success(f"抓到 {len(history)} 期資料")

    st.write("最新一期：",history[0])

    st.write("建立共現矩陣...")

    pair_count = pair_matrix(history)

    st.write("Monte Carlo 模擬...")

    pool = monte_carlo_pool(history)

    core = find_core_three(pool,pair_count)

    results = generate_sets(core,pool)

    st.subheader("三碼核心")

    st.write(core)

    res = []

    for i,r in enumerate(results):

        res.append({

            "排名":f"Top {i+1}",

            "號碼":", ".join([f"{x:02d}" for x in r]),

            "和值":sum(r),

            "跨度":r[-1]-r[0],

            "AC":calculate_ac(r)

        })

    st.subheader("五組推薦")

    st.table(pd.DataFrame(res))

    st.subheader("強勢號碼池")

    st.write(pool)

    st.subheader("歷史回測")

    hit2,hit3 = backtest(history)

    st.write(f"中2次數：{hit2}")

    st.write(f"中3次數：{hit3}")

    st.balloons()