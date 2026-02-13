import random
import numpy as np
import streamlit as st
from datetime import datetime

# ==========================================
# 風險控制引擎
# ==========================================

class CrowdAvoidanceEngine:

    @staticmethod
    def number_risk(n, max_num):
        risk = 0

        # 生日區風險
        if n <= 31:
            risk += 2

        # 熱門數字
        if n in [6, 8, 9, 18, 28]:
            risk += 2

        # 對稱數
        if n in [11, 22, 33]:
            risk += 1.5

        # 太整齊的十位數
        if n % 10 == 0:
            risk += 1

        # 高號區給負風險（加分）
        if n > max_num * 0.7:
            risk -= 1

        return risk

    @staticmethod
    def combo_risk(combo, max_num):
        risk = sum(CrowdAvoidanceEngine.number_risk(n, max_num)
                   for n in combo)

        # 連號懲罰
        combo_sorted = sorted(combo)
        for i in range(len(combo_sorted)-1):
            if combo_sorted[i] + 1 == combo_sorted[i+1]:
                risk += 2

        # 全奇或全偶懲罰
        evens = sum(n%2==0 for n in combo)
        if evens == 0 or evens == len(combo):
            risk += 2

        return risk


# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Low Collision Optimizer", layout="centered")

st.title("💎 真優化選號器 — 低撞號風險模型")

game_type = st.selectbox("選擇遊戲", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num = 39
    pick_count = 5
else:
    max_num = 49
    pick_count = 6

if st.button("🚀 產生 50000 組並找最低撞號風險"):

    best_combo = None
    lowest_risk = float("inf")

    with st.spinner("計算中..."):
        for _ in range(50000):
            combo = sorted(random.sample(range(1, max_num+1), pick_count))
            risk = CrowdAvoidanceEngine.combo_risk(combo, max_num)

            if risk < lowest_risk:
                lowest_risk = risk
                best_combo = combo

    st.success("完成")
    st.markdown(f"## 🎯 推薦號碼：{best_combo}")
    st.metric("撞號風險分數", f"{lowest_risk:.2f}")

    report = f"""
真優化報告
時間: {datetime.now()}
遊戲: {game_type}
推薦號碼: {best_combo}
撞號風險: {lowest_risk}
"""

    st.download_button("下載報告",
                       report,
                       file_name="low_collision_report.txt")