import streamlit as st
import requests
import re
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(page_title="539 AI 回測版", layout="wide")

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

        except Exception:
            page += 1

    return all_data[:target][::-1]


def analyze(history):
    recent50 = history[-50:]
    freq = Counter([n for d in recent50 for n in d])

    scores = {}

    for n in range(1, 40):
        hot = freq[n]

        gap = next(
            (i for i, d in enumerate(reversed(history)) if n in d),
            50
        )

        decay = 0
        for i, d in enumerate(reversed(history[-80:])):
            if n in d:
                decay += 1 / (i + 1)

        score = hot * 1.2 + gap * 0.8 + decay * 8
        scores[n] = score

    return scores


def pick_numbers(scores):
    nums = np.array(list(scores.keys()))
    vals = np.array(list(scores.values()), dtype=float)

    vals = vals + np.random.rand(len(vals)) * 0.05
    probs = vals / vals.sum()

    picks = set()
    while len(picks) < 5:
        picks.add(int(np.random.choice(nums, p=probs)))

    return sorted(picks)


def health(combo):
    odd = sum(1 for x in combo if x % 2 != 0)
    big = sum(1 for x in combo if x >= 20)
    total = sum(combo)

    return f"奇偶 {odd}:{5-odd} ｜ 大小 {big}:{5-big} ｜ 總和 {total}"


def backtest(history, test_size=200):
    hits = []

    if len(history) <= test_size + 80:
        test_size = max(50, len(history) - 100)

    for i in range(len(history) - test_size, len(history)):
        train = history[:i]
        actual = history[i]

        if len(train) < 80:
            continue

        scores = analyze(train)
        pred = pick_numbers(scores)

        hit = len(set(pred) & set(actual))
        hits.append(hit)

    return np.mean(hits), hits


st.title("🔥 539 AI 回測驗證版")

history = load_history()

st.write("📊 資料期數：", len(history))

st.subheader("📅 最新五期")
cols = st.columns(5)

for i, d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(f"{x:02d}" for x in d))


st.subheader("🔥 熱號排行（近50期）")

recent50 = history[-50:]
freq = Counter([n for d in recent50 for n in d])

heat_df = pd.DataFrame([
    {"號碼": n, "次數": freq[n]}
    for n in range(1, 40)
]).sort_values("次數", ascending=False)

st.dataframe(heat_df, use_container_width=True)


if st.button("🚀 AI 預測"):
    scores = analyze(history)

    b1 = pick_numbers(scores)
    b2 = pick_numbers(scores)
    b3 = pick_numbers(scores)

    st.subheader("💰 推薦號碼")

    for idx, b in enumerate([b1, b2, b3], start=1):
        st.success(f"第{idx}組：" + " - ".join(f"{x:02d}" for x in b))
        st.caption(health(b))


if st.button("📊 回測模型"):
    avg_hit, hits = backtest(history, test_size=200)

    st.subheader("📈 回測結果")
    st.metric("平均命中", f"{avg_hit:.2f}")
    st.write("隨機基準：約 0.64")

    dist = Counter(hits)
    dist_df = pd.DataFrame([
        {"命中數": k, "次數": v}
        for k, v in sorted(dist.items())
    ])

    st.dataframe(dist_df, use_container_width=True)
    st.bar_chart(dist_df.set_index("命中數")["次數"])

    if avg_hit > 0.8:
        st.success("🔥 模型略有優勢")
    elif avg_hit > 0.65:
        st.warning("⚠️ 接近隨機，只有微弱優勢")
    else:
        st.error("❌ 沒有優勢，接近亂選")


if st.button("🔄 更新歷史資料"):
    st.cache_data.clear()
    st.rerun()