import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

st.set_page_config(page_title="Multi-Index Decimal Engine", layout="wide")

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
    win_start, win_end = "14:00:00", "15:00:00"
    close_time_str = "15:25:00"
    window_label = "02:00–03:00 PM IST (क्लोजिंग 03:30 PM)"
elif index_choice == "HANG SENG":
    ticker_primary = "^HSI"
    ticker_backup = "2800.HK"
    total_possible = 100
    win_start, win_end = "12:00:00", "13:00:00"
    close_time_str = "13:28:00"
    window_label = "12:00–01:00 PM IST (क्लोजिंग 01:30 PM)"
else:  # TAIEX
    ticker_primary = "^TWII"
    ticker_backup = "0050.TW"
    total_possible = 100
    win_start, win_end = "09:30:00", "10:30:00"
    close_time_str = "10:55:00"
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
    "📅 तारीख चुनें:",
    available_dates,
    index=0
)

day_df = df_all[df_all["Date"] == selected_date].copy()
win_df = day_df.between_time(win_start, win_end).copy()

if total_possible == 20:
    all_possible = [f"{x * 5:02d}" for x in range(20)]
else:
    all_possible = [f"{x:02d}" for x in range(100)]

# =========================================================================
# 🇮🇳 NIFTY 50 DEDICATED ENGINE (पूर्ववत मूल लेआउट - बिल्कुल अपरिवर्तित)
# =========================================================================
if index_choice == "NIFTY 50":
    st.title("🎯 NIFTY 50 Priority Grid & Pools Engine")
    st.caption("02:00–03:00 PM IST विंडो: Top-15 कार्ड्स ऊपर, और नीचे कॉमन, यूनिक व अनसीन के संपूर्ण पूल्स।")
    st.info(f"📌 सक्रिय सत्र: **{selected_date}** | विंडो: **{window_label}**")

    if len(win_df) < 5:
        st.warning(f"⚠️ {window_label} के लिए पर्याप्त इंट्राडे डेटा अभी उपलब्ध नहीं हुआ है।")
    else:
        counts = win_df["Decimal"].value_counts()
        top15_common = counts.head(15)
        common_pool = counts[counts >= 2]
        unique_pool = counts[counts == 1]
        unseen_pool = sorted(list(set(all_possible) - set(counts.index)))

        # 1. Top-15 कार्ड्स
        st.markdown("---")
        st.markdown("### ⭐ 02:00–03:00 PM के Top-15 प्राथमिकता दशमलव")
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

        # 2. संपूर्ण पूल्स विभाजन
        st.markdown("---")
        st.markdown("### 📋 संपूर्ण पूल्स विभाजन (Complete Decimals Breakdown)")
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
            st.caption("विंडो में एक बार भी नहीं दिखे (बाहर रहे):")
            st.write(", ".join([f".{k}" for k in unseen_pool]))

        # 3. क्लोजिंग सत्यापन
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
            elif close_dec in common_pool.index:
                res_tag = "🟡 कॉमन पूल में आया (Top-15 से बाहर)"
            elif close_dec in unique_pool.index:
                res_tag = "🔵 यूनिक पूल में आया"
            else:
                res_tag = "❌ अनसीन (विंडो के बाहर) गया"

            st.success(f"**03:30 PM क्लोजिंग भाव:** {close_price:.2f} (दशमलव: **.{close_dec}**) | **स्टेटस:** {res_tag}")
        else:
            st.info("ℹ️ बाजार अभी खुला है या 03:30 PM की क्लोजिंग नहीं आई है।")

    # 4. 7-दिवसीय हिस्ट्री
    st.markdown("---")
    st.markdown("### 📋 पिछले 7 कारोबारी दिनों का NIFTY समग्र सारांश")
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

# =========================================================================
# 🇭🇰 HANG SENG DEDICATED ENGINE + ADD-ON MODULE
# =========================================================================
elif index_choice == "HANG SENG":
    st.title("🎯 HSI Prediction System + Single/15-Number Add-On")
    st.caption("मौजूदा टाइम-स्लॉट विश्लेषण के आधार पर नया Single Candidate व 15-Number Filter Add-On।")

    st.markdown("## 🧩 Add-On Module: Single Candidate & 15-Number Filters")
    c_m, c_a, c_c = st.columns(3)
    with c_m:
        st.metric("🌅 सुबह का Candidate (07:00–09:30 AM)", ".78", "2/31 Hits (6.45% vs 1% Baseline)")
    with c_a:
        st.metric("☀️ दोपहर का Candidate (12:30–01:30 PM)", ".29", "कमजोर (टाई/नो क्लियर विनर)", delta_color="off")
    with c_c:
        st.metric("⚖️ Combined Candidate (समग्र)", ".78", "ओवरऑल 2 Hits (6.45%)")

    st.markdown("### 🔢 15-Number Filter Sets")
    m_15_set = [".78", ".72", ".17", ".22", ".20", ".35", ".79", ".50", ".56", ".51", ".09", ".13", ".75", ".29", ".47"]
    a_15_set = [".21", ".31", ".47", ".63", ".78", ".51", ".50", ".17", ".72", ".29", ".71", ".75", ".56", ".22", ".12"]
    comb_15_set = [".78", ".29", ".17", ".72", ".22", ".50", ".51", ".56", ".47", ".75", ".12", ".21", ".31", ".63", ".35"]

    t1, t2, t3 = st.tabs(["🌅 सुबह का 15-नंबर सेट", "☀️ दोपहर का 15-नंबर सेट", "⚖️ Combined 15-नंबर सेट"])
    with t1:
        st.write("  •  ".join([f"`{x}`" for x in m_15_set]))
        st.caption("ऐतिहासिक इन-सैंपल कवरेज: 17/31 (54.8%) | बेसलाइन: 15%")
    with t2:
        st.write("  •  ".join([f"`{x}`" for x in a_15_set]))
        st.caption("ऐतिहासिक इन-सैंपल कवरेज: 18/31 (58.1%) | बेसलाइन: 15%")
    with t3:
        st.write("  •  ".join([f"`{x}`" for x in comb_15_set]))
        st.caption("10 ओवरलैप + 5 सक्रिय नंबर | इन-सैंपल: 18/31 (58.1%)")

    st.markdown("---")
    st.subheader(f"📅 दैनिक विश्लेषण: {selected_date}")
    target_close_time = datetime.strptime(close_time_str, "%H:%M:%S").time()
    bars_before_target = day_df[day_df.index.time <= target_close_time]

    if not bars_before_target.empty and len(bars_before_target) >= 10:
        close_bar = bars_before_target.iloc[-1]
        close_price = close_bar["Close"]
        close_dec = f".{close_bar['Decimal']}"
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            if close_dec == ".78":
                st.success(f"**Single Candidate (.78):** ✅ सटीक मैच! भाव: {close_price:.2f}")
            else:
                st.error(f"**Single Candidate (.78):** ❌ मिस! दशमलव `{close_dec}` रहा।")
        with c_res2:
            if close_dec in comb_15_set:
                pos = comb_15_set.index(close_dec) + 1
                st.success(f"**Combined 15-Filter:** ✅ मैच! (रैंक #{pos}) भाव: {close_price:.2f}")
            else:
                st.error(f"**Combined 15-Filter:** ❌ मिस! `{close_dec}` फिल्टर से बाहर रहा।")
    else:
        st.info("ℹ️ 01:30 PM की क्लोजिंग अभी नहीं आई है या बाजार खुला है।")

# =========================================================================
# TAIEX DEFAULT LAYOUT
# =========================================================================
else:
    st.title("🎯 TAIEX Priority Engine")
    st.caption(f"{window_label} का विश्लेषण।")
    if len(win_df) < 5:
        st.warning("पर्याप्त डेटा उपलब्ध नहीं है।")
    else:
        counts = win_df["Decimal"].value_counts()
        top15 = counts.head(15)
        seen_list = counts.index.tolist()
        unseen_pool = sorted(list(set(all_possible) - set(seen_list)))

        st.markdown("### ⭐ Top-15 प्राथमिकता दशमलव")
        for row_idx in range(3):
            cols = st.columns(5)
            for col_idx in range(5):
                idx = row_idx * 5 + col_idx
                with cols[col_idx]:
                    if idx < len(top15):
                        st.metric(f"रैंक #{idx+1}", f".{top15.index[idx]}", f"{top15.iloc[idx]}x")
                    else:
                        st.metric(f"रैंक #{idx+1}", "-", "N/A")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### 👁️ सीन पूल ({len(seen_list)} अंक)")
            st.write(", ".join([f".{k} ({v}x)" for k, v in counts.items()]))
        with c2:
            st.markdown(f"#### 🚫 अनसीन पूल ({len(unseen_pool)} अंक)")
            st.write(", ".join([f".{k}" for k in unseen_pool]))
