import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# ==========================================
# 核心數學模組 - 高斯思維 (致敬高斯)
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
        """計算歷史均值與標準差 (高斯常態分佈基礎)"""
        sums = [sum(row) for row in history_rows]
        return np.mean(sums), np.std(sums)

    @staticmethod
    def is_mod_balanced(nums, mod=3):
        """數論過濾：檢查餘數分佈是否均衡 (同餘理論)"""
        dist = Counter([n % mod for n in nums])
        # 對於 5 碼，單一餘數不應超過 3 個
        return all(v <= 3 for v in dist.values())

    @staticmethod
    def count_consecutive_groups(nums):
        """計算一組號碼中有幾組連號"""
        groups = 0
        nums_sorted = sorted(nums)
        i = 0
        while i < len(nums_sorted) - 1:
            if nums_sorted[i] + 1 == nums_sorted[i+1]:
                groups += 1
                while i < len(nums_sorted) - 1 and nums_sorted[i] + 1 == nums_sorted[i+1]:
                    i += 1
            else:
                i += 1
        return groups

# ==========================================
# Streamlit UI 設定
# ==========================================
st.set_page_config(page_title="今彩 539 高斯分析師", page_icon="📐", layout="centered")

st.title("📐 今彩 539 高斯分析師 (Pro)")
st.markdown("> \"Mathematics is the queen of sciences.\" —— C. F. Gauss")
st.markdown("---")

# 1. 檔案上傳區
uploaded_file = st.file_uploader("📂 請上傳今彩 539 歷史數據 (lotto_539.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        history_rows = []
        all_nums = []
        
        for val in df.iloc[:, 1].dropna().astype(str):
            clean = val.replace(' ', ',').replace('，', ',').replace('?', '')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            if len(nums) == 5:
                history_rows.append(nums)
                all_nums.extend(nums)
        
        if not history_rows:
            st.error("❌ 格式錯誤：找不到符合 5 碼格式的數據。")
            st.stop()

        # --- 核心統計數據 ---
        mean_v, std_v = GaussEngine.get_stats(history_rows)
        
        # --- 顯示區塊 A：最近 30 期歷史掃描 ---
        st.subheader("🕵️ 最近 30 期歷史開獎掃描")
        history_data = []
        max_display = min(30, len(history_rows))
        for i in range(max_display):
            row = history_rows[i]
            history_data.append({
                "期數": f"前 {i+1} 期",
                "開獎號碼": str(row),
                "總和": sum(row),
                "AC值": GaussEngine.calculate_ac_value(row),
                "連號": f"{GaussEngine.count_consecutive_groups(row)} 組"
            })
        
        # 以表格形式呈現歷史數據
        st.table(pd.DataFrame(history_data))
        
        st.markdown("---")

        # --- 顯示區塊 B：高斯指標 ---
        st.subheader("📊 高斯常態分佈指標")
        c1, c2, c3 = st.columns(3)
        c1.metric("均值 μ (中軸)", f"{mean_v:.1f}")
        c2.metric("標準差 σ (離散度)", f"{std_v:.1f}")
        c3.metric("建議總和區間", f"{int(mean_v-std_v)}-{int(mean_v+std_v)}")
        
        st.info(f"💡 根據高斯理論，最常出現的組合總和落在信心區間：**{int(mean_v-std_v)} ~ {int(mean_v+std_v)}**")

        # 側邊欄設定
        st.sidebar.header("📝 參數校正")
        sample_sum = st.sidebar.number_input("輸入現場樣本總和 (選填)", min_value=0, value=0)
        conf_level = st.sidebar.slider("高斯信心強度 (σ 倍數)", 0.5, 2.0, 1.0)

        # --- 核心分析按鈕 ---
        if st.button("🚀 啟動 8000 次高斯權重模擬", use_container_width=True):
            f_counts = Counter(all_nums)
            weighted_pool = []
            for n, count in f_counts.items():
                weighted_pool.extend([n] * count)
            
            # 區間決策邏輯
            if sample_sum > 0:
                t_min, t_max = sample_sum - 15, sample_sum + 15
            else:
                t_min, t_max = mean_v - std_v * conf_level, mean_v + std_v * conf_level

            last_draw = set(history_rows[0])
            candidates = []
            
            with st.spinner('高斯模擬運算中...'):
                for _ in range(8000):
                    # 蒙地卡羅抽樣：根據歷史頻率分配權重
                    res_list = sorted(random.sample(weighted_pool, 5) if len(set(weighted_pool)) >= 5 else random.sample(range(1, 40), 5))
                    
                    f_sum = sum(res_list)
                    ac_val = GaussEngine.calculate_ac_value(res_list)
                    overlap = len(set(res_list).intersection(last_draw))
                    
                    # 高斯過濾條件
                    if (t_min <= f_sum <= t_max and 
                        ac_val >= 5 and 
                        overlap <= 2 and 
                        GaussEngine.is_mod_balanced(res_list)):
                        candidates.append((res_list, f_sum, ac_val))
                        if len(candidates) >= 10: break

            if candidates:
                rec_f, f_sum, ac_val = random.choice(candidates)
                st.success("✨ 分析完成！推薦組合如下：")
                st.markdown(f"## 推薦號碼：`{rec_f}`")

                res_cols = st.columns(3)
                res_cols[0].metric("預測總和", f_sum)
                res_cols[1].metric("AC 複雜度", ac_val)
                res_cols[2].metric("連號組數", GaussEngine.count_consecutive_groups(rec_f))
                
                # 下載結果
                result_text = f"539 高斯分析報告\n時間: {datetime.now()}\n號碼: {rec_f}\n總和: {f_sum}\nAC值: {ac_val}"
                st.download_button("📥 匯出報告", result_text, file_name="gauss_result.txt")
            else:
                st.error("❌ 在 8000 次高斯過濾後未發現適當解，請放寬信心區間。")

    except Exception as e:
        st.error(f"分析失敗: {e}")
else:
    st.info("💡 請上傳 539 歷史數據 Excel 檔開始高斯分析。")

st.markdown("---")
st.caption("Gauss Analyst Pro v2.1 | 歷史掃描 + 高斯模型 + 8000次模擬")
