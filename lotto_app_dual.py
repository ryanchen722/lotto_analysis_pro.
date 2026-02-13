import random
import streamlit as st
from datetime import datetime

# ==========================================
# 風險控制引擎
# ==========================================
class CrowdAvoidanceEngine:

    @staticmethod
    def number_risk(n, max_num):
        """單個數字風險評分"""
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
        # 十位數整齊懲罰
        if n % 10 == 0:
            risk += 1
        # 高號區加分（低撞號）
        if n > max_num * 0.7:
            risk -= 1
        return risk

    @staticmethod
    def combo_risk(combo, max_num):
        """整組號碼風險評分"""
        risk = sum(CrowdAvoidanceEngine.number_risk(n, max_num)
                   for n in combo)

        # 連號懲罰
        combo_sorted = sorted(combo)
        for i in range(len(combo_sorted) - 1):
            if combo_sorted[i] + 1 == combo_sorted[i + 1]:
                risk += 2

        # 全奇或全偶懲罰
        evens = sum(n % 2 == 0 for n in combo)
        if evens == 0 or evens == len(combo):
            risk += 2

        return risk

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="低撞號優化選號器", layout="centered")
st.title("💎 真優化選號器 — 低撞號風險模型 (5 組候選)")

# 遊戲類型選擇
game_type = st.selectbox("選擇遊戲", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num = 39
    pick_count = 5
else:
    max_num = 49
    pick_count = 6

# 模擬生成號碼
if st.button("🚀 產生 5 組最低撞號風險組合"):
    candidates = []

    with st.spinner("計算中..."):
        # 生成 50000 組候選
        for _ in range(50000):
            nums_pool = list(range(1, max_num + 1))
            random.shuffle(nums_pool)
            combo = sorted(random.sample(nums_pool, pick_count))
            risk = CrowdAvoidanceEngine.combo_risk(combo, max_num)
            candidates.append((combo, risk))

        # 按風險排序，取前 5 組
        top5 = sorted(candidates, key=lambda x: x[1])[:5]

    st.success("完成！")
    st.subheader("🎯 5 組推薦號碼")
    for idx, (combo, risk) in enumerate(top5, 1):
        st.markdown(f"**組 {idx}:** {combo}  | 風險分數: {risk:.2f}")

    # 匯出報告
    report_lines = [f"真優化報告 - {datetime.now()}", f"遊戲: {game_type}", ""]
    for idx, (combo, risk) in enumerate(top5, 1):
        report_lines.append(f"組 {idx}: {combo} 風險分數: {risk:.2f}")
    report_text = "\n".join(report_lines)

    st.download_button("📥 下載報告",
                       report_text,
                       file_name=f"{game_type}_low_collision_top5.txt")