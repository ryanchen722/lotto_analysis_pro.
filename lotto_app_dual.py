import random
import streamlit as st
import requests
import re
import numpy as np
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(page_title="539 AI V62 三策略版", layout="wide")

# ==============================
# 抓資料
# ==============================
@st.cache_data(ttl=10800)
def load_history():
    target = 1770
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
# 🧠 盤勢分類
# ==============================
def classify(draw):
    avg = np.mean(draw)
    tails = [n % 10 for n in draw]
    if avg < 18:
        return "冷盤"
    elif avg > 23:
        return "熱盤"
    elif max(Counter(tails).values()) >= 3:
        return "爆發盤"
    else:
        return "均衡盤"

# ==============================
# 🧠 建立轉移機率
# ==============================
def build_transition(history):
    trans = {"冷盤":Counter(),"熱盤":Counter(),"均衡盤":Counter(),"爆發盤":Counter()}
    for i in range(len(history)-1):
        state = classify(history[i])
        for n in history[i+1]:
            trans[state][n] += 1

    probs = {}
    for s in trans:
        total = sum(trans[s].values())
        if total == 0: continue
        probs[s] = {n:trans[s][n]/total for n in range(1,40)}
    return probs

# ==============================
# 🏆 策略1：轉移機率
# ==============================
def strategy_trend(history, probs):
    state = classify(history[-1])
    base = probs.get(state, {n:1/39 for n in range(1,40)})

    nums = np.array(list(base.keys()))
    vals = np.array(list(base.values()))
    p = vals/vals.sum()

    return sorted(np.random.choice(nums,5,replace=False,p=p))

# ==============================
# ⚖️ 策略2：區間補償
# ==============================
def strategy_zone(history):
    last = history[-1]

    small = [n for n in range(1,14)]
    mid = [n for n in range(14,27)]
    big = [n for n in range(27,40)]

    count = {
        "small":sum(1 for n in last if n in small),
        "mid":sum(1 for n in last if n in mid),
        "big":sum(1 for n in last if n in big)
    }

    picks = []

    if count["small"] == 0:
        picks += random.sample(small,2)
    if count["mid"] == 0:
        picks += random.sample(mid,2)
    if count["big"] == 0:
        picks += random.sample(big,2)

    while len(picks) < 5:
        picks.append(random.randint(1,39))

    return sorted(set(picks))[:5]

# ==============================
# 🎲 策略3：冷門反彈
# ==============================
def strategy_cold(history):
    last50 = history[-50:]
    freq = Counter([n for d in last50 for n in d])

    cold = sorted(range(1,40), key=lambda x: freq[x])[:15]

    return sorted(random.sample(cold,5))

# ==============================
# 🎯 投資組合
# ==============================
def build_bets(s1,s2,s3):
    all_nums = s1+s2+s3
    cnt = Counter(all_nums)

    core = [n for n,c in cnt.items() if c>=2]

    def make(base):
        s=set(core)
        for n in base:
            if len(s)>=5: break
            s.add(n)
        while len(s)<5:
            s.add(random.randint(1,39))
        return sorted(s)

    return make(s1), make(s2)

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V62（三策略系統）")

history = load_history()
probs = build_transition(history)

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(map(str,d)))

# 顯示盤勢
state = classify(history[-1])
st.info(f"📊 當前盤勢：{state}")

# 預測
if st.button("🚀 啟動三策略預測"):

    s1 = strategy_trend(history, probs)
    s2 = strategy_zone(history)
    s3 = strategy_cold(history)

    st.subheader("🧠 三策略分析")

    col1,col2,col3 = st.columns(3)

    col1.success(f"🏆 趨勢策略：{' - '.join(map(str,s1))}")
    col2.success(f"⚖️ 區間補償：{' - '.join(map(str,s2))}")
    col3.success(f"🎲 冷門反彈：{' - '.join(map(str,s3))}")

    # 投資組合
    b1,b2 = build_bets(s1,s2,s3)

    st.subheader("💰 最佳投注組合")
    st.success(f"第1注：{' - '.join(map(str,b1))}")
    st.success(f"第2注：{' - '.join(map(str,b2))}")

# 重抓
if st.button("🔄 重抓資料"):
    st.cache_data.clear()
    st.rerun()