import streamlit as st
import pandas as pd
import numpy as np
import itertools
from collections import Counter

# ==========================================
# 基本指標
# ==========================================

def get_metrics(nums):

    nums = sorted(nums)

    diffs=set()
    for i in range(len(nums)):
        for j in range(i+1,len(nums)):
            diffs.add(nums[j]-nums[i])

    ac=len(diffs)-(len(nums)-1)

    span=nums[-1]-nums[0]

    odd=sum(n%2 for n in nums)
    even=5-odd

    gaps=[nums[i]-nums[i-1] for i in range(1,5)]

    return{
        "ac":ac,
        "span":span,
        "odd":odd,
        "even":even,
        "sum":sum(nums),
        "gaps":gaps,
        "set":set(nums)
    }

# ==========================================
# 區間模型
# ==========================================

def zone_score(nums):

    z1=sum(1 for n in nums if 1<=n<=13)
    z2=sum(1 for n in nums if 14<=n<=26)
    z3=sum(1 for n in nums if 27<=n<=39)

    pattern=(z1,z2,z3)

    if pattern==(2,2,1):
        return 40
    elif pattern==(1,2,2):
        return 35
    elif pattern==(2,1,2):
        return 25
    else:
        return -10

# ==========================================
# 尾碼模型
# ==========================================

def last_number_score(nums):

    last=nums[-1]

    if 21<=last<=26:
        return 40
    elif 27<=last<=31:
        return 30
    elif 32<=last<=34:
        return 10
    elif last>=35:
        return -20
    else:
        return 5

# ==========================================
# 連號模型
# ==========================================

def streak_score(nums):

    nums=sorted(nums)

    streak=1
    current=1

    for i in range(1,5):

        if nums[i]==nums[i-1]+1:
            current+=1
            streak=max(streak,current)
        else:
            current=1

    if streak==1:
        return 30
    elif streak==2:
        return 25
    else:
        return -50

# ==========================================
# 歷史分析
# ==========================================

def analyze_history(history):

    flat=[n for draw in history for n in draw]

    counts=Counter(flat)

    hot=[n for n,_ in counts.most_common(10)]
    cold=[n for n,_ in counts.most_common()[-10:]]

    return{
        "hot":hot,
        "cold":cold,
        "counts":counts
    }

# ==========================================
# Markov模型
# ==========================================

def markov_matrix(history):

    matrix=np.zeros((40,40))

    for i in range(len(history)-1):

        a=history[i]
        b=history[i+1]

        for x in a:
            for y in b:
                matrix[x][y]+=1

    return matrix

# ==========================================
# 評分系統
# ==========================================

def score_combo(nums,patterns):

    m=get_metrics(nums)

    score=0

    # AC
    score+=m["ac"]*30

    # odd even
    if (m["odd"],m["even"]) in [(3,2),(2,3)]:
        score+=35
    elif (m["odd"],m["even"])==(5,0) or (m["odd"],m["even"])==(0,5):
        score-=40

    # span
    if 18<=m["span"]<=34:
        score+=25

    # sum
    score-=abs(m["sum"]-100)*0.1

    # hot numbers
    hot=len(m["set"].intersection(patterns["hot"]))

    if 1<=hot<=2:
        score+=40
    elif hot>=4:
        score-=30

    # zone
    score+=zone_score(nums)

    # last digit
    score+=last_number_score(nums)

    # streak
    score+=streak_score(nums)

    return score

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Gauss Master Pro V10",layout="wide")

st.title("💎 Gauss Master Pro V10")

uploaded_file=st.file_uploader("上傳歷史資料 Excel",type=["xlsx"])

if uploaded_file:

    df=pd.read_excel(uploaded_file,header=None)

    history=[]

    for val in df.iloc[:,1].dropna().astype(str):

        nums=[int(x) for x in val.replace('、',',').replace(' ',',').split(',') if x.isdigit()]

        if len(nums)==5:
            history.append(sorted(nums))

    patterns=analyze_history(history)

    st.subheader("🔥 熱號")

    st.write(patterns["hot"])

    st.subheader("❄️ 冷號")

    st.write(patterns["cold"])

    st.subheader("⚡ 全組合計算")

    combos=itertools.combinations(range(1,40),5)

    best=[]

    progress=st.progress(0)

    total=575757
    i=0

    for c in combos:

        s=score_combo(c,patterns)

        best.append((c,s))

        i+=1

        if i%10000==0:
            progress.progress(i/total)

    best=sorted(best,key=lambda x:x[1],reverse=True)[:20]

    result=[]

    for c,s in best:

        m=get_metrics(c)

        result.append({

            "組合":", ".join(f"{x:02d}" for x in c),
            "Score":round(s,2),
            "AC":m["ac"],
            "Odd":m["odd"],
            "Even":m["even"],
            "Sum":m["sum"]

        })

    st.subheader("👑 Top 20 推薦組合")

    st.table(pd.DataFrame(result))

    st.success("計算完成")

else:

    st.info("請上傳歷史資料")