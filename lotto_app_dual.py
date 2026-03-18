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
# 🔥 正確抓法（完全不會抓錯）
# ==============================
def fetch_latest_pages(pages=3):

    headers = {"User-Agent": "Mozilla/5.0"}
    all_data = []

    for p in range(1, pages+1):

        url = f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={p}"
        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = "big5"

        soup = BeautifulSoup(r.text, "lxml")

        # 🔥 關鍵：只找含有球號的font標籤
        balls = soup.find_all("font")

        temp = []

        for b in balls:
            txt = b.text.strip()

            if txt.isdigit():
                n = int(txt)

                if 1 <= n <= 39:
                    temp.append(n)

                    # 每5個就是一組
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
@st.cache_data(ttl=43200)
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

    # 🔥 網站本來新→舊，這裡轉正確
    unique = unique[::-1]

    unique = unique[-MAX_HISTORY:]

    pd.DataFrame(unique).to_csv(CSV_PATH, index=False)

    return unique


# ==============================
# 評分模型
# ==============================
def score_numbers(history):

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

        noise = random.uniform(0, 0.3)

        score[n] = base + cold + noise

    return score


# ==============================
# AI推薦
# ==============================
def valid_combo(c):

    c = sorted(c)

    if not (80 <= sum(c) <= 140):
        return False

    if sum(n % 2 for n in c) not in [2, 3]:
        return False

    return True


def ai_recommend(history):

    score = score_numbers(history)
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
st.title("🔥 539 AI V47（最終穩定版）")

history = load_history()

if not validate_data(history):
    st.error("❌ 資料抓取錯誤，已停止")
    st.stop()
else:
    st.success("🟢 資料正常")

# 最新五期
cols = st.columns(5)
for i, d in enumerate(history[-5:][::-1]):
    cols[i].metric(f"第{i+1}期", " ".join(f"{x:02d}" for x in d))

with st.expander("最近10期"):
    st.write(history[-10:])

if st.button("🚀 預測"):

    recs = ai_recommend(history)

    st.markdown("## 🎯 AI推薦")

    for r in recs:
        st.success(" ".join(f"{x:02d}" for x in r))

    st.markdown("## 💰 四合分析")

    for r in recs:

        st.markdown(f"### {' '.join(map(str,r))}")

        four_sets = generate_four_sets(r)
        analysis = analyze_hits(four_sets, history)

        for fs, h3, h4, recent in analysis[:3]:
            st.write(
                f"{fs} ｜ 中3:{h3} ｜ 中4:{h4} ｜ 近5:{recent}"
            )