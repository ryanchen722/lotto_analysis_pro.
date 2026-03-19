import plotly.express as px # Add this to your imports

# ==============================
# NEW: Heat Map & Zone Analysis
# ==============================
def get_heat_stats(history):
    # Short term (Hot) vs Long term (Average)
    short_term = Counter([n for d in history[-50:] for n in d])
    
    # Calculate Heat Score (0 to 100)
    # Expected appearances in 50 draws is approx 6.4 times
    heat_data = []
    for n in range(1, 40):
        count = short_term[n]
        status = "🔥 Hot" if count > 8 else ("❄️ Cold" if count < 4 else "⚖️ Normal")
        heat_data.append({"Number": n, "Appearances": count, "Status": status})
    
    return pd.DataFrame(heat_data)

# ==============================
# UPDATED UI SECTION
# ==============================
st.set_page_config(page_title="539 AI V54.1", layout="wide")
st.title("🎯 539 AI V54.1 (熱區與冷區強化版)")

history = load_history()
biases = calculate_cross_weights(history)
heat_df = get_heat_stats(history)

# --- Top Stats ---
st.subheader("📊 當前號碼熱度分佈 (近50期)")
fig = px.bar(heat_df, x="Number", y="Appearances", color="Status",
             color_discrete_map={"🔥 Hot": "#ef553b", "❄️ Cold": "#636efa", "⚖️ Normal": "#00cc96"},
             title="號碼出現頻率 (紅色=熱區 / 藍色=冷區)")
st.plotly_chart(fig, use_container_width=True)

# --- Zone Display ---
c1, c2 = st.columns(2)
with c1:
    st.error("### 🔥 熱門號碼 (最近強勢)")
    hot_list = heat_df[heat_df["Status"] == "🔥 Hot"]["Number"].tolist()
    st.write(", ".join(f"{x:02d}" for x in hot_list))

with c2:
    st.info("### ❄️ 冷門號碼 (等待破冰)")
    cold_list = heat_df[heat_df["Status"] == "❄️ Cold"]["Number"].tolist()
    st.write(", ".join(f"{x:02d}" for x in cold_list))

# --- AI Prediction with Zone Strategy ---
st.divider()
if st.button("🚀 啟動 AI 混合策略預測", use_container_width=True):
    # We modify the pick logic slightly to ensure we don't pick ONLY hot or ONLY cold
    with st.spinner('正在分析熱/冷區最佳平衡點...'):
        # Get AI raw scores
        scores_dict = get_number_scores(history, biases)
        
        # Build 3 different strategy combinations
        recs = []
        
        # Strategy 1: AI Optimized (Pure Probability)
        recs.append(ai_recommend(history, biases)[0])
        
        # Strategy 2: Hot/Cold Mix (2 Hot, 2 Cold, 1 Random AI Score)
        if len(hot_list) >= 2 and len(cold_list) >= 2:
            mix = random.sample(hot_list, 2) + random.sample(cold_list, 2)
            # Add one more based on score
            remaining = [n for n in range(1, 40) if n not in mix]
            mix.append(random.choice(remaining))
            recs.append(sorted(mix))
            
        # Strategy 3: Extreme Correction (Focus on ignored numbers from last draw)
        last_draw = history[-1]
        ignored = [n for n in range(1, 40) if n not in last_draw and 10 <= n <= 20]
        if len(ignored) >= 5:
            recs.append(sorted(random.sample(ignored, 5)))
        else: # Fallback if ignored list is small
            recs.append(ai_recommend(history, biases)[1])

    st.subheader("🎯 三種 AI 策略組合")
    res_cols = st.columns(3)
    labels = ["機率最佳化", "熱冷混合平衡", "區間校正策略"]
    for i, r in enumerate(recs[:3]):
        res_cols[i].markdown(f"**{labels[i]}**")
        res_cols[i].success(f"### {' - '.join(f'{x:02d}' for x in r)}")

st.divider()
