import pandas as pd
import numpy as np
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# ==========================================
# Gauss Research Engine V6.5
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
        """深度比對：計算歷史命中分佈"""
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
st.set_page_config(page_title="Gauss Master Pro V6.5", layout="wide", page_icon="💎")
st.title("💎 Gauss Master Pro V6.5 - 數據強化研究版")
st.markdown("本版本新增「最近30期深度走勢」與「Top 10 命中矩陣分析」。")
st.markdown("---")

# 側邊欄設定
st.sidebar.header("🛠 模擬參數設定")
game_type = st.sidebar.selectbox("遊戲模式", ["今彩 539", "大樂透"])

if game_type == "今彩 539":
    max_num, pick_count, ac_threshold = 39, 5, 6
else:
    max_num, pick_count, ac_threshold = 49, 6, 8

hot_mode = st.sidebar.select_slider("權重偏好", options=["極冷", "偏冷", "平衡", "偏熱", "極熱"], value="平衡")
max_collision_limit = st.sidebar.slider("允許歷史最大重複碼數", 1, pick_count, pick_count-1)

uploaded_file = st.file_uploader("📂 上傳歷史 Excel 數據 (第二欄應為號碼)", type=["xlsx"])

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
            st.error("讀取失敗，請確認 Excel 第二欄格式。")
            st.stop()

        # 1. 顯示最近 30 期深度走勢 (含 AC 與 連號)
        st.subheader(f"🕵️ 最近 30 期深度開獎走勢 ({game_type})")
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

        # 基礎數據統計
        sums = [sum(r) for r in history]
        avg_sum = np.mean(sums)
        counts = Counter(all_nums)
        
        # 計算生成權重
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

        if st.button("🚀 執行 20,000 次深度模擬與精選"):
            candidate_pool = []
            with st.spinner("AI 正在分析全歷史碰撞矩陣..."):
                # 模擬循環
                for _ in range(20000):
                    res = sorted(random.choices(num_range, weights=weights, k=pick_count))
                    if len(set(res)) != pick_count: continue

                    s = sum(res)
                    ac = GaussResearchEngine.calculate_ac_value(res)
                    consec = GaussResearchEngine.count_consecutive_groups(res)

                    if abs(s - avg_sum) < 30 and ac >= ac_threshold and consec <= 1:
                        stats, max_hit = GaussResearchEngine.get_detailed_comparison(res, history)
                        if max_hit <= max_collision_limit:
                            # 綜合評分系統
                            score = (ac * 10) - (abs(s - avg_sum) * 0.5) + (stats[2] * 2) + (stats[1] * 0.1)
                            candidate_pool.append({
                                "combo": res, "sum": s, "ac": ac, "consec": consec,
                                "max_hit": max_hit, "stats": stats, "score": score
                            })
                            if len(candidate_pool) >= 20: break # 多抓一點來排序

            if not candidate_pool:
                st.warning("條件過嚴，無法生成組合。請放寬總和區間或 AC 門檻。")
            else:
                # 排序選出最優 10 組
                candidate_pool.sort(key=lambda x: x['score'], reverse=True)
                top_10 = candidate_pool[:10]
                best_one = top_10[0]

                # --- 第一推薦精選 ---
                st.markdown("### 🌟 AI 最終黃金精選 (最強推薦)")
                c1, c2, c3 = st.columns([1.5, 1, 1])
                with c1:
                    st.success(f"## ⭐ `{best_one['combo']}`")
                with c2:
                    st.write(f"🔢 總和：**{best_one['sum']}**")
                    st.write(f"📉 AC 值：**{best_one['ac']}**")
                with c3:
                    st.write(f"🏆 歷史最高：**{best_one['max_hit']} 碼**")
                    st.write(f"🔗 連號：**{best_one['consec']} 組**")

                # --- Top 10 命中矩陣分析 ---
                st.markdown("---")
                st.subheader("📊 Top 1-10 候選組合歷史命中矩陣")
                
                matrix_data = []
                for idx, item in enumerate(top_10, 1):
                    s = item['stats']
                    matrix_data.append({
                        "排行": f"Top {idx}",
                        "號碼組合": str(item['combo']),
                        "中 0 碼": f"{s[0]} 次",
                        "中 1 碼": f"{s[1]} 次",
                        "中 2 碼": f"{s[2]} 次",
                        "中 3 碼": f"{s[3]} 次",
                        "中 4 碼": f"{s[4]} 次",
                        "總和": item['sum'],
                        "評分": round(item['score'], 1)
                    })
                st.table(pd.DataFrame(matrix_data))

                # 報告生成
                report_txt = f"Gauss Master Pro V6.5 旗艦精選報告\n"
                report_txt += f"生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                report_txt += "="*60 + "\n"
                report_txt += f"【AI 終極精選】: {best_one['combo']}\n"
                report_txt += f"參數: 總和={best_one['sum']}, AC={best_one['ac']}, 歷史最高={best_one['max_hit']}碼\n"
                report_txt += f"歷史分佈: 中1({best_one['stats'][1]}次), 中2({best_one['stats'][2]}次), 中3({best_one['stats'][3]}次)\n"
                report_txt += "="*60 + "\n\n"
                report_txt += "【Top 10 命中統計矩陣】\n"
                for idx, item in enumerate(top_10, 1):
                    s = item['stats']
                    report_txt += f"Top {idx}: {item['combo']} | 中1-4碼: ({s[1]}, {s[2]}, {s[3]}, {s[4]}) | Score: {item['score']:.1f}\n"

                st.download_button(
                    label="📥 下載完整 V6.5 分析報告",
                    data=report_txt,
                    file_name=f"{game_type}_Gauss_V6_5_Report.txt",
                    mime="text/plain",
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"分析失敗: {e}")
else:
    st.info("請上傳歷史數據以啟動專業級模擬。")

st.markdown("---")
st.caption("Gauss Master Pro V6.5 | 深度歷史比對 | 命中矩陣分析 | 專業統計模型")

