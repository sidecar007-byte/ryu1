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

category = st.sidebar.selectbox(
    "데이터 분류 선택",
    ["식품(완제품) - I2790", "식품첨가물 - I1250", "식품원재료 - I0020"]
)

if "I2790" in category:
    service_id = "I2790"
    default_types = ["음료류", "과자류", "빵류", "유가공품", "소스"]
elif "I1250" in category:
    service_id = "I1250"
    default_types = ["혼합제제", "천연향료", "합성향료", "착색료"]
else:
    service_id = "I0020"
    default_types = ["식물성", "동물성", "미생물"]

selected_types = st.sidebar.multiselect("분석할 식품유형 선택", options=default_types, default=default_types[:1])

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
    
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{limit}/CHNG_DT={start_str}"

    try:
        with st.spinner("데이터를 분석 중입니다..."):
            response = requests.get(url)
            
            if response.status_code != 200 or not response.text.strip():
                st.error(f"❌ '{service_id}' API 호출 실패. 서비스 권한을 확인하세요.")
                st.stop()

            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                df = pd.DataFrame(rows)
                
                if not df.empty:
                    # 날짜 필터링
                    date_key = 'CHNG_DT' if 'CHNG_DT' in df.columns else 'PRMS_DT'
                    df['temp_date'] = df[date_key].str.replace(r'[^0-9]', '', regex=True).str[:8]
                    df = df[(df['temp_date'] >= start_str) & (df['temp_date'] <= end_str)]
                    
                    # 유형 필터링
                    if selected_types:
                        df = df[df['PRDLST_DCNM'].str.contains('|'.join(selected_types), na=False)]

                    if not df.empty:
                        # [오류 해결 부분] 괄호와 문자열을 완벽히 닫음
                        st.subheader(f"📋 {category} 상세 리스트 (총 {len(df)}건)")
                        st.dataframe(df[['BSSH_NM', 'PRDLST_NM', 'PRDLST_DCNM', 'PRMS_DT']], use_container_width=True)

                        st.markdown("---")
                        
                        # 하단 대시보드
                        c1, c2 = st.columns(2)

                        with c1:
                            st.subheader("🍦 플레이버(Flavor) 분류")
                            keywords = ['딸기', '초코', '바닐라', '포도', '사과', '오렌지', '레몬', '민트']
                            flavor_counts = [{'Flavor': k, 'Count': df['PRDLST_NM'].str.contains(k).sum()} for k in keywords]
                            flavor_df = pd.DataFrame([f for f in flavor_counts if f['Count'] > 0])
                            
                            if not flavor_df.empty:
                                fig1 = px.pie(flavor_df, values='Count', names='Flavor', hole=0.4, 
                                             color_discrete_sequence=px.colors.qualitative.Pastel)
                                st.plotly_chart(fig1, use_container_width=True)
                            else:
                                st.info("플레이버 키워드 제품이 없습니다.")
                            st.caption(f"📅 검색 기간: {start_date} ~ {end_date}")

                        with c2:
                            st.subheader("📊 품목유형별 비중 (%)")
                            type_counts = df['PRDLST_DCNM'].value_counts().reset_index()
                            type_counts.columns = ['Type', 'Count']
                            type_counts['Ratio(%)'] = (type_counts['Count'] / len(df) * 100).round(1)
                            
                            fig2 = px.bar(type_counts, x='Type', y='Count', text='Ratio(%)',
                                         color='Count', color_continuous_scale='Blues')
                            fig2.update_traces(texttemplate='%{text}%', textposition='outside')
                            st.plotly_chart(fig2, use_container_width=True)
                            st.caption(f"📅 검색 기간: {start_date} ~ {end_date}")
                    else:
                        st.warning("🔎 조건에 맞는 데이터가 없습니다.")
                else:
                    st.info("검색된 데이터가 없습니다.")
            else:
                st.error("⚠️ API 응답 형식이 올바르지 않습니다.")
                
    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
