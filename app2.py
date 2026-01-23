import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="서울 기온 데이터 분석소", layout="wide")

@st.cache_data
def load_data(file_path):
    # CSV 파일 로드 (7행의 헤더 무시 설정 필요 시 조정)
    df = pd.read_csv(file_path, encoding='cp949', skiprows=7)
    df.columns = ['날짜', '지점', '평균기온', '최저기온', '최고기온']
    df['날짜'] = pd.to_datetime(df['날짜'])
    return df

# 기본 데이터 로드
try:
    base_df = load_data('ta_20260122174530.csv')
except:
    st.error("기본 데이터 파일을 찾을 수 없습니다.")
    base_df = pd.DataFrame()

# 1. 사이드바: 데이터 업로드
st.sidebar.header("📁 데이터 설정")
uploaded_file = st.sidebar.file_uploader("추가 데이터를 업로드하세요 (CSV)", type=['csv'])

if uploaded_file:
    new_data = pd.read_csv(uploaded_file, encoding='cp949', skiprows=7)
    new_data.columns = ['날짜', '지점', '평균기온', '최저기온', '최고기온']
    new_data['날짜'] = pd.to_datetime(new_data['날짜'])
    df = pd.concat([base_df, new_data]).drop_duplicates('날짜').sort_values('날짜')
    st.sidebar.success("데이터가 성공적으로 병합되었습니다!")
else:
    df = base_df

st.title("🌡️ 서울 역사 기온 분석 웹앱")

# 2. 특정 날짜 비교 분석
st.header("🔍 특정 날짜 기온 비교")
target_date = st.date_input("비교하고 싶은 날짜를 선택하세요", value=df['날짜'].max())
target_md = target_date.strftime('%m-%d')

# 과거 같은 월-일 데이터 추출
same_day_history = df[df['날짜'].dt.strftime('%m-%d') == target_md]
target_info = same_day_history[same_day_history['날짜'] == pd.to_datetime(target_date)]

if not target_info.empty:
    avg_temp = target_info['평균기온'].values[0]
    hist_avg = same_day_history['평균기온'].mean()
    diff = avg_temp - hist_avg
    
    col1, col2, col3 = st.columns(3)
    col1.metric("선택한 날 기온", f"{avg_temp}°C")
    col2.metric("역대 평균 기온", f"{hist_avg:.2f}°C")
    col3.metric("차이", f"{diff:.2f}°C", delta=diff)

    fig = px.line(same_day_history, x='날짜', y='평균기온', title=f"역대 {target_md} 기온 변화")
    st.plotly_chart(fig, use_container_width=True)

# 3. 수능 시험날 별도 분석 (1994~2025)
st.header("📝 역대 수능 시험일 분석 (1994-2025)")

# 실제 수능 날짜 리스트 (데이터가 방대하므로 주요 샘플/규칙 적용 필요)
# 여기서는 예시로 11월 중순 데이터를 필터링하는 로직을 보여줍니다.
suneung_dates = [
    '1993-11-17', '1994-11-23', '1995-11-22', '1996-11-13', '1997-11-19',
    '1998-11-18', '1999-11-17', '2000-11-15', '2001-11-07', '2002-11-06',
    '2003-11-05', '2004-11-17', '2005-11-23', '2006-11-16', '2007-11-15',
    '2008-11-13', '2009-11-12', '2010-11-18', '2011-11-10', '2012-11-08',
    '2013-11-07', '2014-11-13', '2015-11-12', '2016-11-17', '2017-11-23',
    '2018-11-15', '2019-11-14', '2020-12-03', '2021-11-18', '2022-11-17',
    '2023-11-16', '2024-11-14' # 2025년은 확정 날짜 추가 필요
]
suneung_df = df[df['날짜'].isin(pd.to_datetime(suneung_dates))]

if not suneung_df.empty:
    fig_suneung = px.bar(suneung_df, x='날짜', y='최저기온', 
                         color='최저기온', title="역대 수능일 최저기온 (수능 한파 확인)",
                         color_continuous_scale='Bluered')
    st.plotly_chart(fig_suneung, use_container_width=True)
    st.write("최근으로 올수록 수능일 기온이 어떻게 변하고 있는지 확인해보세요.")
