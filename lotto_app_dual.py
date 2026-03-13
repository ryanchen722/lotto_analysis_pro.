import random
import pandas as pd
import streamlit as st
import itertools
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter
import plotly.graph_objects as go


# ==========================
# 抓歷史資料
# ==========================
@st.cache_data(ttl=3600)
def fetch_history():

    headers={"User-Agent":"Mozilla/5.0"}
    history=[]

    for page in range(1,120):

        url=f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={page}"

        r=requests.get(url,headers=headers)
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

    return history[::-1]


# ==========================
# Score模型
# ==========================
def score_numbers(history):

    all_nums=[n for d in history for n in d]

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

        if n<=13:
            zone=0.33
        elif n<=26:
            zone=0.33
        else:
            zone=0.33

        score[n]=(
            0.35*hot+
            0.25*trend+
            0.20*cold+
            0.20*zone
        )

    return score


# ==========================
# 強勢池
# ==========================
def strong_pool(history):

    score=score_numbers(history)

    sorted_nums=sorted(score.items(),key=lambda x:x[1],reverse=True)

    return [n for n,s in sorted_nums[:15]],score


# ==========================
# 組合分數
# ==========================
def combo_score(combo,score):

    base=sum(score[n] for n in combo)

    ac=len(set(abs(a-b) for a,b in itertools.combinations(combo,2)))-4

    span=combo[-1]-combo[0]

    odd=len([n for n in combo if n%2])

    bonus=0

    if 4<=ac<=8:
        bonus+=0.3

    if 20<=span<=32:
        bonus+=0.3

    if odd in [2,3]:
        bonus+=0.3

    return base+bonus


# ==========================
# 推薦
# ==========================
def generate_recommendations(history):

    pool,score=strong_pool(history)

    candidates=[]

    for _ in range(20000):

        combo=sorted(random.sample(pool,5))

        sc=combo_score(combo,score)

        candidates.append((combo,sc))

    candidates=sorted(candidates,key=lambda x:x[1],reverse=True)

    results=[]
    used=set()

    for combo,sc in candidates:

        t=tuple(combo)

        if t not in used:

            results.append(combo)

            used.add(t)

        if len(results)==3:
            break

    return pool,results


# ==========================
# 雷達圖
# ==========================
def radar(nums):

    ac=len(set(abs(a-b) for a,b in itertools.combinations(nums,2)))-4

    metrics=[
        len([n for n in nums if n>=20])/5,
        len([n for n in nums if n%2])/5,
        (sum(nums)-15)/170,
        (nums[-1]-nums[0])/38,
        ac/8
    ]

    fig=go.Figure(data=go.Scatterpolar(
        r=metrics,
        theta=['大','奇','和','跨','AC'],
        fill='toself'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False,range=[0,1])),
        showlegend=False
    )

    return fig


# ==========================
# 歷史重合
# ==========================
def history_overlap(history,combo):

    stats={0:0,1:0,2:0,3:0,4:0,5:0}

    for draw in history:

        hit=len(set(combo)&set(draw))

        stats[hit]+=1

    return stats


# ==========================
# 最近5期重合
# ==========================
def recent_overlap(history,combo):

    last=history[-5:][::-1]

    result=[]

    for draw in last:

        hit=len(set(combo)&set(draw))

        result.append((draw,hit))

    return result


# ==========================
# Streamlit
# ==========================
st.title("539 AI 分析")

history=fetch_history()

st.write("歷史期數:",len(history))


st.subheader("最新五期")

for d in history[-5:][::-1]:

    st.write(" ".join([f"{x:02d}" for x in d]))


if st.button("AI預測"):

    pool,recs=generate_recommendations(history)

    st.info("強勢池: "+",".join([f"{x:02d}" for x in pool]))

    cols=st.columns(3)

    for i,r in enumerate(recs):

        with cols[i]:

            st.success("推薦")

            st.markdown("### "+" ".join([f"{x:02d}" for x in r]))

            st.write("最近5期")

            for draw,hit in recent_overlap(history,r):

                st.write(" ".join([f"{x:02d}" for x in draw]),"→",hit)

            st.write("歷史3000期")

            st.write(history_overlap(history,r))

            st.plotly_chart(radar(r))