import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# ==========================================
# 核心數學模組 - 高斯思維與高效能引擎
# ==========================================
class GaussEngine:
    @staticmethod
    def calculate_ac_value(nums):
        """計算 AC 值 (算術複雜度)"""
        differences = set()
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                differences.add(abs(nums[i] - nums[j]))
        return len(differences) - (len(nums) - 1)

    @staticmethod
    def get_stats(history_rows):
        """計算歷史數據的均值與標準差"""
        sums = [sum(row) for row in history_rows]
        return np.mean(sums), np.std(sums)

    @staticmethod
    def is_mod_balanced(nums, mod=3, limit=3):
        """數論平衡檢查：確保餘數分佈不極端"""
        dist = Counter([n % mod for n in nums])
        return all(v <= limit for v in dist.values())

    @staticmethod
    def get_max_history_hit(combo, history_rows):
        """計算該組號碼在歷史開獎中最高中過幾碼"""
        if not history_rows: return 0
        target_set = set(combo)
        max_hit = 0
        for h in history_rows:
            hit = len(target_set & set(h))
            if hit > max_hit: max_hit = hit
        return max_hit

# ==========================================
# Streamlit UI 設定
# ==========================================
st.set_page_config(page_title="樂透高斯大師 Pro", page_icon="🎯", layout="centered")

st.sidebar.header("🎯 系統模式設定")
game_type = st.sidebar.selectbox("選擇分析遊戲", ["今彩 539", "大樂透"])

# 針對不同遊戲設定參數
if game_type == "今彩 539":
    max_num, pick_count, ac_threshold, mod_limit = 39, 5, 5, 3
else:
    max_num, pick_count, ac_threshold, mod_limit = 49, 6, 7, 4

st.title(f"🚀 {game_type} 高斯大師 (終極整合版)")
st.markdown(f"> 結合 **高斯統計**、**蒙地卡羅 8000 次模擬** 與 **歷史碰撞分析**")
st.markdown("---")

uploaded_file = st.file_uploader(f"📂 上傳 {game_type} 歷史數據 Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        history_rows = []
        all_nums = []
        
        # 解析數據
        for val in df.iloc[:, 1].dropna().astype(str):
            clean = val.replace(' ', ',').replace('，', ',').replace('?', '')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            if len(nums) == pick_count:
                history_rows.append(nums)
                all_nums.extend(nums)
        
        if not history_rows:
            st.error("❌ 無法解析有效的歷史數據。")
            st.stop()

        # 基礎統計
        mean_v, std_v = GaussEngine.get_stats(history_rows)
        
        # 顯示最近 30 期
        with st.expander("🕵️ 最近 30 期趨勢掃描"):
            h_df = pd.DataFrame([{
                "期數": f"前 {i+1} 期",
                "號碼": str(h),
                "總和": sum(h),
                "AC值": GaussEngine.calculate_ac_value(h)
            } for i, h in enumerate(history_rows[:30])])
            st.table(h_df)

        st.subheader("📊 高斯分析指標")
        c1, c2, c3 = st.columns(3)
        c1.metric("歷史總和均值", f"{mean_v:.1f}")
        c2.metric("標準差 σ", f"{std_v:.1f}")
        c3.metric("建議黃金區間", f"{int(mean_v-std_v)}-{int(mean_v+std_v)}")

        # 側邊欄調整
        st.sidebar.markdown("---")
        st.sidebar.header("📝 分析校正")
        sample_sum = st.sidebar.number_input("現場樣本總和 (選填)", value=0)
        conf_level = st.sidebar.slider("信心強度", 0.5, 2.0, 1.0)

        if st.button(f"🔥 執行 8000 次高斯模擬並產出 5 組精選", use_container_width=True):
            f_counts = Counter(all_nums)
            weighted_pool = []
            for n, count in f_counts.items():
                weighted_pool.extend([n] * count)
            
            # 區間判斷
            t_min, t_max = (sample_sum-15, sample_sum+15) if sample_sum > 0 else (mean_v-std_v*conf_level, mean_v+std_v*conf_level)
            
            last_draw = set(history_rows[0])
            final_recommendations = []
            
            with st.spinner('高斯引擎運算中...'):
                # 我們執行 8000 次模擬來尋找「符合數學規律」的組合
                potential_candidates = []
                for _ in range(8000):
                    # 從權重池中抽樣
                    res = sorted(random.sample(weighted_pool, pick_count) if len(set(weighted_pool)) >= pick_count else random.sample(range(1, max_num+1), pick_count))
                    
                    if (t_min <= sum(res) <= t_max and 
                        GaussEngine.calculate_ac_value(res) >= ac_threshold and 
                        len(set(res) & last_draw) <= 2 and
                        GaussEngine.is_mod_balanced(res, limit=mod_limit)):
                        potential_candidates.append(res)
                        if len(potential_candidates) >= 50: break # 先抓 50 組候選

                # 從候選中挑出碰撞度合理的 5 組
                if potential_candidates:
                    selected_samples = random.sample(potential_candidates, min(5, len(potential_candidates)))
                    for combo in selected_samples:
                        max_hit = GaussEngine.get_max_history_hit(combo, history_rows)
                        final_recommendations.append((combo, sum(combo), max_hit))

            if final_recommendations:
                st.subheader("🎯 推薦組合 (由高斯引擎精選)")
                for idx, (nums, s_val, m_hit) in enumerate(final_recommendations, 1):
                    with st.container():
                        st.markdown(f"### 第 {idx} 組：`{nums}`")
                        cc1, cc2, cc3 = st.columns(3)
                        cc1.write(f"🔢 總和：**{s_val}**")
                        cc2.write(f"📉 AC值：**{GaussEngine.calculate_ac_value(nums)}**")
                        cc3.write(f"🏆 歷史最高曾中：**{m_hit}** 碼")
                        st.markdown("---")
                
                # 匯出報告
                report = f"{game_type} 分析報告 - {datetime.now()}\n" + "\n".join([f"組{i+1}: {n} (總和:{s}, 歷史最高中{h}碼)" for i, (n,s,h) in enumerate(final_recommendations)])
                st.download_button("📥 下載完整分析報告", report, file_name=f"{game_type}_report.txt")
            else:
                st.error("❌ 找不到符合高斯規律的組合，請調整信心強度或檢查數據。")

    except Exception as e:
        st.error(f"分析失敗: {e}")
else:
    st.info("💡 請上傳歷史數據開始分析。")

st.caption("Gauss Master Pro v4.0 | 數據驅動與機率優化")

