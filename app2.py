import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="기온 데이터 품질 & 비교 분석", layout="wide")

@st.cache_data
def load_temperature_csv(file):
    df = pd.read_csv(
        file,
        skiprows=7,
        encoding="utf-8"
    )
    df.columns = ["date", "station", "avg", "min", "max"]
    df["date"] = df["date"].astype(str).str.replace(r'[^0-9\-]', '', regex=True)
    df["date"] = pd.to_datetime(df["date"])
    return df

# 기본 데이터 로드
base_df = load_temperature_csv("ta_20260122174530.csv")

st.title("🌡️ 기온 데이터 결측치 · 이상치 분석 & 날짜 비교")

# 추가 업로드
uploaded_files = st.file_uploader(
    "같은 형식의 CSV 업로드 (복수 가능)",
    type="csv",
    accept_multiple_files=True
)

dfs = [base_df]

if uploaded_files:
    for f in uploaded_files:
        dfs.append(load_temperature_csv(f))

df = pd.concat(dfs).drop_duplicates().sort_values("date")

# ======================
# 1. 결측치 확인
# ======================
st.subheader("1️⃣ 결측치 현황")

missing_df = df.isna().sum().reset_index()
missing_df.columns = ["컬럼", "결측치 개수"]

st.dataframe(missing_df, use_container_width=True)

# ======================
# 2. 이상치 탐지 (월별 IQR)
# ======================
st.subheader("2️⃣ 이상치 탐지 (월별 IQR 기준)")

df["month"] = df["date"].dt.month

def detect_outlier(group):
    q1 = group["avg"].quantile(0.25)
    q3 = group["avg"].quantile(0.75)
    iqr = q3 - q1
    return (group["avg"] < q1 - 1.5 * iqr) | (group["avg"] > q3 + 1.5 * iqr)

df["outlier"] = df.groupby("month", group_keys=False).apply(detect_outlier)

st.write(f"🔎 이상치 후보 개수: **{df['outlier'].sum()}건**")

# ======================
# 3. 날짜별 기온 비교
# ======================
st.subheader("3️⃣ 특정 날짜 vs 과거 동일 날짜 평균 비교")

default_date = df["date"].max()

target_date = st.date_input(
    "날짜 선택",
    value=default_date
)

target_date = pd.to_datetime(target_date)

today_row = df[df["date"] == target_date]

if not today_row.empty:
    m = target_date.month
    d = target_date.day

    history = df[
        (df["date"].dt.month == m) &
        (df["date"].dt.day == d)
    ]

    history_avg = history["avg"].mean()
    today_avg = today_row["avg"].iloc[0]

    diff = today_avg - history_avg

    st.metric(
        label="평균기온 차이 (℃)",
        value=f"{today_avg:.1f}℃",
        delta=f"{diff:+.1f}℃"
    )

    fig = px.histogram(
        history,
        x="avg",
        nbins=40,
        title=f"{m}월 {d}일 평균기온 분포 (역사적)"
    )
    fig.add_vline(
        x=today_avg,
        line_dash="dash",
        annotation_text="선택 날짜"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("선택한 날짜 데이터가 없습니다.")
