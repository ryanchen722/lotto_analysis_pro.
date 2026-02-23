import random
import streamlit as st
import pandas as pd
from datetime import datetime
from collections import Counter

# ==========================================
# 進階反人性算法邏輯
# ==========================================

def calculate_ac(nums):
    """計算算術複雜度 (AC值)"""
    if not nums: return 0
    diffs = set()
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    return len(diffs) - (len(nums) - 1)

def has_bad_patterns(nums):
    """偵測是否有容易被大眾選中的模式"""
    nums = sorted(nums)
    
    # 1. 偵測三連號以上 (人性喜歡連號)
    count = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i-1] + 1:
            count += 1
            if count >= 3: return True
        else:
            count = 1
            
    # 2. 偵測尾數重複度 (人性喜歡特定尾數)
    tails = [n % 10 for n in nums]
    tail_counts = Counter(tails)
    if any(count >= 3 for count in tail_counts.values()):
        return True
        
    # 3. 偵測等差數列 (例如 05, 10, 15...)
    if len(nums) >= 5:
        d = nums[1] - nums[0]
        is_arithmetic = True
        for i in range(1, len(nums)):
            if nums[i] - nums[i-1] != d:
                is_arithmetic = False
                break
        if is_arithmetic: return True
            
    return False

def generate_anti_human_combo(max_num, pick_count, ac_min):
    """產生反人性號碼核心函數"""
    attempts = 0
    while attempts < 5000:
        attempts += 1
        combo = sorted(random.sample(range(1, max_num+1), pick_count))
        
        # 條件 A: 至少一個號碼 > 31 (避開生日選號潮)
        if not any(n > 31 for n in combo):
            continue
            
        # 條件 B: 排除常見模式 (連號、尾數、等差)
        if has_bad_patterns(combo):
            continue
            
        # 條件 C: AC 值過濾 (強制高複雜度)
        if calculate_ac(combo) < ac_min:
            continue
            
        return combo, calculate_ac(combo)
    return None, 0

# ==========================================
# UI 介面設定
# ==========================================

st.set_page_config(page_title="Gauss Master V6.9.1 反人性版", page_icon="👺", layout="wide")

st.title("👺 Gauss Master V6.9.1 - 反人性戰略選號器")
st.markdown("""
### 核心戰略：期望值極大化
這個工具**不會**提高中獎機率，但會確保您**避開大眾喜好的號碼**。
當您中獎時，能有效減少與他人平分獎金的機率，從而獲得更高的獎金。
""")

with st.sidebar:
    st.header("🛠️ 策略參數")
    game_type = st.selectbox("選擇遊戲", ["今彩 539", "大樂透"])
    
    if game_type == "今彩 539":
        max_num, pick_count, def_ac = 39, 5, 6
    else:
        max_num, pick_count, def_ac = 49, 6, 8
        
    ac_min = st.slider("最低 AC 複雜度 (越亂越好)", 1, 10, def_ac)
    num_sets = st.number_input("產生組數", 1, 50, 5)
    
    st.info("💡 AC 值（算術複雜度）越高，代表號碼間的距離越隨機，越難被一般人選中。")

if st.button("🔥 啟動反人性掃描生成"):
    results = []
    
    for i in range(int(num_sets)):
        combo, ac_val = generate_anti_human_combo(max_num, pick_count, ac_min)
        if combo:
            results.append({
                "排行": f"組別 {i+1}", 
                "號碼組合": ", ".join(map(str, combo)), 
                "AC值": ac_val, 
                "總和": sum(combo)
            })
    
    if results:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📋 反人性精選清單")
            # 修正處：確保已導入 pandas 並正確轉換
            df_display = pd.DataFrame(results)
            st.dataframe(df_display, use_container_width=True, hide_index=True)

        with col2:
            st.subheader("🧠 戰略分析報告")
            avg_sum = sum([x['總和'] for x in results]) / len(results)
            st.metric("平均總和", f"{avg_sum:.1f}")
            st.success("✅ 排除 1-31 生日選號群")
            st.success("✅ 排除 3 連號以上規律")
            st.success(f"✅ 強制 AC 複雜度 >= {ac_min}")
            st.warning("記住：彩票是博弈，反人性是技術。")

        # 生成下載報告
        report_txt = f"Gauss Master V6.9.1 反人性選號報告\n"
        report_txt += f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report_txt += "="*50 + "\n"
        for r in results:
            report_txt += f"{r['排行']}: [{r['號碼組合']}] | AC:{r['AC值']} | 總和:{r['總和']}\n"
        report_txt += "="*50 + "\n"
        report_txt += "策略關鍵：提高中獎時的獨佔機率。"

        st.download_button(
            label="📥 下載完整選號報告",
            data=report_txt,
            file_name=f"AntiHuman_Report_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.error("目前的 AC 門檻過高，無法產生組合。請嘗試調低側邊欄的 AC 門檻。")

st.markdown("---")
st.caption("Gauss Master Professional | 反大眾行為分析系統 | 數據科學實驗室")

