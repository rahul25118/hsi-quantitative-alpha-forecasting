import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime
import os

st.set_page_config(
    page_title="Multi-Index Intraday Decimal Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Multi-Index Decimal & Intraday Dynamics")
st.caption("Live Monitoring, Cross-Timeframe Intersections & Historical Audits for NSE Nifty 50 and HKEX Hang Seng")

# ---------------------------------------------------------
# साइडबार: इंडेक्स और सेटिंग्स
# ---------------------------------------------------------
st.sidebar.header("⚙️ कॉन्फ़िगरेशन")
selected_market = st.sidebar.selectbox(
    "इंडेक्स चुनें:",
    ["NIFTY 50 (India - NSE)", "Hang Seng Index (Hong Kong - HKEX)"],
    index=0
)

is_nifty = "NIFTY" in selected_market
ticker = "^NSEI" if is_nifty else "^HSI"
tz_name = "Asia/Kolkata" if is_nifty else "Asia/Hong_Kong"

timeframe_map = {
    "1-Minute": "1min",
    "5-Minute": "5min",
    "15-Minute": "15min",
    "30-Minute": "30min",
    "1-Hour": "1h",
    "2-Hour": "2h"
}

# ---------------------------------------------------------
# डेटा लोडर (कैश 15 सेकंड)
# ---------------------------------------------------------
@st.cache_data(ttl=15)
def load_market_data(ticker_symbol, tz):
    df = yf.download(ticker_symbol, period="7d", interval="1m", progress=False)
    if df.empty or len(df) < 50:
        backup = "NIFTYBEES.NS" if "^NSEI" in ticker_symbol else "HSI=F"
        df = yf.download(backup, period="7d", interval="1m", progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert(tz)
    else:
        df.index = df.index.tz_convert(tz)

    df["Date"] = df.index.date
    df["Decimal"] = df["Close"].apply(lambda x: f"{float(x):.2f}".split(".")[1].zfill(2))
    return df

with st.spinner(f"{ticker} का इंट्राडे डेटा लोड हो रहा है..."):
    try:
        df_1m = load_market_data(ticker, tz_name)
    except Exception as e:
        st.error(f"डेटा लोड करने में त्रुटि: {e}")
        st.stop()

available_dates = sorted(df_1m["Date"].unique(), reverse=True)
selected_date = st.sidebar.selectbox("ट्रेडिंग सत्र चुनें:", available_dates, index=0)

day_1m = df_1m[df_1m["Date"] == selected_date].copy()
if day_1m.empty:
    st.warning("चुने गए दिन के लिए पर्याप्त डेटा उपलब्ध नहीं है।")
    st.stop()

latest_row = day_1m.iloc[-1]
latest_price = latest_row["Close"]
latest_decimal = latest_row["Decimal"]
latest_time = day_1m.index[-1].strftime("%H:%M:%S")

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("अंतिम रिकॉर्डेड भाव", f"{latest_price:.2f}")
col_m2.metric("अंतिम दशमलव", f".{latest_decimal}")
col_m3.metric(f"अंतिम समय ({tz_name.split('/')[1]})", latest_time)
col_m4.metric("कुल 1-मिनट बार्स", f"{len(day_1m)}")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📡 मल्टी-टाइमफ्रेम मैट्रिक्स", "🎯 ऐतिहासिक क्लोज-मैच ऑडिट", "🔬 टाइमफ्रेम डीप-डाइव"])

# =========================================================
# TAB 1: मल्टी-टाइमफ्रेम मैट्रिक्स और कॉमन इंटरसेक्शन
# =========================================================
with tab1:
    st.subheader(f"📊 मल्टी-टाइमफ्रेम बारंबारता सारांश ({selected_date})")

    tf_summaries = []
    resampled_dict = {}
    sets_dict = {}

    for tf_name, tf_code in timeframe_map.items():
        if tf_code == "1min":
            df_tf = day_1m.copy()
        else:
            df_tf = day_1m.resample(tf_code).agg({
                "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"
            }).dropna()
            df_tf["Decimal"] = df_tf["Close"].apply(lambda x: f"{float(x):.2f}".split(".")[1].zfill(2))

        resampled_dict[tf_name] = df_tf
        n_bars = len(df_tf)
        if n_bars == 0:
            continue

        counts = df_tf["Decimal"].value_counts()
        sets_dict[tf_name] = set(counts.index)

        top1_dec = counts.index[0]
        top1_freq = counts.iloc[0]
        curr_freq = counts.get(latest_decimal, 0)
        rank_list = list(counts.index)
        curr_rank = f"#{rank_list.index(latest_decimal)+1}" if latest_decimal in rank_list else "Not Seen"

        total_possible = 20 if is_nifty else 100

        tf_summaries.append({
            "Timeframe": tf_name,
            "Total_Bars": n_bars,
            "Unique_Decimals": f"{len(counts)} / {total_possible}",
            "Top-1_Mode": f".{top1_dec} ({top1_freq}x)",
            "Current_Dec_Freq": f"{curr_freq} बार",
            "Current_Dec_Rank": curr_rank
        })

    st.dataframe(pd.DataFrame(tf_summaries), use_container_width=True)

    st.markdown("#### 🔗 सभी टाइमफ्रेम्स में कॉमन दशमलव (Cross-Timeframe Intersection)")
    valid_sets = [s for s in sets_dict.values() if len(s) > 0]
    if valid_sets:
        common_all = set.intersection(*valid_sets)
        formatted_common = [f".{d}" for d in sorted(common_all)]
        st.success(f"सभी टाइमफ्रेम्स में कॉमन दशमलव ({len(common_all)}): **{', '.join(formatted_common)}**")

# =========================================================
# TAB 2: ऐतिहासिक क्लोजिंग मैच टेस्ट
# =========================================================
with tab2:
    st.subheader(f"🧪 हिस्टोरिकल क्लोज-मैच ऑडिट ({selected_market})")

    audit_results = []

    for tf_name, tf_code in timeframe_map.items():
        if tf_code == "1min":
            df_full_tf = df_1m.copy()
        else:
            df_full_tf = df_1m.resample(tf_code).agg({
                "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"
            }).dropna()
            df_full_tf["Date"] = df_full_tf.index.date
            df_full_tf["Decimal"] = df_full_tf["Close"].apply(lambda x: f"{float(x):.2f}".split(".")[1].zfill(2))

        dates_list = sorted(df_full_tf["Date"].unique())
        hits_top1, hits_top5, hits_top10, hits_top20, total_days = 0, 0, 0, 0, 0
        bars_count = []

        for d in dates_list:
            day_slice = df_full_tf[df_full_tf["Date"] == d]
            if len(day_slice) < 4:
                continue
            total_days += 1
            bars_count.append(len(day_slice))
            close_dec = day_slice.iloc[-1]["Decimal"]
            counts = day_slice["Decimal"].value_counts()
            ranked = list(counts.index)

            if close_dec in ranked:
                r = ranked.index(close_dec) + 1
                if r == 1: hits_top1 += 1
                if r <= 5: hits_top5 += 1
                if r <= 10: hits_top10 += 1
                if r <= 20: hits_top20 += 1

        if total_days > 0:
            audit_results.append({
                "Timeframe": tf_name,
                "Avg_Bars/Day": int(np.mean(bars_count)),
                "Tested_Days": total_days,
                "Top-01 Hit Rate": f"{(hits_top1/total_days)*100:.1f}% ({hits_top1}/{total_days})",
                "Top-05 Hit Rate": f"{(hits_top5/total_days)*100:.1f}% ({hits_top5}/{total_days})",
                "Top-10 Hit Rate": f"{(hits_top10/total_days)*100:.1f}% ({hits_top10}/{total_days})",
                "Top-20 Hit Rate": f"{(hits_top20/total_days)*100:.1f}% ({hits_top20}/{total_days})"
            })

    st.dataframe(pd.DataFrame(audit_results), use_container_width=True)

# =========================================================
# TAB 3: टाइमफ्रेम डीप-डाइव
# =========================================================
with tab3:
    st.subheader("🔍 टाइमफ्रेम अनुसार विस्तृत बारंबारता")
    selected_tf_view = st.selectbox("टाइमफ्रेम चुनें:", list(timeframe_map.keys()), index=1)

    df_view = resampled_dict.get(selected_tf_view, pd.DataFrame())
    if not df_view.empty:
        col_t1, col_t2 = st.columns([1, 1])

        with col_t1:
            st.markdown(f"**{selected_tf_view} पर सबसे ज़्यादा बार आए दशमलव:**")
            counts_v = df_view["Decimal"].value_counts().reset_index()
            counts_v.columns = ["Decimal", "Frequency"]
            counts_v["Decimal"] = counts_v["Decimal"].apply(lambda x: f".{x}")

            fig = px.bar(counts_v.head(15), x="Decimal", y="Frequency", color="Frequency",
                         title=f"Top Decimals on {selected_tf_view}",
                         color_continuous_scale="Viridis")
            st.plotly_chart(fig, use_container_width=True)

        with col_t2:
            st.markdown(f"**{selected_tf_view} कैंडल्स का क्रमवार विवरण:**")
            log_view = df_view[["Open", "High", "Low", "Close", "Decimal"]].copy()
            log_view.index = log_view.index.strftime("%H:%M")
            st.dataframe(log_view, height=350, use_container_width=True)
