import random
import streamlit as st
from datetime import datetime

# ==========================================
# 反人性隨機選號器
# ==========================================

def calculate_ac(nums):
    diffs = set()
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    return len(diffs) - (len(nums) - 1)

def has_long_consecutive(nums):
    nums = sorted(nums)
    count = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i-1] + 1:
            count += 1
            if count >= 3:
                return True
        else:
            count = 1
    return False

def generate_smart_random(max_num, pick_count):

    while True:
        combo = sorted(random.sample(range(1, max_num+1), pick_count))

        # 1️⃣ 至少一個 >31
        if max_num >= 39:
            if not any(n > 31 for n in combo):
                continue

        # 2️⃣ 避免3連號
        if has_long_consecutive(combo):
            continue

        # 3️⃣ AC值不要太低
        if calculate_ac(combo) < 2:
            continue

        return combo

# ==========================================
# UI
# ==========================================

st.set_page_config(page_title="反人性隨機選號器", page_icon="🎲", layout="centered")
st.title("🎲 反人性隨機選號器")
st.markdown("不提高中獎機率，但降低分獎風險。")

game_type = st.selectbox("選擇遊戲", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num = 39
    pick_count = 5
else:
    max_num = 49
    pick_count = 6

num_sets = st.slider("產生幾組號碼", 1, 10, 5)

if st.button("🎯 產生反人性號碼"):

    results = []

    for i in range(num_sets):
        combo = generate_smart_random(max_num, pick_count)
        results.append(combo)
        st.write(f"組 {i+1}: {combo}")

    report = f"{game_type} 反人性選號報告\n"
    report += f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for i, combo in enumerate(results, 1):
        report += f"組 {i}: {combo}\n"

    st.download_button(
        "📥 下載結果",
        report,
        file_name=f"{game_type}_AntiPopular_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

st.markdown("---")
st.caption("Anti-Popular Strategy | 機率不變 | 降低分獎風險")