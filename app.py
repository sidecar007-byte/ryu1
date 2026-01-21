import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from urllib.parse import quote

# 1. 페이지 설정
st.set_page_config(page_title="식품 품목제조 분석 시스템", layout="wide")
st.title("📊 식품 품목제조보고 분석 대시보드")

# 2. 사이드바 검색 조건 설정
st.sidebar.header("🔍 세부 검색 설정")

# [기능 1] 분류 선택 (원료/완제품 vs 첨가물)
category_mode = st.sidebar.radio(
    "품목 대분류 선택",
    ["식품(완제품/원료)", "식품첨가물"]
)

# 분류에 따른 서비스 ID 매핑
service_id = "I2790" if category_mode == "식품(완제품/원료)" else "I1250"
api_key = "9171f7ffd72f4ffcb62f"

# [기능 2] 식품유형 드롭다운 (멀티 선택 가능)
if category_mode == "식품(완제품/원료)":
    type_options = ["음료류", "과자류", "빵류", "유가공품", "소스", "즉석섭취식품", "기타가공품"]
else:
    type_options = ["혼합제제", "천연향료", "합성향료", "착색료", "보존료", "유화제"]
    
target_types = st.sidebar.multiselect("조회할 식품유형 선택", options=type_options, default=type_options[0])

# 기간 설정
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
with col2:
    end_date = st.date_input("종료일", datetime.now())

search_limit = st.sidebar.slider("데이터 호출량", 200, 1000, 500)

if st.sidebar.button("데이터 분석 시작"):
    # API 호출 (기본 기간 설정)
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={start_str}"

    try:
        with st.spinner("데이터 수집 및 시각화 중..."):
            response = requests.get(url)
            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                df = pd.DataFrame(rows)
                
                # 기간 및 유형 필터링
                if not df.empty:
                    # 날짜 필터
                    date_col = next((c for c in ['CHNG_DT', 'PRMS_DT'] if c in df.columns), None)
                    if date_col:
                        df['clean_date'] = df[date_col].str.replace(r'[^0-9]', '', regex=True).str[:8]
                        df = df[(df['clean_date'] >= start_str) & (df['clean_date'] <= end_str)]
                    
                    # 드롭다운 유형 필터
                    if target_types:
                        df = df[df['PRDLST_DCNM'].str.contains('|'.join(target_types), na=False)]

                if not df.empty:
                    # 메인 표 출력
                    st.subheader(f"📋 조회 결과 (총 {len(df)}건)")
                    st.dataframe(df[['BSSH_NM', 'PRDLST_NM', 'PRDLST_DCNM', 'PRMS_DT']], use_container_width=True)

                    st.markdown("---")

                    # [기능 3] 대시보드 하단 차트화
                    char_col1, char_col2 = st.columns(2)

                    with char_col1:
                        st.subheader("🍓 주요 플레이버 분류")
                        # 제품명에서 플레이버 키워드 추출
                        flavor_keywords = ['딸기', '초코', '바닐라', '포도', '사과', '오렌지', '레몬', '민트']
                        flavor_counts = {}
                        for f in flavor_keywords:
                            cnt = df['PRDLST_NM'].str.contains(f).sum()
                            if cnt > 0: flavor_counts[f] = cnt
                        
                        if flavor_counts:
                            flavor_df = pd.DataFrame(list(flavor_counts.items()), columns=['Flavor', 'Count'])
                            fig1 = px.pie(flavor_df, values='Count', names='Flavor', hole=0.3, color_discrete_sequence=px.colors.sequential.RdBu)
                            st.plotly_chart(fig1, use_container_width=True)
                        else:
                            st.write("해당 데이터 내 주요 플레이버 키워드가 없습니다.")
                        st.caption(f"📅 검색 기간: {start_date} ~ {end_date}")

                    with char_col2:
                        st.subheader("📊 유형별 신고 비중")
                        type_counts = df['PRDLST_DCNM'].value_counts().reset_index()
                        type_counts.columns = ['Type', 'Count']
                        # 전체 대비 비율 계산
                        type_counts['Ratio(%)'] = (type_counts['Count'] / len(df) * 100).round(1)
                        
                        fig2 = px.bar(type_counts, x='Type', y='Count', text='Ratio(%)',
                                     color='Count', labels={'Count':'신고 건수'})
                        fig2.update_traces(texttemplate='%{text}%', textposition='outside')
                        st.plotly_chart(fig2, use_container_width=True)
                        st.caption(f"📅 검색 기간: {start_date} ~ {end_date}")

                else:
                    st.warning("🔎 조건에 맞는 데이터가 없습니다.")
            else:
                st.error("API 응답 오류. 권한을 확인하세요.")
    except Exception as e:
        st.error(f"🔌 오류 발생: {e}")
