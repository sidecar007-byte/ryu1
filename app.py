import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="식품첨가물 품목분석", layout="wide")
st.title("🧪 식품첨가물(I1250) 분석 대시보드")

# 2. 사이드바 검색 조건 설정
st.sidebar.header("🔍 세부 검색 설정")

food_code_types = [
    "과자", "캔디류", "빵류", "음료류", "탄산음료", "유가공품", "아이스크림류", 
    "소스류", "절임류", "주류", "혼합제제", "천연향료", "합성향료", "착색료"
]

target_types = st.sidebar.multiselect(
    "식품공전 식품유형 선택", 
    options=food_code_types, 
    default=["혼합제제", "천연향료"]
)

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
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{limit}/CHNG_DT={start_str}"

    try:
        with st.spinner("데이터 수집 중..."):
            response = requests.get(url)
            if not response.text or response.text.startswith("<"):
                st.error("❌ API 응답 오류. 권한 또는 네트워크 상태를 확인하세요.")
                st.stop()

            data = response.json()
            if service_id in data:
                rows = data[service_id].get("row", [])
                df = pd.DataFrame(rows)
                
                if not df.empty:
                    # [오류 해결 핵심] 날짜 컬럼 유무 확인 및 자동 선택
                    # CHNG_DT가 없으면 PRMS_DT를 사용하고, 둘 다 없으면 필터링 스킵
                    date_col = None
                    for col in ['CHNG_DT', 'PRMS_DT']:
                        if col in df.columns:
                            date_col = col
                            break
                    
                    if date_col:
                        df['temp_date'] = df[date_col].str.replace(r'[^0-9]', '', regex=True).str[:8]
                        df = df[(df['temp_date'] >= start_str) & (df['temp_date'] <= end_date.strftime('%Y%m%d'))]
                    
                    # 식품유형 필터링
                    if target_types and 'PRDLST_DCNM' in df.columns:
                        df = df[df['PRDLST_DCNM'].str.contains('|'.join(target_types), na=False)]

                    if not df.empty:
                        st.subheader(f"📋 분석 결과 목록 (총 {len(df)}건)")
                        # 안전한 컬럼 출력을 위해 필터링
                        cols_to_show = [c for c in ['BSSH_NM', 'PRDLST_NM', 'PRDLST_DCNM', date_col] if c in df.columns]
                        st.dataframe(df[cols_to_show], use_container_width=True)

                        st.markdown("---")
                        
                        # 3. 대시보드 시각화
                        l_chart, r_chart = st.columns(2)

                        with l_chart:
                            st.subheader("🍦 주요 플레이버 키워드 분석")
                            flavors = ['딸기', '초코', '바닐라', '포도', '사과', '오렌지', '레몬', '민트']
                            if 'PRDLST_NM' in df.columns:
                                f_data = [{'맛': f, '건수': df['PRDLST_NM'].str.contains(f).sum()} for f in flavors]
                                f_df = pd.DataFrame([x for x in f_data if x['건수'] > 0])
                                if not f_df.empty:
                                    st.plotly_chart(px.pie(f_df, values='건수', names='맛', hole=0.4), use_container_width=True)
                                else:
                                    st.info("플레이버 키워드가 없습니다.")
                            st.caption(f"📅 분석 범위: {start_date} ~ {end_date}")

                        with r_chart:
                            st.subheader("📊 선택 유형별 점유율 (%)")
                            if 'PRDLST_DCNM' in df.columns:
                                type_counts = df['PRDLST_DCNM'].value_counts().reset_index()
                                type_counts.columns = ['Type', 'Count']
                                type_counts['Ratio(%)'] = (type_counts['Count'] / len(df) * 100).round(1)
                                
                                fig2 = px.bar(type_counts, x='Type', y='Count', text='Ratio(%)',
                                             color='Count', color_continuous_scale='Reds')
                                fig2.update_traces(texttemplate='%{text}%', textposition='outside')
                                st.plotly_chart(fig2, use_container_width=True)
                            st.caption(f"📅 분석 범위: {start_date} ~ {end_date}")
                    else:
                        st.warning("🔎 선택하신 유형에 맞는 데이터가 없습니다.")
                else:
                    st.info("데이터가 존재하지 않습니다.")
            else:
                st.error("⚠️ API 응답 형식이 올바르지 않습니다.")
    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
