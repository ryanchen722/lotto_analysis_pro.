import pandas as pd
import numpy as np
import random
from collections import Counter
import streamlit as st

# ==========================================
# Gauss V11 Engine
# ==========================================

class GaussV11Engine:

    @staticmethod
    def calculate_ac_value(nums):
        diffs = set()
        for i in range(len(nums)):
            for j in range(i+1, len(nums)):
                diffs.add(abs(nums[j]-nums[i]))
        return len(diffs) - (len(nums)-1)

    @staticmethod
    def odd_even_ratio(nums):
        odd = sum(n % 2 for n in nums)
        even = len(nums) - odd
        return odd, even

    @staticmethod
    def zone_distribution(nums):
        z1 = sum(1 <= n <= 10 for n in nums)
        z2 = sum(11 <= n <= 20 for n in nums)
        z3 = sum(21 <= n <= 30 for n in nums)
        z4 = sum(31 <= n <= 40 for n in nums)
        z5 = sum(n >= 41 for n in nums)
        zones = [z1,z2,z3,z4,z5]
        return max(zones) <= 3

    @staticmethod
    def tail_distribution(nums):
        tails = [n % 10 for n in nums]
        count = Counter(tails)
        return max(count.values()) <= 2

    @staticmethod
    def weighted_choice(numbers, weights):
        total = sum(weights)
        r = random.uniform(0,total)
        upto = 0
        for n,w in zip(numbers,weights):
            if upto + w >= r:
                return n
            upto += w
        return numbers[-1]

    @staticmethod
    def generate_numbers(freq):
        numbers = list(range(1,50))
        weights = [1 + freq.get(n,0)*0.6 for n in numbers]
        result = set()
        while len(result) < 6:
            n = GaussV11Engine.weighted_choice(numbers, weights)
            result.add(n)
        nums = sorted(result)
        # AC
        ac = GaussV11Engine.calculate_ac_value(nums)
        if ac < 3 or ac > 10:
            return None
        # 奇偶
        odd,even = GaussV11Engine.odd_even_ratio(nums)
        if odd < 2 or even < 2:
            return None
        # 區間
        if not GaussV11Engine.zone_distribution(nums):
            return None
        # 尾數
        if not GaussV11Engine.tail_distribution(nums):
            return None
        return nums

# ==========================================
# Streamlit UI
# ==========================================

st.title("Gauss Lottery Engine V11 (兼容 CSV/Excel)")

uploaded = st.file_uploader("上傳歷史資料 CSV 或 Excel", type=["csv","xlsx"])

if uploaded:

    df = None

    # 嘗試讀 CSV
    if uploaded.name.endswith(".csv"):
        try:
            df = pd.read_csv(uploaded)
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded, encoding="utf-8-sig")
        except pd.errors.ParserError:
            df = pd.read_excel(uploaded, header=None)
    else:
        df = pd.read_excel(uploaded, header=None)

    # 將數字整理成列表
    history = []
    for row in df.iloc[:,1:7].values.tolist():
        nums = [int(n) for n in row if pd.notna(n)]
        if len(nums) == 6:
            history.append(nums)

    nums_all = np.array(history).flatten()
    freq = Counter(nums_all)
    history_set = set(tuple(sorted(h)) for h in history)

    st.subheader("歷史號碼頻率")
    st.write(freq)

    # 生成推薦號碼
    results = []
    while len(results) < 10:
        r = GaussV11Engine.generate_numbers(freq)
        if r and tuple(r) not in history_set and r not in results:
            results.append(r)

    st.subheader("推薦號碼")
    for r in results:
        st.write(r)

else:
    st.info("請上傳 CSV 或 Excel 歷史資料")