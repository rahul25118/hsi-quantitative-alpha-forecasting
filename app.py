import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Index Decimal Analytics: 12-1 PM Unique vs Common",
    page_icon="🎯",
    layout="wide"
)

# ऑटो-रीफ्रेश (हर 20 सेकंड में लाइव अपडेट)
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=20 * 1000, key="auto_refresh_tick")
except Exception:
    pass

st.title("🎯 Index Decimal Dynamics: 12:00-01:00 PM Window Analytics")
st.caption("Live Unique (1x) vs Common (2x+) Frequency Breakdown & Closing Decimal Audit for NIFTY 50 and HSI")

# ---------------------------------------------------------
# साइडबार कॉन्फ़िगरेशन
# ---------------------------------------------------------
st.sidebar.header("⚙️ इंडेक्स चयन")
market_choice = st.sidebar.selectbox(
    "इंडेक्स चुनें:",
    ["NIFTY 50 (India - NSE)", "Hang Seng Index (Hong Kong - HKEX)"],
    index=0
)

is_nifty = "NIFTY" in market_choice
ticker_symbol = "^NSEI" if is_nifty else "^HSI"
backup_symbol = "NIFTYBEES.NS" if is_nifty else "HSI=F"
tz_name = "Asia/Kolkata"  # दोनों के लिए 12-1 PM IST तुलना

# ---------------------------------------------------------
# डेटा लोडर (Zero-Delay Fast Info + 1m Bars)
# ---------------------------------------------------------
@st.cache_data(ttl=10)
def load_market_data(primary_tk, backup_tk, tz):
    t = yf.Ticker(primary_tk)
    live_price = None
    try:
        live_price = t.fast_info.get("last_price")
    except Exception:
        pass

    if live_price is None:
        try:
            live_price = yf.Ticker(backup_tk).fast_info.get("last_price")
        except Exception:
            pass

    df = yf.download(primary_tk, period="7d", interval="1m", progress=False)
    if df.empty or len(df) < 30:
        df = yf.download(backup_tk, period="7d", interval="1m", progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert(tz)
    else:
        df.index = df.index.tz_convert(tz)

    if live_price is not None and not df.empty:
        last_rec = df["Close"].iloc[-1]
        now_time = pd.Timestamp.now(tz=tz)
        if (now_time - df.index[-1]).total_seconds() > 60 or abs(live_price - last_rec) > 0.001:
            inject_bar = pd.DataFrame([{
                "Open": live_price, "High": live_price, "Low": live_price,
                "Close": live_price, "Volume": 0
            }], index=[now_time])
            df = pd.concat([df, inject_bar])

    df["Date"] = df.index.date
    df["Decimal"] = df["Close"].apply(lambda x: f"{float(x):.2f}".split(".")[1].zfill(2))
    return df

with st.spinner(f"{ticker_symbol} का डेटा लोड हो रहा है..."):
    try:
        df_1m = load_market_data(ticker_symbol, backup_symbol, tz_name)
    except Exception as e:
        st.error(f"डेटा लोड त्रुटि: {e}")
        st.stop()

available_dates = sorted(df_1m["Date"].unique(), reverse=True)
selected_date = st.sidebar.selectbox("सत्र चुनें:", available_dates, index=0)

day_df = df_1m[df_1m["Date"] == selected_date].copy()
if day_df.empty:
    st.warning("सत्र का डेटा उपलब्ध नहीं है।")
    st.stop()

actual_close_price = day_df.iloc[-1]["Close"]
actual_close_dec = day_df.iloc[-1]["Decimal"]
latest_time = day_df.index[-1].strftime("%H:%M:%S")

col1, col2, col3, col4 = st.columns(4)
col1.metric("अंतिम भाव", f"{actual_close_price:.2f}")
col2.metric("क्लोजिंग दशमलव", f".{actual_close_dec}")
col3.metric("अंतिम टिक समय (IST)", latest_time)
col4.metric("सत्र के कुल 1-मिनट बार्स", f"{len(day_df)}")

st.markdown("---")

tab1, tab2 = st.tabs(["🔍 12:00-01:00 PM विंडो विश्लेषण", "📊 7-दिवसीय तुलनात्मक ऑडिट"])

# =========================================================
# TAB 1: 12:00 से 01:00 PM विंडो विश्लेषण
# =========================================================
with tab1:
    st.subheader(f"📅 तारीख: {selected_date} (12:00 PM से 01:00 PM IST विंडो)")
    win_df = day_df.between_time("12:00:00", "13:00:00")

    if win_df.empty:
        st.warning("इस सत्र में 12:00 से 01:00 PM के बीच कोई कैंडल्स उपलब्ध नहीं हैं।")
    else:
        counts = win_df["Decimal"].value_counts()
        single_unique = sorted(list(counts[counts == 1].index))
        common_series = counts[counts > 1]

        avg_f = common_series.mean() if not common_series.empty else 0
        super_common = common_series[common_series > avg_f]

        close_in_win = actual_close_dec in counts.index
        close_freq = counts.get(actual_close_dec, 0)
        ranked = list(counts.index)
        close_rank = f"#{ranked.index(actual_close_dec) + 1}" if close_in_win else "विंडो से बाहर (0 बार)"

        if not close_in_win:
            match_status = "❌ क्लोजिंग दशमलव 12-1 की विंडो में था ही नहीं"
            status_color = "error"
        elif actual_close_dec in super_common.index:
            match_status = f"★ हाई-फ़्रीक्वेंसी कॉमन पूल में था ({close_freq} बार आया था)"
            status_color = "success"
        elif actual_close_dec in common_series.index:
            match_status = f"✓ सामान्य कॉमन पूल में था ({close_freq} बार आया था)"
            status_color = "info"
        else:
            match_status = "• सिंगल यूनिक पूल में था (सिर्फ 1 बार आया था)"
            status_color = "warning"

        if status_color == "success":
            st.success(f"**क्लोजिंग परिणाम:** .{actual_close_dec} | रैंक: {close_rank} | {match_status}")
        elif status_color == "info":
            st.info(f"**क्लोजिंग परिणाम:** .{actual_close_dec} | रैंक: {close_rank} | {match_status}")
        elif status_color == "warning":
            st.warning(f"**क्लोजिंग परिणाम:** .{actual_close_dec} | रैंक: {close_rank} | {match_status}")
        else:
            st.error(f"**क्लोजिंग परिणाम:** .{actual_close_dec} | {match_status}")

        c_u, c_c, c_h = st.columns(3)
        c_u.metric("यूनिक दशमलव (1 बार आए)", len(single_unique))
        c_c.metric("कॉमन दशमलव (2+ बार आए)", len(common_series))
        c_h.metric("हाई-फ़्रीक्वेंसी दशमलव", len(super_common))

        st.markdown("#### 1. शुद्ध यूनिक दशमलव (Only 1x):")
        st.code(", ".join([f".{d}" for d in single_unique]) if single_unique else "कोई नहीं")

        st.markdown("#### 2. कॉमन दशमलव (2x या अधिक):")
        if not common_series.empty:
            common_df = pd.DataFrame({
                "दशमलव": [f".{k}" for k in common_series.index],
                "बारंबारता (Frequency)": common_series.values,
                "श्रेणी": ["★ हाई-फ़्रीक्वेंसी" if k in super_common.index else "सामान्य कॉमन" for k in common_series.index]
            })
            st.dataframe(common_df, use_container_width=True, height=250)

            fig = px.bar(
                common_df.head(15), x="दशमलव", y="बारंबारता (Frequency)", color="श्रेणी",
                title="12:00-01:00 PM के टॉप कॉमन दशमलव",
                color_discrete_map={"★ हाई-फ़्रीक्वेंसी": "#00CC96", "सामान्य कॉमन": "#636EFA"}
            )
            st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 2: 7-दिवसीय ऑडिट टेबल
# =========================================================
with tab2:
    st.subheader(f"📊 7-दिवसीय क्लोजिंग मैच ऑडिट ({market_choice})")

    audit_rows = []
    for d in sorted(df_1m["Date"].unique()):
        sub_d = df_1m[df_1m["Date"] == d]
        if len(sub_d) < 40:
            continue
        c_dec = sub_d.iloc[-1]["Decimal"]
        w_df = sub_d.between_time("12:00:00", "13:00:00")
        if w_df.empty:
            continue

        w_counts = w_df["Decimal"].value_counts()
        w_single = w_counts[w_counts == 1]
        w_common = w_counts[w_counts > 1]
        w_avg = w_common.mean() if not w_common.empty else 0
        w_super = w_common[w_common > w_avg]

        freq = w_counts.get(c_dec, 0)
        ranked = list(w_counts.index)
        rk = f"#{ranked.index(c_dec) + 1}" if c_dec in ranked else "विंडो से बाहर"

        if freq == 0:
            b_label = "❌ दिखा ही नहीं"
        elif c_dec in w_super.index:
            b_label = "★ हाई-फ़्रीक्वेंसी"
        elif c_dec in w_common.index:
            b_label = "✓ सामान्य कॉमन"
        else:
            b_label = "• सिंगल यूनिक"

        top1 = f".{w_counts.index[0]} ({w_counts.iloc[0]}x)"
        top1_match = "✓ हाँ" if c_dec == w_counts.index[0] else "✗ नहीं"

        audit_rows.append({
            "तारीख": str(d),
            "क्लोजिंग दशमलव": f".{c_dec}",
            "12-1 टॉप मोड": top1,
            "टॉप मोड मैच?": top1_match,
            "12-1 बारंबारता": f"{freq} बार",
            "रैंक": rk,
            "क्लोजिंग श्रेणी": b_label,
            "यूनिक संख्या": len(w_single),
            "कॉमन संख्या": len(w_common)
        })

    df_audit = pd.DataFrame(audit_rows)
    st.dataframe(df_audit, use_container_width=True)
