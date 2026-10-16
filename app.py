import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

st.set_page_config(page_title="Multi-Index Decimal & Add-On Engine", layout="wide")

# साइडबार
st.sidebar.header("⚙️ सेटिंग्स")
index_choice = st.sidebar.selectbox("इंडेक्स चुनें:", ["HANG SENG", "NIFTY 50", "TAIEX (Taiwan)"])
ist = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(ist)
st.sidebar.info(f"🕒 वर्तमान IST: {now_ist.strftime('%Y-%m-%d %H:%M:%S')}")

if index_choice == "HANG SENG":
    ticker_primary = "^HSI"
    ticker_backup = "2800.HK"
    total_possible = 100
    win_start, win_end = "12:00:00", "13:00:00"
    close_time_str = "13:28:00"
    window_label = "12:00–01:00 PM IST (क्लोजिंग 01:30 PM)"
elif index_choice == "NIFTY 50":
    ticker_primary = "^NSEI"
    ticker_backup = "NIFTYBEES.NS"
    total_possible = 20
    win_start, win_end = "14:00:00", "15:00:00"
    close_time_str = "15:25:00"
    window_label = "02:00–03:00 PM IST (क्लोजिंग 03:30 PM)"
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
# 🇭🇰 HANG SENG DEDICATED ENGINE + ADD-ON MODULE
# =========================================================================
if index_choice == "HANG SENG":
    st.title("🎯 HSI Prediction System + Single/15-Number Add-On")
    st.caption("मौजूदा टाइम-स्लॉट विश्लेषण के आधार पर नया Single Candidate व 15-Number Filter Add-On।")

    # -------------------------------------------------------------
    # 🆕 ADD-ON MODULE SECTION (TOP OF HSI DASHBOARD)
    # -------------------------------------------------------------
    st.markdown("## 🧩 Add-On Module: Single Candidate & 15-Number Filters")
    st.caption("सुबह (07:00–09:30 AM) और दोपहर (12:30–01:30 PM) के ऐतिहासिक ऑडिट निष्कर्षों पर आधारित:")

    # 1. Single Candidates Cards
    c_m, c_a, c_c = st.columns(3)
    with c_m:
        st.metric(
            label="🌅 सुबह का Candidate (07:00–09:30 AM)",
            value=".78",
            delta="2/31 Hits (6.45% vs 1% Baseline)",
            help="सुबह के स्लॉट में 2 बार आने वाला एकमात्र नंबर।"
        )
    with c_a:
        st.metric(
            label="☀️ दोपहर का Candidate (12:30–01:30 PM)",
            value=".29",
            delta="कमजोर (टाई/नो क्लियर विनर)",
            delta_color="off",
            help="12:30-1:30 PM में सभी नंबर 1-1 बार आए। पूरे दोपहर सत्र में केवल .29 दो बार दिखा।"
        )
    with c_c:
        st.metric(
            label="⚖️ Combined Candidate (समग्र)",
            value=".78",
            delta="ओवरऑल 2 Hits (6.45%)",
            help="सुबह व दोपहर दोनों स्लॉट्स में सक्रिय रहने वाला नंबर।"
        )

    # 2. 15-Number Filters Display
    st.markdown("### 🔢 15-Number Filter Sets")

    m_15_set = [".78", ".72", ".17", ".22", ".20", ".35", ".79", ".50", ".56", ".51", ".09", ".13", ".75", ".29", ".47"]
    a_15_set = [".21", ".31", ".47", ".63", ".78", ".51", ".50", ".17", ".72", ".29", ".71", ".75", ".56", ".22", ".12"]
    comb_15_set = [".78", ".29", ".17", ".72", ".22", ".50", ".51", ".56", ".47", ".75", ".12", ".21", ".31", ".63", ".35"]

    t1, t2, t3 = st.tabs(["🌅 सुबह का 15-नंबर सेट", "☀️ दोपहर का 15-नंबर सेट", "⚖️ Combined 15-नंबर सेट"])
    with t1:
        st.markdown("**सुबह के 15 नंबर (07:00–09:30 AM IST):**")
        st.write("  •  ".join([f"`{x}`" for x in m_15_set]))
        st.caption("ऐतिहासिक इन-सैंपल कवरेज: 17/31 (54.8%) | बेसलाइन: 15%")
    with t2:
        st.markdown("**दोपहर के 15 नंबर (12:30–01:30 PM IST):**")
        st.write("  •  ".join([f"`{x}`" for x in a_15_set]))
        st.caption("ऐतिहासिक इन-सैंपल कवरेज: 18/31 (58.1%) | बेसलाइन: 15%")
    with t3:
        st.markdown("**Combined 15-नंबर सेट (Overlap + Recency):**")
        st.write("  •  ".join([f"`{x}`" for x in comb_15_set]))
        st.caption("10 ओवरलैप नंबर + 5 उच्चतम सक्रिय नंबर | इन-सैंपल: 18/31 (58.1%)")

    # 3. Statistical Baseline Comparison Table
    st.markdown("### 📊 Statistical Validation & Baseline Comparison")
    st.caption("यूनिफॉर्म रैंडम बेसलाइन बनाम इन-सैंपल व आउट-ऑफ-सैंपल सांख्यिकीय वास्तविकता:")

    validation_data = [
        {
            "समय": "सुबह (07:00–09:30)",
            "Single Candidate": ".78",
            "15-Number Filter": ", ".join(m_15_set),
            "Historical Hits": "17 / 31",
            "Hit Rate": "54.84%",
            "Evidence": "कमजोर (केवल .78 दो बार आया; आउट-ऑफ-सैंपल में कोई बढ़त नहीं)"
        },
        {
            "समय": "दोपहर (12:30–01:30)",
            "Single Candidate": ".29 (कमजोर)",
            "15-Number Filter": ", ".join(a_15_set),
            "Historical Hits": "18 / 31",
            "Hit Rate": "58.06%",
            "Evidence": "अत्यंत कमजोर (12:30-1:30 में सभी 1x टाई; .29 केवल 10:30-1:30 में 2x)"
        },
        {
            "समय": "Combined (समग्र)",
            "Single Candidate": ".78",
            "15-Number Filter": ", ".join(comb_15_set),
            "Historical Hits": "18 / 31",
            "Hit Rate": "58.06%",
            "Evidence": "ओवरफिटिंग (आउट-ऑफ-सैंपल वॉक-फॉरवर्ड में गिरकर 6.67% रह गया)"
        }
    ]
    st.dataframe(pd.DataFrame(validation_data), use_container_width=True)

    st.markdown("---")
    # -------------------------------------------------------------
    # 🔍 DAILY SESSION AUDIT & CLOSE VERIFICATION
    # -------------------------------------------------------------
    st.subheader(f"📅 दैनिक विश्लेषण: {selected_date}")

    if len(win_df) < 5:
        st.warning("⚠️ दोपहर विंडो का पर्याप्त डेटा उपलब्ध नहीं है।")
    else:
        target_close_time = datetime.strptime(close_time_str, "%H:%M:%S").time()
        bars_before_target = day_df[day_df.index.time <= target_close_time]

        if not bars_before_target.empty and len(bars_before_target) >= 10:
            close_bar = bars_before_target.iloc[-1]
            close_price = close_bar["Close"]
            close_dec = close_bar["Decimal"]
            formatted_dec = f".{close_dec}"

            # Check matches with Add-On candidates
            is_single_hit = (formatted_dec == ".78")
            is_comb15_hit = (formatted_dec in comb_15_set)

            c_res1, c_res2 = st.columns(2)
            with c_res1:
                if is_single_hit:
                    st.success(f"**Single Candidate (.78):** ✅ सटीक मैच हुआ! क्लोजिंग भाव: {close_price:.2f}")
                else:
                    st.error(f"**Single Candidate (.78):** ❌ मिस! क्लोजिंग दशमलव `{formatted_dec}` रहा।")
            with c_res2:
                if is_comb15_hit:
                    pos = comb_15_set.index(formatted_dec) + 1
                    st.success(f"**Combined 15-Filter:** ✅ मैच! (रैंक #{pos}) भाव: {close_price:.2f}")
                else:
                    st.error(f"**Combined 15-Filter:** ❌ मिस! `{formatted_dec}` फिल्टर से बाहर रहा।")
        else:
            st.info("ℹ️ 01:30 PM की क्लोजिंग अभी नहीं आई है या बाजार खुला है।")

    # -------------------------------------------------------------
    # 📋 7-DAY AUDIT TABLE
    # -------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 📋 पिछले 7 कारोबारी दिनों का Add-On परफॉर्मेंस ऑडिट")
    history_rows = []
    for d in available_dates[:7]:
        d_df = df_all[df_all["Date"] == d].copy()
        target_bars = d_df[d_df.index.time <= datetime.strptime(close_time_str, "%H:%M:%S").time()]
        if len(d_df) < 15 or target_bars.empty:
            continue
        c_dec = f".{target_bars.iloc[-1]['Decimal']}"
        c_price = target_bars.iloc[-1]["Close"]

        hit_single = "✅ हिट" if c_dec == ".78" else "❌ मिस"
        hit_15 = "✅ हिट" if c_dec in comb_15_set else "❌ मिस"

        history_rows.append({
            "तारीख": str(d),
            "क्लोजिंग भाव": f"{c_price:.2f}",
            "क्लोज दशमलव": c_dec,
            "Single (.78)": hit_single,
            "Combined 15 Filter": hit_15
        })

    if history_rows:
        st.dataframe(pd.DataFrame(history_rows), use_container_width=True)

# =========================================================================
# NIFTY & TAIEX DEFAULT LAYOUT (यथावत सुरक्षित)
# =========================================================================
else:
    st.title(f"🎯 {index_choice} Priority Engine")
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
