import random
import streamlit as st
import requests
import re
import pandas as pd
import numpy as np
import json
import os
from bs4 import BeautifulSoup
from collections import Counter

st.set_page_config(page_title="539 AI V58 穩定版", layout="wide")

PERF_FILE = "performance.json"
BET_FILE = "last_bet.json"

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
            continue

    return all_data[:target][::-1]

# ==============================
# 工具
# ==============================
def load_json(file):
    if os.path.exists(file):
        return json.load(open(file))
    return []

def save_json(file,data):
    json.dump(data, open(file,"w"), indent=2)

# ==============================
# 條件
# ==============================
def cond_extreme(d): return min(d) >= 21
def cond_big(d): return min(d) >= 20
def cond_tail(d):
    return max(Counter([n%10 for n in d]).values()) >= 3

# ==============================
# 市場判斷
# ==============================
def ai_market_state(history):
    nums = [n for d in history[-10:] for n in d]
    avg = np.mean(nums)

    if avg > 23:
        return "熱盤"
    elif avg < 17:
        return "冷盤"
    else:
        return "均衡盤"

# ==============================
# 權重
# ==============================
def calc_weights(history):

    bias = {k:{i:0 for i in range(1,40)} for k in ["extreme","big","tail"]}
    count = {"extreme":0,"big":0,"tail":0}
    total = len(history)

    for i in range(len(history)-1):

        decay = (i/total)**2
        curr = history[i]
        nxt = history[i+1]

        if cond_extreme(curr):
            count["extreme"] += decay
            for n in nxt: bias["extreme"][n] += decay

        if cond_big(curr):
            count["big"] += decay
            for n in nxt: bias["big"][n] += decay

        if cond_tail(curr):
            count["tail"] += decay
            for n in nxt: bias["tail"][n] += decay

    avg = 5/39
    for k in bias:
        if count[k] > 0:
            for n in range(1,40):
                bias[k][n] = (bias[k][n]/count[k]) - avg

    return bias

# ==============================
# 評分
# ==============================
def score_numbers(history, bias, market):

    short = Counter([n for d in history[-30:] for n in d])
    scores = {}

    for n in range(1,40):

        base = short[n]
        gap = next((i for i,d in enumerate(reversed(history)) if n in d),50)
        ai = sum(bias[k][n]*20 for k in bias)

        if market == "熱盤":
            base *= 0.8
            gap *= 1.2
        elif market == "冷盤":
            base *= 1.2

        scores[n] = max(0.1, base + gap/20 + ai + random.uniform(0,0.3))

    return scores

# ==============================
# 選號
# ==============================
def pick_numbers(history, bias, market):

    scores = score_numbers(history, bias, market)

    nums = np.array(list(scores.keys()))
    vals = np.array(list(scores.values()))
    probs = vals / vals.sum()

    picks = []

    for _ in range(1000):
        c = sorted([int(x) for x in np.random.choice(nums,5,replace=False,p=probs)])
        if c not in picks:
            picks.append(c)
        if len(picks) >= 3:
            break

    return picks

# ==============================
# 投資組合
# ==============================
def build_bets(picks):

    all_nums = sum(picks, [])
    cnt = Counter(all_nums)

    core = [n for n,c in cnt.items() if c>=2]

    def build(base):
        s=set(core)
        for n in base:
            if len(s)>=5: break
            s.add(n)
        while len(s)<5:
            s.add(random.randint(1,39))
        return sorted(s)

    return build(picks[0]), build(picks[1])

# ==============================
# 評估
# ==============================
def evaluate(bets, draw):
    res = []
    for b in bets:
        hit = len(set(b) & set(draw))
        res.append({
            "下注": b,
            "開獎": draw,
            "命中": hit,
            "誤差": 5-hit
        })
    return res

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V58（穩定驗證版）")

history = load_history()
bias = calc_weights(history)
market = ai_market_state(history)

st.write(f"📊 市場狀態：{market}")
st.write(f"📦 資料期數：{len(history)}")

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(f"{x:02d}" for x in d))

# ==============================
# 產生預測
# ==============================
if st.button("🚀 產生 AI 投資組合"):

    picks = pick_numbers(history, bias, market)
    bet1, bet2 = build_bets(picks)

    st.subheader("💰 本期投注")
    st.success(" ".join(map(str,bet1)))
    st.success(" ".join(map(str,bet2)))

    # 🔥 存下注（含期數）
    save_json(BET_FILE, {
        "bets":[bet1,bet2],
        "index": len(history)
    })

# ==============================
# 🔥 自動驗證（核心）
# ==============================
if os.path.exists(BET_FILE):

    bet_data = load_json(BET_FILE)

    if bet_data:

        bet_index = bet_data["index"]

        if len(history) > bet_index:

            next_draw = history[bet_index]

            result = evaluate(bet_data["bets"], next_draw)

            perf = load_json(PERF_FILE)
            perf.extend(result)
            save_json(PERF_FILE, perf)

            os.remove(BET_FILE)

            st.success("✅ 已完成『下一期驗證』")

# ==============================
# 績效
# ==============================
perf = load_json(PERF_FILE)

if perf:
    df = pd.DataFrame(perf)

    st.subheader("📊 投資績效")
    st.dataframe(df.tail(20))

    st.metric("平均命中", f"{df['命中'].mean():.2f}")

# ==============================
# 重抓
# ==============================
if st.button("🔄 重抓資料"):
    st.cache_data.clear()
    st.rerun()