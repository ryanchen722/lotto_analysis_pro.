import pandas as pd
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# 設定網頁標題與風格
st.set_page_config(page_title="威力彩大數據大師", layout="centered")

def calculate_ac_value(nums):
    """計算 AC 值 (算術複雜度)"""
    differences = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            differences.add(abs(nums[i] - nums[j]))
    return len(differences) - (len(nums) - 1)

def count_consecutive_groups(nums):
    """計算連號組數"""
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

st.title("🎲 威力彩精準分析 App")
st.markdown("---")

# 1. 檔案上傳區
uploaded_file = st.file_uploader("📂 請上傳威力彩歷史數據 (lotto_data.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        first_zone_rows = []
        all_first = []
        history_ac_values = []
        
        for val in df.iloc[:, 1].dropna().astype(str):
            clean = val.replace('?', '').replace(' ', ',').replace('，', ',')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            if len(nums) == 6:
                first_zone_rows.append(nums)
                all_first.extend(nums)
                # 計算每一期的歷史 AC 值
                history_ac_values.append(calculate_ac_value(nums))
        
        second_zone = []
        for n in df.iloc[:, 2].dropna():
            clean_s = str(n).replace('?', '').strip()
            if clean_s.isdigit(): second_zone.append(int(clean_s))

        # --- 側邊欄：手動樣本輸入 ---
        st.sidebar.header("📝 現場樣本參考")
        st.sidebar.info("若在投注站看到電腦選號，請輸入其總和以校正算法。")
        sample_sum = st.sidebar.number_input("輸入樣本總和 (若無則維持 0)", min_value=0, value=0)

        # --- 歷史規律與 AC 值展示 ---
        st.subheader("🕵️ 歷史規律掃描 (最近 30 期)")
        
        # 1. 顯示最近 5 期的卡片 (重點顯示)
        st.markdown("##### 最近 5 期摘要")
        cols = st.columns(5)
        for i in range(min(5, len(first_zone_rows))):
            current_ac = history_ac_values[i]
            cols[i].metric(
                f"前 {i+1} 期", 
                f"AC: {current_ac}", 
                f"Sum: {sum(first_zone_rows[i])}"
            )
            cols[i].caption(f"{first_zone_rows[i]}")

        # 2. 展開顯示其餘期數 (至第 30 期)
        with st.expander("查看更多歷史數據 (前 6-30 期)"):
            history_data = []
            max_hist = min(30, len(first_zone_rows))
            for i in range(max_hist):
                history_data.append({
                    "期數": f"前 {i+1} 期",
                    "號碼": str(first_zone_rows[i]),
                    "總和": sum(first_zone_rows[i]),
                    "AC值": history_ac_values[i],
                    "連號": f"{count_consecutive_groups(first_zone_rows[i])} 組"
                })
            st.table(pd.DataFrame(history_data))

        # 顯示 AC 統計摘要
        if history_ac_values:
            # 計算前 30 期的統計數據
            recent_30_ac = history_ac_values[:30]
            avg_ac = sum(recent_30_ac) / len(recent_30_ac)
            most_common_ac = Counter(recent_30_ac).most_common(1)[0][0]
            
            st.info(f"""
            **📈 最近 30 期 AC 數據分析：**
            * 歷史平均 AC 值：`{avg_ac:.2f}`
            * 出現頻率最高 AC 值：`{most_common_ac}` (建議區間：7-10)
            """)

        # --- 核心分析按鈕 ---
        if st.button("🚀 開始精準模擬分析", use_container_width=True):
            f_counts = Counter(all_first)
            weighted_pool = []
            for n, count in f_counts.items():
                weighted_pool.extend([n] * count)
            
            if sample_sum > 0:
                target_min, target_max = sample_sum - 20, sample_sum + 20
            else:
                target_min, target_max = 95, 155

            last_draw = set(first_zone_rows[0]) if first_zone_rows else set()
            candidates = []
            with st.spinner('正在進行 5000 次蒙地卡羅模擬...'):
                for _ in range(5000):
                    res_set = set()
                    while len(res_set) < 6:
                        res_set.add(random.choice(weighted_pool))
                    
                    res_list = sorted(list(res_set))
                    f_sum = sum(res_list)
                    ac_val = calculate_ac_value(res_list)
                    overlap = len(set(res_list).intersection(last_draw))
                    has_triple = any(res_list[j]+2 == res_list[j+1]+1 == res_list[j+2] for j in range(4))

                    if (target_min <= f_sum <= target_max and 
                        ac_val >= 7 and overlap <= 2 and not has_triple):
                        candidates.append((res_list, f_sum, ac_val))
                        if len(candidates) >= 10: break

            if candidates:
                rec_f, f_sum, ac_val = random.choice(candidates)
                s_counts = Counter(second_zone)
                hot_s = [n for n, c in s_counts.most_common(3)]
                rec_s = random.choice(hot_s) if random.random() > 0.5 else random.randint(1, 8)

                st.success("✨ 分析完成！推薦組合如下：")
                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    st.markdown(f"### 第一區：\n`{rec_f}`")
                with res_col2:
                    st.markdown(f"### 第二區：\n`[{rec_s:02d}]`")

                st.info(f"📊 分析數據：總和 {f_sum} | AC 複雜度 {ac_val} | 連號 {count_consecutive_groups(rec_f)} 組")
                
                result_text = f"分析時間: {datetime.now()}\n第一區: {rec_f}\n第二區: {rec_s}\n總和: {f_sum}\nAC值: {ac_val}"
                st.download_button("📥 下載分析結果", result_text, file_name="lotto_result.txt")
            else:
                st.error("❌ 無法找到符合嚴格過濾條件的組合，請重試或放寬樣本限制。")

    except Exception as e:
        st.error(f"讀取檔案失敗: {e}")
else:
    st.info("💡 請上傳您的 Excel 資料表開始分析。")

st.markdown("---")
st.caption("本工具僅供統計分析參考，請理性投注。")
