import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# ==========================================
# 核心數學模組 - 高斯進化引擎 (Gauss V5.4 Engine)
# ==========================================
class GaussV5Engine:
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
        """掃描全歷史：回傳最高命中碼數與詳細分佈"""
        if not history_rows: return 0, {}
        target_set = set(combo)
        hit_counts = Counter()
        max_hit = 0
        for h in history_rows:
            hit = len(target_set & set(h))
            if hit > 0:
                hit_counts[hit] += 1
            if hit > max_hit:
                max_hit = hit
        return max_hit, dict(hit_counts)

# ==========================================
# Streamlit UI 設定
# ==========================================
st.set_page_config(page_title="樂透高斯大師 V5.4", page_icon="💎", layout="centered")

st.sidebar.header("🕹️ 遊戲分析模式")
game_type = st.sidebar.selectbox("請選擇遊戲", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num, pick_count, ac_threshold = 39, 5, 5
else:
    max_num, pick_count, ac_threshold = 49, 6, 7

st.title(f"💎 {game_type} 高斯大師 V5.4")
st.markdown("---")

uploaded_file = st.file_uploader(f"📂 請上傳 {game_type} 歷史數據 Excel", type=["xlsx"])

if uploaded_file:
    try:
        # 讀取數據
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        history_rows = []
        all_nums = []
        history_consecutive_count = 0
        
        for val in df.iloc[:, 1].dropna().astype(str):
            clean = val.replace(' ', ',').replace('，', ',').replace('?', '')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            if len(nums) == pick_count:
                history_rows.append(nums)
                all_nums.extend(nums)
                if GaussV5Engine.count_consecutive_groups(nums) > 0:
                    history_consecutive_count += 1
        
        if not history_rows:
            st.error("❌ 無法從檔案中提取有效的歷史紀錄。")
            st.stop()

        # 基礎規律統計
        sums = [sum(row) for row in history_rows]
        mean_v, std_v = np.mean(sums), np.std(sums)
        consecutive_rate = (history_consecutive_count / len(history_rows)) * 100
        
        st.subheader("📊 歷史大數據看板")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("歷史均值 μ", f"{mean_v:.1f}")
        col2.metric("標準差 σ", f"{std_v:.1f}")
        col3.metric("連號率", f"{consecutive_rate:.1f}%")
        col4.metric("總期數", f"{len(history_rows)}")

        # 側邊欄控制
        st.sidebar.markdown("---")
        st.sidebar.header("⚙️ 篩選優化")
        conf_level = st.sidebar.slider("高斯信心區間 (σ)", 0.5, 2.0, 1.0)
        
        if st.button(f"🚀 啟動 8000 次模擬並產生報告", use_container_width=True):
            t_min, t_max = mean_v - std_v * conf_level, mean_v + std_v * conf_level
            
            # 自動計算權重
            counts = Counter(all_nums)
            weights = [counts.get(i, 1) for i in range(1, max_num + 1)]
            num_range = list(range(1, max_num + 1))
            
            last_draw = set(history_rows[0])
            candidates = []
            
            with st.spinner('AI 正在全速運算並掃描全歷史碰撞...'):
                for _ in range(8000):
                    res = sorted(random.choices(num_range, weights=weights, k=pick_count))
                    if len(set(res)) != pick_count: continue
                    
                    f_sum = sum(res)
                    ac_val = GaussV5Engine.calculate_ac_value(res)
                    consec_grp = GaussV5Engine.count_consecutive_groups(res)
                    
                    # 結合高斯、AC 值與連號邏輯篩選
                    if (t_min <= f_sum <= t_max and ac_val >= ac_threshold and consec_grp <= 2 and len(set(res) & last_draw) <= 2):
                        candidates.append(res)
                        if len(candidates) >= 5: break # 取得前 5 組最佳解

            if candidates:
                st.subheader("🎯 推薦組合與歷史碰撞報告")
                report_content = f"{game_type} 高斯分析報告\n生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                report_content += f"歷史統計: 均值={mean_v:.1f}, 連號率={consecutive_rate:.1f}%\n"
                report_content += "-"*30 + "\n"

                for idx, combo in enumerate(candidates, 1):
                    max_hit, hit_dist = GaussV5Engine.analyze_full_history_collision(combo, history_rows)
                    consec_grp = GaussV5Engine.count_consecutive_groups(combo)
                    
                    with st.expander(f"組合 {idx}：{combo}", expanded=True):
                        # 指標區
                        m1, m2, m3, m4 = st.columns(4)
                        m1.write(f"🔢 總和: **{sum(combo)}**")
                        m2.write(f"📉 AC值: **{GaussV5Engine.calculate_ac_value(combo)}**")
                        m3.write(f"🔗 連號: **{consec_grp} 組**")
                        m4.write(f"🏆 最高中: :red[**{max_hit} 碼**]")
                        
                        # 歷史命中詳情
                        st.markdown("**📜 歷史詳細碰撞次數：**")
                        dist_cols = st.columns(pick_count)
                        for k in range(1, pick_count + 1):
                            count = hit_dist.get(k, 0)
                            dist_cols[k-1].metric(f"{k}碼", f"{count}次")
                    
                    # 寫入報告
                    report_content += f"組合 {idx}: {combo}\n"
                    report_content += f"  總和: {sum(combo)}, AC值: {GaussV5Engine.calculate_ac_value(combo)}, 連號: {consec_grp}組\n"
                    report_content += f"  歷史最高命中: {max_hit} 碼\n"
                    report_content += f"  命中分佈: {dict(sorted(hit_dist.items()))}\n\n"

                st.markdown("---")
                st.download_button(
                    label="📥 下載完整分析報告 (.txt)",
                    data=report_content,
                    file_name=f"{game_type}_Gauss_Report_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ 在 8000 次模擬內未發現符合高斯規律的組合，請嘗試調大信心區間。")

    except Exception as e:
        st.error(f"分析發生錯誤: {e}")
else:
    st.info("💡 請上傳歷史 Excel 數據檔案以啟動高斯全功能分析。")

st.markdown("---")
st.caption("Gauss Master Pro V5.4 | 全歷史碰撞回測 | 連號規律監控 | 數據導出")

