import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

st.set_page_config(page_title="Decimal Tracker: NIFTY & HSI", layout="wide")
st.title("🎯 12:00–01:00 PM Decimal Tracker & Top-5 Consensus Engine")
st.caption("1:00 PM पर 12-1 विंडो लॉक होते ही Top-5, यूनिक और कॉमन नंबर्स ऑटो-कैलकुलेट होंगे।")

index_choice = st.sidebar.selectbox("इंडेक्स चुनें:", ["NIFTY 50", "HANG SENG"])
ist = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(ist)
st.sidebar.info(f"🕒 वर्तमान IST समय: {now_ist.strftime('%Y-%m-%d %H:%M:%S')}")

if index_choice == "NIFTY 50":
    ticker_primary = "^NSEI"
    ticker_backup = "NIFTYBEES.NS"
    total_possible = 20
else:
    ticker_primary = "^HSI"
    ticker_backup = "2800.HK"
    total_possible = 100

@st.cache_data(ttl=60)
def fetch_today_data(primary, backup):
    df = yf.Ticker(primary).history(period="5d", interval="1m")
    if df.empty or len(df) < 30:
        df = yf.Ticker(backup).history(period="5d", interval="1m")
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

df_all = fetch_today_data(ticker_primary, ticker_backup)

if df_all.empty:
    st.error("डेटा फेच करने में समस्या आ रही है। कृपया रिफ्रेश करें।")
    st.stop()

latest_date = df_all["Date"].max()
day_df = df_all[df_all["Date"] == latest_date].copy()
win_df = day_df.between_time("12:00:00", "13:00:00").copy()

st.subheader(f"📅 सत्र: {latest_date} ({index_choice})")

if len(win_df) < 5:
    st.warning("⚠️ 12:00 PM से 01:00 PM की विंडो का पर्याप्त डेटा अभी उपलब्ध नहीं हुआ है। (1:00 PM के बाद पूरा डेटा लॉक होगा)")
    st.stop()

counts = win_df["Decimal"].value_counts()
top5_common = counts.head(5)
common_pool = counts[counts >= 2]
unique_pool = counts[counts == 1]

if total_possible == 20:
    all_possible = [f"{x * 5:02d}" for x in range(20)]
else:
    all_possible = [f"{x:02d}" for x in range(100)]
unseen_pool = sorted(list(set(all_possible) - set(counts.index)))

# Top-5 कार्ड्स डिस्प्ले
st.markdown("---")
st.markdown("### ⭐ 12:00–01:00 PM के Top-5 डोमिनेंट नंबर")

cols = st.columns(5)
for i in range(5):
    with cols[i]:
        if i < len(top5_common):
            dec_val = top5_common.index[i]
            rep_cnt = top5_common.iloc[i]
            st.metric(
                label=f"रैंक #{i+1}",
                value=f".{dec_val}",
                delta=f"{rep_cnt} बार आया"
            )
        else:
            st.metric(label=f"रैंक #{i+1}", value="-", delta="उपलब्ध नहीं")

st.markdown("---")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"#### 🔄 कॉमन पूल ({len(common_pool)} अंक)")
    st.caption("जो 12-1 के बीच 2 या उससे अधिक बार आए:")
    if not common_pool.empty:
        c_disp = [f".{k} ({v}x)" for k, v in common_pool.items()]
        st.write(", ".join(c_disp))
    else:
        st.write("कोई कॉमन नंबर नहीं बना।")

with c2:
    st.markdown(f"#### ⚡ यूनिक पूल ({len(unique_pool)} अंक)")
    st.caption("जो 12-1 के बीच सिर्फ 1 बार आए:")
    if not unique_pool.empty:
        u_disp = [f".{k}" for k in sorted(unique_pool.index)]
        st.write(", ".join(u_disp))
    else:
        st.write("कोई यूनिक नंबर नहीं।")

with c3:
    st.markdown(f"#### 🚫 अनसीन पूल ({len(unseen_pool)} अंक)")
    st.caption("जो 12-1 विंडो में नहीं दिखे:")
    st.write(", ".join([f".{k}" for k in unseen_pool]))

last_bar_time = day_df.index[-1].time()
st.markdown("---")

if last_bar_time >= datetime.strptime("15:25:00", "%H:%M:%S").time():
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

    st.success(f"**03:30 PM क्लोजिंग भाव:** {close_price:.2f} (दशमलव: **.{close_dec}**) | **स्टेटस:** {res_tag}")
else:
    st.info("ℹ️ बाजार अभी खुला है या 3:30 PM क्लोजिंग नहीं आई है। क्लोजिंग वेरिफिकेशन 03:30 PM पर एक्टिव होगा।")
