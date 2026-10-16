import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

st.set_page_config(page_title="Decimal Tracker: NIFTY, HSI & TAIEX", layout="wide")
st.title("🎯 Multi-Index Decimal Tracker: Pre-Close 1-Hour Engine")
st.caption("NIFTY (02:00–03:00 PM IST), HANG SENG (12:00–01:00 PM IST) और TAIEX के अंतिम 1-घंटे की विंडो का विश्लेषण।")

# साइडबार
st.sidebar.header("⚙️ सेटिंग्स")
index_choice = st.sidebar.selectbox("इंडेक्स चुनें:", ["NIFTY 50", "HANG SENG", "TAIEX (Taiwan)"])
ist = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(ist)
st.sidebar.info(f"🕒 वर्तमान IST समय: {now_ist.strftime('%Y-%m-%d %H:%M:%S')}")

if index_choice == "NIFTY 50":
    ticker_primary = "^NSEI"
    ticker_backup = "NIFTYBEES.NS"
    total_possible = 20
    win_start, win_end = "14:00:00", "15:00:00"  # 02:00 से 03:00 PM IST
    close_time_str = "15:25:00"
    window_label = "02:00–03:00 PM IST (क्लोजिंग 03:30 PM)"
elif index_choice == "HANG SENG":
    ticker_primary = "^HSI"
    ticker_backup = "2800.HK"
    total_possible = 100
    win_start, win_end = "12:00:00", "13:00:00"  # 12:00 से 01:00 PM IST
    close_time_str = "13:25:00"                  # 01:30 PM IST क्लोज
    window_label = "12:00–01:00 PM IST (क्लोजिंग 01:30 PM)"
else:  # TAIEX (Taiwan)
    ticker_primary = "^TWII"
    ticker_backup = "0050.TW"
    total_possible = 100
    win_start, win_end = "09:30:00", "10:30:00"  # 09:30 से 10:30 AM IST
    close_time_str = "10:55:00"                  # 11:00 AM IST क्लोज
    window_label = "09:30–10:30 AM IST (क्लोजिंग 11:00 AM)"

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
st.info(f"📌 विश्लेषण विंडो: **{window_label}**")

if len(win_df) < 5:
    st.warning(f"⚠️ {window_label} विंडो का पर्याप्त डेटा अभी उपलब्ध नहीं हुआ है।")
else:
    counts = win_df["Decimal"].value_counts()

    # 1. Top-15 प्रायोरिटी लिस्ट
    top15_common = counts.head(15)

    # 2. पूल्स
    common_pool = counts[counts >= 2]
    unique_pool = counts[counts == 1]

    if total_possible == 20:
        all_possible = [f"{x * 5:02d}" for x in range(20)]
    else:
        all_possible = [f"{x:02d}" for x in range(100)]
    unseen_pool = sorted(list(set(all_possible) - set(counts.index)))

    # =========================================================================
    # ⭐ TOP-15 डोमिनेंट नंबर डिस्प्ले (3 पंक्तियों में 5-5 कार्ड्स)
    # =========================================================================
    st.markdown("---")
    st.markdown("### ⭐ विंडो के Top-15 प्राथमिकता नंबर (Top-15 Priority Decimals)")
    st.caption("विंडो में सर्वाधिक बार रिकॉर्ड किए गए 15 दशमलव:")

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
                    st.metric(label=f"रैंक #{idx+1}", value="-", delta="उपलब्ध नहीं")

    # =========================================================================
    # 📋 नीचे सभी पूल्स का संपूर्ण विवरण
    # =========================================================================
    st.markdown("---")
    st.markdown("### 📋 संपूर्ण पूल्स विभाजन (Complete Decimals Breakdown)")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"#### 🔄 कॉमन पूल ({len(common_pool)} अंक)")
        st.caption("विंडो में $\ge 2	imes$ रिपीट हुए:")
        if not common_pool.empty:
            c_items = [f".{k} ({v}x)" for k, v in common_pool.items()]
            st.write(", ".join(c_items))
        else:
            st.write("कोई कॉमन नंबर नहीं।")

    with c2:
        st.markdown(f"#### ⚡ यूनिक पूल ({len(unique_pool)} अंक)")
        st.caption("विंडो में सिर्फ $1	imes$ आए:")
        if not unique_pool.empty:
            u_items = [f".{k}" for k in sorted(unique_pool.index)]
            st.write(", ".join(u_items))
        else:
            st.write("कोई यूनिक नंबर नहीं।")

    with c3:
        st.markdown(f"#### 🚫 अनसीन पूल ({len(unseen_pool)} अंक)")
        st.caption("विंडो में एक बार भी नहीं दिखे (बाहर रहे):")
        st.write(", ".join([f".{k}" for k in unseen_pool]))

    # =========================================================================
    # 🏁 क्लोजिंग परिणाम सत्यापन
    # =========================================================================
    st.markdown("---")
    last_bar_time = day_df.index[-1].time()
    is_today = (selected_date == datetime.now(ist).date())
    target_close_time = datetime.strptime(close_time_str, "%H:%M:%S").time()

    if not is_today or last_bar_time >= target_close_time:
        close_price = day_df.iloc[-1]["Close"]
        close_dec = day_df.iloc[-1]["Decimal"]

        if close_dec in top15_common.index:
            rank_hit = list(top15_common.index).index(close_dec) + 1
            res_tag = f"✅ Top-15 में मैच हुआ! (रैंक #{rank_hit})"
        elif close_dec in counts.index:
            res_tag = "🟡 सीन पूल में आया (Top-15 से बाहर)"
        else:
            res_tag = "❌ अनसीन (विंडो के बाहर) गया"

        st.success(f"**अंतिम क्लोजिंग भाव:** {close_price:.2f} (दशमलव: **.{close_dec}**) | **स्टेटस:** {res_tag}")
    else:
        st.info("ℹ️ बाजार अभी खुला है या सत्र की अंतिम क्लोजिंग नहीं आई है। क्लोजिंग वेरिफिकेशन क्लोज टाइम पर एक्टिव होगा।")

# =========================================================================
# 📅 7-दिवसीय पूर्ण ऐतिहासिक ऑडिट टेबल (History Table)
# =========================================================================
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

    t15 = w_counts.head(15).index.tolist()

    if c_dec in t15:
        r_pos = t15.index(c_dec) + 1
        outcome = f"✅ Top-15 मैच (रैंक #{r_pos})"
    elif c_dec in w_counts.index:
        outcome = "🟡 सीन (Top-15 बाहर)"
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
