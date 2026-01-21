import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from urllib.parse import quote

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="식품 데이터 통합 분석 시스템", layout="wide")
st.title("📊 식품 품목제조 및 원재료 분석 대시보드")

# 2. 사이드바 검색 및 분류 설정
st.sidebar.header("🔍 세부 검색 설정")

# [기능 1] ID 기반 대분류 선택
category_mode = st.sidebar.selectbox(
    "데이터 분류 선택",
    ["식품(완제품/원료) - I2790", "식품첨가물 - I1250", "식품원재료 - I0020"]
)

# 분류에 따른 서비스 ID 매핑
if "I2790" in category_mode:
    service_id = "I2790"
    type_options = ["음료류", "과자류", "빵류", "유가공품", "소스", "즉석섭취식품", "기타가공품"]
elif "I1250" in category_mode:
    service_id = "I1250"
    type_options = ["혼합제제", "천연향료", "합성향료", "착색료", "보존료", "유화제"]
else:
    service_id = "I0020"
    type_options = ["식물성", "동물성", "미생물", "기타"]

# [기능 2] 식품유형 드롭다운 (멀티 선택)
target_types = st.sidebar.multiselect("세부 유형 선택", options=type_options, default=[type_options[0]])

# 기간 설정 (원재료 DB인 I0020은 기간 검색 대신 명칭 검색 위주로 동작할 수 있음)
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
with col2:
    end_date = st.date_input("종료일", datetime.now())

search_limit = st.sidebar.slider("데이터 호출량", 200, 1000, 500)
api_key = "9171f7ffd72f4ffcb62f"

if st.sidebar.button("데이터 분석 시작"):
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    # API 호출 주소 설정
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={start_str}"

    try:
        with st.spinner("식약처 서버에서 데이터를 수집 중..."):
            response = requests.get(url)
            
            # 응답 데이터 유효성 검사
           if not response.text or response.text.startswith("<"):
    st.error(f"❌ 서버 응답 내용: {response.text[:200]}") # 서버가 보내는 실제 에러 메시지 출력

            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                df = pd.DataFrame(rows)
                
                if not df.empty:
                    # 1. 날짜 필터링 (종료일 기준)
                    date_col = next((c for c in ['CHNG_DT', 'PRMS_DT', 'LAST_UPDT_DTM'] if c in df.columns), None)
                    if date_col:
                        df['temp_date'] = df[date_col].str.replace(r'[^0-9]', '', regex=True).str[:8]
                        df = df[(df['temp_date'] >= start_str) & (df['temp_date'] <= end_str)]
                    
                    # 2. 드롭다운 유형 필터링
                    if target_types:
                        df = df[df['PRDLST_DCNM'].str.contains('|'.join(target_types), na=False) | 
                                df.get('RAWMED_NM', pd.Series()).str.contains('|'.join(target_types), na=False)]

                    if not df.empty:
                        st.subheader(f"📋 {category_mode} 조회 결과 (총 {len(df)}건)")
                        # 주요 컬럼만 표시
                        display_cols = [c for c in ['BSSH_NM', 'PRDLST_NM', 'PRDLST_DCNM', 'PRMS_DT', 'RAWMED_NM'] if c in df.columns]
                        st.dataframe(df[display_cols], use_container_width=True)

                        st.markdown("---")

                        # [기능 3] 하단 대시보드 (차트 2종)
                        chart_col1, chart_col2 = st.columns(2)

                        with chart_col1:
                            st.subheader("🍦 제품명 기반 플레이버 분류")
                            flavors = ['딸기', '초코', '바닐라', '포도', '사과', '오렌지', '레몬', '민트', '피치', '커피']
                            name_col = 'PRDLST_NM' if 'PRDLST_NM' in df.columns else 'RAWMED_NM'
                            flavor_data = [{'플레이버': f, '건수': df[name_col].str.contains(f).sum()} for f in flavors]
                            flavor_df = pd.DataFrame([f for f in flavor_data if f['건수'] > 0])
                            
                            if not flavor_df.empty:
                                fig1 = px.pie(flavor_df, values='건수', names='플레이버', hole=0.4, 
                                             color_discrete_sequence=px.colors.qualitative.Safe)
                                st.plotly_chart(fig1, use_container_width=True)
                            else:
                                st.write("선택된 데이터 내에 주요 플레이버 키워드가 없습니다.")
                            st.caption(f"📅 검색 기간: {start_date} ~ {end_date}")

                        with chart_col2:
                            st.subheader("📊 신고 유형별 비중 및 건수")
                            type_col = 'PRDLST_DCNM' if 'PRDLST_DCNM' in df.columns else 'RAWMED_NM'
                            type_counts = df[type_col].value_counts().reset_index()
                            type_counts.columns = ['유형', '건수']
                            type_counts['비율(%)'] = (type_counts['건수'] / len(df) * 100).round(1)
                            
                            fig2 = px.bar(type_counts, x='유형', y='건수', text='비율(%)', 
                                         color='건수', color_continuous_scale='Blues')
                            fig2.update_traces(texttemplate='%{text}%', textposition='outside')
                            st.plotly_chart(fig2, use_container_width=True)
                            st.caption(f"📅 검색 기간: {start_date} ~ {end_date}")
                    else:
                        st.warning("🔎 필터 조건에 일치하는 데이터가 없습니다.")
                else:
                    st.info("해당 기간에 등록된 원본 데이터가 없습니다.")
            else:
                st.error("API 응답 구조에 오류가 있습니다. 인증키 권한을 확인하세요.")
                
    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
