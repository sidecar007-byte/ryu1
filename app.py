import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="식품첨가물 품목제조 분석", layout="wide")
st.title("🧪 식품첨가물(I1250) 품목제조 분석 대시보드")

# 2. 사이드바 검색 조건 설정
st.sidebar.header("🔍 세부 검색 설정")

# [기능 1] 식품원료/완제품 구분 입력
category_sub = st.sidebar.selectbox(
    "품목 구분 선택",
    ["식품첨가물(완제품)", "식품첨가물(원료)"]
)

# [기능 2] 식품유형 드롭다운 (샘플 기반 주요 유형)
type_options = ["혼합제제", "천연향료", "합성향료", "착색료", "보존료", "유화제", "증점제"]
target_types = st.sidebar.multiselect("식품유형 선택", options=type_options, default=["혼합제제", "천연향료"])

# 기간 및 호출량 설정
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
with col2:
    end_date = st.date_input("종료일", datetime.now())

limit = st.sidebar.slider("데이터 호출량", 200, 1000, 500)
api_key = "9171f7ffd72f4ffcb62f"
service_id = "I1250"

if st.sidebar.button("데이터 분석 시작"):
    start_str = start_date.strftime('%Y%m%d')
    # 명세서 기준 URL (JSON 형식)
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{limit}/CHNG_DT={start_str}"

    try:
        with st.spinner("I1250 데이터를 수집 중입니다..."):
            response = requests.get(url)
            
            # 응답 검증 (char 0 에러 방지)
            if not response.text or response.text.startswith("<"):
                st.error("❌ I1250 서비스 응답 오류. API 키 권한을 확인하세요.")
                st.stop()

            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                df = pd.DataFrame(rows)
                
                if not df.empty:
                    # 날짜 필터링 (사용자 선택 종료일 기준)
                    df['temp_date'] = df['CHNG_DT'].str.replace(r'[^0-9]', '', regex=True).str[:8]
                    df = df[(df['temp_date'] >= start_str) & (df['temp_date'] <= end_date.strftime('%Y%m%d'))]
                    
                    # 식품유형 드롭다운 필터링
                    if target_types:
                        df = df[df['PRDLST_DCNM'].str.contains('|'.join(target_types), na=False)]

                    if not df.empty:
                        st.subheader(f"📋 조회 결과 (총 {len(df)}건)")
                        st.dataframe(df[['BSSH_NM', 'PRDLST_NM', 'PRDLST_DCNM', 'CHNG_DT']], use_container_width=True)

                        st.markdown("---")
                        
                        # [기능 3] 대시보드 하단 차트화
                        left_chart, right_chart = st.columns(2)

                        with left_chart:
                            st.subheader("🍦 제품명 기반 플레이버 분류")
                            flavors = ['딸기', '초코', '바닐라', '포도', '사과', '오렌지', '레몬', '민트', '피치']
                            f_data = [{'맛': f, '건수': df['PRDLST_NM'].str.contains(f).sum()} for f in flavors]
                            f_df = pd.DataFrame([x for x in f_data if x['건수'] > 0])
                            
                            if not f_df.empty:
                                fig1 = px.pie(f_df, values='건수', names='맛', hole=0.4, 
                                             color_discrete_sequence=px.colors.qualitative.Pastel)
                                st.plotly_chart(fig1, use_container_width=True)
                            else:
                                st.info("선택된 데이터 내에 주요 플레이버 키워드가 없습니다.")
                            st.caption(f"📅 검색 기간: {start_date} ~ {end_date}")

                        with right_chart:
                            st.subheader("📊 품목유형별 신고 비중 (전체 대비 %)")
                            type_counts = df['PRDLST_DCNM'].value_counts().reset_index()
                            type_counts.columns = ['Type', 'Count']
                            # 전체 대비 비율 계산
                            type_counts['Ratio(%)'] = (type_counts['Count'] / len(df) * 100).round(1)
                            
                            fig2 = px.bar(type_counts, x='Type', y='Count', text='Ratio(%)',
                                         color='Count', color_continuous_scale='Reds')
                            fig2.update_traces(texttemplate='%{text}%', textposition='outside')
                            st.plotly_chart(fig2, use_container_width=True)
                            st.caption(f"📅 검색 기간: {start_date} ~ {end_date}")
                    else:
                        st.warning("🔎 필터 조건에 맞는 데이터가 없습니다.")
                else:
                    st.info("해당 기간에 등록된 데이터가 없습니다.")
            else:
                st.error("⚠️ API 응답 형식이 올바르지 않습니다.")
                
    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
