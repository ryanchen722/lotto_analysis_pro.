import itertools
import pandas as pd
import streamlit as st
import numpy as np
from collections import Counter

# =====================================
# 指標計算
# =====================================

def get_metrics(nums):

    nums=sorted(nums)

    diffs=set()
    for i in range(5):
        for j in range(i+1,5):
            diffs.add(nums[j]-nums[i])

    ac=len(diffs)-4

    gaps=[nums[i]-nums[i-1] for i in range(1,5)]

    odd=sum(n%2 for n in nums)

    return{
        "ac":ac,
        "span":nums[-1]-nums[0],
        "sum":sum(nums),
        "gaps":gaps,
        "odd":odd,
        "even":5-odd,
        "set":set(nums)
    }

# =====================================
# 冷熱動量
# =====================================

def hot_cold_analysis(history):

    last50=history[:50]

    flat=[n for d in last50 for n in d]

    counts=Counter(flat)

    hot=[n for n,_ in counts.most_common(10)]

    cold=[n for n,_ in counts.most_common()[-10:]]

    return hot,cold

# =====================================
# Markov轉移
# =====================================

def markov_matrix(history):

    transition=np.zeros((40,40))

    for i in range(len(history)-1):

        a=history[i]
        b=history[i+1]

        for x in a:
            for y in b:
                transition[x][y]+=1

    return transition

# =====================================
# Gap模型
# =====================================

def gap_score(gaps):

    score=0

    for g in gaps:

        if 3<=g<=12:
            score+=10
        else:
            score-=5

    return score

# =====================================
# V9 評分
# =====================================

def score_v9(nums,metrics,hot,cold,transition):

    score=0

    # AC
    score+=metrics["ac"]*28

    # 奇偶
    if metrics["odd"] in [2,3]:
        score+=30

    # span
    if 20<=metrics["span"]<=34:
        score+=20

    # gap
    score+=gap_score(metrics["gaps"])

    # 熱號
    hot_count=len(metrics["set"].intersection(hot))

    if 1<=hot_count<=2:
        score+=35

    # 冷號
    cold_count=len(metrics["set"].intersection(cold))

    if cold_count==1:
        score+=15

    # Markov
    markov_bonus=0

    for n in nums:
        markov_bonus+=transition[n].sum()

    score+=markov_bonus*0.001

    # sum
    score-=abs(metrics["sum"]-100)*0.1

    return score

# =====================================
# Streamlit
# =====================================

st.title("💎 Gauss Master Pro V9 AI Engine")

file=st.file_uploader("上傳歷史Excel",type=["xlsx"])

if file:

    df=pd.read_excel(file,header=None)

    history=[]

    for v in df.iloc[:,1].dropna().astype(str):

        nums=[int(x) for x in v.replace('、',',').replace(' ',',').split(',') if x.isdigit()]

        if len(nums)==5:
            history.append(sorted(nums))

    hot,cold=hot_cold_analysis(history)

    transition=markov_matrix(history)

    st.write("🔥 熱號",hot)
    st.write("❄️ 冷號",cold)

    st.write("⚡ AI 全組合運算中...")

    best=[]

    for combo in itertools.combinations(range(1,40),5):

        m=get_metrics(combo)

        s=score_v9(combo,m,hot,cold,transition)

        best.append((combo,s))

    best=sorted(best,key=lambda x:x[1],reverse=True)[:20]

    result=[]

    for c,s in best:

        result.append({
            "組合":", ".join(f"{x:02d}" for x in c),
            "Score":round(s,2)
        })

    st.subheader("👑 AI推薦 Top20")

    st.table(pd.DataFrame(result))