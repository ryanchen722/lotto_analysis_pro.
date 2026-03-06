import random
import pandas as pd
import streamlit as st
from collections import Counter

# ==========================================
# V13 完整 539 模擬 + 最後一碼自然分布
# ==========================================

def get_metrics_batch(combos):
    """批量計算 AC值、跨度、連號、尾數、奇偶"""
    metrics_list=[]
    for nums in combos:
        nums=sorted(nums)
        diffs=set()
        for i in range(len(nums)):
            for j in range(i+1,len(nums)):
                diffs.add(abs(nums[i]-nums[j]))
        ac = len(diffs)-(len(nums)-1)
        span = nums[-1]-nums[0]

        max_streak = 1
        current = 1
        for i in range(1,len(nums)):
            if nums[i]==nums[i-1]+1:
                current+=1
                max_streak=max(max_streak,current)
            else:
                current=1

        last_digits=[n%10 for n in nums]
        same_tail_count=max(Counter(last_digits).values())

        odd=sum(n%2 for n in nums)
        even=len(nums)-odd

        metrics_list.append({
            "ac":ac,"span":span,"streak":max_streak,
            "same_tail":same_tail_count,"sum":sum(nums),
            "last_num":nums[-1],"nums_set":set(nums),
            "odd":odd,"even":even
        })
    return metrics_list

def analyze_full_history(history):
    all_draws=[num for sublist in history for num in sublist]
    counts=Counter(all_draws)
    hot_numbers=[num for num,_ in counts.most_common(10)]
    recent_15=history[:15]
    streak_count=sum(1 for d in recent_15 if any(d[i]==d[i-1]+1 for i in range(1,5)))
    streak_tendency=2.6 if streak_count<4 else 1.2
    return {"hot":hot_numbers,"streak_tendency":streak_tendency,"counts":counts}

def get_god_score_batch(metrics_list,patterns):
    scores=[]
    for m in metrics_list:
        base=m['ac']*26
        if m['streak']==2:
            base+=38*patterns['streak_tendency']
        elif m['streak']>=3:
            base-=75
        if m['same_tail']==2:
            base+=35
        hot_in_combo=len(m['nums_set'].intersection(set(patterns['hot'])))
        if 1<=hot_in_combo<=2:
            base+=45
        elif hot_in_combo>=4:
            base-=40
        base+=max(0,10-abs(m['odd']-m['even']))  # 奇偶平衡
        # 熵值微擾
        entropy=random.uniform(0.1,19.9)
        sum_penalty=abs(m['sum']-100)*0.05
        scores.append(round(base+entropy-sum_penalty,3))
    return scores

def adjust_last_number(combo):
    """最後一碼自然分布策略"""
    middle_nums=combo[:-1]
    # 最後一碼隨機抽 1~39，排除已在中間的數字
    candidates=[n for n in range(1,40) if n not in middle_nums]
    combo[-1]=random.choice(candidates)
    combo.sort()
    return combo

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Master Pro V13", page_icon="💎", layout="wide")
st.title("💎 Gauss Master Pro V13 優化版")
st.markdown("💡 570,000 次完整539組合運算 + 最後一碼自然分布 + 奇偶冷熱調整")

with st.sidebar:
    st.header("📂 數據核心")
    uploaded_file=st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    st.divider()
    st.write("🔥 天機決策機制：")
    st.info("🌡️ 冷熱平衡")
    st.info("🧬 破壁技術")
    st.info("🎲 全息隨機分布")
    st.error("⏳ 模擬規模：570,000 次")

if uploaded_file:
    try:
        df=pd.read_excel(uploaded_file,header=None)
        history=[]
        for val in df.iloc[:,1].dropna().astype(str):
            nums=[int(n) for n in val.replace(' ',' ,').replace('、',',').split(',') if n.strip().isdigit()]
            if len(nums)==5:
                history.append(sorted(nums))

        if history:
            patterns=analyze_full_history(history)
            c1,c2,c3=st.columns(3)
            with c1:
                st.metric("核心熱門號碼",f"{patterns['hot'][0]:02d}")
            with c2:
                st.metric("連號引導強度",f"{patterns['streak_tendency']:.1f}x")
            with c3:
                st.write("Top10 熱號：")
                st.write(", ".join([f"{x:02d}" for x in patterns['hot']]))

            # =======================
            # 批量生成 570,000 組號
            # =======================
            progress_bar=st.progress(0)
            batch_size=10000
            all_top=[]
            for i in range(0,575757,batch_size):
                combos=[sorted(random.sample(range(1,40),5)) for _ in range(batch_size)]
                metrics_list=get_metrics_batch(combos)
                scores=get_god_score_batch(metrics_list,patterns)
                for combo,score,m in zip(combos,scores,metrics_list):
                    combo=adjust_last_number(combo)
                    all_top.append({"combo":combo,"score":score,"metrics":m})
                progress_bar.progress((i+batch_size)/570000)

            # Top100 分數最高組合
            all_top=sorted(all_top,key=lambda x:x['score'],reverse=True)[:100]

            # Top5 精選
            final_top5=all_top[:5]
            final_fusion=[]
            for idx,item in enumerate(final_top5):
                c=list(item["combo"])
                m_f=item["metrics"]
                final_fusion.append({
                    "類型":"至尊融合組" if idx>0 else "破壁小尾組",
                    "推薦組合":", ".join([f"{x:02d}" for x in c]),
                    "天機動態評分":item["score"],
                    "熱號數":len(set(c).intersection(set(patterns['hot']))),
                    "AC值":m_f["ac"],
                    "最後一碼":c[-1],
                    "總和":m_f["sum"],
                    "奇偶":f"{m_f['odd']}:{m_f['even']}"
                })

            st.subheader("👑 V13 天機融合最終精選 Top 5")
            st.table(pd.DataFrame(final_fusion))

            st.divider()
            final_s=set()
            for res in final_fusion:
                final_s.update([int(n) for n in res["推薦組合"].split(", ")])
            st.write("🧬 最終遺漏號碼")
            st.code(", ".join([f"{x:02d}" for x in sorted(list(set(range(1,40))-final_s))]))

            st.success("✅ 570,000 次完整539運算完成，Top5號碼已生成！")

        else:
            st.error("Excel 格式錯誤，請檢查第二欄是否為開獎號碼。")
    except Exception as e:
        st.error(f"執行異常: {e}")
else:
    st.info("請上傳歷史數據 Excel 啟動天機終極模擬。")

st.markdown("---")
st.caption("Gauss Master Pro V13 | 570,000 Brute-Force 539 Simulation")