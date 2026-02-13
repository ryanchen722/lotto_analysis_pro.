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
    def is_mod_balanced(nums, mod=3, limit=3):
        """數論過濾：檢查餘數分佈是否均衡 (同餘理論)"""
        dist = Counter([n % mod for n in nums])
        return all(v <= limit for v in dist.values())

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
st.set_page_config(page_title="樂透高斯分析 Pro", page_icon="📐", layout="centered")

# 側邊欄配置：選擇遊戲類型
st.sidebar.header("🎯 遊戲模式設定")
game_type = st.sidebar.selectbox("選擇分析遊戲", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num = 39
    pick_count = 5
    ac_threshold = 5
    mod_limit = 3
    file_label = "lotto_539.xlsx"
else:
    max_num = 49
    pick_count = 6
    ac_threshold = 7
    mod_limit = 3
    file_label = "lotto_649.xlsx"

st.title(f"📐 {game_type} 高斯分析師 (Pro)")
st.markdown(f"> \"Mathematics is the queen of sciences.\" —— C. F. Gauss | 當前模式：{game_type}")
st.markdown("---")

# 1. 檔案上傳區
uploaded_file = st.file_uploader(f"📂 請上傳 {game_type} 歷史數據 ({file_label})", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        history_rows = []
        all_nums = []
        
        # 讀取第二欄 (開獎號碼欄)
        for val in df.iloc[:, 1].dropna().astype(str):
            clean = val.replace(' ', ',').replace('，', ',').replace('?', '')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            # 根據遊戲類型過濾號碼數
            if len(nums) == pick_count:
                history_rows.append(nums)
                all_nums.extend(nums)
        
        if not history_rows:
            st.error(f"❌ 格式錯誤：找不到符合 {pick_count} 碼格式的數據。")
            st.stop()

        # --- 核心統計數據 ---
        mean_v, std_v = GaussEngine.get_stats(history_rows)
        
        # --- 顯示區塊 A：最近 30 期歷史掃描 ---
        st.subheader(f"🕵️ 最近 30 期歷史開獎掃描 ({game_type})")
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
        
        st.table(pd.DataFrame(history_data))
        
        st.markdown("---")

        # --- 顯示區塊 B：高斯指標 ---
        st.subheader("📊 高斯常態分佈指標")
        c1, c2, c3 = st.columns(3)
        c1.metric("均值 μ (中軸)", f"{mean_v:.1f}")
        c2.metric("標準差 σ (離散度)", f"{std_v:.1f}")
        c3.metric("建議總和區間", f"{int(mean_v-std_v)}-{int(mean_v+std_v)}")
        
        st.info(f"💡 根據高斯理論，{game_type} 最常出現的組合總和落在：**{int(mean_v-std_v)} ~ {int(mean_v+std_v)}**")

        # 側邊欄參數校正
        st.sidebar.markdown("---")
        st.sidebar.header("📝 參數校正")
        sample_sum = st.sidebar.number_input("輸入現場樣本總和 (選填)", min_value=0, value=0)
        conf_level = st.sidebar.slider("高斯信心強度 (σ 倍數)", 0.5, 2.0, 1.0)

        # --- 核心分析按鈕 ---
        if st.button(f"🚀 啟動 8000 次高斯權重模擬", use_container_width=True):
            f_counts = Counter(all_nums)
            weighted_pool = []
            for n, count in f_counts.items():
                weighted_pool.extend([n] * count)
            
            # 區間決策邏輯
            if sample_sum > 0:
                t_min, t_max = sample_sum - 20, sample_sum + 20
            else:
                t_min, t_max = mean_v - std_v * conf_level, mean_v + std_v * conf_level

            last_draw = set(history_rows[0])
            candidates = []
            
            with st.spinner(f'{game_type} 運算中...'):
                for _ in range(8000):
                    # 蒙地卡羅抽樣：根據歷史頻率分配權重
                    if len(set(weighted_pool)) >= pick_count:
                        res_list = sorted(random.sample(weighted_pool, pick_count))
                    else:
                        res_list = sorted(random.sample(range(1, max_num + 1), pick_count))
                    
                    # 確保號碼不重複 (從 pool 抽樣通常不會，但保險起見)
                    if len(set(res_list)) != pick_count: continue

                    f_sum = sum(res_list)
                    ac_val = GaussEngine.calculate_ac_value(res_list)
                    overlap = len(set(res_list).intersection(last_draw))
                    
                    # 高斯過濾條件 (大樂透 AC 值通常較高)
                    if (t_min <= f_sum <= t_max and 
                        ac_val >= ac_threshold and 
                        overlap <= 2 and 
                        GaussEngine.is_mod_balanced(res_list, limit=mod_limit)):
                        candidates.append((res_list, f_sum, ac_val))
                        if len(candidates) >= 10: break

            if candidates:
                rec_f, f_sum, ac_val = random.choice(candidates)
                st.success(f"✨ {game_type} 分析完成！")
                st.markdown(f"## 推薦號碼：`{rec_f}`")

                res_cols = st.columns(3)
                res_cols[0].metric("預測總和", f_sum)
                res_cols[1].metric("AC 複雜度", ac_val)
                res_cols[2].metric("連號組數", GaussEngine.count_consecutive_groups(rec_f))
                
                # 下載結果
                result_text = f"{game_type} 高斯分析報告\n時間: {datetime.now()}\n號碼: {rec_f}\n總和: {f_sum}\nAC值: {ac_val}"
                st.download_button("📥 匯出報告", result_text, file_name=f"{game_type}_gauss_result.txt")
            else:
                st.error("❌ 在 8000 次模擬內找不到完美符合解。建議放寬「信心強度」或檢查檔案數據。")

    except Exception as e:
        st.error(f"分析失敗: {e}")
else:
    st.info(f"💡 請上傳您的 {game_type} 歷史數據 Excel 檔開始分析。")

st.markdown("---")
st.caption(f"Gauss Analyst Pro v3.0 | 支援雙版本開關 | 歷史掃描 + 高斯模型")
