import random
import pandas as pd
import streamlit as st
import itertools
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
import plotly.graph_objects as go


# ==========================
# 抓取539歷史資料
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
        showlegend=False,
        height=260
    )

    return fig


# ==========================
# 歷史重合分析
# ==========================
def history_overlap(history,combo):

    stats={0:0,1:0,2:0,3:0,4:0,5:0}

    combo=set(combo)

    for draw in history:

        hit=len(combo & set(draw))

        stats[hit]+=1

    return stats


# ==========================
# 最新5期 vs 歷史
# ==========================
def latest_vs_history(history):

    result=[]

    last5=history[-5:][::-1]

    for draw in last5:

        stats={0:0,1:0,2:0,3:0,4:0,5:0}

        for h in history:

            hit=len(set(draw)&set(h))

            stats[hit]+=1

        max_hit=max([k for k,v in stats.items() if v>1])

        result.append((draw,stats,max_hit))

    return result


# ==========================
# 最近5期重合
# ==========================
def recent_overlap(history,combo):

    combo=set(combo)

    last=history[-5:][::-1]

    result=[]

    for i,draw in enumerate(last):

        hit=len(combo & set(draw))

        result.append((i,draw,hit))

    return result


# ==========================
# 回測
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

    return {k:round(v/total*100,2) for k,v in results.items()}


# ==========================
# Streamlit UI
# ==========================
st.set_page_config(page_title="Gauss539",layout="wide")

st.title("🎯 Gauss 539 AI 分析系統")

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


# 最新五期 vs 歷史
st.subheader("最新5期 vs 歷史3000期")

latest_stats=latest_vs_history(history)

for draw,stats,max_hit in latest_stats:

    st.write("號碼:", " ".join([f"{x:02d}" for x in draw]))

    st.write(stats)

    st.write("歷史最大重合:",max_hit)

    st.divider()


# ==========================
# AI預測
# ==========================
if st.button("AI預測"):

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

            st.write("最近5期重合")

            recent=recent_overlap(history,r)

            for idx,draw,hit in recent:

                label="最新期" if idx==0 else f"前{idx}期"

                st.write(label," ".join([f"{x:02d}" for x in draw]),f"→ {hit}顆")

            stats=history_overlap(history,r)

            st.write("歷史3000期重合")

            st.write(stats)

            st.plotly_chart(radar(r),use_container_width=True)


st.divider()


# ==========================
# 回測
# ==========================
if st.button("模型回測 (200期)"):

    stats=backtest_pool(history)

    st.subheader("強勢池命中率 %")

    st.write(stats)