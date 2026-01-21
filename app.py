import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정 및 이름 변경
st.set_page_config(page_title="식품신제품검색", layout="wide")
st.title("🔍 식품신제품검색 (식품첨가물 I1250 분석)")

# 2. 사이드바 검색 옵션
st.sidebar.header("🔍 검색 및 필터 옵션")

# 제품명/키워드 통합 검색창
search_keyword = st.sidebar.text_input("제품명 또는 성분 검색 (예: 딸기, 포도, 제로)", "")

# 식품안전나라 기준 표준 식품유형 리스트
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

# 제외 설정
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

# 3. 데이터 조회 및 시각화 로직
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
                    
                    # 제외 설정 적용
                    if exclude_flavor:
                        df = df[~df['PRDLST_DCNM'].str.contains('향료', na=False)]
                    if exclude_raw:
                        df = df[~df['PRDLST_DCNM'].str.contains('원재료|원료', na=False)]
                    if exclude_mixed:
                        df = df[~df['PRDLST_DCNM'].str.contains('혼합제제', na=False)]
                    
                    # 제품명 키워드 검색
                    if search_keyword:
                        df = df[df['PRDLST_NM'].str.contains(search_keyword, na=False)]
                    
                    # 식품유형 필터링
                    if selected_food_types:
                        df = df[df['PRDLST_DCNM'].str.contains('|'.join(selected_food_types), na=False)]

                    if not df.empty:
                        # [오류 해결] f-string 중괄호 문법을 안전하게 수정
                        display_name = search_keyword if search_keyword else "전체"
                        st.subheader(f"📋 '{display_name}' 검색 결과 (총 {len(df)}건)")
                        
                        cols = [c for c in ['BSSH_NM', 'PRDLST_NM', 'PRDLST_DCNM', date_col] if c in df.columns]
                        st.dataframe(df[cols], use_container_width=True)

                        st.markdown("---")
                        
                        # 속성 분석 대시보드
                        l_chart, r_chart = st.columns(2)
                        with l_chart:
                            st.subheader(f"🎯 '{display_name}' 연관 속성 분석")
                            attr_keywords = ['무설탕', '제로', '유기농', '고단백', '비건', '천연', '가공', '농축']
                            fruits = ['딸기', '초코', '바닐라', '포도', '사과', '오렌지', '레몬', '민트', '복숭아', '블루베리']
                            
                            combined_keywords = list(set(attr_keywords + fruits))
                            attr_data = [{'속성': k, '건수': df['PRDLST_NM'].str.contains(k).sum()} for k in combined_keywords]
                            attr_df = pd.DataFrame([x for x in attr_data if x['건수'] > 0]).sort_values(by='건수', ascending=False)
                            
                            if not attr_df.empty:
                                fig1 = px.bar(attr_df, x='속성', y='건수', color='속성', text_auto=True)
                                st.plotly_chart(fig1, use_container_width=True)
                            else:
                                st.info("추출된 주요 속성이 없습니다.")
                        
                        with r_chart:
                            st.subheader("📊 식품유형별 분포")
                            type_counts = df['PRDLST_DCNM'].value_counts().reset_index()
                            type_counts.columns = ['유형', '건수']
                            fig2 = px.pie(type_counts, values='건수', names='유형', hole=0.4)
                            st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.warning("🔎 검색 조건 및 필터에 맞는 제품이 없습니다.")
                else:
                    st.info("데이터가 존재하지 않습니다.")
            else:
                st.error("⚠️ API 응답 형식이 올바르지 않습니다.")
    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
