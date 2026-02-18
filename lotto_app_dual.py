import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# ==========================================
# Gauss Research Engine V6.7.1
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
        """深度比對：計算歷史命中分佈 (核心戰績)"""
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
st.set_page_config(page_title="Gauss Master Pro V6.7.1", layout="wide", page_icon="💎")
st.title("💎 Gauss Master Pro V6.7.1 - 邏輯透明版")
st.markdown("如果您想看到 AC 值較低（如 4）的組合，請調整左側滑桿門檻。")
st.markdown("---")

# 側邊欄設定
st.sidebar.header("⚙️ 核心研究參數")
game_type = st.sidebar.selectbox("遊戲模式", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num, pick_count = 39, 5
    # 將最小值設為 1，方便使用者觀察低 AC 組合
    ac_threshold = st.sidebar.slider("AC 值最小門檻 (調低可看規律號)", 1, 10, 6)
else:
    max_num, pick_count = 49, 6
    ac_threshold = st.sidebar.slider("AC 值最小門檻 (調低可看規律號)", 1, 15, 8)

hot_mode = st.sidebar.select_slider("數字權重偏好", options=["極冷", "偏冷", "平衡", "偏熱", "極熱"], value="平衡")
max_collision_limit = st.sidebar.slider("禁止出現過大獎的組合 (排除歷史命中 > X)", 1, pick_count, pick_count-1)

uploaded_file = st.file_uploader("📂 上傳歷史數據 Excel", type=["xlsx"])

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
            st.error("格式錯誤，請檢查 Excel 資料。")
            st.stop()

        # 最近 30 期深度走勢
        st.subheader(f"🕵️ 最近 30 期開獎數據 ({game_type})")
        recent_data = []
        for i in range(min(30, len(history))):
            row = history[i]
            recent_data.append({
                "期數": f"前 {i+1} 期",
                "號碼組合": " , ".join(map(str, row)),
                "總和": sum(row),
                "AC 值": GaussResearchEngine.calculate_ac_value(row),
                "連號組數": GaussResearchEngine.count_consecutive_groups(row)
            })
        st.table(pd.DataFrame(recent_data))
        st.markdown("---")

        sums = [sum(r) for r in history]
        avg_sum = np.mean(sums)
        counts = Counter(all_nums)
        
        num_range = list(range(1, max_num + 1))
        weights = [counts.get(i, 1) for i in num_range] # 簡化示範權重

        if st.button("🚀 執行精選模擬"):
            candidate_pool = []
            with st.spinner(f"正在搜尋 AC >= {ac_threshold} 的組合..."):
                for _ in range(30000):
                    res = sorted(random.choices(num_range, weights=weights, k=pick_count))
                    if len(set(res)) != pick_count: continue

                    s = sum(res)
                    ac = GaussResearchEngine.calculate_ac_value(res)
                    consec = GaussResearchEngine.count_consecutive_groups(res)

                    # 門檻檢查：如果 ac_threshold 設為 4，則 AC 4, 5, 6... 都會出現
                    if abs(s - avg_sum) < 35 and ac >= ac_threshold and consec <= 2:
                        stats, max_hit = GaussResearchEngine.get_detailed_comparison(res, history)
                        if max_hit <= max_collision_limit:
                            score = (ac * 10) - (abs(s - avg_sum) * 0.5) + (stats[2] * 3)
                            candidate_pool.append({
                                "combo": res, "sum": s, "ac": ac, "consec": consec,
                                "max_hit": max_hit, "stats": stats, "score": score
                            })
                            if len(candidate_pool) >= 15: break

            if not candidate_pool:
                st.warning("找不到符合設定的組合，請嘗試調低滑桿。")
            else:
                candidate_pool.sort(key=lambda x: x['score'], reverse=True)
                top_10 = candidate_pool[:10]
                
                st.markdown(f"### 🌟 AI 推薦首選 (AC 實際值: {top_10[0]['ac']})")
                st.success(f"## ⭐ `{top_10[0]['combo']}`")

                st.markdown("---")
                st.subheader("📊 Top 1-10 候選組合核心命中統計")
                matrix_data = []
                for idx, item in enumerate(top_10, 1):
                    s = item['stats']
                    matrix_data.append({
                        "排行": f"Top {idx}",
                        "號碼組合": " , ".join(map(str, item['combo'])),
                        "中 2 碼": f"{s[2]} 次",
                        "中 3 碼": f"{s[3]} 次",
                        "中 4 碼": f"{s[4]} 次",
                        "AC 值": item['ac'],
                        "AI 評分": round(item['score'], 1)
                    })
                st.table(pd.DataFrame(matrix_data))

    except Exception as e:
        st.error(f"分析錯誤: {e}")
else:
    st.info("請上傳歷史數據以啟動分析。")

