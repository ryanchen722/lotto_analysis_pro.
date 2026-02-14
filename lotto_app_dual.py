import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st

# ==========================================
# Gauss Research Engine V6.2 (Enhanced Comparison)
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
    def get_detailed_comparison(combo, history):
        """
        深度比對：計算這組號碼在歷史中分別中過幾碼
        返回一個統計字典
        """
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
st.set_page_config(page_title="Gauss Master Pro V6.2", layout="wide")
st.title("💎 Gauss Master Pro V6.2 - 歷史深度比對版")
st.markdown("本版本強化了與過去歷史數據的「全吻合度」比對功能。")

# 側邊欄
st.sidebar.header("⚙ 模擬參數")
game_type = st.sidebar.selectbox("選擇遊戲", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num, pick_count, ac_threshold = 39, 5, 6
else:
    max_num, pick_count, ac_threshold = 49, 6, 8

# 過濾邏輯
st.sidebar.subheader("🛡 歷史過濾門檻")
exclude_already_won = st.sidebar.checkbox("自動排除歷史曾中過 4 碼以上的組合", value=True)
max_collision_limit = st.sidebar.slider("允許最高歷史重複碼數", 1, pick_count, 3 if exclude_already_won else pick_count)

uploaded_file = st.file_uploader("📂 上傳歷史數據 (Excel)", type=["xlsx"])

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
            st.error("讀取失敗，請檢查 Excel 格式")
            st.stop()

        # 數據統計
        sums = [sum(r) for r in history]
        avg_sum = np.mean(sums)
        counts = Counter(all_nums)
        
        # 權重計算 (預設平衡)
        num_range = list(range(1, max_num + 1))
        weights = [counts.get(i, 1) for i in num_range]

        if st.button("🚀 執行深度比對模擬"):
            st.write("### 🔍 模擬分析結果")
            
            candidate_pool = []
            attempts = 0
            # 增加嘗試次數以確保過濾後仍有結果
            while len(candidate_pool) < 5 and attempts < 20000:
                attempts += 1
                res = sorted(random.choices(num_range, weights=weights, k=pick_count))
                if len(set(res)) != pick_count: continue

                s = sum(res)
                ac = GaussResearchEngine.calculate_ac_value(res)
                
                # 基礎過濾：總和與 AC 值
                if abs(s - avg_sum) < 30 and ac >= ac_threshold:
                    # 執行歷史比對
                    stats, max_hit = GaussResearchEngine.get_detailed_comparison(res, history)
                    
                    # 衝突檢查過濾
                    if max_hit <= max_collision_limit:
                        candidate_pool.append({
                            "combo": res,
                            "ac": ac,
                            "max_hit": max_hit,
                            "history_stats": stats,
                            "sum": s
                        })

            if not candidate_pool:
                st.warning("符合「低重複」條件的組合較難產生，請嘗試放寬『最高歷史重複碼數』。")
            else:
                for idx, item in enumerate(candidate_pool):
                    with st.expander(f"推薦組合 {idx+1}: {item['combo']} (歷史最高重複: {item['max_hit']} 碼)"):
                        c1, c2 = st.columns([1, 2])
                        with c1:
                            st.write("**統計指標**")
                            st.write(f"- AC 值: {item['ac']}")
                            st.write(f"- 總和: {item['sum']}")
                            st.write(f"- 歷史最大重複: {item['max_hit']}")
                        
                        with c2:
                            st.write("**過去比對統計 (次數)**")
                            s = item['history_stats']
                            # 建立一個小表格顯示這組號碼在過去的表現
                            comp_data = {
                                "命中碼數": ["中 0 碼", "中 1 碼", "中 2 碼", "中 3 碼", "中 4 碼"],
                                "歷史次數": [s[0], s[1], s[2], s[3], s[4]]
                            }
                            st.table(pd.DataFrame(comp_data))
                
                st.success(f"比對完成！已從 {attempts} 次嘗試中篩選出最符合『低重複度』的 5 組號碼。")

    except Exception as e:
        st.error(f"錯誤: {e}")
else:
    st.info("請上傳歷史數據以啟動深度比對功能。")

st.markdown("---")
st.caption("Gauss Master Pro V6.2 | 歷史深度比對技術 | 排除死號組合")

