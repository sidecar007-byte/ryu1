import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정 및 제목 (괄호 삭제)
st.set_page_config(page_title="식품 품목제조 분석 시스템", layout="wide")
st.title("📊 식품 품목제조보고 분석 대시보드")

# 2. 사이드바 설정
st.sidebar.header("🔍 세부 검색 설정")

# [기능 1] 식품(완제품) vs 식품첨가물 구분
category_mode = st.sidebar.radio(
    "품목 대분류 선택",
    ["식품(완제품/원료)", "식품첨가물"]
)

# API 키 및 서비스 ID 설정
api_key = "9171f7ffd72f4ffcb62f"
# 완제품은 I2790, 첨가물은 I1250 사용
service_id = "I1260" if category_mode == "식품(완제품/원료)" else "I1250"

# [기능 2] 유형 드롭다운 목록
if category_mode == "식품(완제품/원료)":
    type_options = ["음료류", "과자류", "빵류", "유가공품", "소스", "즉석섭취식품"]
else:
    type_options = ["혼합제제", "천연향료", "합성향료", "착색료", "유화제"]
    
target_types = st.sidebar.multiselect("식품유형 선택", options=type_options, default=[type_options[0]])

# 기간 설정
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
with col2:
    end_date = st.date_input("종료일", datetime.now())

search_limit = st.sidebar.slider("데이터 호출량", 200, 1000, 500)

if st.sidebar.button("데이터 분석 시작"):
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    # 명세서 기준 URL (추가 인자는 & 기호 사용 가능성 대비)
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={start_str}"

    try:
        with st.spinner("데이터를 불러오는 중..."):
            response = requests.get(url)
            
            # [오류 해결] 응답 내용 확인 로직 추가
            if not response.text or response.text.strip() == "":
                st.error("❌ 서버로부터 받은 데이터가 비어 있습니다. (Empty Response)")
                st.info("💡 원인: 해당 날짜에 데이터가 없거나, API 키의 권한이 선택한 서비스 ID에 없을 수 있습니다.")
                st.stop()

            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                df = pd.DataFrame(rows)
                
                if not df.empty:
                    # 1. 종료일 기준 필터링
                    date_col = next((c for c in ['CHNG_DT', 'PRMS_DT'] if c in df.columns), None)
                    if date_col:
                        df['temp_date'] = df[date_col].str.replace(r'[^0-9]', '', regex=True).str[:8]
                        df = df[(df['temp_date'] >= start_str) & (df['temp_date'] <= end_str)]
                    
                    # 2. 드롭다운 유형 필터링
                    if target_types:
                        df = df[df['PRDLST_DCNM'].str.contains('|'.join(target_types), na=False)]

                    if not df.empty:
                        st.subheader(f"📋 {category_mode} 상세 목록")
                        st.dataframe(df[['BSSH_NM', 'PRDLST_NM', 'PRDLST_DCNM', 'PRMS_DT']], use_container_width=True)

                        st.markdown("---")

                        # [기능 3] 하단 대시보드 시각화
                        chart_col1, chart_col2 = st.columns(2)

                        with chart_col1:
                            st.subheader("🍦 제품명 기준 플레이버 분류")
                            flavors = ['딸기', '초코', '바닐라', '포도', '사과', '오렌지', '레몬', '민트', '피치']
                            flavor_data = [{'맛': f, '건수': df['PRDLST_NM'].str.contains(f).sum()} for f in flavors]
                            flavor_df = pd.DataFrame([f for f in flavor_data if f['건수'] > 0])
                            
                            if not flavor_df.empty:
                                fig1 = px.pie(flavor_df, values='건수', names='맛', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                                st.plotly_chart(fig1, use_container_width=True)
                            else:
                                st.write("검색된 데이터 내에 주요 플레이버 키워드가 없습니다.")
                            st.caption(f"📅 검색 기간: {start_date} ~ {end_date}")

                        with chart_col2:
                            st.subheader("📊 신고 유형별 비중 및 건수")
                            type_counts = df['PRDLST_DCNM'].value_counts().reset_index()
                            type_counts.columns = ['유형', '건수']
                            type_counts['비율(%)'] = (type_counts['건수'] / len(df) * 100).round(1)
                            
                            fig2 = px.bar(type_counts, x='유형', y='건수', text='비율(%)', color='건수')
                            fig2.update_traces(texttemplate='%{text}%', textposition='outside')
                            st.plotly_chart(fig2, use_container_width=True)
                            st.caption(f"📅 검색 기간: {start_date} ~ {end_date}")
                    else:
                        st.warning("🔎 필터링 결과 조건에 맞는 데이터가 없습니다.")
                else:
                    st.info("해당 기간에 등록된 데이터가 없습니다.")
            else:
                st.error("API 응답 구조가 잘못되었습니다. 권한을 확인하세요.")
                
    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
