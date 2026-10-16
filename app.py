import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

st.set_page_config(page_title="Decimal Tracker: NIFTY, HSI & TAIEX", layout="wide")
st.title("🎯 Multi-Index Decimal Tracker & Historical Audit Engine")
st.caption("NIFTY 50 (भारत), HANG SENG (हांगकांग) और TAIEX (ताइवान) के मिड-डे दशमलव व क्लोजिंग का विश्लेषण।")

# साइडबार
st.sidebar.header("⚙️ सेटिंग्स")
index_choice = st.sidebar.selectbox("इंडेक्स चुनें:", ["NIFTY 50", "HANG SENG", "TAIEX (Taiwan)"])
ist = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(ist)
st.sidebar.info(f"🕒 वर्तमान IST: {now_ist.strftime('%Y-%m-%d %H:%M:%S')}")

if index_choice == "NIFTY 50":
    ticker_primary = "^NSEI"
    ticker_backup = "NIFTYBEES.NS"
    total_possible = 20
    win_start, win_end = "12:00:00", "13:00:00"
    close_time_str = "15:25:00"
    window_label = "12:00–01:00 PM IST"
elif index_choice == "HANG SENG":
    ticker_primary = "^HSI"
    ticker_backup = "2800.HK"
    total_possible = 100
    win_start, win_end = "12:00:00", "13:00:00"
    close_time_str = "15:25:00"
    window_label = "12:00–01:00 PM IST"
else:  # TAIEX (ताइवान)
    ticker_primary = "^TWII"
    ticker_backup = "0050.TW"  # Yuanta Taiwan Top 50 ETF
    total_possible = 100
    # ताइवान लंच ऑवर: 11:00-12:00 स्थानीय = 08:30-09:30 AM IST (मार्केट क्लोज़ 11:00 AM IST)
    win_start, win_end = "08:30:00", "09:30:00"
    close_time_str = "10:55:00"
    window_label = "08:30–09:30 AM IST (11:00–12:00 ताइवान समय)"

@st.cache_data(ttl=60)
def fetch_multi_day_data(primary, backup):
    df = yf.Ticker(primary).history(period="12d", interval="2m")
    if df.empty or len(df) < 40:
        df = yf.Ticker(backup).history(period="12d", interval="2m")
    if df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert("Asia/Kolkata")
    else:
        df.index = df.index.tz_convert("Asia/Kolkata")
    df["Date"] = df.index.date
    df["Decimal"] = df["Close"].apply(lambda x: f"{float(x):.2f}".split(".")[1].zfill(2))
    return df

df_all = fetch_multi_day_data(ticker_primary, ticker_backup)

if df_all.empty:
    st.error(f"{index_choice} का डेटा फेच करने में समस्या आ रही है। कृपया पुनः प्रयास करें।")
    st.stop()

available_dates = sorted(df_all["Date"].unique(), reverse=True)

selected_date = st.sidebar.selectbox(
    "📅 तारीख चुनें (दैनिक विश्लेषण):",
    available_dates,
    index=0
)

day_df = df_all[df_all["Date"] == selected_date].copy()
win_df = day_df.between_time(win_start, win_end).copy()

st.subheader(f"📊 सत्र विश्लेषण: {selected_date} ({index_choice})")
st.info(f"📌 विश्लेषण विंडो: **{window_label}**")

if len(win_df) < 5:
    st.warning(f"⚠️ इस तारीख के लिए {window_label} विंडो का पर्याप्त डेटा उपलब्ध नहीं है।")
else:
    counts = win_df["Decimal"].value_counts()
    top5_common = counts.head(5)
    common_pool = counts[counts >= 2]
    unique_pool = counts[counts == 1]

    if total_possible == 20:
        all_possible = [f"{x * 5:02d}" for x in range(20)]
    else:
        all_possible = [f"{x:02d}" for x in range(100)]
    unseen_pool = sorted(list(set(all_possible) - set(counts.index)))

    st.markdown("### ⭐ विंडो के Top-5 डोमिनेंट नंबर")
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            if i < len(top5_common):
                dec_val = top5_common.index[i]
                rep_cnt = top5_common.iloc[i]
                st.metric(label=f"रैंक #{i+1}", value=f".{dec_val}", delta=f"{rep_cnt} बार आया")
            else:
                st.metric(label=f"रैंक #{i+1}", value="-", delta="N/A")

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"#### 🔄 कॉमन पूल ({len(common_pool)} अंक)")
        st.caption("विंडो में 2x या उससे अधिक बार आए:")
        if not common_pool.empty:
            st.write(", ".join([f".{k} ({v}x)" for k, v in common_pool.items()]))
        else:
            st.write("कोई कॉमन नंबर नहीं।")

    with c2:
        st.markdown(f"#### ⚡ यूनिक पूल ({len(unique_pool)} अंक)")
        st.caption("विंडो में सिर्फ 1 बार आए:")
        if not unique_pool.empty:
            st.write(", ".join([f".{k}" for k in sorted(unique_pool.index)]))
        else:
            st.write("कोई यूनिक नंबर नहीं।")

    with c3:
        st.markdown(f"#### 🚫 अनसीन पूल ({len(unseen_pool)} अंक)")
        st.caption("विंडो में नहीं दिखे:")
        st.write(", ".join([f".{k}" for k in unseen_pool]))

    st.markdown("---")
    last_bar_time = day_df.index[-1].time()
    is_today = (selected_date == datetime.now(ist).date())
    target_close_time = datetime.strptime(close_time_str, "%H:%M:%S").time()

    if not is_today or last_bar_time >= target_close_time:
        close_price = day_df.iloc[-1]["Close"]
        close_dec = day_df.iloc[-1]["Decimal"]

        if close_dec in top5_common.index:
            res_tag = "✅ Top-5 कॉमन में मैच हुआ!"
        elif close_dec in common_pool.index:
            res_tag = "🟡 कॉमन पूल में आया (Top-5 से बाहर)"
        elif close_dec in unique_pool.index:
            res_tag = "🔵 यूनिक पूल में आया"
        else:
            res_tag = "❌ अनसीन (विंडो के बाहर) गया"

        st.success(f"**अंतिम क्लोजिंग भाव:** {close_price:.2f} (दशमलव: **.{close_dec}**) | **स्टेटस:** {res_tag}")
    else:
        st.info("ℹ️ बाजार अभी खुला है या सत्र की अंतिम क्लोजिंग नहीं आई है।")

# 7-दिवसीय हिस्ट्री समरी
st.markdown("---")
st.markdown("### 📋 पिछले 7 कारोबारी दिनों का समग्र सारांश")

history_rows = []
for d in available_dates[:7]:
    d_df = df_all[df_all["Date"] == d].copy()
    w_df = d_df.between_time(win_start, win_end).copy()
    if len(w_df) < 5 or len(d_df) < 15:
        continue

    c_dec = d_df.iloc[-1]["Decimal"]
    c_price = d_df.iloc[-1]["Close"]
    w_counts = w_df["Decimal"].value_counts()

    t5 = w_counts.head(5).index.tolist()
    c_pool = w_counts[w_counts >= 2].index.tolist()
    u_pool = w_counts[w_counts == 1].index.tolist()

    if c_dec in t5:
        outcome = "✅ Top-5 मैच"
    elif c_dec in c_pool:
        outcome = "🟡 कॉमन (Top-5 बाहर)"
    elif c_dec in u_pool:
        outcome = "🔵 यूनिक (1x)"
    else:
        outcome = "❌ अनसीन (बाहर)"

    history_rows.append({
        "तारीख": str(d),
        "क्लोजिंग भाव": f"{c_price:.2f}",
        "क्लोज दशमलव": f".{c_dec}",
        "Top-5 कॉमन नंबर्स": ", ".join([f".{x}" for x in t5]),
        "परिणाम": outcome
    })

if history_rows:
    st.dataframe(pd.DataFrame(history_rows), use_container_width=True)
