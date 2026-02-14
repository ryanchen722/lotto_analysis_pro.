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
        """計算 AC 值 (算術複雜度)"""
        differences = set()
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                differences.add(abs(nums[i] - nums[j]))
        return len(differences) - (len(nums) - 1)

    @staticmethod
    def count_consecutive_groups(nums):
        """計算連號組數"""
        groups = 0
        sorted_nums = sorted(nums)
        i = 0
        while i < len(sorted_nums) - 1:
            if sorted_nums[i] + 1 == sorted_nums[i+1]:
                groups += 1
                while i < len(sorted_nums) - 1 and sorted_nums[i] + 1 == sorted_nums[i+1]:
                    i += 1
            else:
                i += 1
        return groups

    @staticmethod
    def analyze_full_history_collision(combo, history_rows):
        """分析全歷史：回傳最高命中碼數與詳細分佈"""
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
st.set_page_config(page_title="Gauss Master Pro V6", page_icon="💎", layout="wide")
st.title("💎 Gauss Master Pro V6")
st.markdown("---")

# 側邊欄設定
st.sidebar.header("🕹️ 遊戲分析模式")
game_type = st.sidebar.selectbox("選擇遊戲", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num, pick_count, ac_threshold = 39, 5, 5
else:
    max_num, pick_count, ac_threshold = 49, 6, 7

uploaded_file = st.file_uploader("📂 上傳歷史數據 Excel", type=["xlsx"])

if uploaded_file:
    try:
        # 1. 讀取數據
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        history_rows = []
        all_nums = []

        for val in df.iloc[:, 1].dropna().astype(str):
            # 兼容不同分隔符號
            clean = val.replace(' ', ',').replace('，', ',').replace('?', '')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            if len(nums) == pick_count:
                history_rows.append(nums)
                all_nums.extend(nums)

        if not history_rows:
            st.error("❌ 無法提取有效的歷史紀錄，請檢查 Excel 格式。")
            st.stop()

        # 2. 顯示最近 30 期歷史掃描 (使用者要求)
        st.subheader(f"🕵️ 最近 30 期歷史開獎掃描 ({game_type})")
        recent_data = []
        for i in range(min(30, len(history_rows))):
            row = history_rows[i]
            recent_data.append({
                "期數": f"前 {i+1} 期",
                "開獎號碼": str(row),
                "總和": sum(row),
                "AC值": GaussV6Engine.calculate_ac_value(row),
                "連號組數": GaussV6Engine.count_consecutive_groups(row)
            })
        st.table(pd.DataFrame(recent_data))
        st.markdown("---")

        # 3. 大數據看板
        sums = [sum(r) for r in history_rows]
        mean_v = np.mean(sums)
        std_v = np.std(sums)
        
        st.subheader("📊 歷史統計規律")
        col1, col2, col3 = st.columns(3)
        col1.metric("歷史均值 μ", f"{mean_v:.1f}")
        col2.metric("標準差 σ", f"{std_v:.1f}")
        col3.metric("總歷史期數", f"{len(history_rows)}")

        conf_level = st.sidebar.slider("高斯信心區間 σ", 0.5, 2.0, 1.0)
        st.sidebar.markdown("---")
        
        # 4. 啟動模擬
        if st.button("🚀 啟動 8000 次 V6 完整模擬"):
            t_min = mean_v - std_v * conf_level
            t_max = mean_v + std_v * conf_level

            counts = Counter(all_nums)
            # 🔥 V6 冷號補償權重
            weights = [1 / (counts.get(i, 0) + 1) for i in range(1, max_num + 1)]
            num_range = list(range(1, max_num + 1))

            last_draw = set(history_rows[0])
            candidate_pool = []

            with st.spinner("AI 正在進行 V6 深度規律碰撞..."):
                for _ in range(8000):
                    res = sorted(random.choices(num_range, weights=weights, k=pick_count))
                    if len(set(res)) != pick_count:
                        continue

                    s = sum(res)
                    ac = GaussV6Engine.calculate_ac_value(res)
                    consec = GaussV6Engine.count_consecutive_groups(res)

                    # V6 複合篩選條件
                    if (t_min <= s <= t_max 
                        and ac >= ac_threshold 
                        and consec <= 2 
                        and len(set(res) & last_draw) <= 2):
                        
                        max_hit, hit_dist = GaussV6Engine.analyze_full_history_collision(res, history_rows)
                        
                        candidate_pool.append({
                            "combo": res,
                            "sum_val": s,
                            "sum_diff": abs(s - mean_v),
                            "ac": ac,
                            "consec": consec,
                            "max_hit": max_hit,
                            "hit_dist": hit_dist
                        })

            if not candidate_pool:
                st.warning("⚠️ 找不到符合高斯規律的組合，請嘗試調大「信心區間」。")
            else:
                # 🔥 V6 核心排序邏輯
                candidate_pool.sort(
                    key=lambda x: (
                        -x["max_hit"],    # 1. 歷史實戰最高命中優先
                        -x["ac"],         # 2. 算術複雜度高優先
                        x["sum_diff"]     # 3. 越接近均值越好
                    )
                )

                top5 = candidate_pool[:5]
                st.subheader("🎯 V6 最終推薦 Top 5 (基於歷史實戰排序)")

                for idx, item in enumerate(top5, 1):
                    combo = item["combo"]
                    with st.expander(f"組別 {idx}：{combo}", expanded=True):
                        c1, c2, c3, c4 = st.columns(4)
                        c1.write(f"🔢 總和: **{item['sum_val']}**")
                        c2.write(f"📉 AC值: **{item['ac']}**")
                        c3.write(f"🔗 連號: **{item['consec']} 組**")
                        c4.write(f"🏆 歷史最高: :red[**{item['max_hit']} 碼**]")
                        
                        st.markdown("**📜 歷史命中分佈：**")
                        dist_cols = st.columns(pick_count)
                        for k in range(1, pick_count + 1):
                            count = item['hit_dist'].get(k, 0)
                            dist_cols[k-1].metric(f"{k}碼", f"{count}次")

                # 生成報告
                report = f"{game_type} Gauss V6 旗艦分析報告\n"
                report += f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                report += f"分析期數: {len(history_rows)} 期\n"
                report += "-"*40 + "\n"
                for idx, item in enumerate(top5, 1):
                    report += f"推薦組 {idx}: {item['combo']}\n"
                    report += f"  - 總和: {item['sum_val']} (偏離均值: {item['sum_diff']:.1f})\n"
                    report += f"  - AC值: {item['ac']}\n"
                    report += f"  - 歷史最高命中: {item['max_hit']} 碼\n\n"

                st.download_button(
                    label="📥 下載 V6 完整報告",
                    data=report,
                    file_name=f"{game_type}_GaussV6_Report.txt",
                    mime="text/plain",
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"數據處理錯誤: {e}")
else:
    st.info("💡 請上傳歷史 Excel 檔案後，系統將自動掃描最近 30 期並準備模擬。")

st.markdown("---")
st.caption("Gauss Master Pro V6 | 冷號補償權重 | 歷史最高命中排序 | 最近30期走勢掃描")

