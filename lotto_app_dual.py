import random
import streamlit as st
import itertools
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter
import plotly.graph_objects as go


# ==========================
# 抓取歷史資料
# ==========================
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


# ==========================
# Score模型
# ==========================
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

        score[n]=(
            0.4*hot+
            0.3*trend+
            0.3*cold
        )

    return score


# ==========================
# AI熱門球機率
# ==========================
def hot_probability(history):

    score=score_numbers(history)

    total=sum(score.values())

    probs={}

    for n,s in score.items():

        probs[n]=(s/total)*100

    probs=sorted(probs.items(),key=lambda x:x[1],reverse=True)

    return probs[:10]


# ==========================
# 強勢池與核心
# ==========================
def strong_pool(history):

    score=score_numbers(history)

    sorted_nums=sorted(score.items(),key=lambda x:x[1],reverse=True)

    pool=[n for n,s in sorted_nums[:18]]
    core=[n for n,s in sorted_nums[:5]]

    return pool,core,score


# ==========================
# 結構預測
# ==========================
def structure_predict(history):

    odd=[]
    span=[]

    for d in history[-200:]:

        odd.append(len([n for n in d if n%2]))
        span.append(max(d)-min(d))

    odd_mode=Counter(odd).most_common(1)[0][0]
    span_avg=int(sum(span)/len(span))

    return odd_mode,span_avg


# ==========================
# 組合評分
# ==========================
def combo_score(combo,score):

    base=sum(score[n] for n in combo)

    ac=len(set(abs(a-b) for a,b in itertools.combinations(combo,2)))-4

    bonus=0

    if 4<=ac<=8:
        bonus+=0.5

    return base+bonus


# ==========================
# AI推薦引擎
# ==========================
def ai_recommend(history):

    pool,core,score=strong_pool(history)

    odd_target,span_target=structure_predict(history)

    combos=[]

    for _ in range(60000):

        c=set(random.sample(core,2))

        while len(c)<5:
            c.add(random.choice(pool))

        c=tuple(sorted(c))

        odd=len([n for n in c if n%2])
        span=c[-1]-c[0]

        if abs(odd-odd_target)<=1 and abs(span-span_target)<=6:

            sc=combo_score(c,score)

            combos.append((c,sc))

    combos=sorted(combos,key=lambda x:x[1],reverse=True)

    top100=[c for c,s in combos[:100]]

    freq=Counter(top100)

    stable=sorted(freq.items(),key=lambda x:x[1],reverse=True)

    top10=[list(c) for c,_ in stable[:10]]

    top3=[
        top10[0],
        top10[3],
        top10[6]
    ]

    return pool,core[:2],top3,top10


# ==========================
# 四碼命中引擎
# ==========================
def four_hit_engine(history,top10):

    results=[]

    for combo in top10:

        four_hits=0

        for draw in history:

            if len(set(combo)&set(draw))>=4:

                four_hits+=1

        results.append((combo,four_hits))

    results=sorted(results,key=lambda x:x[1],reverse=True)

    return results[:5]


# ==========================
# 歷史重合分析
# ==========================
def history_overlap(history,combo):

    stats={0:0,1:0,2:0,3:0,4:0,5:0}

    for draw in history:

        hit=len(set(combo)&set(draw))

        stats[hit]+=1

    return stats


# ==========================
# 最近五期重合
# ==========================
def recent_overlap(history,combo):

    last=history[-5:][::-1]

    result=[]

    for draw in last:

        hit=len(set(combo)&set(draw))

        result.append((draw,hit))

    return result


# ==========================
# 冷號爆發預測
# ==========================
def cold_burst(history):

    last_seen={}

    for n in range(1,40):

        for i,d in enumerate(reversed(history)):

            if n in d:
                last_seen[n]=i
                break

    cold_candidates=sorted(last_seen.items(),key=lambda x:x[1],reverse=True)

    return [n for n,_ in cold_candidates[:6]]


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
# Streamlit UI
# ==========================
st.set_page_config(page_title="539 AI V34",layout="wide")

st.title("🎯 539 AI V34 預測系統")

history=fetch_history()

st.write("歷史期數:",len(history))


# 最新五期
st.subheader("📅 最新五期")

cols=st.columns(5)

for i,d in enumerate(history[-5:][::-1]):

    with cols[i]:

        st.metric(
            label=f"第 {i+1} 期",
            value=" ".join([f"{x:02d}" for x in d])
        )


# AI預測
if st.button("🚀 AI預測"):

    pool,core,recs,top10=ai_recommend(history)

    st.info("強勢池: "+",".join([f"{x:02d}" for x in pool]))

    st.success("AI核心號碼: "+" ".join([f"{x:02d}" for x in core]))


    # AI熱門球
    st.subheader("🔥 AI熱門球預測機率")

    hot=hot_probability(history)

    for n,p in hot:

        st.write(f"{n:02d} → {p:.2f} %")


    # Top10
    st.subheader("📊 Top10推薦")

    for r in top10:
        st.write(" ".join([f"{x:02d}" for x in r]))


    # AI推薦
    st.subheader("🎯 AI推薦3組")

    cols=st.columns(3)

    for i,r in enumerate(recs):

        with cols[i]:

            st.markdown("### "+" ".join([f"{x:02d}" for x in r]))

            st.write("最近5期")

            for draw,hit in recent_overlap(history,r):

                st.write(" ".join([f"{x:02d}" for x in draw]),"→",hit)

            st.write("歷史3000期")

            st.write(history_overlap(history,r))

            st.plotly_chart(radar(r),use_container_width=True)


    # 四碼引擎
    st.subheader("🎯 四碼命中引擎")

    four=four_hit_engine(history,top10)

    for combo,count in four:

        st.write(" ".join([f"{x:02d}" for x in combo]),"→ 歷史4碼命中",count,"次")


    # 冷號爆發
    st.subheader("❄️ 冷號爆發預測")

    cold_nums=cold_burst(history)

    st.write("可能爆發冷號："," ".join([f"{x:02d}" for x in cold_nums]))