import random
import streamlit as st
import requests
import os
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter
from itertools import combinations

# ==============================
# 設定
# ==============================
CSV_PATH = "539_history.csv"
MAX_HISTORY = 1700

# ==============================
# 抓最新資料（修正版🔥）
# ==============================
def fetch_latest():
    headers = {"User-Agent": "Mozilla/5.0"}
    url = "https://www.pilio.idv.tw/lto539/list.asp?indexpage=1"

    r = requests.get(url, headers=headers, timeout=10)
    r.encoding = "big5"
    soup = BeautifulSoup(r.text, "lxml")

    rows = soup.find_all("tr")
    data = []

    for row in rows:
        tds = row.find_all("td")

        if len(tds) < 7:
            continue

        nums = []

        for td in tds:
            txt = td.text.strip()

            if txt.isdigit():
                n = int(txt)
                if 1 <= n <= 39:
                    nums.append(n)

        if len(nums) == 5:
            data.append(sorted(nums))

    return data


# ==============================
# 載入 + 增量更新CSV
# ==============================
@st.cache_data(ttl=43200)
def load_history():

    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        history = df.values.tolist()
    else:
        history = []

    latest = fetch_latest()

    # 合併 + 去重
    combined = history + latest
    unique = []

    for d in combined:
        if d not in unique:
            unique.append(d)

    # 清洗資料（防止污染🔥）
    cleaned = []
    for d in unique:
        if (
            isinstance(d, list)
            and len(d) == 5
            and all(1 <= int(x) <= 39 for x in d)
        ):
            cleaned.append(sorted([int(x) for x in d]))

    # 保留最新1700期
    cleaned = cleaned[-MAX_HISTORY:]

    # 存CSV
    df = pd.DataFrame(cleaned)
    df.to_csv(CSV_PATH, index=False)

    return cleaned


# ==============================
# 評分模型（防固定🔥）
# ==============================
def score_numbers(history):

    short = Counter([n for d in history[-30:] for n in d])
    mid = Counter([n for d in history[-100:] for n in d])
    long = Counter([n for d in history[-500:] for n in d])

    score = {}

    for n in range(1, 40):

        base = short[n]*0.5 + mid[n]*0.3 + long[n]*0.2

        # 冷號補償
        last_seen = 100
        for i, d in enumerate(reversed(history)):
            if n in d:
                last_seen = i
                break

        cold = min(last_seen/50, 1)

        # 隨機擾動（避免固定）
        noise = random.uniform(0, 0.3)

        score[n] = base + cold + noise

    return score


# ==============================
# 組合過濾
# ==============================
def valid_combo(c):

    c = sorted(c)

    # 奇偶
    odd = sum(n % 2 for n in c)
    if odd not in [2, 3]:
        return False

    # 區間
    if not any(n <= 13 for n in c): return False
    if not any(14 <= n <= 26 for n in c): return False
    if not any(n >= 27 for n in c): return False

    # 和值
    if not (80 <= sum(c) <= 140):
        return False

    return True


# ==============================
# AI推薦
# ==============================
def ai_recommend(history):

    score = score_numbers(history)
    combos = set()

    for _ in range(80000):
        c = random.sample(range(1, 40), 5)

        if not valid_combo(c):
            continue

        combos.add(tuple(sorted(c)))

    combos = list(combos)

    scored = [(c, sum(score[n] for n in c)) for c in combos]
    scored.sort(key=lambda x: x[1], reverse=True)

    # 防止每次一樣
    picks = random.sample(scored[:25], 3)

    return [list(c) for c, _ in picks]


# ==============================
# 四合策略
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
st.title("🔥 539 AI 四合策略 V45（穩定版）")

history = load_history()

st.markdown(f"### 📊 資料：{len(history)}期（已優化）")

# 最新5期
st.markdown("### 📅 最新五期")
cols = st.columns(5)

for i, d in enumerate(history[-5:][::-1]):
    cols[i].metric(f"第{i+1}期", " ".join(f"{x:02d}" for x in d))

# Debug（可關掉）
with st.expander("🔍 檢查資料"):
    st.write(history[-10:])

# 按鈕
if st.button("🚀 產生策略"):

    recs = ai_recommend(history)

    st.divider()
    st.markdown("## 🎯 AI推薦號碼")

    for r in recs:
        st.success(" ".join(f"{x:02d}" for x in r))

    st.divider()
    st.markdown("## 💰 四合策略")

    for r in recs:

        st.markdown(f"### 🔹 {' '.join(f'{x:02d}' for x in r)}")

        four_sets = generate_four_sets(r)
        analysis = analyze_hits(four_sets, history)

        for fs, h3, h4, recent in analysis[:3]:
            st.write(
                f"{' '.join(f'{x:02d}' for x in fs)} ｜ "
                f"中3:{h3} ｜ 中4:{h4} ｜ 近5期:{recent}"
            )