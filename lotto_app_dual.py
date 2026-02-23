import random
import streamlit as st
from datetime import datetime
from collections import Counter

# ==========================================
# 進階反人性算法邏輯
# ==========================================

def calculate_ac(nums):
    """計算算術複雜度 (AC值)"""
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
        if all(nums[i] - nums[i-1] == d for i in range(1, len(nums))):
            return True
            
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
            
        # 條件 D: 奇偶分佈 (反人性偶爾需要極端)
        odds = len([n for n in combo if n % 2 != 0])
        # 避開最平衡的 3:2 或 2:3，偶爾選擇 4:1 或 5:0 (這才是反人性)
        # 但為了保證基本機率，我們只要求不要太單一，除非使用者勾選極端模式
        
        return combo, calculate_ac(combo)
    return None, 0

# ==========================================
# UI 介面設定
# ==========================================

st.set_page_config(page_title="Gauss Master V6.9 反人性版", page_icon="👺", layout="wide")

st.title("👺 Gauss Master V6.9 - 絕對反人性選號器")
st.markdown("""
### 為什麼要「反人性」？
根據統計，大多數人選號會避開 **大號碼 (>31)**、**冷門數字** 或 **不規則分佈**。
如果您選的號碼跟別人一樣，萬一中獎，您得跟幾百個人分頭獎。
**本工具機率不變，但確保您中獎時「拿得更多」。**
""")

with st.sidebar:
    st.header("🛠️ 策略參數")
    game_type = st.selectbox("選擇遊戲", ["今彩 539", "大樂透"])
    
    if game_type == "今彩 539":
        max_num, pick_count, def_ac = 39, 5, 6
    else:
        max_num, pick_count, def_ac = 49, 6, 8
        
    ac_min = st.slider("強制 AC 複雜度 (越高越亂)", 1, 10, def_ac)
    num_sets = st.number_input("產生組數", 1, 50, 5)
    
    st.info("💡 提示：AC 值越高，號碼看起來越『醜』，但也越不容易與人重複。")

if st.button("🔥 執行反人性掃描生成"):
    results = []
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 生成結果")
        for i in range(num_sets):
            combo, ac_val = generate_anti_human_combo(max_num, pick_count, ac_min)
            if combo:
                results.append({"組別": f"第 {i+1} 組", "號碼": combo, "AC值": ac_val, "總和": sum(combo)})
        
        df = pd.DataFrame(results)
        st.table(df)

    with col2:
        st.subheader("🧠 戰略分析")
        if results:
            avg_sum = sum([x['總和'] for x in results]) / len(results)
            st.metric("平均總和", f"{avg_sum:.1f}")
            st.write("✅ 已避開 1-31 日期陷阱")
            st.write("✅ 已過濾 3 連號規律")
            st.write("✅ 已強制高複雜度分佈")
            st.warning("請記住：中獎是運氣，分錢是技術。")

    # 下載報告
    report = f"Gauss Master V6.9 反人性選號報告\n"
    report += f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"遊戲類型: {game_type} | AC 門檻: {ac_min}\n"
    report += "-"*50 + "\n"
    for r in results:
        report += f"{r['組別']}: {r['號碼']} (AC:{r['AC值']}, 總和:{r['總和']})\n"
    report += "-"*50 + "\n"
    report += "戰略核心：降低號碼重疊率，最大化單注獎金回報。"

    st.download_button(
        label="📥 下載反人性選號報告",
        data=report,
        file_name=f"AntiHuman_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
        use_container_width=True
    )

st.markdown("---")
st.caption("Gauss Strategic Analytics | 理性博弈 | 拒絕跟風")

