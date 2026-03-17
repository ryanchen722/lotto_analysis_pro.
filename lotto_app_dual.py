import random
import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter
import json
import os

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
# 尾數學習（V42核心）
# ==============================
def learn_tail_distribution(history):

    recent = history[-100:]
    tails = [n%10 for d in recent for n in d]
    counter = Counter(tails)

    total = sum(counter.values())

    prob = {t: counter[t]/total for t in range(10)}

    return prob


# ==============================
# 分數模型（動態）
# ==============================
def score_numbers(history):

    freq120=Counter([n for d in history[-120:] for n in d])
    freq30=Counter([n for d in history[-30:] for n in d])
    recent5=Counter([n for d in history[-5:] for n in d])

    score={}

    for n in range(1,40):

        hot=freq120[n]/120
        trend=freq30[n]/30

        last_seen=50
        for i,d in enumerate(reversed(history)):
            if n in d:
                last_seen=i
                break

        cold=min(last_seen/40,1)
        cold_boost = 0.3 if last_seen>20 else 0
        recent_boost = recent5[n]*0.3  # 提高影響力

        score[n]=(
            hot*0.3 +
            trend*0.2 +
            cold*0.2 +
            cold_boost +
            recent_boost
        )

    return score


# ==============================
# 分佈限制（升級版）
# ==============================
def valid_combo(combo):

    # 連號限制
    pair_count=sum(1 for i in range(4) if combo[i+1]-combo[i]==1)
    if pair_count>=3:
        return False

    # 奇偶
    odd=sum(1 for n in combo if n%2==1)
    if not (odd==2 or odd==3):
        return False

    # 區間
    zone1=sum(1 for n in combo if 1<=n<=13)
    zone2=sum(1 for n in combo if 14<=n<=26)
    zone3=sum(1 for n in combo if 27<=n<=39)

    if min(zone1,zone2,zone3)==0:
        return False

    # 和值
    s=sum(combo)
    if not (80<=s<=140):
        return False

    return True


# ==============================
# AI推薦（進化版）
# ==============================
def ai_recommend(history):

    score=score_numbers(history)
    tail_prob=learn_tail_distribution(history)
    last_draw=history[-1]

    combos=set()

    for _ in range(150000):

        combo=random.sample(range(1,40),5)

        if random.random()<0.7:
            combo=[n for n in combo if n not in last_draw]

        while len(combo)<5:
            combo=list(set(combo+[random.randint(1,39)]))

        combo=tuple(sorted(combo))

        if not valid_combo(combo):
            continue

        combos.add(combo)

    combos=list(combos)

    scored=[]

    for c in combos:

        base=sum(score[n] for n in c)

        # 尾數評分（學習）
        tail_score=sum(tail_prob[n%10] for n in c)

        # 連號評分
        pair_count=sum(1 for i in range(4) if c[i+1]-c[i]==1)

        if pair_count==1:
            pair_bonus=0.4
        elif pair_count==2:
            pair_bonus=0.2
        else:
            pair_bonus=0

        final_score=base + tail_score + pair_bonus

        scored.append((c,final_score))

    scored=sorted(scored,key=lambda x:x[1],reverse=True)

    top_pool=scored[:50]
    picks=random.sample(top_pool,3)

    top3=[list(c) for c,_ in picks]
    top10=[list(c) for c,_ in scored[:10]]

    return top3,top10


# ==============================
# UI
# ==============================
st.set_page_config(layout="wide")
st.title("🔥 539 AI 預測 V42 Evolution")

history=fetch_history()

st.markdown(f"### 📊 資料量：{len(history)}期")

# 最新五期
st.markdown("### 📅 最新五期")
cols=st.columns(5)

for i,d in enumerate(history[-5:][::-1]):
    cols[i].metric(f"第{i+1}期"," ".join(f"{x:02d}" for x in d))


# 執行
if st.button("🚀 AI開始預測"):

    top3,top10=ai_recommend(history)

    st.divider()

    st.markdown("### 🎯 AI推薦（V42自我學習）")

    cols=st.columns(3)

    for i,r in enumerate(top3):
        with cols[i]:
            st.success(" ".join(f"{x:02d}" for x in r))

    st.divider()

    with st.expander("📊 Top10參考"):
        for r in top10:
            st.write(" ".join(f"{x:02d}" for x in r))