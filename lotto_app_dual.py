import random
import streamlit as st
import requests
import os
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter
from itertools import combinations

CSV_PATH = "539_history.csv"
MAX_HISTORY = 1700


# ==============================
# 抓資料（穩定）
# ==============================
def fetch_latest_pages(pages=3):

    headers = {"User-Agent": "Mozilla/5.0"}
    all_data = []

    for p in range(1, pages+1):

        url = f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={p}"
        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = "big5"

        soup = BeautifulSoup(r.text, "lxml")

        balls = soup.find_all("font")

        temp = []

        for b in balls:
            txt = b.text.strip()

            if txt.isdigit():
                n = int(txt)

                if 1 <= n <= 39:
                    temp.append(n)

                    if len(temp) == 5:
                        all_data.append(sorted(temp))
                        temp = []

    return all_data


# ==============================
# 驗證
# ==============================
def validate_data(history):
    for d in history:
        if len(d) != 5:
            return False
        if any(n < 1 or n > 39 for n in d):
            return False
    return True


# ==============================
# 載入資料
# ==============================
@st.cache_data(ttl=10800)
def load_history():

    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        history = df.values.tolist()
    else:
        history = []

    latest = fetch_latest_pages()
    combined = history + latest

    unique = []
    for d in combined:
        if d not in unique:
            unique.append(d)

    unique = unique[::-1]
    unique = unique[-MAX_HISTORY:]

    pd.DataFrame(unique).to_csv(CSV_PATH, index=False)

    return unique


# ==============================
# 🔥 極端事件分析
# ==============================
def extreme_analysis(history):

    events = []
    gaps = []
    last_index = None

    for i, d in enumerate(history):

        # 👉 極端條件：最小號 >= 21
        if min(d) >= 21:

            events.append(i)

            if last_index is not None:
                gaps.append(i - last_index)

            last_index = i

    prob = len(events) / len(history) if history else 0
    avg_gap = sum(gaps)/len(gaps) if gaps else 0

    # 現在距離上次
    current_gap = len(history) - 1 - last_index if last_index is not None else 0

    return prob, avg_gap, current_gap


# ==============================
# 評分模型（加入極端判斷🔥）
# ==============================
def score_numbers(history, boost_extreme=False):

    short = Counter([n for d in history[-30:] for n in d])
    mid = Counter([n for d in history[-100:] for n in d])
    long = Counter([n for d in history[-500:] for n in d])

    score = {}

    for n in range(1, 40):

        base = short[n]*0.5 + mid[n]*0.3 + long[n]*0.2

        last_seen = 100
        for i, d in enumerate(reversed(history)):
            if n in d:
                last_seen = i
                break

        cold = min(last_seen/50, 1)

        # 🔥 如果要爆冷 → 加強大號
        if boost_extreme and n >= 21:
            bonus = 1.5
        else:
            bonus = 0

        noise = random.uniform(0, 0.3)

        score[n] = base + cold + noise + bonus

    return score


# ==============================
# AI推薦
# ==============================
def valid_combo(c):

    if not (80 <= sum(c) <= 140):
        return False

    if sum(n % 2 for n in c) not in [2, 3]:
        return False

    return True


def ai_recommend(history, boost_extreme=False):

    score = score_numbers(history, boost_extreme)

    combos = set()

    for _ in range(80000):

        c = random.sample(range(1, 40), 5)

        if valid_combo(c):
            combos.add(tuple(sorted(c)))

    combos = list(combos)

    scored = [(c, sum(score[n] for n in c)) for c in combos]
    scored.sort(key=lambda x: x[1], reverse=True)

    picks = random.sample(scored[:25], 3)

    return [list(c) for c, _ in picks]


# ==============================
# 四合
# ==============================
def generate_four_sets(combo):
    return list(combinations(combo, 4))


def analyze_hits(four_sets, history):

    result = []

    for fs in four_sets:

        hit3 = 0
        hit4 = 0

        for d in history:
            m = len(set(fs) & set(d))
            if m == 3: hit3 += 1
            elif m == 4: hit4 += 1

        recent = sum(
            1 for d in history[-5:]
            if len(set(fs) & set(d)) >= 3
        )

        result.append((fs, hit3, hit4, recent))

    return sorted(result, key=lambda x: (x[2], x[1], x[3]), reverse=True)


# ==============================
# UI
# ==============================
st.set_page_config(layout="wide")
st.title("🔥 539 AI V48（極端事件判斷版）")

history = load_history()

if not validate_data(history):
    st.error("❌ 資料錯誤")
    st.stop()

# ==============================
# 極端分析顯示🔥
# ==============================
prob, avg_gap, current_gap = extreme_analysis(history)

st.markdown("## 🧠 極端事件分析（最小號 ≥ 21）")

col1, col2, col3 = st.columns(3)

col1.metric("發生機率", f"{prob*100:.2f}%")
col2.metric("平均間隔", f"{avg_gap:.1f}期")
col3.metric("目前間隔", f"{current_gap}期")

# 判斷狀態
if avg_gap > 0 and current_gap >= avg_gap * 0.9:
    st.error("🔴 高機率區（可能快出現）")
    boost = True
else:
    st.success("🟢 正常區")
    boost = False


# 最新五期
st.markdown("### 📅 最新五期")
cols = st.columns(5)
for i, d in enumerate(history[-5:][::-1]):
    cols[i].metric(f"第{i+1}期", " ".join(f"{x:02d}" for x in d))


# ==============================
# 預測
# ==============================
if st.button("🚀 AI預測"):

    recs = ai_recommend(history, boost)

    st.markdown("## 🎯 AI推薦")

    for r in recs:
        st.success(" ".join(f"{x:02d}" for x in r))

    st.markdown("## 💰 四合策略")

    for r in recs:

        st.markdown(f"### {' '.join(map(str,r))}")

        four_sets = generate_four_sets(r)
        analysis = analyze_hits(four_sets, history)

        for fs, h3, h4, recent in analysis[:3]:
            st.write(
                f"{fs} ｜ 中3:{h3} ｜ 中4:{h4} ｜ 近5:{recent}"
            )