import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="식품 데이터 통합 분석 시스템", layout="wide")
st.title("📊 식품 품목제조 및 원재료 분석 대시보드")

# 2. 사이드바 설정
st.sidebar.header("🔍 세부 검색 설정")

category_mode = st.sidebar.selectbox(
    "데이터 분류 선택",
    ["식품(완제품/원료) - I2790", "식품첨가물 - I1250", "식품원재료 - I0020"]
)

if "I2790" in category_mode:
    service_id = "I2790"
    type_options = ["음료류", "과자류", "빵류", "유가공품", "소스", "즉석섭취식품"]
elif "I1250" in category_mode:
    service_id = "I1250"
    type_options = ["혼합제제", "천연향료", "합성향료", "착색료", "유화제"]
else:
    service_id = "I0020"
    type_options = ["식물성", "동물성", "미생물", "기타"]

target_types = st.sidebar.multiselect("세부 유형 선택", options=type_options, default=[type_options[0]])

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
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={start_str}"

    try:
        with st.spinner("데이터 수집 중..."):
            response = requests.get(url)
            
            # 여기서 발생하던 들여쓰기 오류를 수정했습니다.
            if not response.text or response.text.startswith("<"):
                st.error(f"❌ '{service_id}' 서비스 응답 오류. 권한 승인 여부를 확인하세요.")
                st.stop()

            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                df = pd.DataFrame(rows)
                
                if not df.empty:
                    date_col = next((c for c in ['CHNG_DT', 'PRMS_DT', 'LAST_UPDT_DTM'] if c in df.columns), None)
                    if date_col:
                        df['temp_date'] = df[date_col].str.replace(r'[^0-9]', '', regex=True).str[:8]
                        df = df[(df['temp_date'] >= start_str) & (df['temp_date'] <= end_str)]
                    
                    if target_types:
                        df = df[df['PRDLST_DCNM'].str.contains('|'.join(target_types), na=False)]

                    if not df.empty:
                        st.subheader(f"📋 {category_mode} 조회 결과")
                        st.dataframe(df, use_container_width=True)

                        st.markdown("---")
                        c1, c2 = st.columns(2)

                        with c1:
                            st.subheader("🍦 플레이버 분류")
                            flavors = ['딸기', '초코', '바닐라', '포도', '사과', '오렌지', '레몬', '민트']
                            f_data = [{'맛': f, '건수': df['PRDLST_NM'].str.contains(f).sum()} for f in flavors]
                            f_df = pd.DataFrame([x for x in f_data if x['건수'] > 0])
                            if not f_df.empty:
                                st.plotly_chart(px.pie(f_df, values='건수', names='맛', hole=0.4), use_container_width=True)
                            st.caption(f"📅 {start_date} ~ {end_date}")

                        with c2:
                            st.subheader("📊 유형별 비중")
                            t_counts = df['PRDLST_DCNM'].value_counts().reset_index()
                            t_counts.columns = ['유형', '건수']
                            t_counts['비율(%)'] = (t_counts['건수'] / len(df) * 100).round(1)
                            st.plotly_chart(px.bar(t_counts, x='유형', y='건수', text='비율(%)'), use_container_width=True)
                            st.caption(f"📅 {start_date} ~ {end_date}")
                    else:
                        st.warning("🔎 조건에 맞는 데이터가 없습니다.")
                else:
                    st.info("데이터가 없습니다.")
            else:
                st.error("API 구조 오류.")
    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
