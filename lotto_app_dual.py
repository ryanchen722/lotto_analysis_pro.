import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# ==========================================
# 核心數學模組 - 高斯進化引擎 (Gauss V5 Engine)
# ==========================================
class GaussV5Engine:
    @staticmethod
    def calculate_ac_value(nums):
        """計算 AC 值 - 衡量組合的隨機複雜度"""
        differences = set()
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                differences.add(abs(nums[i] - nums[j]))
        return len(differences) - (len(nums) - 1)

    @staticmethod
    def get_smart_weights(all_nums, max_num):
        """自動計算熱門度權重 - 吸收 ChatGPT 的優點並自動化"""
        counts = Counter(all_nums)
        # 確保每個號碼至少有 1 次權重，避免冷門號永遠消失
        weights = [counts.get(i, 1) for i in range(1, max_num + 1)]
        return weights

    @staticmethod
    def get_max_history_hit(combo, history_rows):
        """計算歷史最高碰撞碼數"""
        if not history_rows: return 0
        target_set = set(combo)
        # 使用 numpy 加速比對邏輯 (如果歷史數據極大時)
        max_hit = 0
        for h in history_rows:
            hit = len(target_set & set(h))
            if hit > max_hit: max_hit = hit
        return max_hit

# ==========================================
# Streamlit UI 設定
# ==========================================
st.set_page_config(page_title="樂透高斯大師 V5", page_icon="💎", layout="centered")

st.sidebar.header("🕹️ 遊戲設定")
game_type = st.sidebar.selectbox("分析模式", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num, pick_count, ac_threshold, mod_limit = 39, 5, 5, 3
else:
    max_num, pick_count, ac_threshold, mod_limit = 49, 6, 7, 4

st.title(f"💎 {game_type} 高斯大師 V5")
st.markdown(f"**「與其大海撈針，不如按圖索驥。」** —— 整合高斯統計與熱門權重補償。")
st.markdown("---")

uploaded_file = st.file_uploader(f"📂 上傳 {game_type} 歷史 Excel 檔案", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        history_rows = []
        all_nums = []
        
        for val in df.iloc[:, 1].dropna().astype(str):
            clean = val.replace(' ', ',').replace('，', ',').replace('?', '')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            if len(nums) == pick_count:
                history_rows.append(nums)
                all_nums.extend(nums)
        
        if not history_rows:
            st.error("❌ 讀取失敗，請確認檔案格式是否正確（號碼需在第二欄）。")
            st.stop()

        # 計算統計數據
        sums = [sum(row) for row in history_rows]
        mean_v = np.mean(sums)
        std_v = np.std(sums)
        weights = GaussV5Engine.get_smart_weights(all_nums, max_num)
        
        st.subheader("📊 數據科學看板")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("均值 μ", f"{mean_v:.1f}")
        col_b.metric("標準差 σ", f"{std_v:.1f}")
        col_c.metric("熱門號比例", f"{len([n for n in set(all_nums) if all_nums.count(n) > len(history_rows)/max_num*pick_count])} 個")

        # 側邊欄：進階過濾
        st.sidebar.markdown("---")
        st.sidebar.header("⚙️ 進階過濾")
        conf_level = st.sidebar.slider("高斯信心區間 (σ)", 0.5, 2.0, 1.0)
        user_sum = st.sidebar.number_input("強制指定總和 (0為自動)", value=0)

        if st.button("🔥 啟動高斯進化模擬 (自動權重優化)", use_container_width=True):
            # 設定搜尋區間
            if user_sum > 0:
                t_min, t_max = user_sum - 12, user_sum + 12
            else:
                t_min, t_max = mean_v - std_v * conf_level, mean_v + std_v * conf_level

            candidates = []
            last_draw = set(history_rows[0])
            num_range = list(range(1, max_num + 1))
            
            with st.spinner('正在從機率海中過濾精華...'):
                # 雖然次數是 8000，但因為有權重，這 8000 次的質量遠高於隨機的 8 萬次
                for _ in range(8000):
                    # 基於歷史頻率權重進行選號 (吸收 ChatGPT 優點)
                    res = sorted(random.choices(num_range, weights=weights, k=pick_count))
                    
                    # 排除重複號碼 (因為 random.choices 是取後放回)
                    if len(set(res)) != pick_count: continue
                    
                    f_sum = sum(res)
                    ac_val = GaussV5Engine.calculate_ac_value(res)
                    
                    # 高斯大師的層層篩選
                    if (t_min <= f_sum <= t_max and 
                        ac_val >= ac_threshold and 
                        len(set(res) & last_draw) <= 2):
                        
                        # 同餘平衡檢查
                        mod_dist = Counter([n % 3 for n in res])
                        if all(v <= 3 for v in mod_dist.values()):
                            candidates.append(res)
                            if len(candidates) >= 30: break

            if candidates:
                # 從合格候選中選出 5 組
                final_picks = random.sample(candidates, min(5, len(candidates)))
                
                st.subheader("🎯 高斯精選推薦 (Top 5)")
                for idx, combo in enumerate(final_picks, 1):
                    max_hit = GaussV5Engine.get_max_history_hit(combo, history_rows)
                    with st.expander(f"第 {idx} 組：{combo}", expanded=True):
                        c1, c2, c3 = st.columns(3)
                        c1.write(f"總和: **{sum(combo)}**")
                        c2.write(f"AC值: **{GaussV5Engine.calculate_ac_value(combo)}**")
                        c3.write(f"歷史高碰撞: **{max_hit} 碼**")
                
                # 報告導出
                report = f"高斯大師 V5 分析報告\n模式: {game_type}\n時間: {datetime.now()}\n"
                for i, c in enumerate(final_picks, 1):
                    report += f"組{i}: {c} (總和:{sum(c)}, 最高碰撞:{GaussV5Engine.get_max_history_hit(c, history_rows)})\n"
                st.download_button("📥 下載專家報告", report, file_name=f"GaussV5_{game_type}.txt")
            else:
                st.warning("⚠️ 在當前條件下找不到完美組合，請嘗試調大「信心區間」。")

    except Exception as e:
        st.error(f"分析失敗: {e}")
else:
    st.info("💡 請上傳歷史數據 Excel 以啟動高斯進化引擎。")

