import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="식품 데이터 통합 분석", layout="wide")
st.title("📊 식품(완제품/첨가물/원재료) 통합 분석 대시보드")

# 2. 사이드바 설정
st.sidebar.header("🔍 검색 및 분석 필터")

category = st.sidebar.selectbox(
    "데이터 분류 선택",
    ["식품(완제품) - I2790", "식품첨가물 - I1250", "식품원재료 - I0020"]
)

# API ID 설정
if "I2790" in category:
    service_id = "I2790"
    default_types = ["음료류", "과자류", "빵류", "소스"]
elif "I1250" in category:
    service_id = "I1250"
    default_types = ["혼합제제", "천연향료", "합성향료"]
else:
    service_id = "I0020"
    default_types = ["식물성", "동물성", "기타"]

selected_types = st.sidebar.multiselect("유형 선택", options=default_types, default=default_types[:1])

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
with col2:
    end_date = st.date_input("종료일", datetime.now())

limit = st.sidebar.slider("데이터 호출량", 200, 1000, 500)
api_key = "9171f7ffd72f4ffcb62f"

if st.sidebar.button("데이터 분석 시작"):
    start_str = start_date.strftime('%Y%m%d')
    # 명세서 기반 URL 구성 (샘플 이미지의 구조 준수)
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{limit}/CHNG_DT={start_str}"

    try:
        with st.spinner("데이터를 가져오는 중입니다..."):
            response = requests.get(url)
            
            # [오류 해결 핵심] 응답 검증 로직
            if not response.text or response.text.startswith("<"):
                st.error(f"❌ '{service_id}' 서비스 응답 오류 (JSON 데이터 없음)")
                st.warning("식품안전나라 마이페이지에서 해당 서비스 ID의 '활용 승인' 상태를 확인하세요.")
                st.stop()

            data = response.json()
            
            # API 키 유효성 및 데이터 존재 여부 확인
            if service_id not in data:
                st.error("⚠️ API 인증키 또는 서비스 ID에 권한이 없습니다.")
                st.stop()

            rows = data[service_id].get("row", [])
            df = pd.DataFrame(rows)
            
            if not df.empty:
                # 날짜 및 유형 필터링
                date_key = 'CHNG_DT' if 'CHNG_DT' in df.columns else 'PRMS_DT'
                df['temp_date'] = df[date_key].str.replace(r'[^0-9]', '', regex=True).str[:8]
                df = df[(df['temp_date'] >= start_str) & (df['temp_date'] <= end_date.strftime('%Y%m%d'))]
                
                if selected_types:
                    df = df[df['PRDLST_DCNM'].str.contains('|'.join(selected_types), na=False)]

                if not df.empty:
                    st.subheader(f"📋 {category} 리스트 (총 {len(df)}건)")
                    st.dataframe(df[['BSSH_NM', 'PRDLST_NM', 'PRDLST_DCNM', 'PRMS_DT']], use_container_width=True)

                    st.markdown("---")
                    
                    # 시각화 대시보드
                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("🍦 플레이버(Flavor) 분류")
                        flavors = ['딸기', '초코', '바닐라', '포도', '사과', '오렌지', '레몬', '민트']
                        f_df = pd.DataFrame([{'맛': f, '건수': df['PRDLST_NM'].str.contains(f).sum()} for f in flavors])
                        f_df = f_df[f_df['건수'] > 0]
                        if not f_df.empty:
                            st.plotly_chart(px.pie(f_df, values='건수', names='맛', hole=0.4), use_container_width=True)
                        st.caption(f"📅 기간: {start_date} ~ {end_date}")

                    with c2:
                        st.subheader("📊 유형별 비중 (%)")
                        t_counts = df['PRDLST_DCNM'].value_counts().reset_index()
                        t_counts.columns = ['Type', 'Count']
                        st.plotly_chart(px.bar(t_counts, x='Type', y='Count', text=(t_counts['Count']/len(df)*100).round(1).astype(str)+'%'), use_container_width=True)
                        st.caption(f"📅 기간: {start_date} ~ {end_date}")
                else:
                    st.warning("🔎 조건에 맞는 데이터가 없습니다.")
            else:
                st.info("조회된 데이터가 없습니다.")
                
    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
