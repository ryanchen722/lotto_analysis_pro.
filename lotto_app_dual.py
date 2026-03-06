import random
import pandas as pd
import streamlit as st
import numpy as np
from collections import Counter

# ==========================================
# V12 優化 539 模擬
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
        base+=max(0,10-abs(m['odd']-m['even']))
        entropy=random.uniform(0.1,19.9)
        sum_penalty=abs(m['sum']-100)*0.05
        scores.append(round(base+entropy-sum_penalty,3))
    return scores

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Master Pro V12", page_icon="💎", layout="wide")

st.title("💎 Gauss Master Pro V12 優化版")
st.markdown("💡 570,000 次完整539組合運算 + 優化批量計算 + 冷熱與奇偶調整 + 盲區融合")

with st.sidebar:
    st.header("📂 數據核心")
    uploaded_file=st.file_uploader("上傳歷史數據 Excel", type=["xlsx"])
    st.divider()
    st.write("🔥 天機決策機制：")
    st.info("🌡️ 冷熱平衡")
    st.info("🧬 破壁技術")
    st.info("🎲 全息融合")
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
            for i in range(0,570000,batch_size):
                combos=[sorted(random.sample(range(1,40),5)) for _ in range(batch_size)]
                metrics_list=get_metrics_batch(combos)
                scores=get_god_score_batch(metrics_list,patterns)
                for combo,score in zip(combos,scores):
                    all_top.append({"combo":combo,"score":score,"metrics":metrics_list.pop(0)})
                progress_bar.progress((i+batch_size)/570000)

            all_top=sorted(all_top,key=lambda x:x['score'],reverse=True)[:100]

            # 盲區融合 Top5
            final_raw=all_top[:5]
            initial_all_selected=set()
            for x in final_raw: initial_all_selected.update(x["combo"])
            blind_spot=sorted(list(set(range(1,40))-initial_all_selected))

            final_fusion=[]
            for idx,item in enumerate(final_raw):
                c=list(item["combo"])
                if blind_spot:
                    fill=random.choice(blind_spot)
                    if fill not in c:
                        pos=random.randint(1,3)
                        c[pos]=fill
                    blind_spot.remove(fill)
                c=sorted(c)
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

            st.subheader("👑 V12 天機融合最終精選 Top 5")
            st.table(pd.DataFrame(final_fusion))

            st.divider()
            c1,c2=st.columns(2)
            with c1:
                st.write("🚫 初始盲區")
                st.code(", ".join([f"{x:02d}" for x in sorted(list(set(range(1,40))-initial_all_selected))]))
            with c2:
                final_s=set()
                for res in final_fusion:
                    final_s.update([int(n) for n in res["推薦組合"].split(", ")])
                st.write("🧬 融合後最終遺漏")
                st.code(", ".join([f"{x:02d}" for x in sorted(list(set(range(1,40))-final_s))]))

            st.success("✅ 570,000 次完整539運算完成，Top5號碼已生成！")

        else:
            st.error("Excel 格式錯誤，請檢查第二欄是否為開獎號碼。")

    except Exception as e:
        st.error(f"執行異常: {e}")
else:
    st.info("請上傳歷史數據 Excel 啟動天機終極模擬。")

st.markdown("---")
st.caption("Gauss Master Pro V12 優化版 | 570,000 Brute-Force 539 Simulation")