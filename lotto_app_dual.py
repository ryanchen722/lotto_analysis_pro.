import pandas as pd
import numpy as np
import random
from collections import Counter
import streamlit as st

# ==========================================
# Gauss V11 Engine
# ==========================================

class GaussV11Engine:

    # AC值
    @staticmethod
    def calculate_ac_value(nums):
        diffs = set()
        for i in range(len(nums)):
            for j in range(i+1, len(nums)):
                diffs.add(abs(nums[j] - nums[i]))
        return len(diffs) - (len(nums) - 1)

    # 奇偶比例
    @staticmethod
    def odd_even_ratio(nums):
        odd = sum(n % 2 for n in nums)
        even = len(nums) - odd
        return odd, even

    # 區間分布
    @staticmethod
    def zone_distribution(nums):

        z1 = sum(1 for n in nums if n <= 10)
        z2 = sum(1 for n in nums if 11 <= n <= 20)
        z3 = sum(1 for n in nums if 21 <= n <= 30)
        z4 = sum(1 for n in nums if 31 <= n <= 40)
        z5 = sum(1 for n in nums if n >= 41)

        zones = [z1,z2,z3,z4,z5]

        if max(zones) > 3:
            return False

        return True

    # 尾數分布
    @staticmethod
    def tail_distribution(nums):

        tails = [n % 10 for n in nums]

        count = Counter(tails)

        if max(count.values()) > 2:
            return False

        return True

    # 權重抽樣
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

    # 生成號碼
    @staticmethod
    def generate_numbers(freq):

        numbers = list(range(1,50))

        weights = []

        for n in numbers:

            hot = freq.get(n,0)

            # 冷號補償
            w = 1 + hot*0.6

            weights.append(w)

        result = set()

        while len(result) < 6:

            n = GaussV11Engine.weighted_choice(numbers,weights)

            result.add(n)

        nums = sorted(result)

        # AC值
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
# Streamlit
# ==========================================

st.title("Gauss Lottery Engine V11")

uploaded = st.file_uploader("上傳歷史開獎 CSV")

if uploaded:

    df = pd.read_csv(uploaded)

    history = df.iloc[:,1:7].values.tolist()

    nums = np.array(history).flatten()

    freq = Counter(nums)

    history_set = set(tuple(sorted(h)) for h in history)

    results = []

    while len(results) < 10:

        r = GaussV11Engine.generate_numbers(freq)

        if r and tuple(r) not in history_set and r not in results:

            results.append(r)

    st.subheader("推薦號碼")

    for r in results:
        st.write(r)