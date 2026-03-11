import random
import pandas as pd
import streamlit as st
import numpy as np
import re
import itertools
from collections import Counter

# ==========================================
# AC值計算
# ==========================================

def calculate_ac(nums):
    return len(set(abs(a-b) for a,b in itertools.combinations(nums,2))) - 4


# ==========================================
# 結構評分
# ==========================================

def structure_score(nums, history):

    nums = sorted(nums)

    score = 0

    # AC值
    ac = calculate_ac(nums)

    if 4 <= ac <= 8:
        score += 120

    # 跨度
    span = nums[-1] - nums[0]

    if 22 <= span <= 32:
        score += 150
    else:
        score -= abs(span - 27) * 5

    # 奇偶
    odd = sum(n % 2 for n in nums)

    if odd in [2,3]:
        score += 80

    # 連號
    consecutive = sum(1 for i in range(4) if nums[i+1] - nums[i] == 1)

    if consecutive == 1:
        score += 50

    # 尾數群
    tails = [n % 10 for n in nums]

    if len(set(tails)) <= 4:
        score += 40

    # 冷號
    recent = [n for sub in history[:10] for n in sub]

    cold = [n for n in nums if n not in recent]

    score += len(cold) * 20

    return score


# ==========================================
# Monte Carlo 模擬
# ==========================================

def monte_carlo(history, simulations=200000):

    candidates = []

    for _ in range(simulations):

        nums = sorted(random.sample(range(1,40),5))

        score = structure_score(nums, history)

        if score > 200:

            candidates.append((nums,score))

    candidates.sort(key=lambda x:x[1], reverse=True)

    return candidates[:10]


# ==========================================
# UI
# ==========================================

st.set_page_config(page_title="Gauss Master V23", page_icon="🚀", layout="wide")

st.title("🚀 Gauss Master 539 V23")

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

            if st.button("🚀 執行 Monte Carlo 模擬"):

                progress_bar = st.progress(0)

                st.write("模擬運算中...")

                results = monte_carlo(history)

                progress_bar.progress(1.0)

                st.subheader("👑 推薦組合")

                res = []

                for idx,(nums,score) in enumerate(results):

                    res.append({
                        "排名":f"Top {idx+1}",
                        "推薦組合":", ".join([f"{x:02d}" for x in nums]),
                        "和值":sum(nums),
                        "跨度":nums[-1]-nums[0],
                        "AC":calculate_ac(nums),
                        "評分":score
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