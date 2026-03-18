import random
import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter, defaultdict

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
# 評分模型（簡化穩定版）
# ==============================
def score_numbers(history):

    freq100=Counter([n for d in history[-100:] for n in d])
    recent10=Counter([n for d in history[-10:] for n in d])

    score={}

    for n in range(1,40):

        hot=freq100[n]/100
        trend=recent10[n]/10

        last_seen=50
        for i,d in enumerate(reversed(history)):
            if n in d:
                last_seen=i
                break

        cold=min(last_seen/30,1)

        score[n]=hot*0.4 + trend*0.3 + cold*0.3

    return score


# ==============================
# 分佈限制
# ==============================
def valid_combo(combo):

    combo=sorted(combo)

    # 奇偶
    odd=sum(1 for n in combo if n%2)
    if odd not in [2,3]:
        return False

    # 區間
    if not any(n<=13 for n in combo): return False
    if not any(14<=n<=26 for n in combo): return False
    if not any(n>=27 for n in combo): return False

    # 和值
    if not (80<=sum(combo)<=140):
        return False

    # 尾數分散
    tails=len(set(n%10 for n in combo))
    if tails<3:
        return False

    return True


# ==============================
# AI推薦
# ==============================
def ai_recommend(history):

    score=score_numbers(history)

    combos=set()

    for _ in range(100000):

        combo=random.sample(range(1,40),5)

        if not valid_combo(combo):
            continue

        combo=tuple(sorted(combo))
        combos.add(combo)

    combos=list(combos)

    scored=[]

    for c in combos:
        s=sum(score[n] for n in c)
        scored.append((c,s))

    scored=sorted(scored,key=lambda x:x[1],reverse=True)

    picks=random.sample(scored[:30],3)

    return [list(c) for c,_ in picks]


# ==============================
# 拆四合（核心🔥）
# ==============================
def generate_four_sets(combo):
    from itertools import combinations
    return list(combinations(combo,4))


# ==============================
# 命中分析
# ==============================
def analyze_hits(four_sets, history):

    result=[]

    for fs in four_sets:

        hit3=0
        hit4=0

        for draw in history[-3000:]:
            match=len(set(fs)&set(draw))

            if match==3:
                hit3+=1
            elif match==4:
                hit4+=1

        recent_hit=sum(
            1 for draw in history[-5:]
            if len(set(fs)&set(draw))>=3
        )

        result.append({
            "set":fs,
            "hit3":hit3,
            "hit4":hit4,
            "recent":recent_hit
        })

    return sorted(result,key=lambda x:(x["hit4"],x["hit3"],x["recent"]),reverse=True)


# ==============================
# UI
# ==============================
st.set_page_config(layout="wide")
st.title("🔥 539 AI + 四合策略引擎 V43")

history=fetch_history()

st.markdown(f"### 📊 資料量：{len(history)}期")

# 最新五期
st.markdown("### 📅 最新五期")
cols=st.columns(5)

for i,d in enumerate(history[-5:][::-1]):
    cols[i].metric(f"第{i+1}期"," ".join(f"{x:02d}" for x in d))


# 執行
if st.button("🚀 產生策略"):

    recs=ai_recommend(history)

    st.divider()
    st.markdown("## 🎯 AI推薦號碼")

    for r in recs:
        st.success(" ".join(f"{x:02d}" for x in r))

    st.divider()
    st.markdown("## 💰 四合最佳策略")

    for r in recs:

        st.markdown(f"### 🔹 來源組：{' '.join(f'{x:02d}' for x in r)}")

        four_sets=generate_four_sets(r)
        analysis=analyze_hits(four_sets,history)

        for a in analysis[:3]:
            st.write(
                f"{' '.join(f'{x:02d}' for x in a['set'])} ｜ "
                f"中3:{a['hit3']}次 ｜ 中4:{a['hit4']}次 ｜ "
                f"近5期:{a['recent']}"
            )