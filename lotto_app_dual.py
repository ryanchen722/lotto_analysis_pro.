import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# ==========================================
# Gauss Research Engine V6.3 (Ultimate Edition)
# ==========================================
class GaussResearchEngine:

    @staticmethod
    def calculate_ac_value(nums):
        """計算 AC 值：衡量號碼組合的複雜度"""
        diffs = set()
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                diffs.add(abs(nums[i] - nums[j]))
        return len(diffs) - (len(nums) - 1)

    @staticmethod
    def count_consecutive_groups(nums):
        """計算連號組數"""
        nums = sorted(nums)
        groups = 0
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
    def get_detailed_comparison(combo, history):
        """深度比對：計算歷史命中分佈"""
        target = set(combo)
        stats = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        max_hit = 0
        for row in history:
            hit = len(target & set(row))
            if hit in stats:
                stats[hit] += 1
            if hit > max_hit:
                max_hit = hit
        return stats, max_hit

    @staticmethod
    def get_zone_dist(nums, max_num):
        """三分區分佈"""
        z1 = len([n for n in nums if n <= max_num // 3])
        z2 = len([n for n in nums if max_num // 3 < n <= (max_num // 3) * 2])
        z3 = len([n for n in nums if n > (max_num // 3) * 2])
        return f"{z1}:{z2}:{z3}"

# ==========================================
# UI Configuration
# ==========================================
st.set_page_config(page_title="Gauss Master Pro V6.3", layout="wide", page_icon="💎")
st.title("💎 Gauss Master Pro V6.3 - 旗艦研究版")
st.markdown("---")

# 側邊欄參數設定
st.sidebar.header("🛠 模擬與研究參數")
game_type = st.sidebar.selectbox("選擇遊戲模式", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num, pick_count, ac_threshold = 39, 5, 6
else:
    max_num, pick_count, ac_threshold = 49, 6, 8

hot_mode = st.sidebar.select_slider(
    "權重偏好 (冷熱補償)",
    options=["極冷", "偏冷", "平衡", "偏熱", "極熱"],
    value="平衡"
)

max_collision_limit = st.sidebar.slider("允許歷史最大重複碼數", 1, pick_count, pick_count-1)

uploaded_file = st.file_uploader("📂 上傳歷史 Excel 數據", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        history = []
        all_nums = []

        # 數據解析與清洗
        for val in df.iloc[:, 1].dropna().astype(str):
            clean = val.replace(' ', ',').replace('，', ',').replace('、', ',')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            if len(nums) == pick_count:
                history.append(nums)
                all_nums.extend(nums)

        if not history:
            st.error("讀取失敗，請檢查 Excel 第二欄格式是否正確。")
            st.stop()

        # 顯示最近 30 期掃描
        st.subheader(f"🕵️ 最近 30 期開獎走勢 ({game_type})")
        recent_30 = []
        for i in range(min(30, len(history))):
            row = history[i]
            recent_30.append({
                "期數": f"前 {i+1} 期",
                "號碼": str(row),
                "總和": sum(row),
                "AC值": GaussResearchEngine.calculate_ac_value(row),
                "連號": GaussResearchEngine.count_consecutive_groups(row)
            })
        st.table(pd.DataFrame(recent_30))
        st.markdown("---")

        # 歷史全局統計看板
        sums = [sum(r) for r in history]
        avg_sum = np.mean(sums)
        counts = Counter(all_nums)
        
        st.subheader("📊 歷史大數據特徵")
        k1, k2, k3 = st.columns(3)
        k1.metric("總歷史期數", f"{len(history)}")
        k2.metric("總和平均值", f"{avg_sum:.1f}")
        k3.metric("樣本範圍", f"{min(sums)} - {max(sums)}")

        # 計算生成權重
        num_range = list(range(1, max_num + 1))
        weights = []
        for i in num_range:
            freq = counts.get(i, 0)
            if hot_mode == "極熱": w = freq ** 2 + 1
            elif hot_mode == "偏熱": w = freq + 1
            elif hot_mode == "偏冷": w = 1 / (freq + 1)
            elif hot_mode == "極冷": w = 1 / (freq ** 2 + 1)
            else: w = 1
            weights.append(w)

        if st.button(f"🚀 啟動 15,000 次深度比對模擬"):
            candidate_pool = []
            with st.spinner("AI 正在遍歷歷史碰撞數據並計算結構規律..."):
                for _ in range(15000):
                    res = sorted(random.choices(num_range, weights=weights, k=pick_count))
                    if len(set(res)) != pick_count: continue

                    s = sum(res)
                    ac = GaussResearchEngine.calculate_ac_value(res)
                    consec = GaussResearchEngine.count_consecutive_groups(res)

                    # 篩選邏輯
                    if abs(s - avg_sum) < 35 and ac >= ac_threshold and consec <= 1:
                        stats, max_hit = GaussResearchEngine.get_detailed_comparison(res, history)
                        
                        if max_hit <= max_collision_limit:
                            candidate_pool.append({
                                "combo": res,
                                "sum": s,
                                "ac": ac,
                                "consec": consec,
                                "max_hit": max_hit,
                                "stats": stats,
                                "zones": GaussResearchEngine.get_zone_dist(res, max_num)
                            })
                            if len(candidate_pool) >= 10: break

            if not candidate_pool:
                st.warning("找不到符合條件組合。請嘗試增加『允許最大重複碼數』或調整權重。")
            else:
                st.subheader("🎯 高斯旗艦版推薦組合")
                
                # 初始化報告內容
                report_txt = f"Gauss Master Pro V6.3 旗艦研究報告\n"
                report_txt += f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                report_txt += f"遊戲類型: {game_type} | 權重模式: {hot_mode}\n"
                report_txt += f"歷史參考期數: {len(history)} 期\n"
                report_txt += "="*50 + "\n\n"

                for idx, item in enumerate(candidate_pool, 1):
                    combo_str = " , ".join(map(str, item['combo']))
                    with st.expander(f"推薦組合 {idx}: {item['combo']} (歷史最高: {item['max_hit']} 碼)", expanded=True):
                        c1, c2, c3 = st.columns(3)
                        c1.write(f"🔢 總和: **{item['sum']}**")
                        c2.write(f"📉 AC 值: **{item['ac']}**")
                        c3.write(f"🌍 分區: **{item['zones']}**")
                        
                        # 比對數據表
                        s = item['stats']
                        comp_df = pd.DataFrame({
                            "命中碼數": ["中 1 碼", "中 2 碼", "中 3 碼", f"中 {max_collision_limit} 碼"],
                            "歷史次數": [s[1], s[2], s[3], s[max_collision_limit]]
                        })
                        st.table(comp_df)

                    # 加入報告
                    report_txt += f"【推薦組合 {idx}】: {item['combo']}\n"
                    report_txt += f" - 結構參數: 總和={item['sum']}, AC值={item['ac']}, 分區={item['zones']}\n"
                    report_txt += f" - 歷史實戰: 最高命中 {item['max_hit']} 碼\n"
                    report_txt += f" - 碰撞詳情: 中1碼({s[1]}次), 中2碼({s[2]}次), 中3碼({s[3]}次)\n"
                    report_txt += "-"*30 + "\n"

                st.markdown("---")
                # 下載報告按鈕
                st.download_button(
                    label="📥 下載完整分析報告 (.txt)",
                    data=report_txt,
                    file_name=f"{game_type}_Gauss_V6_3_Report.txt",
                    mime="text/plain",
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"分析出錯: {e}")
else:
    st.info("💡 請上傳歷史 Excel 資料夾以啟動研究。建議包含『日期』與『號碼』兩欄。")

st.markdown("---")
st.caption("Gauss Master Pro V6.3 | 歷史深度碰撞回測 | 自動報告生成 | 專業統計模型")

