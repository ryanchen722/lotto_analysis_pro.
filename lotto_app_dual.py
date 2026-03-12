import os
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

CSV_FILE = "539_history.csv"

# ==========================
# 1. 爬蟲
# ==========================
def crawl_539():

    headers = {"User-Agent":"Mozilla/5.0"}
    history=[]

    for page in range(1,120):

        url=f"https://www.pilio.idv.tw/lto539/list.asp?indexpage={page}"

        try:

            r=requests.get(url,headers=headers,timeout=10)

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
# 2. CSV
# ==========================
def load_csv():

    if os.path.exists(CSV_FILE):

        df=pd.read_csv(CSV_FILE)

        return df.values.tolist()

    return []


def save_csv(history):

    df=pd.DataFrame(history,columns=["n1","n2","n3","n4","n5"])

    df.to_csv(CSV_FILE,index=False)


@st.cache_data(ttl=3600)
def fetch_history():

    history=load_csv()

    if len(history)<100:

        history=crawl_539()

        save_csv(history)

    return history


# ==========================
# 3. HMM
# ==========================
def hmm_analysis(history):

    if len(history)<10:
        return sorted(random.sample(range(1,40),15))

    all_nums=[n for d in history for n in d]

    heat=Counter(all_nums)

    avg=len(all_nums)/39

    def get_state(n):

        if heat[n]<avg*0.8:
            return 0
        elif heat[n]>avg*1.2:
            return 2
        else:
            return 1

    states=[tuple(sorted([get_state(n) for n in d])) for d in history]

    trans=defaultdict(lambda: defaultdict(int))

    for i in range(len(states)-1):

        trans[states[i]][states[i+1]]+=1

    curr=states[-1]

    next_state=max(trans[curr],key=trans[curr].get) if curr in trans else (2,2,1,1,0)

    s_map=defaultdict(list)

    for n in range(1,40):
        s_map[get_state(n)].append(n)

    pool=[]

    for s in next_state:

        if s_map[s]:
            pool.append(random.choice(s_map[s]))

    while len(set(pool))<15:

        n=random.randint(1,39)

        if n not in pool:
            pool.append(n)

    pool=[n for n in pool if 1<=n<=39]

    return sorted(list(set(pool))[:15])


# ==========================
# 4. 雷達圖
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
# UI
# ==========================
st.set_page_config(page_title="Gauss 539",layout="wide")

st.title("🎯 Gauss 539 預測系統")

with st.spinner("載入歷史資料..."):

    history=fetch_history()

if not history:

    st.error("抓不到資料")

    st.stop()


# 最新五期
st.subheader("最新五期")

cols=st.columns(5)

last5=history[-5:][::-1]

for i,d in enumerate(last5):

    with cols[i]:

        st.metric("最新期" if i==0 else f"前{i}期"," ".join([f"{x:02d}" for x in d]))

        ac=len(set(abs(a-b) for a,b in itertools.combinations(d,2)))-4

        st.caption(f"和值:{sum(d)} AC:{ac}")


st.divider()


# 預測
if st.button("執行預測"):

    pool=hmm_analysis(history)

    st.info("強勢號碼池: "+", ".join([f"{x:02d}" for x in pool]))

    history_sets=[set(h) for h in history]

    recs=[]

    for _ in range(20000):

        sample=sorted(random.sample(pool,5))

        ac=len(set(abs(a-b) for a,b in itertools.combinations(sample,2)))-4

        span=sample[-1]-sample[0]

        if 4<=ac<=8 and 20<=span<=32:

            if set(sample) not in history_sets:

                if sample not in recs:
                    recs.append(sample)

        if len(recs)>=3:
            break

    if len(recs)==0:

        for _ in range(3):
            recs.append(sorted(random.sample(pool,5)))

    cols=st.columns(3)

    for i,r in enumerate(recs):

        with cols[i]:

            st.success(f"推薦組合 {i+1}")

            st.markdown(f"### {' '.join([f'{x:02d}' for x in r])}")

            st.plotly_chart(radar(r),use_container_width=True)


st.divider()


# 歷史資料
st.subheader("歷史資料")

df=pd.DataFrame(history[::-1],columns=["號1","號2","號3","號4","號5"])

st.dataframe(df,height=400,use_container_width=True)


# CSV下載
csv=df.to_csv(index=False).encode("utf-8")

st.download_button(
    "下載 CSV",
    csv,
    "539_history.csv",
    "text/csv"
)