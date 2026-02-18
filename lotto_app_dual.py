import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# ==========================================
# Gauss Research Engine V6.7
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
st.set_page_config(page_title="Gauss Master Pro V6.7", layout="wide", page_icon="💎")
st.title("💎 Gauss Master Pro V6.7 - 專家級 AC 調控版")
st.markdown("本版本新增「AC 值門檻自定義滑桿」，讓研究者能精確控制組合複雜度。")
st.markdown("---")

# 側邊欄設定
st.sidebar.header("⚙️ 核心研究參數")
game_type = st.sidebar.selectbox("遊戲模式", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num, pick_count = 39, 5
    default_ac = 6
    max_ac_val = 10
else:
    max_num, pick_count = 49, 6
    default_ac = 8
    max_ac_val = 15

# 🔥 新增：AC 值調整滑桿
ac_threshold = st.sidebar.slider(
    "AC 值最小門檻 (複雜度)", 
    min_value=1, 
    max_value=max_ac_val, 
    value=default_ac,
    help="AC 值越高，號碼分佈越隨機。通常 539 建議 6 以上，大樂透建議 8 以上。"
)

hot_mode = st.sidebar.select_slider("數字權重偏好", options=["極冷", "偏冷", "平衡", "偏熱", "極熱"], value="平衡")
max_collision_limit = st.sidebar.slider("禁止出現過大獎的組合 (排除歷史命中 > X)", 1, pick_count, pick_count-1)

uploaded_file = st.file_uploader("📂 上傳歷史數據 Excel (第二欄為開獎號碼)", type=["xlsx"])

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
            st.error("格式錯誤：請確保 Excel 第二欄包含號碼數據。")
            st.stop()

        # 最近 30 期深度走勢
        st.subheader(f"🕵️ 最近 30 期深度走勢統計 ({game_type})")
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

        # 歷史統計
        sums = [sum(r) for r in history]
        avg_sum = np.mean(sums)
        counts = Counter(all_nums)
        
        # 權重計算
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

        if st.button("🚀 啟動二次加權精選模擬"):
            candidate_pool = []
            with st.spinner(f"AI 正在過濾 AC < {ac_threshold} 的組合並執行評分..."):
                # 增加嘗試次數以應對高 AC 門檻
                for _ in range(30000):
                    res = sorted(random.choices(num_range, weights=weights, k=pick_count))
                    if len(set(res)) != pick_count: continue

                    s = sum(res)
                    ac = GaussResearchEngine.calculate_ac_value(res)
                    consec = GaussResearchEngine.count_consecutive_groups(res)

                    # 應用使用者定義的 AC 門檻
                    if abs(s - avg_sum) < 30 and ac >= ac_threshold and consec <= 1:
                        stats, max_hit = GaussResearchEngine.get_detailed_comparison(res, history)
                        if max_hit <= max_collision_limit:
                            # 綜合評分依據：AC值加權 + 總和接近度 + 歷史2碼活性
                            score = (ac * 12) - (abs(s - avg_sum) * 0.4) + (stats[2] * 2.5)
                            candidate_pool.append({
                                "combo": res, "sum": s, "ac": ac, "consec": consec,
                                "max_hit": max_hit, "stats": stats, "score": score
                            })
                            if len(candidate_pool) >= 30: break

            if not candidate_pool:
                st.warning(f"目前設定下 (AC >= {ac_threshold}) 無法產生有效組合。請嘗試調低 AC 滑桿或放寬碰撞限制。")
            else:
                candidate_pool.sort(key=lambda x: x['score'], reverse=True)
                top_10 = candidate_pool[:10]
                best_one = top_10[0]

                # --- AI 第一精選展示 ---
                st.markdown("### 🌟 AI 最終黃金精選")
                st.info(f"當前 AC 過濾門檻設定為: {ac_threshold}")
                c1, c2, c3 = st.columns([1.5, 1, 1])
                with c1:
                    st.success(f"## ⭐ `{best_one['combo']}`")
                with c2:
                    st.write(f"🔢 總和：**{best_one['sum']}**")
                    st.write(f"📉 AC 值：**{best_one['ac']}**")
                with c3:
                    st.write(f"🏆 歷史最高：**{best_one['max_hit']} 碼**")
                    st.write(f"🧬 綜合評分：**{best_one['score']:.1f}**")

                # --- Top 10 命中矩陣 ---
                st.markdown("---")
                st.subheader("📊 Top 1-10 候選組合核心命中統計 (中 2 碼以上)")
                
                matrix_data = []
                for idx, item in enumerate(top_10, 1):
                    s = item['stats']
                    matrix_data.append({
                        "排行": f"Top {idx}",
                        "號碼組合": " , ".join(map(str, item['combo'])),
                        "中 2 碼次數": f"{s[2]} 次",
                        "中 3 碼次數": f"{s[3]} 次",
                        "中 4 碼次數": f"{s[4]} 次",
                        "總和": item['sum'],
                        "AC 值": item['ac'],
                        "AI 綜合評分": round(item['score'], 1)
                    })
                st.table(pd.DataFrame(matrix_data))

                # 報告下載
                report_txt = f"Gauss Master Pro V6.7 精選報告\n"
                report_txt += f"生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                report_txt += f"AC 過濾門檻: {ac_threshold}\n"
                report_txt += "="*60 + "\n"
                report_txt += f"【第一推薦】: {best_one['combo']}\n"
                report_txt += f"歷史戰績: 中2碼({best_one['stats'][2]}次), 中3({best_one['stats'][3]}次), 中4({best_one['stats'][4]}次)\n"
                report_txt += "="*60 + "\n\n"
                for idx, item in enumerate(top_10, 1):
                    s = item['stats']
                    report_txt += f"Top {idx}: {item['combo']} | AC: {item['ac']} | 2/3/4碼命中: ({s[2]}, {s[3]}, {s[4]})\n"

                st.download_button(
                    label="📥 下載完整 V6.7 研究報告",
                    data=report_txt,
                    file_name=f"Gauss_V6_7_Report.txt",
                    mime="text/plain",
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"分析失敗: {e}")
else:
    st.info("👋 請上傳歷史 Excel 資料並於側邊欄設定 AC 門檻。")

st.markdown("---")
st.caption("Gauss Master Pro V6.7 | 自定義 AC 門檻 | 命中矩陣分析 | 歷史回歸模型")

