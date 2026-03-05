import random
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from collections import Counter

# ==========================================
# 終極演算法：冷熱週期 + 物理慣性 + 熵值擾動
# ==========================================

def get_detailed_metrics(nums):
    """計算物理結構指標"""
    nums = sorted(nums)
    # AC 值 (複雜度)
    diffs = set()
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    ac = len(diffs) - (len(nums) - 1)
    
    span = nums[-1] - nums[0]
    last_digit_zone = (nums[-1] - 1) // 13 
    
    # 連號計算
    max_streak = 1
    current = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i-1] + 1:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 1
            
    # 尾數分析
    last_digits = [n % 10 for n in nums]
    same_tail_count = max(Counter(last_digits).values()) 
    
    return {
        "ac": ac, "span": span, "streak": max_streak, 
        "same_tail": same_tail_count, "last_zone": last_digit_zone,
        "sum": sum(nums), "last_num": nums[-1], "nums_set": set(nums)
    }

def analyze_full_history(history):
    """分析歷史 300 期冷熱趨勢與連號傾向"""
    all_draws = [num for sublist in history for num in sublist]
    counts = Counter(all_draws)
    
    # 冷熱號碼判定 (取頻率最高前 10 名)
    hot_numbers = [num for num, count in counts.most_common(10)]
    
    # 分析連號缺失狀況 (近期 15 期)
    recent_15 = history[:15]
    streak_count = sum(1 for d in recent_15 if any(d[i] == d[i-1] + 1 for i in range(1, 5)))
    # 若近期連號極少，大幅提高連號權重
    streak_tendency = 2.6 if streak_count < 4 else 1.2
    
    return {
        "hot": hot_numbers,
        "streak_tendency": streak_tendency,
        "counts": counts
    }

def get_god_score(m, patterns):
    """V7.0 至尊評分系統"""
    # 1. 物理底盤分數 (AC 值為核心)
    base = m['ac'] * 26
    
    # 2. 連號回歸補償
    if m['streak'] == 2: 
        base += (38 * patterns['streak_tendency'])
    elif m['streak'] >= 3: 
        base -= 75 # 排除極低機率三連號
        
    # 3. 尾數自然重複獎勵
    if m['same_tail'] == 2: 
        base += 35
        
    # 4. 冷熱平衡權重 (關鍵：1-2 個熱號最優)
    hot_in_combo = len(m['nums_set'].intersection(set(patterns['hot'])))
    if 1 <= hot_in_combo <= 2:
        base += 45 
    elif hot_in_combo >= 4:
        base -= 40
        
    # 5. 熵值擾動 (打破同分僵局，模擬微觀不確定性)
    entropy = random.uniform(0.1, 19.9)
    
    # 6. 總和平衡微調 (放寬限制，僅做極微小修正)
    sum_penalty = abs(m['sum'] - 100) * 0.05
    
    return round(base + entropy - sum_penalty, 3)

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Master Pro V7.0", page_icon="💎", layout="wide")

st.title("💎 Gauss Master Pro V7.0 (天機終極至尊版)")
st.markdown("這是一場 **50,000 次模擬** 與 **歷史冷熱規律** 的巔峰對決。我們為你選出結構最強的五組號碼，並融合盲區遺漏數位。")

with st.sidebar:
    st.header("📂 數據核心")
    uploaded_file = st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    st.divider()
    st.write("🔥 **天機決策機制：**")
    st.info("🌡️ **冷熱平衡**：確保組合具備爆發力。")
    st.info("🧬 **破壁技術**：最後一碼分佈完全打散。")
    st.info("🎲 **全息融合**：將被遺忘的號碼重新注入。")
    st.error("⏳ 模擬規模：50,000 次暴力篩選")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        history = []
        for val in df.iloc[:, 1].dropna().astype(str):
            nums = [int(n) for n in val.replace(' ', ',').replace('、', ',').split(',') if n.strip().isdigit()]
            if len(nums) == 5:
                history.append(sorted(nums))
        
        if history:
            patterns = analyze_full_history(history)
            
            # 顯示分析面板
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("核心熱門號碼", f"{patterns['hot'][0]:02d}")
            with c2:
                st.metric("連號引導強度", f"{patterns['streak_tendency']:.1f}x")
            with c3:
                st.write("當前 Top 10 熱號：")
                st.write(", ".join([f"{x:02d}" for x in patterns['hot']]))

            # 階段 1: 五萬次暴力海選 (區間存儲)
            zones_pool = {0: [], 1: [], 2: []}
            progress_bar = st.progress(0)
            
            for i in range(50000):
                combo = sorted(random.sample(range(1, 40), 5))
                m = get_detailed_metrics(combo)
                score = get_god_score(m, patterns)
                
                zone = m['last_zone']
                zones_pool[zone].append({"combo": combo, "score": score, "metrics": m})
                
                # 保留各區間前 100 名
                if len(zones_pool[zone]) > 100:
                    zones_pool[zone] = sorted(zones_pool[zone], key=lambda x: x["score"], reverse=True)[:50]
                
                if i % 10000 == 0:
                    progress_bar.progress((i + 10000) / 50000)

            # 階段 2: 跨區錄取與盲區統計
            final_raw = []
            # 強制錄取一組小結尾 (14-26) 以打破偏誤
            if zones_pool[1]: final_raw.append(zones_pool[1][0])
            # 錄取四組傳統結尾 (27-39)
            for k in range(4):
                if len(zones_pool[2]) > k: final_raw.append(zones_pool[2][k])
            
            initial_all_selected = set()
            for x in final_raw: initial_all_selected.update(x["combo"])
            blind_spot = sorted(list(set(range(1, 40)) - initial_all_selected))

            # 階段 3: 全息融合
            final_fusion = []
            for idx, item in enumerate(final_raw):
                c = list(item["combo"])
                if blind_spot:
                    # 從盲區選取號碼滲透
                    fill = random.choice(blind_spot)
                    if fill not in c:
                        # 隨機替換中間三碼之一，保留底盤結構
                        pos = random.randint(1, 3)
                        c[pos] = fill
                    blind_spot.remove(fill)
                
                c = sorted(c)
                m_f = get_detailed_metrics(c)
                final_fusion.append({
                    "類型": "至尊融合組" if idx > 0 else "破壁小尾組",
                    "推薦組合": ", ".join([f"{x:02d}" for x in c]),
                    "天機動態評分": item["score"],
                    "熱號數": len(set(c).intersection(set(patterns['hot']))),
                    "AC值": m_f["ac"],
                    "最後一碼": c[-1],
                    "總和": m_f["sum"]
                })

            st.subheader("👑 V7.0 天機融合最終精選 Top 5")
            st.table(pd.DataFrame(final_fusion))

            # 盲區深度解析
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.write("🚫 **初始盲區 (未融合前)**")
                st.code(", ".join([f"{x:02d}" for x in sorted(list(set(range(1, 40)) - initial_all_selected))]))
            with c2:
                final_s = set()
                for res in final_fusion:
                    final_s.update([int(n) for n in res["推薦組合"].split(", ")])
                st.write("🧬 **融合後最終遺漏 (覆蓋極大化)**")
                st.code(", ".join([f"{x:02d}" for x in sorted(list(set(range(1, 40)) - final_s))]))

            st.success("✅ 十年約定，終極運算完成。這五組號碼已將所有物理偏誤降至最低。祝你好運！")

        else:
            st.error("Excel 格式錯誤，請檢查第二欄是否為開獎號碼。")
    except Exception as e:
        st.error(f"執行系統異常: {e}")
else:
    st.info("👋 請上傳歷史數據，啟動 V7.0 天機終極至尊模擬。")

st.markdown("---")
st.caption("Gauss Master Pro v7.0 | God Mode Fusion | 50,000 Brute-Force Simulation")

