import random
import streamlit as st
from datetime import datetime

# ==========================================
# 高命中率號碼生成引擎
# ==========================================
class HighHitRateEngine:

    @staticmethod
    def generate_combo(max_num, pick_count, hot_numbers, hot_ratio=0.6):
        """
        生成一組高命中率號碼
        hot_numbers: 熱門號列表
        hot_ratio: 組合中熱門號比例
        """
        num_hot = max(1, int(pick_count * hot_ratio))  # 至少一個熱門號
        num_other = pick_count - num_hot

        hot_pool = hot_numbers.copy()
        other_pool = [n for n in range(1, max_num + 1) if n not in hot_pool]

        combo = random.sample(hot_pool, min(num_hot, len(hot_pool)))
        combo += random.sample(other_pool, num_other)
        random.shuffle(combo)
        return sorted(combo)

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="高命中率選號器", layout="centered")
st.title("🎯 高命中率選號器 — 天天中小獎版")

# 遊戲類型選擇
game_type = st.selectbox("選擇遊戲", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num = 39
    pick_count = 5
    # 539 常見熱門號
    hot_numbers = [1,3,5,7,9,11,13,15,17,18,21,23,25,28,31]
else:
    max_num = 49
    pick_count = 6
    # 大樂透熱門號
    hot_numbers = [1,3,7,8,11,13,17,18,21,23,28,31,33,35,37,40,42,45,48]

# 生成號碼
if st.button("🚀 產生 5 組高命中率號碼"):
    top5 = []
    for _ in range(5):
        combo = HighHitRateEngine.generate_combo(max_num, pick_count, hot_numbers)
        top5.append(combo)

    st.success("完成！")
    st.subheader("🎯 5 組推薦號碼")
    for idx, combo in enumerate(top5, 1):
        st.markdown(f"**組 {idx}:** {combo}")

    # 匯出報告
    report_lines = [f"高命中率報告 - {datetime.now()}", f"遊戲: {game_type}", ""]
    for idx, combo in enumerate(top5, 1):
        report_lines.append(f"組 {idx}: {combo}")
    report_text = "\n".join(report_lines)

    st.download_button("📥 下載報告",
                       report_text,
                       file_name=f"{game_type}_high_hit_top5.txt")