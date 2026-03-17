import random
import streamlit as st
import itertools
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter

# ==============================
# 抓資料
# ==============================
@st.cache_data(ttl=3600)
def fetch_history():
    headers={"User-Agent":"Mozilla/5.0"}
    history=[]

    for page in range(1,120):
        url=f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={page}"

        try:
            r=requests.get(url,headers=headers,timeout=10)
            r.encoding="big5"

            soup=BeautifulSoup(r.text,"lxml")
            rows=soup.find_all("tr")

            for row in rows:
                nums=re.findall(r'\b\d{1,2}\b',row.text)

                if len(nums)>=5:
                    n=list(map(int,nums[-5:]))
                    n=[x for x in n if 1<=x<=39]

                    if len(n)==5:
                        draw=sorted(n)
                        if draw not in history:
                            history.append(draw)

        except:
            break

    return history[::-1]


# ==============================
# 自學權重
# ==============================
def learn_weights(history):

    weights={
        "hot":0.4,
        "trend":0.3,
        "cold":0.3,
        "pair":0.3,
        "tail":0.3
    }

    recent=history[-200:]
    pair_count=0

    for d in recent:
        for i in range(4):
            if d[i+1]-d[i]==1:
                pair_count+=1

    if pair_count>60:
        weights["pair"]=0.45
    else:
        weights["pair"]=0.2

    weights["tail"]=0.4 if pair_count>60 else 0.25

    return weights


# ==============================
# 分數模型
# ==============================
def score_numbers(history,weights):

    freq120=Counter([n for d in history[-120:] for n in d])
    freq30=Counter([n for d in history[-30:] for n in d])

    score={}

    for n in range(1,40):

        hot=freq120[n]/120
        trend=freq30[n]/30

        last_seen=0
        for i,d in enumerate(reversed(history)):
            if n in d:
                last_seen=i
                break

        cold=min(last_seen/40,1)

        score[n]=(
            weights["hot"]*hot+
            weights["trend"]*trend+
            weights["cold"]*cold
        )

    return score


# ==============================
# 連號
# ==============================
def find_pairs(history):

    pair=Counter()

    for d in history[-200:]:
        for i in range(4):
            if d[i+1]-d[i]==1:
                pair[(d[i],d[i+1])]+=1

    return [p for p,_ in pair.most_common(5)]


# ==============================
# 尾數
# ==============================
def tail_cluster(history):

    tail=Counter()

    for d in history[-200:]:
        for n in d:
            tail[n%10]+=1

    return [t for t,_ in tail.most_common(3)]


# ==============================
# AI推薦
# ==============================
def ai_recommend(history):

    weights=learn_weights(history)
    score=score_numbers(history,weights)

    pairs=find_pairs(history)
    tails=tail_cluster(history)

    combos=set()

    for _ in range(80000):

        combo=random.sample(range(1,40),5)

        # 連號
        if pairs and random.random()<weights["pair"]:
            p=random.choice(pairs)
            combo[0]=p[0]
            combo[1]=p[1]

        # 尾數
        if random.random()<weights["tail"]:
            t=random.choice(tails)
            combo[random.randint(0,4)]=random.choice([x for x in range(1,40) if x%10==t])

        combo=tuple(sorted(set(combo)))

        while len(combo)<5:
            combo=tuple(sorted(set(list(combo)+[random.randint(1,39)])))

        combos.add(combo)

    combos=list(combos)

    scored=[(c,sum(score[n] for n in c)) for c in combos]
    scored=sorted(scored,key=lambda x:x[1],reverse=True)

    top10=[list(c) for c,_ in scored[:10]]
    top3=top10[:3]

    return top3,top10,weights,pairs,tails


# ==============================
# UI
# ==============================
st.set_page_config(layout="wide")
st.title("🔥 539 AI 預測 V39 UI Pro")

history=fetch_history()

st.markdown(f"### 📊 歷史資料：{len(history)} 期")

# 最新五期
st.markdown("### 📅 最新五期")
cols=st.columns(5)

for i,d in enumerate(history[-5:][::-1]):
    cols[i].metric(f"第{i+1}期"," ".join(f"{x:02d}" for x in d))


# 按鈕
if st.button("🚀 AI開始預測"):

    top3,top10,weights,pairs,tails=ai_recommend(history)

    st.divider()

    # 權重
    st.markdown("### 🧠 AI學習權重")

    for k,v in weights.items():
        st.progress(v,text=f"{k}：{v:.2f}")

    st.divider()

    # 推薦
    st.markdown("### 🎯 AI推薦號碼")

    cols=st.columns(3)

    for i,r in enumerate(top3):
        with cols[i]:
            st.markdown("#### 🎯 推薦組合")
            st.success(" ".join(f"{x:02d}" for x in r))

    st.divider()

    # 結構
    st.markdown("### 📈 結構分析")

    col1,col2=st.columns(2)

    with col1:
        st.markdown("#### 🔥 熱門連號")
        for p in pairs:
            st.success(f"{p[0]:02d} - {p[1]:02d}")

    with col2:
        st.markdown("#### 🔥 尾數群聚")
        st.info(" / ".join(str(t) for t in tails))

    st.divider()

    # Top10
    with st.expander("📊 Top10完整預測"):
        for r in top10:
            st.write(" ".join(f"{x:02d}" for x in r))