import random
import streamlit as st
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
# 核心分數模型（強化版）
# ==============================
def score_numbers(history):

    freq120=Counter([n for d in history[-120:] for n in d])
    freq30=Counter([n for d in history[-30:] for n in d])
    recent5=Counter([n for d in history[-5:] for n in d])

    score={}

    for n in range(1,40):

        hot = freq120[n]/120
        trend = freq30[n]/30

        # 冷號（多久沒出）
        last_seen=50
        for i,d in enumerate(reversed(history)):
            if n in d:
                last_seen=i
                break

        cold = min(last_seen/40,1)

        # 冷號爆發（超過20期沒出 → 加強）
        cold_boost = 0.3 if last_seen>20 else 0

        # 最新期影響
        recent_boost = recent5[n]*0.15

        score[n]=(
            hot*0.35 +
            trend*0.25 +
            cold*0.25 +
            cold_boost +
            recent_boost
        )

    return score


# ==============================
# AI推薦（核心升級）
# ==============================
def ai_recommend(history):

    score=score_numbers(history)
    last_draw=history[-1]

    combos=set()

    for _ in range(120000):

        combo=random.sample(range(1,40),5)

        # 避開上期（70%機率）
        if random.random()<0.7:
            combo=[n for n in combo if n not in last_draw]

        while len(combo)<5:
            combo=list(set(combo+[random.randint(1,39)]))

        combo=tuple(sorted(combo))

        combos.add(combo)

    combos=list(combos)

    # 評分（加入命中導向）
    scored=[]

    for c in combos:

        base=sum(score[n] for n in c)

        # 結構加分（連號 / 尾數）
        pair_bonus=0
        for i in range(4):
            if c[i+1]-c[i]==1:
                pair_bonus+=0.3

        tail=len(set([n%10 for n in c]))
        tail_bonus = 0.2 if tail<=3 else 0

        final_score=base + pair_bonus + tail_bonus

        scored.append((c,final_score))

    scored=sorted(scored,key=lambda x:x[1],reverse=True)

    # 🔥 關鍵：不要鎖死
    top_pool=scored[:50]

    # 隨機抽3組（重點）
    picks=random.sample(top_pool,3)

    top3=[list(c) for c,_ in picks]
    top10=[list(c) for c,_ in scored[:10]]

    return top3,top10


# ==============================
# UI
# ==============================
st.set_page_config(layout="wide")
st.title("🔥 539 AI 預測 V40 Ultimate")

history=fetch_history()

st.markdown(f"### 📊 資料量：{len(history)}期")

# 最新五期
st.markdown("### 📅 最新五期")
cols=st.columns(5)

for i,d in enumerate(history[-5:][::-1]):
    cols[i].metric(f"第{i+1}期"," ".join(f"{x:02d}" for x in d))


# 按鈕
if st.button("🚀 開始AI預測"):

    top3,top10=ai_recommend(history)

    st.divider()

    # 推薦
    st.markdown("### 🎯 AI推薦（動態）")

    cols=st.columns(3)

    for i,r in enumerate(top3):
        with cols[i]:
            st.success(" ".join(f"{x:02d}" for x in r))

    st.divider()

    # Top10
    with st.expander("📊 Top10參考"):
        for r in top10:
            st.write(" ".join(f"{x:02d}" for x in r))