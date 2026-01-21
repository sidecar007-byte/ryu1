import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정 및 이름 변경
st.set_page_config(page_title="식품신제품검색", layout="wide")
st.title("🔍 식품신제품검색 (식품첨가물 I1250 분석)")

# 2. 사이드바 검색 조건 설정
st.sidebar.header("🔍 검색 옵션")

# [기능 1] 식품안전나라/식품공전 기준 표준 식품유형 리스트
food_types = [
    "과자", "캔디류", "추잉껌", "빵류", "떡류", "초콜릿류", "잼류", "음료류", 
    "과채주스", "탄산음료", "유가공품", "아이스크림류", "식육가공품", "어육가공품", 
    "면류", "소스류", "절임류", "조림류", "주류", "건강기능식품", "기타가공품"
]

selected_food_types = st.sidebar.multiselect(
    "식품유형 선택", 
    options=food_types, 
    default=["음료류", "과자"]
)

# [기능 2] 특정 항목 제외 버튼 (향료, 원재료, 혼합제제)
st.sidebar.subheader("🚫 제외 설정")
exclude_flavor = st.sidebar.checkbox("향료 제외 (천연/합성향료)", value=True)
exclude_raw = st.sidebar.checkbox("원재료 제외", value=True)
exclude_mixed = st.sidebar.checkbox("혼합제제 제외", value=False)

# 기간 및 호출량 설정
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=30))
with col2:
    end_date = st.date_input("종료일", datetime.now())

limit = st.sidebar.slider("데이터 호출량", 200, 1000, 500)
api_key = "9171f7ffd72f4ffcb62f"
service_id = "I1250"

if st.sidebar.button("신제품 검색 시작"):
    start_str = start_date.strftime('%Y%m%d')
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{limit}/CHNG_DT={start_str}"

    try:
        with st.spinner("데이터 분석 중..."):
            response = requests.get(url)
            if not response.text or response.text.startswith("<"):
                st.error("❌ API 응답 오류. 권한 또는 네트워크 상태를 확인하세요.")
                st.stop()

            data = response.json()
            if service_id in data:
                rows = data[service_id].get("row", [])
                df = pd.DataFrame(rows)
                
                if not df.empty:
                    # 날짜 필터링
                    date_col = next((c for c in ['CHNG_DT', 'PRMS_DT'] if c in df.columns), None)
                    if date_col:
                        df['temp_date'] = df[date_col].str.replace(r'[^0-9]', '', regex=True).str[:8]
                        df = df[(df['temp_date'] >= start_str) & (df['temp_date'] <= end_date.strftime('%Y%m%d'))]
                    
                    # [기능 3] 제외 로직 적용
                    if exclude_flavor:
                        df = df[~df['PRDLST_DCNM'].str.contains('향료', na=False)]
                    if exclude_raw:
                        df = df[~df['PRDLST_DCNM'].str.contains('원재료|원료', na=False)]
                    if exclude_mixed:
                        df = df[~df['PRDLST_DCNM'].str.contains('혼합제제', na=False)]
                    
                    # 식품유형 필터링
                    if selected_food_types:
                        df = df[df['PRDLST_DCNM'].str.contains('|'.join(selected_food_types), na=False)]

                    if not df.empty:
                        st.subheader(f"📋 신제품 검색 결과 (총 {len(df)}건)")
                        cols = [c for c in ['BSSH_NM', 'PRDLST_NM', 'PRDLST_DCNM', date_col] if c in df.columns]
                        st.dataframe(df[cols], use_container_width=True)

                        st.markdown("---")
                        
                        # 4. 대시보드 시각화
                        l_chart, r_chart = st.columns(2)
                        with l_chart:
                            st.subheader("🍦 맛(Flavor) 트렌드 분석")
                            flavors = ['딸기', '초코', '바닐라', '포도', '사과', '오렌지', '레몬', '민트', '피치', '커피']
                            f_data = [{'맛': f, '건수': df['PRDLST_NM'].str.contains(f).sum()} for f in flavors]
                            f_df = pd.DataFrame([x for x in f_data if x['건수'] > 0])
                            if not f_df.empty:
                                st.plotly_chart(px.pie(f_df, values='건수', names='맛', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
                        
                        with r_chart:
                            st.subheader("📊 식품유형별 신제품 비중")
                            type_counts = df['PRDLST_DCNM'].value_counts().reset_index()
                            type_counts.columns = ['유형', '건수']
                            st.plotly_chart(px.bar(type_counts, x='유형', y='건수', text=(type_counts['건수']/len(df)*100).round(1).astype(str)+'%', color='건수', color_continuous_scale='Viridis'), use_container_width=True)
                    else:
                        st.warning("🔎 제외 설정 및 필터 조건에 맞는 데이터가 없습니다.")
                else:
                    st.info("데이터가 존재하지 않습니다.")
    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
