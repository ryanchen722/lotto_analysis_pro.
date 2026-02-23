import random
import streamlit as st
from datetime import datetime

# ==========================================
# 純隨機獨立事件選號器
# ==========================================

def generate_random_combo(max_num, pick_count):
    """產生一組完全隨機、不重複號碼"""
    return sorted(random.sample(range(1, max_num + 1), pick_count))

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="獨立事件隨機選號器", page_icon="🎲", layout="centered")
st.title("🎲 樂透純隨機選號器（獨立事件版）")
st.markdown("每一組號碼機率完全相同，無任何歷史推測。")

# 遊戲選擇
game_type = st.selectbox("選擇遊戲", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num = 39
    pick_count = 5
else:
    max_num = 49
    pick_count = 6

num_sets = st.slider("產生幾組號碼", 1, 10, 5)

if st.button("🎯 產生隨機號碼"):

    st.subheader("隨機產生結果")

    results = []
    for i in range(num_sets):
        combo = generate_random_combo(max_num, pick_count)
        results.append(combo)
        st.write(f"組 {i+1}: {combo}")

    # 生成下載報告
    report = f"{game_type} 純隨機選號報告\n"
    report += f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for i, combo in enumerate(results, 1):
        report += f"組 {i}: {combo}\n"

    st.download_button(
        label="📥 下載結果",
        data=report,
        file_name=f"{game_type}_Random_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

st.markdown("---")
st.caption("Independent Random Generator | 每組機率完全相同")