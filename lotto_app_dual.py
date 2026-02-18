import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# ==========================================
# Gauss Research Engine V6.8
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
        """深度比對：計算歷史命中分佈 (聚焦中 3 碼以上)"""
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
st.set_page_config(page_title="Gauss Master Pro V6.8", layout="wide", page_icon="💎")
st.title("💎 Gauss Master Pro V6.8 - 總和與核心命中版")
st.markdown("本版本過濾了中 0, 1, 2 碼數據，強化了「總和」與「中 3 碼以上」的深度分析。")
st.markdown("---")

# 側邊欄設定
st.sidebar.header("⚙️ 核心研究參數")
game_type = st.sidebar.selectbox("遊戲模式", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num, pick_count = 39, 5
    ac_slider_max = 10
    default_ac = 6
else:
    max_num, pick_count = 49, 6
    ac_slider_max = 15
    default_ac = 8

# AC 值調整滑桿
ac_threshold = st.sidebar.slider("AC 值最小門檻 (複雜度)", 1, ac_slider_max, default_ac)

hot_mode = st.sidebar.select_slider("數字權重偏好", options=["極冷", "偏冷", "平衡", "偏熱", "極熱"], value="平衡")
max_collision_limit = st.sidebar.slider("禁止出現過大獎的組合 (排除歷史命中 > X)", 1, pick_count, pick_count-1)

uploaded_file = st.file_uploader("📂 上傳歷史 Excel 數據", type=["xlsx"])

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

        # 最近 30 期走勢
        st.subheader(f"🕵️ 最近 30 期開獎走勢 ({game_type})")
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

        if st.button("🚀 啟動總和核心精選"):
            candidate_pool = []
            with st.spinner("AI 正在遍歷歷史數據並執行多因子加權評分..."):
                for _ in range(30000):
                    res = sorted(random.choices(num_range, weights=weights, k=pick_count))
                    if len(set(res)) != pick_count: continue

                    s = sum(res)
                    ac = GaussResearchEngine.calculate_ac_value(res)
                    consec = GaussResearchEngine.count_consecutive_groups(res)

                    if abs(s - avg_sum) < 30 and ac >= ac_threshold and consec <= 1:
                        stats, max_hit = GaussResearchEngine.get_detailed_comparison(res, history)
                        if max_hit <= max_collision_limit:
                            # 評分邏輯優化：AC(40%) + 總和(40%) + 中3碼穩定度(20%)
                            score = (ac * 10) - (abs(s - avg_sum) * 0.6) + (stats[3] * 5)
                            candidate_pool.append({
                                "combo": res, "sum": s, "ac": ac, "consec": consec,
                                "max_hit": max_hit, "stats": stats, "score": score
                            })
                            if len(candidate_pool) >= 15: break

            if not candidate_pool:
                st.warning("條件設定下找不到組合，請嘗試調低 AC 門檻。")
            else:
                candidate_pool.sort(key=lambda x: x['score'], reverse=True)
                top_10 = candidate_pool[:10]
                best_one = top_10[0]

                # --- 第一精選展示 ---
                st.markdown("### 🌟 AI 最終黃金精選")
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
                st.subheader("📊 Top 1-10 候選組合核心命中統計 (中 3 碼以上)")
                
                matrix_data = []
                for idx, item in enumerate(top_10, 1):
                    s = item['stats']
                    matrix_data.append({
                        "排行": f"Top {idx}",
                        "號碼組合": " , ".join(map(str, item['combo'])),
                        "總和": item['sum'],
                        "中 3 碼次數": f"{s[3]} 次",
                        "中 4 碼次數": f"{s[4]} 次",
                        "AC 值": item['ac'],
                        "AI 綜合評分": round(item['score'], 1)
                    })
                st.table(pd.DataFrame(matrix_data))

                # 報告下載
                report_txt = f"Gauss Master Pro V6.8 報告\n"
                report_txt += f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                report_txt += f"AC 門檻: {ac_threshold}\n"
                report_txt += "="*50 + "\n"
                report_txt += f"【AI 首選】: {best_one['combo']}\n"
                report_txt += f"總和: {best_one['sum']}, AC: {best_one['ac']}\n"
                report_txt += f"戰績: 中3碼({best_one['stats'][3]}次), 中4碼({best_one['stats'][4]}次)\n"
                report_txt += "="*50 + "\n\n"
                for idx, item in enumerate(top_10, 1):
                    s = item['stats']
                    report_txt += f"Top {idx}: {item['combo']} | 總和: {item['sum']} | 3/4碼命中: ({s[3]}, {s[4]})\n"

                st.download_button(
                    label="📥 下載完整 V6.8 研究報告",
                    data=report_txt,
                    file_name=f"Gauss_V6_8_Report.txt",
                    mime="text/plain",
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"分析失敗: {e}")
else:
    st.info("請上傳歷史數據以啟動總和分析模型。")

st.markdown("---")
st.caption("Gauss Master Pro V6.8 | 總和回歸分析 | 核心命中統計 | AC 值自定義")

