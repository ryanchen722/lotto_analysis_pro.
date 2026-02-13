import random
import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 高命中率號碼生成引擎
# ==========================================
class HighHitRateEngine:

    @staticmethod
    def generate_combo(max_num, pick_count, hot_numbers, hot_ratio=0.6):
        """生成一組高命中率號碼"""
        num_hot = max(1, int(pick_count * hot_ratio))
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
st.set_page_config(page_title="高命中率選號器 + 歷史比對", layout="centered")
st.title("🎯 高命中率選號器 + 歷史比對 + 平均中小獎命中率")

# 遊戲選擇
game_type = st.selectbox("選擇遊戲", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num = 39
    pick_count = 5
    hot_numbers = [1,3,5,7,9,11,13,15,17,18,21,23,25,28,31]
else:
    max_num = 49
    pick_count = 6
    hot_numbers = [1,3,7,8,11,13,17,18,21,23,28,31,33,35,37,40,42,45,48]

# 歷史資料上傳
uploaded_file = st.file_uploader(f"上傳 {game_type} 歷史開獎號碼 Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
    history_rows = []
    for val in df.iloc[:, 1].dropna().astype(str):
        clean = val.replace(' ', ',').replace('，', ',').replace('?', '')
        nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
        if len(nums) == pick_count:
            history_rows.append(nums)

    st.success(f"歷史數據讀取完成，共 {len(history_rows)} 期")

    # 生成號碼
    if st.button("🚀 產生 5 組高命中率號碼並比對歷史"):
        top5 = []
        for _ in range(5):
            combo = HighHitRateEngine.generate_combo(max_num, pick_count, hot_numbers)
            
            # 計算歷史命中次數
            match_count = sum(len(set(combo) & set(hist)) for hist in history_rows)
            
            # 計算平均每期中小獎數
            avg_hit_per_draw = sum(len(set(combo) & set(hist)) for hist in history_rows) / len(history_rows)
            
            top5.append((combo, match_count, avg_hit_per_draw))

        st.subheader("🎯 5 組推薦號碼與歷史命中統計")
        for idx, (combo, match_count, avg_hit) in enumerate(top5, 1):
            st.markdown(f"**組 {idx}:** {combo}  | 歷史命中次數: {match_count} | 平均每期命中: {avg_hit:.2f}")

        # 匯出報告
        report_lines = [f"高命中率報告 + 歷史比對 - {datetime.now()}", f"遊戲: {game_type}", ""]
        for idx, (combo, match_count, avg_hit) in enumerate(top5, 1):
            report_lines.append(f"組 {idx}: {combo}  歷史命中次數: {match_count} | 平均每期命中: {avg_hit:.2f}")
        report_text = "\n".join(report_lines)

        st.download_button("📥 下載報告",
                           report_text,
                           file_name=f"{game_type}_high_hit_history_top5.txt")
else:
    st.info("💡 請先上傳歷史開獎 Excel 檔案")