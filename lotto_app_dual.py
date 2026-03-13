import random
import pandas as pd
import streamlit as st
import numpy as np
import itertools
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
import plotly.graph_objects as go


# ==========================
# 抓539歷史資料
# ==========================
@st.cache_data(ttl=3600)
def fetch_539_history():

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

                    numbers=list(map(int,nums[-5:]))

                    numbers=[n for n in numbers if 1<=n<=39]

                    if len(numbers)==5:

                        draw=sorted(numbers)

                        if draw not in history:
                            history.append(draw)

        except:
            break

    return history[::-1]


# ==========================
# HMM 強勢號碼池
# ==========================
def hmm_analysis(history):

    if len(history)<10:
        return sorted(random.sample(range(1,40),15))

    all_nums=[n for d in history for n in d]

    heat=Counter(all_nums)

    avg=len(all_nums)/39

    def state(n):

        if heat[n]<avg*0.8:
            return 0
        elif heat[n]>avg*1.2:
            return 2
        else:
            return 1

    states=[tuple(sorted([state(n) for n in d])) for d in history]

    trans=defaultdict(lambda: defaultdict(int))

    for i in range(len(states)-1):
        trans[states[i]][states[i+1]]+=1

    curr=states[-1]

    next_state=max(trans[curr],key=trans[curr].get) if curr in trans else (2,2,1,1,0)

    s_map=defaultdict(list)

    for n in range(1,40):
        s_map[state(n)].append(n)

    pool=[]

    for s in next_state:

        if s_map[s]:
            pool.append(random.choice(s_map[s]))

    while len(set(pool))<15:

        n=random.randint(1,39)

        if n not in pool:
            pool.append(n)

    return sorted(list(set(pool))[:15])


# ==========================
# 雷達圖
# ==========================
def radar(nums):

    ac=len(set(abs(a-b) for a,b in itertools.combinations(nums,2)))-4

    metrics=[
        len([n for n in nums if n>=20])/5,
        len([n for n in nums if n%2!=0])/5,
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
        showlegend=False,
        height=250
    )

    return fig


# ==========================
# 歷史重合分析
# ==========================
def history_overlap_stats(history, combo):

    stats={0:0,1:0,2:0,3:0,4:0,5:0}

    combo=set(combo)

    for draw in history:

        hit=len(combo & set(draw))

        stats[hit]+=1

    return stats


# ==========================
# 回測強勢池
# ==========================
def backtest_pool(history,window=200):

    results={0:0,1:0,2:0,3:0,4:0,5:0}

    for i in range(len(history)-window,len(history)-1):

        train=history[:i]

        real=history[i]

        pool=hmm_analysis(train)

        hit=len(set(pool)&set(real))

        results[hit]+=1

    total=sum(results.values())

    stats={k:round(v/total*100,2) for k,v in results.items()}

    return stats


# ==========================
# UI
# ==========================
st.set_page_config(page_title="Gauss 539",layout="wide")

st.title("🎯 Gauss 539 預測系統")


with st.spinner("抓取歷史資料..."):

    history=fetch_539_history()

st.write("資料期數:",len(history))


# 最新五期
st.subheader("最新五期")

cols=st.columns(5)

for i,d in enumerate(history[-5:][::-1]):

    with cols[i]:

        st.metric("最新期" if i==0 else f"前{i}期"," ".join([f"{x:02d}" for x in d]))


st.divider()


# ==========================
# 預測
# ==========================
if st.button("執行預測"):

    pool=hmm_analysis(history)

    st.info("強勢號碼池: "+", ".join([f"{x:02d}" for x in pool]))

    recs=[]

    for _ in range(20000):

        sample=sorted(random.sample(pool,5))

        ac=len(set(abs(a-b) for a,b in itertools.combinations(sample,2)))-4

        span=sample[-1]-sample[0]

        if 4<=ac<=8 and 20<=span<=32:

            if sample not in recs:
                recs.append(sample)

        if len(recs)>=3:
            break

    cols=st.columns(3)

    for i,r in enumerate(recs):

        with cols[i]:

            st.success(f"推薦組合 {i+1}")

            st.markdown(f"### {' '.join([f'{x:02d}' for x in r])}")

            stats=history_overlap_stats(history,r)

            st.write("歷史3000期重合分析")

            st.write({
                "0顆":stats[0],
                "1顆":stats[1],
                "2顆":stats[2],
                "3顆":stats[3],
                "4顆":stats[4],
                "5顆":stats[5]
            })

            max_hit=max([k for k,v in stats.items() if v>0])

            st.write("歷史最大重合:",max_hit)

            st.plotly_chart(radar(r),use_container_width=True)


st.divider()


# ==========================
# 回測
# ==========================
if st.button("回測模型(最近200期)"):

    stats=backtest_pool(history,200)

    st.subheader("強勢池命中率 %")

    st.write(stats)