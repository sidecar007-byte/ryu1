import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote

# 1. 페이지 설정
st.set_page_config(page_title="완제품 중심 식품조회 시스템", layout="wide")

st.title("🍎 식품품목제조보고 최신화 (완제품 필터링 모드)")
st.info("첨가물(향료 등)을 제외하고 음료류, 과자류 등 완제품 위주로 조회합니다.")

# 2. 고정 설정
api_key = "9171f7ffd72f4ffcb62f"
service_id = "I1250" 

# 3. 사이드바 필터
st.sidebar.header("🔍 검색 설정")
target_type = st.sidebar.text_input("보고 싶은 유형 (예: 음료, 과자, 주스)", value="음료")
# 첨가물 제외 여부 선택
exclude_additive = st.sidebar.checkbox("향료/첨가물 제외하기", value=True)
search_limit = st.sidebar.slider("데이터 호출량 (많이 불러올수록 정확함)", 100, 1000, 500)

# 날짜 계산 (오늘 기준 3개월 전)
today = datetime.now()
three_months_ago = (today - timedelta(days=90)).strftime('%Y%m%d')

if st.sidebar.button("데이터 필터링 조회"):
    # URL 구성 (최대한 많이 불러와서 파이썬으로 정밀 필터링합니다)
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={three_months_ago}"

    try:
        with st.spinner("데이터를 분석하고 필터링하는 중..."):
            response = requests.get(url)
            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # [단계 1] 향료 및 첨가물 강제 제외 로직
                    if exclude_additive:
                        # 유형(PRDLST_DCNM)이나 제품명(PRDLST_NM)에 '향료', '첨가물', '혼합제제'가 들어간 행 삭제
                        stop_words = ['향료', '첨가물', '혼합제제', '후레바', '에센스']
                        df = df[~df['PRDLST_DCNM'].str.contains('|'.join(stop_words), na=False)]
                        df = df[~df['PRDLST_NM'].str.contains('|'.join(stop_words), na=False)]

                    # [단계 2] 사용자가 입력한 키워드 필터링 (음료, 과자 등)
                    if target_type:
                        # 제품명이나 유형에 해당 키워드가 있는 것만 남김
                        df = df[df['PRDLST_DCNM'].str.contains(target_type, na=False) | 
                                df['PRDLST_NM'].str.contains(target_type, na=False)]

                    # [단계 3] 결과 정리 및 출력
                    if not df.empty:
                        cols_map = {
                            'LCNS_NO': '인허가번호', 'BSSH_NM': '업소명', 'PRMS_DT': '허가일자',
                            'PRDLST_NM': '제품명', 'PRDLST_DCNM': '유형', 'POG_DAYCNT': '유통기한'
                        }
                        display_df = df.rename(columns={k: v for k, v in cols_map.items() if k in df.columns})
                        
                        st.success(f"✅ '{target_type}' 관련 완제품 {len(display_df)}건을 찾았습니다.")
                        st.dataframe(display_df, use_container_width=True)
                        
                        csv = display_df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📥 결과 저장", csv, f"filtered_report.csv", "text/csv")
                    else:
                        st.warning(f"🔎 검색 조건(유형: {target_type})에 맞는 완제품 데이터가 없습니다. 호출량을 늘려보세요.")
                else:
                    st.info("해당 기간 내에 보고된 데이터가 없습니다.")
            else:
                st.error("API 호출에 실패했습니다. 인증키나 ID를 확인하세요.")

    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
