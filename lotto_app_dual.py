import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# ==========================================
# Gauss Research Engine V6.4
# ==========================================
class GaussResearchEngine:

    @staticmethod
    def calculate_ac_value(nums):
        diffs = set()
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                diffs.add(abs(nums[i] - nums[j]))
        return len(diffs) - (len(nums) - 1)

    @staticmethod
    def count_consecutive_groups(nums):
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

# ==========================================
# UI Configuration
# ==========================================
st.set_page_config(page_title="Gauss Master Pro V6.4", layout="wide", page_icon="🏆")
st.title("🏆 Gauss Master Pro V6.4 - 終極精選版")
st.markdown("---")

st.sidebar.header("🛠 研究參數")
game_type = st.sidebar.selectbox("遊戲模式", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num, pick_count, ac_threshold = 39, 5, 6
else:
    max_num, pick_count, ac_threshold = 49, 6, 8

hot_mode = st.sidebar.select_slider("權重偏好", options=["極冷", "偏冷", "平衡", "偏熱", "極熱"], value="平衡")
max_collision_limit = st.sidebar.slider("允許歷史最大重複碼數", 1, pick_count, pick_count-1)

uploaded_file = st.file_uploader("📂 上傳歷史 Excel 數據", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        history = []
        all_nums = []

        for val in df.iloc[:, 1].dropna().astype(str):
            clean = val.replace(' ', ',').replace('，', ',').replace('、', ',')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            if len(nums) == pick_count:
                history.append(nums)
                all_nums.extend(nums)

        if not history:
            st.error("讀取失敗，請確認格式。")
            st.stop()

        sums = [sum(r) for r in history]
        avg_sum = np.mean(sums)
        counts = Counter(all_nums)
        
        # 顯示統計看板
        k1, k2, k3 = st.columns(3)
        k1.metric("總期數", f"{len(history)}")
        k2.metric("平均總和", f"{avg_sum:.1f}")
        k3.metric("最近 30 期連號率", f"{(len([r for r in history[:30] if GaussResearchEngine.count_consecutive_groups(r)>0])/30)*100:.1f}%")

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

        if st.button("🚀 啟動終極精選模擬"):
            candidate_pool = []
            with st.spinner("AI 正在從 20,000 次模擬中篩選最優 10 組並進行二次評估..."):
                for _ in range(20000):
                    res = sorted(random.choices(num_range, weights=weights, k=pick_count))
                    if len(set(res)) != pick_count: continue

                    s = sum(res)
                    ac = GaussResearchEngine.calculate_ac_value(res)
                    consec = GaussResearchEngine.count_consecutive_groups(res)

                    if abs(s - avg_sum) < 30 and ac >= ac_threshold and consec <= 1:
                        stats, max_hit = GaussResearchEngine.get_detailed_comparison(res, history)
                        if max_hit <= max_collision_limit:
                            # 綜合評分：AC值越高、總和越接近平均值、歷史重複次數越穩定得分越高
                            score = (ac * 10) - (abs(s - avg_sum) * 0.5) + (stats[2] * 2)
                            candidate_pool.append({
                                "combo": res, "sum": s, "ac": ac, "consec": consec,
                                "max_hit": max_hit, "stats": stats, "score": score
                            })
                            if len(candidate_pool) >= 10: break

            if not candidate_pool:
                st.warning("條件太嚴苛，請放寬限制。")
            else:
                # 按照評分排序，選出最優的一組
                candidate_pool.sort(key=lambda x: x['score'], reverse=True)
                best_one = candidate_pool[0]

                # --- 頂級精選區 ---
                st.markdown("### 🌟 AI 最終黃金精選 (最推薦組合)")
                st.info(f"這組號碼在 AC 複雜度、總和偏離度及歷史穩定度中獲得最高分：{best_one['score']:.1f}")
                
                b1, b2 = st.columns([1, 1])
                with b1:
                    st.markdown(f"## ⭐ `{best_one['combo']}`")
                with b2:
                    st.write(f"🔢 總和：**{best_one['sum']}**")
                    st.write(f"📉 AC 值：**{best_one['ac']}**")
                    st.write(f"🏆 歷史最高：**{best_one['max_hit']} 碼**")

                st.markdown("---")
                st.subheader("📋 其餘候選組合 (Top 2-10)")
                for idx, item in enumerate(candidate_pool[1:], 2):
                    st.write(f"候選 {idx}: {item['combo']} | 總和: {item['sum']} | AC: {item['ac']} | 評分: {item['score']:.1f}")

                # 報告生成
                report_txt = f"Gauss Master Pro V6.4 終極精選報告\n"
                report_txt += f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                report_txt += "="*40 + "\n"
                report_txt += f"【AI 第一推薦】: {best_one['combo']}\n"
                report_txt += f"參數: 總和={best_one['sum']}, AC={best_one['ac']}, 歷史最高={best_one['max_hit']}碼\n"
                report_txt += f"歷史命中分布: 中1({best_one['stats'][1]}次), 中2({best_one['stats'][2]}次), 中3({best_one['stats'][3]}次)\n"
                report_txt += "="*40 + "\n\n"
                for idx, item in enumerate(candidate_pool[1:], 2):
                    report_txt += f"候選 {idx}: {item['combo']} (評分: {item['score']:.1f})\n"

                st.download_button(
                    label="📥 下載完整精選報告",
                    data=report_txt,
                    file_name=f"{game_type}_Gauss_Final_Choice.txt",
                    mime="text/plain",
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"分析錯誤: {e}")
else:
    st.info("💡 請上傳歷史數據啟動終極精選邏輯。")

