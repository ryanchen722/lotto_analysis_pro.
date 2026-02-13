import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# ==========================================
# 核心數學模組 - 高斯思維
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
        """計算歷史均值與標準差"""
        sums = [sum(row) for row in history_rows]
        return np.mean(sums), np.std(sums)

    @staticmethod
    def is_mod_balanced(nums, mod=3):
        """數論過濾：檢查餘數分佈是否均衡"""
        dist = Counter([n % mod for n in nums])
        # 對於 5-6 碼，單一餘數不應超過 4 個
        return all(v <= 4 for v in dist.values())

# ==========================================
# Streamlit UI 設定
# ==========================================
st.set_page_config(page_title="大樂透分析師 - Pro", page_icon="📐", layout="centered")

st.title("📐 大樂透分析師 (Gauss Pro)")
st.markdown("---")

# 選擇模式
mode = st.radio("選擇分析模式", ["大樂透 (6/49)", "今彩 539 (5/39)"], horizontal=True)
ball_count = 6 if "大樂透" in mode else 5
ac_threshold = 7 if ball_count == 6 else 5

uploaded_file = st.file_uploader(f"📂 上傳 {mode} 歷史數據 (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        history_rows = []
        all_nums = []
        
        for val in df.iloc[:, 1].dropna().astype(str):
            clean = val.replace(' ', ',').replace('，', ',')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            if len(nums) == ball_count:
                history_rows.append(nums)
                all_nums.extend(nums)
        
        if not history_rows:
            st.error("檔案格式不符，請確認第二欄包含正確的號碼。")
            st.stop()

        # 高斯分析展示
        mean_v, std_v = GaussEngine.get_stats(history_rows)
        
        st.subheader("📊 統計趨勢 (Gaussian Distribution)")
        c1, c2, c3 = st.columns(3)
        c1.metric("均值 μ", f"{mean_v:.1f}")
        c2.metric("標準差 σ", f"{std_v:.1f}")
        c3.metric("建議區間", f"{int(mean_v-std_v)}-{int(mean_v+std_v)}")

        # 側邊欄設定
        st.sidebar.header("📝 參數校正")
        sample_sum = st.sidebar.number_input("現場電腦選號總和", min_value=0, value=0)
        conf_level = st.sidebar.slider("信心區間倍數", 0.5, 2.0, 1.0)

        if st.button(f"🚀 啟動 8000 次高斯模擬", use_container_width=True):
            f_counts = Counter(all_nums)
            weighted_pool = []
            for n, count in f_counts.items():
                weighted_pool.extend([n] * count)
            
            # 區間決策
            t_min, t_max = (sample_sum - 15, sample_sum + 15) if sample_sum > 0 else (mean_v - std_v * conf_level, mean_v + std_v * conf_level)

            candidates = []
            last_draw = set(history_rows[0])

            with st.spinner('進行蒙地卡羅運算中...'):
                for _ in range(8000):
                    res = sorted(random.sample(weighted_pool, ball_count) if len(set(weighted_pool)) >= ball_count else random.sample(range(1, 50), ball_count))
                    f_sum = sum(res)
                    ac_val = GaussEngine.calculate_ac_value(res)
                    
                    if (t_min <= f_sum <= t_max and 
                        ac_val >= ac_threshold and 
                        len(set(res).intersection(last_draw)) <= 2 and
                        GaussEngine.is_mod_balanced(res)):
                        candidates.append((res, f_sum, ac_val))
                        if len(candidates) >= 10: break

            if candidates:
                final_res, final_sum, final_ac = random.choice(candidates)
                st.success(f"### 推薦號碼：{final_res}")
                
                # 回測
                target_set = set(final_res)
                hits = {i: 0 for i in range(2, ball_count + 1)}
                for h in history_rows:
                    m = len(target_set.intersection(set(h)))
                    if m in hits: hits[m] += 1
                
                st.markdown("### 📜 歷史回測碰撞")
                cols = st.columns(len(hits))
                for i, (k, v) in enumerate(reversed(list(hits.items()))):
                    cols[i].metric(f"中 {k} 碼", f"{v} 次")
            else:
                st.error("找不到符合高斯規律的解，請調整參數。")

    except Exception as e:
        st.error(f"分析錯誤: {e}")
else:
    st.info("💡 請上傳歷史數據以啟動數學分析模型。")

st.markdown("---")
st.caption("Gauss Analysis Tool v1.0 | 數據科學與機率研究")