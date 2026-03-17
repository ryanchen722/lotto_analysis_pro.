import random
import streamlit as st
import itertools
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter
import plotly.graph_objects as go

# ==============================
# 抓歷史資料
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
# 分數模型
# ==============================
def score_numbers(history):

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

        score[n]=0.4*hot+0.3*trend+0.3*cold

    return score


# ==============================
# 位置模型
# ==============================
def position_model(history):

    pos=[Counter() for _ in range(5)]

    for d in history:
        d=sorted(d)
        for i,n in enumerate(d):
            pos[i][n]+=1

    return pos


# ==============================
# ⭐ 連號偵測
# ==============================
def find_pairs(history):

    pair_count=Counter()

    for d in history[-200:]:
        for i in range(4):
            if d[i+1]-d[i]==1:
                pair=(d[i],d[i+1])
                pair_count[pair]+=1

    return [p for p,_ in pair_count.most_common(5)]


# ==============================
# ⭐ 尾數群聚
# ==============================
def tail_cluster(history):

    tail=Counter()

    for d in history[-200:]:
        for n in d:
            tail[n%10]+=1

    return [t for t,_ in tail.most_common(3)]


# ==============================
# AI推薦（V38）
# ==============================
def ai_recommend(history):

    score=score_numbers(history)
    pos=position_model(history)

    pairs=find_pairs(history)
    tails=tail_cluster(history)

    ranges=[(1,10),(5,15),(10,25),(20,35),(25,39)]

    combos=set()

    for _ in range(90000):

        combo=[]

        # 位置選號
        for i in range(5):

            candidates=list(range(1,40))
            weights=[score[n]*(pos[i][n]+1) for n in candidates]

            pick=random.choices(candidates,weights=weights,k=1)[0]
            combo.append(pick)

        # 加入連號（30%機率）
        if pairs and random.random()<0.3:
            pair=random.choice(pairs)
            combo[3]=pair[0]
            combo[4]=pair[1]

        # 尾數群聚（40%機率）
        if random.random()<0.4:
            t=random.choice(tails)
            combo[random.randint(0,4)]=random.choice([x for x in range(1,40) if x%10==t])

        combo=sorted(set(combo))

        while len(combo)<5:
            combo.append(random.randint(1,39))
            combo=list(set(combo))

        combo=tuple(sorted(combo))

        # 區間限制
        ok=True
        for i,n in enumerate(combo):
            if not (ranges[i][0]<=n<=ranges[i][1]):
                ok=False
                break

        if not ok:
            continue

        combos.add(combo)

    combos=list(combos)

    scored=[(c,sum(score[n] for n in c)) for c in combos]
    scored=sorted(scored,key=lambda x:x[1],reverse=True)

    top10=[list(c) for c,_ in scored[:10]]
    top3=top10[:3]

    return top3,top10,pairs,tails


# ==============================
# UI
# ==============================
st.set_page_config(layout="wide")
st.title("🔥 539 AI 預測 V38（命中強化版）")

history=fetch_history()

st.write("歷史期數：",len(history))

st.subheader("📅 最新五期")
cols=st.columns(5)
for i,d in enumerate(history[-5:][::-1]):
    cols[i].metric(f"第{i+1}期"," ".join(f"{x:02d}" for x in d))


if st.button("🚀 AI預測"):

    top3,top10,pairs,tails=ai_recommend(history)

    st.divider()

    st.subheader("🎯 AI推薦")
    cols=st.columns(3)

    for i,r in enumerate(top3):
        cols[i].subheader(" ".join(f"{x:02d}" for x in r))

    st.divider()

    with st.expander("📊 進階分析"):

        st.write("🔥 熱門連號：",pairs)
        st.write("🔥 尾數群聚：",tails)

        st.write("Top10：")
        for r in top10:
            st.write(" ".join(f"{x:02d}" for x in r))