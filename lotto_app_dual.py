import random
import streamlit as st
import pandas as pd  # 確保導入 pandas
from datetime import datetime
from collections import Counter

# ==========================================
# 核心演算法：反人性選號邏輯
# ==========================================

def calculate_ac(nums):
    """計算算術複雜度 (AC值)"""
    if not nums or len(nums) < 2:
        return 0
    diffs = set()
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    return len(diffs) - (len(nums) - 1)

def has_bad_patterns(nums):
    """偵測並排除容易與大眾重複的號碼模式"""
    nums = sorted(nums)
    
    # 1. 排除三連號 (人性喜歡連號)
    count = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i-1] + 1:
            count += 1
            if count >= 3: return True
        else:
            count = 1
            
    # 2. 排除尾數過度重複 (例如 02, 12, 22)
    tails = [n % 10 for n in nums]
    tail_counts = Counter(tails)
    if any(c >= 3 for c in tail_counts.values()):
        return True
        
    # 3. 排除等差數列 (例如 05, 10, 15, 20...)
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
    """產生一組符合反人性特徵的號碼"""
    for _ in range(5000):  # 限制嘗試次數防止死迴圈
        combo = sorted(random.sample(range(1, max_num+1), pick_count))
        
        # 條件 A: 必須包含 > 31 的號碼 (避開生日選號潮)
        if not any(n > 31 for n in combo):
            continue
            
        # 條件 B: 排除常見模式
        if has_bad_patterns(combo):
            continue
            
        # 條件 C: AC 值門檻過濾
        ac_val = calculate_ac(combo)
        if ac_val < ac_min:
            continue
            
        return combo, ac_val
    return None, 0

# ==========================================
# Streamlit UI 介面
# ==========================================

st.set_page_config(page_title="Gauss V6.9.2 反人性版", page_icon="👺", layout="wide")

st.title("👺 Gauss Master V6.9.2 - 反人性戰略選號器")
st.markdown("這不是預測工具，而是**獎金獨佔最大化策略**工具。")

# 側邊欄設定
with st.sidebar:
    st.header("⚙️ 參數設定")
    game_type = st.selectbox("遊戲模式", ["今彩 539", "大樂透"])
    
    if game_type == "今彩 539":
        max_num, pick_count, default_ac = 39, 5, 6
    else:
        max_num, pick_count, default_ac = 49, 6, 8
        
    ac_min = st.slider("最低 AC 門檻 (越亂越好)", 1, 10, default_ac)
    num_sets = st.number_input("產生組數", 1, 100, 5)

# 主程式執行
if st.button("🚀 執行反人性掃描"):
    results_list = []  # 改名以避免衝突
    
    for i in range(int(num_sets)):
        combo, ac_val = generate_anti_human_combo(max_num, pick_count, ac_min)
        if combo:
            results_list.append({
                "組別": f"No.{i+1}", 
                "推薦號碼": ", ".join(map(str, combo)), 
                "AC複雜度": ac_val, 
                "總和": sum(combo)
            })
    
    # 檢查是否有結果，防止 DataFrame 報錯
    if results_list:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📋 策略建議號碼")
            # 修正處：確保 pd 被正確調用，且 results_list 有內容
            final_df = pd.DataFrame(results_list)
            st.dataframe(final_df, use_container_width=True, hide_index=True)

        with col2:
            st.subheader("💡 戰略分析報告")
            avg_sum = sum([x['總和'] for x in results_list]) / len(results_list)
            st.metric("平均總和", f"{avg_sum:.1f}")
            st.success("✅ 避開日期效應 (>31)")
            st.success(f"✅ 強制複雜度 (AC >= {ac_min})")
            st.info("模式備註：已過濾等差與三連號")

        # 報告下載功能
        report_txt = f"Gauss Master V6.9.2 戰略報告\n生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report_txt += "="*50 + "\n"
        for r in results_list:
            report_txt += f"{r['組別']}: {r['推薦號碼']} | AC: {r['AC複雜度']}\n"
        
        st.download_button(
            "📥 下載戰略分析報告",
            report_txt,
            file_name=f"AntiHuman_Strategy_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.error("❌ 無法在目前的參數下產生號碼，請嘗試調低側邊欄的 AC 門檻。")

st.markdown("---")
st.caption("Gauss Strategic Analytics | 獨立隨機事件博弈策略")

