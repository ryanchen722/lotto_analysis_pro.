import random
import streamlit as st
import itertools
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter
import plotly.graph_objects as go

# ==============================
# 抓歷史資料
# ==============================
@st.cache_data(ttl=3600)
def fetch_history():
    headers = {"User-Agent": "Mozilla/5.0"}
    history = []

    for page in range(1, 120):
        url = f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={page}"

        try:
            r = requests.get(url, headers=headers, timeout=10)
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

        except:
            break

    return history[::-1]


# ==============================
# 分數模型
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
# ⭐ 位置模型
# ==============================
def position_model(history):
    pos_freq = [Counter() for _ in range(5)]

    for draw in history:
        draw = sorted(draw)
        for i, n in enumerate(draw):
            pos_freq[i][n] += 1

    return pos_freq


# ==============================
# 熱門球機率
# ==============================
def hot_probability(history):
    score = score_numbers(history)
    total = sum(score.values())

    probs = {}
    for n, s in score.items():
        probs[n] = (s / total) * 100

    return sorted(probs.items(), key=lambda x: x[1], reverse=True)[:10]


# ==============================
# 強勢池
# ==============================
def strong_pool(history):
    score = score_numbers(history)
    sorted_nums = sorted(score.items(), key=lambda x: x[1], reverse=True)

    pool = [n for n, s in sorted_nums[:18]]
    core = [n for n, s in sorted_nums[:5]]

    return pool, core, score


# ==============================
# 結構預測
# ==============================
def structure_predict(history):
    odd = []
    span = []

    for d in history[-200:]:
        odd.append(len([n for n in d if n % 2]))
        span.append(max(d) - min(d))

    return Counter(odd).most_common(1)[0][0], int(sum(span) / len(span))


# ==============================
# 組合評分
# ==============================
def combo_score(combo, score):
    base = sum(score[n] for n in combo)

    ac = len(set(abs(a - b) for a, b in itertools.combinations(combo, 2))) - 4
    if 4 <= ac <= 8:
        base += 0.5

    return base


# ==============================
# ⭐ AI推薦（最終版）
# ==============================
def ai_recommend(history):
    pool, core, score = strong_pool(history)
    pos_freq = position_model(history)

    odd_target, span_target = structure_predict(history)

    ranges = [(1, 10), (5, 15), (10, 25), (20, 35), (25, 39)]

    combos = set()

    for _ in range(80000):
        combo = []

        for i in range(5):
            candidates = list(range(1, 40))
            weights = [score[n] * (pos_freq[i][n] + 1) for n in candidates]

            pick = random.choices(candidates, weights=weights, k=1)[0]
            combo.append(pick)

        combo = sorted(set(combo))

        while len(combo) < 5:
            combo.append(random.randint(1, 39))
            combo = list(set(combo))

        combo = tuple(sorted(combo))

        # 區間限制
        ok = True
        for i, n in enumerate(combo):
            if not (ranges[i][0] <= n <= ranges[i][1]):
                ok = False
                break

        if not ok:
            continue

        # 結構限制
        odd = len([n for n in combo if n % 2])
        span = combo[-1] - combo[0]

        if abs(odd - odd_target) <= 1 and abs(span - span_target) <= 6:
            combos.add(combo)

    combos = list(combos)

    scored = [(c, combo_score(c, score)) for c in combos]
    scored = sorted(scored, key=lambda x: x[1], reverse=True)

    top10 = [list(c) for c, _ in scored[:10]]
    top3 = top10[:3]

    return top3, top10


# ==============================
# 四碼引擎
# ==============================
def four_hit_engine(history, top10):
    results = []

    for combo in top10:
        count = 0
        for draw in history:
            if len(set(combo) & set(draw)) >= 4:
                count += 1

        results.append((combo, count))

    return sorted(results, key=lambda x: x[1], reverse=True)[:5]


# ==============================
# 冷號爆發
# ==============================
def cold_burst(history):
    last_seen = {}

    for n in range(1, 40):
        for i, d in enumerate(reversed(history)):
            if n in d:
                last_seen[n] = i
                break

    return [n for n, _ in sorted(last_seen.items(), key=lambda x: x[1], reverse=True)[:6]]


# ==============================
# 雷達圖
# ==============================
def radar(nums):
    ac = len(set(abs(a - b) for a, b in itertools.combinations(nums, 2))) - 4

    metrics = [
        len([n for n in nums if n >= 20]) / 5,
        len([n for n in nums if n % 2]) / 5,
        (sum(nums) - 15) / 170,
        (nums[-1] - nums[0]) / 38,
        ac / 8
    ]

    fig = go.Figure(data=go.Scatterpolar(
        r=metrics,
        theta=['大', '奇', '和值', '跨度', 'AC'],
        fill='toself'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False, range=[0, 1])),
        showlegend=False
    )

    return fig


# ==============================
# UI
# ==============================
st.set_page_config(layout="wide")

st.title("🎯 539 AI 預測 V37（最終穩定版）")

history = fetch_history()

st.write("歷史期數：", len(history))

# 最新五期
st.subheader("📅 最新五期")

cols = st.columns(5)
for i, d in enumerate(history[-5:][::-1]):
    cols[i].metric(f"第{i+1}期", " ".join(f"{x:02d}" for x in d))


# AI預測
if st.button("🚀 AI預測"):

    top3, top10 = ai_recommend(history)

    st.divider()

    # 熱門球
    st.subheader("🔥 熱門球機率")
    for n, p in hot_probability(history):
        st.progress(p / 10, text=f"{n:02d} {p:.2f}%")

    st.divider()

    # 推薦
    st.subheader("🎯 AI推薦")

    cols = st.columns(3)
    four = four_hit_engine(history, top10)

    for i, r in enumerate(top3):
        with cols[i]:
            st.subheader(" ".join(f"{x:02d}" for x in r))

            for combo, count in four:
                if combo == r:
                    st.success(f"歷史4碼命中 {count} 次")

            st.plotly_chart(radar(r), use_container_width=True)

    # 進階
    with st.expander("📊 進階分析"):
        st.write("Top10推薦：")
        for r in top10:
            st.write(" ".join(f"{x:02d}" for x in r))

        st.write("冷號爆發：", cold_burst(history))