import random
import streamlit as st
import requests
import re
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(page_title="539 AI 測試版", layout="wide")

# ==============================
# 抓歷史資料
# ==============================
@st.cache_data(ttl=10800)
def load_history():

    target = 300
    headers = {"User-Agent": "Mozilla/5.0"}

    all_data = []
    page = 1

    while len(all_data) < target:

        url = f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={page}"

        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = "big5"

            soup = BeautifulSoup(r.text, "lxml")

            rows = soup.find_all("tr")

            page_data = []

            for row in rows:

                nums = re.findall(r'\b\d{1,2}\b', row.text)

                nums = [int(x) for x in nums if 1 <= int(x) <= 39]

                if len(nums) >= 5:
                    page_data.append(sorted(nums[-5:]))

            if len(page_data) < 10:
                break

            all_data.extend(page_data)

            page += 1

        except:
            page += 1

    return all_data[:target][::-1]

# ==============================
# 分析
# ==============================
def analyze(history):

    # 最近50期熱度
    recent50 = history[-50:]

    freq = Counter([n for d in recent50 for n in d])

    scores = {}

    for n in range(1,40):

        # 熱度
        hot = freq[n]

        # gap（多久沒出）
        gap = next(
            (i for i,d in enumerate(reversed(history)) if n in d),
            50
        )

        # 最近權重（越近越重要）
        decay = 0

        for i,d in enumerate(reversed(history[-80:])):

            if n in d:
                decay += 1 / (i+1)

        # 最終分數
        score = (
            hot * 1.2 +
            gap * 0.8 +
            decay * 8
        )

        scores[n] = score

    return scores

# ==============================
# AI 選號
# ==============================
def pick_numbers(scores):

    nums = np.array(list(scores.keys()))

    vals = np.array(list(scores.values()))

    # 防止固定
    vals = vals + np.random.rand(len(vals))*0.05

    probs = vals / vals.sum()

    picks = set()

    while len(picks) < 5:

        n = int(np.random.choice(nums, p=probs))

        picks.add(n)

    return sorted(list(picks))

# ==============================
# 健康度
# ==============================
def health(combo):

    odd = sum([1 for x in combo if x % 2 != 0])

    big = sum([1 for x in combo if x >= 20])

    return f"奇偶 {odd}:{5-odd} ｜ 大小 {big}:{5-big}"

# ==============================
# UI
# ==============================
st.title("🔥 539 AI 測試版")

history = load_history()

# ==============================
# 最新五期
# ==============================
st.subheader("📅 最新五期")

cols = st.columns(5)

for i,d in enumerate(history[-5:][::-1]):

    cols[i].code(" ".join(f"{x:02d}" for x in d))

# ==============================
# 熱號排行
# ==============================
st.subheader("🔥 熱號排行（近50期）")

recent50 = history[-50:]

freq = Counter([n for d in recent50 for n in d])

heat_df = pd.DataFrame([
    {
        "號碼": n,
        "次數": freq[n]
    }
    for n in range(1,40)
])

heat_df = heat_df.sort_values("次數", ascending=False)

st.dataframe(heat_df)

# ==============================
# 預測
# ==============================
if st.button("🚀 AI 預測"):

    scores = analyze(history)

    b1 = pick_numbers(scores)
    b2 = pick_numbers(scores)
    b3 = pick_numbers(scores)

    st.subheader("💰 推薦號碼")

    st.success(
        "第1組：" +
        " - ".join(f"{x:02d}" for x in b1)
    )

    st.caption(health(b1))

    st.success(
        "第2組：" +
        " - ".join(f"{x:02d}" for x in b2)
    )

    st.caption(health(b2))

    st.success(
        "第3組：" +
        " - ".join(f"{x:02d}" for x in b3)
    )

    st.caption(health(b3))

# ==============================
# 重抓
# ==============================
if st.button("🔄 更新歷史資料"):

    st.cache_data.clear()

    st.rerun()