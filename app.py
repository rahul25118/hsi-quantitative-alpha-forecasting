import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

st.set_page_config(page_title="Multi-Session Decimal Engine", layout="wide")
st.title("🎯 HSI (Morning & Afternoon) & NIFTY Multi-Session Decimal Engine")
st.caption("हैंग सेंग के मॉर्निंग (07:00-09:30 AM) व आफ्टरनून (10:30-01:30 PM) सत्रों का स्वतंत्र विश्लेषण।")

# साइडबार
st.sidebar.header("⚙️ सेटिंग्स")
index_choice = st.sidebar.selectbox("इंडेक्स चुनें:", ["HANG SENG", "NIFTY 50", "TAIEX (Taiwan)"])
ist = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(ist)
st.sidebar.info(f"🕒 वर्तमान IST: {now_ist.strftime('%Y-%m-%d %H:%M:%S')}")

# इंडेक्स व सत्र कॉन्फ़िगरेशन
if index_choice == "HANG SENG":
    ticker_primary = "^HSI"
    ticker_backup = "2800.HK"
    total_possible = 100

    hsi_session = st.sidebar.radio(
        "📌 HSI सत्र चुनें:",
        [
            "1. मॉर्निंग सत्र (07:00–09:30 AM)",
            "2. आफ्टरनून सत्र (10:30 AM–01:30 PM)",
            "3. मॉर्निंग विंडो -> फाइनल 01:30 PM क्लोज"
        ]
    )

    if "मॉर्निंग सत्र" in hsi_session and "फाइनल" not in hsi_session:
        win_start, win_end = "07:30:00", "09:00:00"
        close_time_str = "09:28:00"
        window_label = "HSI मॉर्निंग विंडो: 07:30–09:00 AM IST (क्लोजिंग 09:30 AM)"
    elif "आफ्टरनून सत्र" in hsi_session:
        win_start, win_end = "12:00:00", "13:00:00"
        close_time_str = "13:28:00"
        window_label = "HSI आफ्टरनून विंडो: 12:00–01:00 PM IST (क्लोजिंग 01:30 PM)"
    else:  # क्रॉस-सत्र
        win_start, win_end = "07:00:00", "09:30:00"
        close_time_str = "13:28:00"
        window_label = "HSI संपूर्ण मॉर्निंग पूल (07:00–09:30 AM) -> फाइनल 01:30 PM क्लोज"

elif index_choice == "NIFTY 50":
    ticker_primary = "^NSEI"
    ticker_backup = "NIFTYBEES.NS"
    total_possible = 20
    win_start, win_end = "14:00:00", "15:00:00"
    close_time_str = "15:25:00"
    window_label = "NIFTY विंडो: 02:00–03:00 PM IST (क्लोजिंग 03:30 PM)"

else:  # TAIEX
    ticker_primary = "^TWII"
    ticker_backup = "0050.TW"
    total_possible = 100
    win_start, win_end = "09:30:00", "10:30:00"
    close_time_str = "10:55:00"
    window_label = "TAIEX विंडो: 09:30–10:30 AM IST (क्लोजिंग 11:00 AM)"

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
    st.error(f"{index_choice} का डेटा लोड नहीं हो सका।")
    st.stop()

available_dates = sorted(df_all["Date"].unique(), reverse=True)

selected_date = st.sidebar.selectbox(
    "📅 तारीख चुनें (सत्र विश्लेषण):",
    available_dates,
    index=0
)

day_df = df_all[df_all["Date"] == selected_date].copy()
win_df = day_df.between_time(win_start, win_end).copy()

st.subheader(f"📊 सत्र विश्लेषण: {selected_date} ({index_choice})")
st.info(f"📌 सक्रिय कॉन्फ़िगरेशन: **{window_label}**")

if len(win_df) < 5:
    st.warning(f"⚠️ {window_label} के लिए पर्याप्त इंट्राडे डेटा उपलब्ध नहीं हुआ है।")
else:
    counts = win_df["Decimal"].value_counts()
    top15_common = counts.head(15)
    common_pool = counts[counts >= 2]
    unique_pool = counts[counts == 1]

    if total_possible == 20:
        all_possible = [f"{x * 5:02d}" for x in range(20)]
    else:
        all_possible = [f"{x:02d}" for x in range(100)]
    unseen_pool = sorted(list(set(all_possible) - set(counts.index)))

    # Top-15 प्रायोरिटी कार्ड्स
    st.markdown("---")
    st.markdown("### ⭐ सत्र के Top-15 प्राथमिकता दशमलव (Top-15 Decimals)")
    for row_idx in range(3):
        cols = st.columns(5)
        for col_idx in range(5):
            idx = row_idx * 5 + col_idx
            with cols[col_idx]:
                if idx < len(top15_common):
                    dec_val = top15_common.index[idx]
                    rep_cnt = top15_common.iloc[idx]
                    st.metric(
                        label=f"रैंक #{idx+1}",
                        value=f".{dec_val}",
                        delta=f"{rep_cnt} बार आया"
                    )
                else:
                    st.metric(label=f"रैंक #{idx+1}", value="-", delta="N/A")

    # पूल्स का पूरा विवरण
    st.markdown("---")
    st.markdown("### 📋 संपूर्ण पूल्स विभाजन (Pools Breakdown)")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"#### 🔄 कॉमन पूल ({len(common_pool)} अंक)")
        st.caption("विंडो में $\ge 2	imes$ रिपीट हुए:")
        if not common_pool.empty:
            st.write(", ".join([f".{k} ({v}x)" for k, v in common_pool.items()]))
        else:
            st.write("कोई कॉमन नंबर नहीं।")

    with c2:
        st.markdown(f"#### ⚡ यूनिक पूल ({len(unique_pool)} अंक)")
        st.caption("विंडो में सिर्फ $1	imes$ आए:")
        if not unique_pool.empty:
            st.write(", ".join([f".{k}" for k in sorted(unique_pool.index)]))
        else:
            st.write("कोई यूनिक नंबर नहीं।")

    with c3:
        st.markdown(f"#### 🚫 अनसीन पूल ({len(unseen_pool)} अंक)")
        st.caption("विंडो में नहीं दिखे (बाहर रहे):")
        st.write(", ".join([f".{k}" for k in unseen_pool]))

    # क्लोजिंग मैचिंग
    st.markdown("---")
    target_close_time = datetime.strptime(close_time_str, "%H:%M:%S").time()

    # लक्ष्य समय के निकटतम कैंडल खोजना
    bars_before_target = day_df[day_df.index.time <= target_close_time]

    if not bars_before_target.empty and len(bars_before_target) >= 10:
        close_bar = bars_before_target.iloc[-1]
        close_price = close_bar["Close"]
        close_dec = close_bar["Decimal"]
        close_bar_time = close_bar.name.strftime("%H:%M:%S")

        if close_dec in top15_common.index:
            r_pos = list(top15_common.index).index(close_dec) + 1
            res_tag = f"✅ Top-15 में मैच हुआ! (रैंक #{r_pos})"
        elif close_dec in counts.index:
            res_tag = "🟡 सीन पूल में आया (Top-15 से बाहर)"
        else:
            res_tag = "❌ अनसीन (विंडो के बाहर) गया"

        st.success(f"**सत्र क्लोजिंग भाव ({close_bar_time} IST):** {close_price:.2f} (दशमलव: **.{close_dec}**) | **स्टेटस:** {res_tag}")
    else:
        st.info("ℹ️ इस सत्र की क्लोजिंग अभी नहीं आई है या बाजार खुला है।")

# 7-दिवसीय हिस्ट्री समरी
st.markdown("---")
st.markdown("### 📋 पिछले 7 कारोबारी दिनों का सत्रवार सारांश")

history_rows = []
for d in available_dates[:7]:
    d_df = df_all[df_all["Date"] == d].copy()
    w_df = d_df.between_time(win_start, win_end).copy()
    target_bars = d_df[d_df.index.time <= target_close_time]

    if len(w_df) < 5 or target_bars.empty:
        continue

    c_dec = target_bars.iloc[-1]["Decimal"]
    c_price = target_bars.iloc[-1]["Close"]
    w_counts = w_df["Decimal"].value_counts()
    t15 = w_counts.head(15).index.tolist()

    if c_dec in t15:
        r_pos = t15.index(c_dec) + 1
        outcome = f"✅ Top-15 (रैंक #{r_pos})"
    elif c_dec in w_counts.index:
        outcome = "🟡 सीन"
    else:
        outcome = "❌ अनसीन (बाहर)"

    history_rows.append({
        "तारीख": str(d),
        "क्लोजिंग भाव": f"{c_price:.2f}",
        "क्लोज दशमलव": f".{c_dec}",
        "Top-15 नंबर्स": ", ".join([f".{x}" for x in t15]),
        "परिणाम": outcome
    })

if history_rows:
    st.dataframe(pd.DataFrame(history_rows), use_container_width=True)
