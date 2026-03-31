import random
import streamlit as st
import requests
import re
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter
from sklearn.linear_model import LogisticRegression

st.set_page_config(page_title="539 AI V67 Lite", layout="wide")

# ==============================
# 抓資料
# ==============================
@st.cache_data(ttl=10800)
def load_history():
    target = 800  # 🔥 減少資料量（更快）
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
# 特徵工程（簡化版）
# ==============================
def build_features(history):

    X, Y = [], []

    for i in range(50, len(history)-1):

        past = history[:i]

        freq = Counter([n for d in past[-30:] for n in d])

        row = []

        for n in range(1,40):
            gap = next((j for j,d in enumerate(reversed(past)) if n in d), 50)
            row.extend([freq[n], gap])

        label = [1 if n in history[i] else 0 for n in range(1,40)]

        X.append(row)
        Y.append(label)

    return np.array(X), np.array(Y)

# ==============================
# 🔥 模型（快取）
# ==============================
@st.cache_resource
def train_models(history):

    X, Y = build_features(history)

    models = []

    for i in range(39):
        y = Y[:,i]
        model = LogisticRegression(max_iter=500)
        model.fit(X, y)
        models.append(model)

    return models

# ==============================
# 預測
# ==============================
def predict(models, history):

    freq = Counter([n for d in history[-30:] for n in d])

    row = []

    for n in range(1,40):
        gap = next((j for j,d in enumerate(reversed(history)) if n in d), 50)
        row.extend([freq[n], gap])

    row = np.array(row).reshape(1,-1)

    probs = []

    for m in models:
        p = m.predict_proba(row)[0][1]
        probs.append(p)

    return {i+1:probs[i] for i in range(39)}

# ==============================
# 選號
# ==============================
def pick_numbers(prob):

    nums = np.array(list(prob.keys()))
    vals = np.array(list(prob.values()))
    vals = vals / vals.sum()

    return sorted(np.random.choice(nums,5,replace=False,p=vals))

# ==============================
# UI
# ==============================
st.title("🔥 539 AI V67 Lite（Stream版）")

history = load_history()

# 最新五期
st.subheader("📅 最新五期")
cols = st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].code(" ".join(map(str,d)))

# ==============================
# 執行
# ==============================
if st.button("🚀 AI預測"):

    with st.spinner("AI學習中（只會跑一次）..."):

        models = train_models(history)  # 🔥 只會訓練一次
        prob = predict(models, history)
        pred = pick_numbers(prob)

    # 機率
    st.subheader("📊 機率 Top10")
    top10 = sorted(prob.items(), key=lambda x:x[1], reverse=True)[:10]
    st.write(top10)

    # 推薦
    st.subheader("💰 推薦號碼")
    st.success(" - ".join(f"{n:02d}" for n in pred))

# 重抓
if st.button("🔄 重抓資料"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()