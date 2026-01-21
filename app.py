import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="식품 데이터 분석 대시보드", layout="wide")
st.title("📊 식품 품목제조 보고 실시간 분석")

# 2. 사이드바 검색 조건 설정
st.sidebar.header("🔍 검색 및 분석 필터")

# 서비스 ID 선택 (완제품 I2790 / 첨가물 I1250 / 원재료 I0020)
category = st.sidebar.selectbox(
    "데이터 분류 선택",
    ["식품(완제품) - I2790", "식품첨가물 - I1250", "식품원재료 - I0020"]
)

# 선택된 카테고리에 따른 서비스 ID 할당
if "I2790" in category:
    service_id = "I2790"
    default_types = ["음료류", "과자류", "빵류"]
elif "I1250" in category:
    service_id = "I1250"
    default_types = ["혼합제제", "천연향료", "합성향료"]
else:
    service_id = "I0020"
    default_types = ["식물성", "동물성"]

# 식품유형 멀티 선택 (드롭다운)
selected_types = st.sidebar.multiselect("분석할 식품유형 선택", options=default_types, default=default_types[:1])

# 날짜 및 호출량 설정
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
with col2:
    end_date = st.date_input("종료일", datetime.now())

limit = st.sidebar.slider("데이터 호출량", 200, 1000, 500)
api_key = "9171f7ffd72f4ffcb62f"

# 3. 데이터 조회 및 시각화 로직
if st.sidebar.button("데이터 분석 시작"):
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    # API 요청 URL (샘플 규격 준수)
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{limit}/CHNG_DT={start_str}"

    try:
        with st.spinner("식약처 데이터를 분석 중입니다..."):
            response = requests.get(url)
            
            # 응답 체크 및 JSON 파싱
            if response.status_code != 200 or not response.text.strip():
                st.error(f"❌ '{service_id}' API 호출 실패. 권한 신청 여부를 확인하세요.")
                st.stop()

            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                df = pd.DataFrame(rows)
                
                if not df.empty:
                    # 1. 기간 필터링 (종료일 기준 추가 필터)
                    date_key = 'CHNG_DT' if 'CHNG_DT' in df.columns else 'PRMS_DT'
                    df['temp_date'] = df[date_key].str.replace(r'[^0-9]', '', regex=True).str[:8]
                    df = df[(df['temp_date'] >= start_str) & (df['temp_date'] <= end_str)]
                    
                    # 2. 선택 유형 필터링
                    if selected_types:
                        df = df[df['PRDLST_DCNM'].str.contains('|'.join(selected_types), na=False)]

                    if not df.empty:
                        # 상단 데이터 테이블
                        st.subheader(f"📋 {category} 상세 리스트 (총 {len(
