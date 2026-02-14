import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# ==========================================
# Gauss V6 Engine
# ==========================================
class GaussV6Engine:

    @staticmethod
    def calculate_ac_value(nums):
        differences = set()
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                differences.add(abs(nums[i] - nums[j]))
        return len(differences) - (len(nums) - 1)

    @staticmethod
    def count_consecutive_groups(nums):
        groups = 0
        nums = sorted(nums)
        i = 0
        while i < len(nums) - 1:
            if nums[i] + 1 == nums[i+1]:
                groups += 1
                while i < len(nums) - 1 and nums[i] + 1 == nums[i+1]:
                    i += 1
            else:
                i += 1
        return groups

    @staticmethod
    def analyze_full_history_collision(combo, history_rows):
        target = set(combo)
        max_hit = 0
        hit_counts = Counter()
        for row in history_rows:
            hit = len(target & set(row))
            if hit > 0:
                hit_counts[hit] += 1
            max_hit = max(max_hit, hit)
        return max_hit, dict(hit_counts)

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="Gauss Master Pro V6", layout="wide")
st.title("💎 Gauss Master Pro V6")

game_type = st.sidebar.selectbox("選擇遊戲", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num, pick_count, ac_threshold = 39, 5, 5
else:
    max_num, pick_count, ac_threshold = 49, 6, 7

uploaded_file = st.file_uploader("上傳歷史 Excel", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
    history_rows = []
    all_nums = []

    for val in df.iloc[:, 1].dropna().astype(str):
        clean = val.replace(' ', ',').replace('，', ',')
        nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
        if len(nums) == pick_count:
            history_rows.append(nums)
            all_nums.extend(nums)

    if not history_rows:
        st.error("歷史資料錯誤")
        st.stop()

    sums = [sum(r) for r in history_rows]
    mean_v = np.mean(sums)
    std_v = np.std(sums)

    st.write(f"歷史均值 μ = {mean_v:.1f}")
    st.write(f"標準差 σ = {std_v:.1f}")

    conf_level = st.sidebar.slider("高斯信心區間 σ", 0.5, 2.0, 1.0)

    if st.button("🚀 啟動 8000 次完整模擬"):

        t_min = mean_v - std_v * conf_level
        t_max = mean_v + std_v * conf_level

        counts = Counter(all_nums)

        # 🔥 冷號補償權重
        weights = [1 / (counts.get(i, 0) + 1) for i in range(1, max_num+1)]
        num_range = list(range(1, max_num+1))

        last_draw = set(history_rows[0])
        candidate_pool = []

        with st.spinner("V6 正在完整模擬 8000 次..."):

            for _ in range(8000):

                res = sorted(random.choices(num_range, weights=weights, k=pick_count))
                if len(set(res)) != pick_count:
                    continue

                s = sum(res)
                ac = GaussV6Engine.calculate_ac_value(res)
                consec = GaussV6Engine.count_consecutive_groups(res)

                if (
                    t_min <= s <= t_max
                    and ac >= ac_threshold
                    and consec <= 2
                    and len(set(res) & last_draw) <= 2
                ):
                    max_hit, hit_dist = GaussV6Engine.analyze_full_history_collision(res, history_rows)

                    # 排序依據存入
                    candidate_pool.append({
                        "combo": res,
                        "sum_diff": abs(s - mean_v),
                        "ac": ac,
                        "max_hit": max_hit,
                        "hit_dist": hit_dist
                    })

        if not candidate_pool:
            st.warning("找不到符合條件組合")
            st.stop()

        # 🔥 排序邏輯
        candidate_pool.sort(
            key=lambda x: (
                -x["max_hit"],      # 歷史最高命中碼優先
                -x["ac"],           # AC值高優先
                x["sum_diff"]       # 越接近均值越好
            )
        )

        top5 = candidate_pool[:5]

        st.subheader("🎯 V6 最終推薦 Top 5")

        for idx, item in enumerate(top5, 1):
            combo = item["combo"]
            with st.expander(f"組 {idx}: {combo}", expanded=True):
                st.write(f"總和: {sum(combo)}")
                st.write(f"AC值: {item['ac']}")
                st.write(f"歷史最高命中: {item['max_hit']} 碼")
                st.write(f"命中分布: {item['hit_dist']}")

        report = f"{game_type} Gauss V6 分析報告\n"
        report += f"生成時間: {datetime.now()}\n\n"

        for idx, item in enumerate(top5, 1):
            report += f"組 {idx}: {item['combo']}\n"
            report += f"  歷史最高命中: {item['max_hit']} 碼\n"
            report += f"  AC: {item['ac']}\n\n"

        st.download_button(
            "📥 下載報告",
            report,
            file_name=f"{game_type}_GaussV6.txt"
        )