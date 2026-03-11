import random
import pandas as pd
import streamlit as st
import numpy as np
import re
import itertools
from collections import Counter
from sklearn.ensemble import RandomForestClassifier

# ==========================================
# AC值
# ==========================================

def calculate_ac(nums):
    return len(set(abs(a-b) for a,b in itertools.combinations(nums,2))) - 4


# ==========================================
# 特徵工程
# ==========================================

def extract_features(nums):

    nums = sorted(nums)

    odd = sum(n % 2 for n in nums)

    consecutive = sum(1 for i in range(4) if nums[i+1] - nums[i] == 1)

    tails = [n % 10 for n in nums]

    tail_cluster = len(tails) - len(set(tails))

    return [
        sum(nums),
        nums[-1] - nums[0],
        odd,
        5 - odd,
        calculate_ac(nums),
        consecutive,
        tail_cluster
    ]


# ==========================================
# AI模型訓練
# ==========================================

def train_model(history):

    X = []
    y = []

    # 正樣本
    for nums in history:

        X.append(extract_features(nums))

        y.append(1)

    # 負樣本
    for _ in range(len(history) * 3):

        nums = sorted(random.sample(range(1,40),5))

        X.append(extract_features(nums))

        y.append(0)

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        random_state=42
    )

    model.fit(X,y)

    return model


# ==========================================
# AI生成候選組合
# ==========================================

def generate_candidates(model, simulations=200000):

    best = []

    for _ in range(simulations):

        nums = sorted(random.sample(range(1,40),5))

        features = extract_features(nums)

        prob = model.predict_proba([features])[0][1]

        best.append((nums,prob))

    best.sort(key=lambda x:x[1], reverse=True)

    return best[:10]


# ==========================================
# UI 介面
# ==========================================

st.set_page_config(page_title="Gauss Master AI", page_icon="🚀", layout="wide")

st.title("🚀 Gauss Master AI 539")

uploaded_file = st.file_uploader("上傳 539 歷史 Excel", type=["xlsx"])

if uploaded_file:

    try:

        df = pd.read_excel(uploaded_file, header=None)

        history = []

        for _, row in df.iterrows():

            nums = [int(n) for n in re.findall(r'\d+', str(row.values)) if 1 <= int(n) <= 39]

            if len(nums) >= 5:

                history.append(sorted(nums[:5]))

        if history:

            st.markdown(f"### 📅 最新期：`{', '.join([f'{x:02d}' for x in history[0]])}`")

            st.divider()

            if st.button("🚀 執行 AI 模擬"):

                progress_bar = st.progress(0)

                st.write("AI 訓練中...")

                model = train_model(history)

                progress_bar.progress(0.4)

                st.write("AI 模擬生成號碼...")

                results = generate_candidates(model)

                progress_bar.progress(1.0)

                st.subheader("👑 AI 推薦組合")

                res = []

                for idx, (nums, prob) in enumerate(results):

                    res.append({
                        "排名": f"Top {idx+1}",
                        "推薦組合": ", ".join([f"{x:02d}" for x in nums]),
                        "和值": sum(nums),
                        "跨度": nums[-1] - nums[0],
                        "AC": calculate_ac(nums),
                        "AI機率": round(prob,4)
                    })

                st.table(pd.DataFrame(res))

                # 強勢號碼池
                pool_nums = [n for combo,_ in results for n in combo]

                pool = [n for n,_ in Counter(pool_nums).most_common(20)]

                st.markdown(
                    f"📊 **強勢號碼池**：\n`{', '.join([f'{x:02d}' for x in pool])}`"
                )

                st.balloons()

    except Exception as e:

        st.error(f"錯誤: {e}")