import random
import streamlit as st
import requests
import re
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
# 抓資料（穩定版）
# ==============================
def fetch_latest_pages(pages=3):
    headers = {"User-Agent": "Mozilla/5.0"}
    all_data = []

    for p in range(1, pages+1):
        url = f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={p}"

        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = "big5"

        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.find_all("tr")

        for row in rows:
            nums = re.findall(r'\b\d{1,2}\b', row.text)

            # 只保留1~39
            nums = [int(x) for x in nums if 1 <= int(x) <= 39]

            if len(nums) >= 5:
                draw = sorted(nums[-5:])
                all_data.append(draw)

    return all_data


# ==============================
# 驗證系統🔥
# ==============================
def validate_data(history):

    errors = []

    for i, d in enumerate(history[-50:]):

        if len(d) != 5:
            errors.append(f"第{i}筆數量錯誤: {d}")

        if any(n < 1 or n > 39 for n in d):
            errors.append(f"第{i}筆範圍錯誤: {d}")

    return errors


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

    # 去重
    unique = []
    for d in combined:
        if d not in unique:
            unique.append(d)

    # 清洗
    cleaned = []
    for d in unique:
        if len(d) == 5 and all(1 <= int(x) <= 39 for x in d):
            cleaned.append(sorted([int(x) for x in d]))

    # 新→舊 轉 舊→新
    cleaned = cleaned[::-1]

    # 限制筆數
    cleaned = cleaned[-MAX_HISTORY:]

    pd.DataFrame(cleaned).to_csv(CSV_PATH, index=False)

    return cleaned


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
# 組合過濾
# ==============================
def valid_combo(c):

    c = sorted(c)

    odd = sum(n % 2 for n in c)
    if odd not in [2, 3]:
        return False

    if not any(n <= 13 for n in c): return False
    if not any(14 <= n <= 26 for n in c): return False
    if not any(n >= 27 for n in c): return False

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
st.title("🔥 539 AI 四合策略 V46（驗證版）")

history = load_history()

# ==============================
# 驗證顯示🔥
# ==============================
errors = validate_data(history)

if errors:
    st.error("❌ 資料異常，已停止AI預測")
    for e in errors[:5]:
        st.write(e)
    st.stop()
else:
    st.success("🟢 資料正常，可進行預測")

# 最新5期
st.markdown("### 📅 最新五期")
cols = st.columns(5)

for i, d in enumerate(history[-5:][::-1]):
    cols[i].metric(f"第{i+1}期", " ".join(f"{x:02d}" for x in d))

# Debug
with st.expander("🔍 最近10期資料"):
    st.write(history[-10:])

# ==============================
# 按鈕
# ==============================
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