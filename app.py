import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="식품품목제조보고 최신화 내역", layout="wide")
st.title("🍎 식품품목제조보고 최신화 내역")

# 2. 사이드바 검색 조건 설정
st.sidebar.header("🔍 검색 조건 설정")

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
with col2:
    end_date = st.date_input("종료일", datetime.now())

# API 전송용 날짜 문자열
start_date_str = start_date.strftime('%Y%m%d')
end_date_str = end_date.strftime('%Y%m%d')

target_type = st.sidebar.text_input("조회할 식품유형 (예: 음료, 과자)", value="")
exclude_additive = st.sidebar.checkbox("향료 및 첨가물 제외", value=True)
search_limit = st.sidebar.slider("데이터 호출량", 100, 1000, 500)

api_key = "9171f7ffd72f4ffcb62f"
service_id = "I1250"

if st.sidebar.button("데이터 조회 시작"):
    # CHNG_DT 대신 시작일 기준으로 API 호출 (기본 검색 인자)
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={start_date_str}"

    try:
        with st.spinner("데이터를 분석 중입니다..."):
            response = requests.get(url)
            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # [오류 해결] 날짜 필드 자동 매칭 (CHNG_DT가 없을 경우 PRMS_DT나 LAST_UPDT_DTM 사용)
                    date_col = None
                    for col in ['CHNG_DT', 'PRMS_DT', 'LAST_UPDT_DTM']:
                        if col in df.columns:
                            date_col = col
                            break
                    
                    if date_col:
                        # 날짜 형식 통일 (8자리 숫자만 남기기)
                        df['temp_date'] = df[date_col].str.replace(r'[^0-9]', '', regex=True).str[:8]
                        # 기간 필터링
                        df = df[(df['temp_date'] >= start_date_str) & (df['temp_date'] <= end_date_str)]
                    
                    # [필터] 향료 및 첨가물 제외
                    if exclude_additive:
                        stop_words = ['향료', '첨가물', '혼합제제', '후레바', '에센스', '천연향료', '합성향료']
                        df = df[~df['PRDLST_DCNM'].str.contains('|'.join(stop_words), na=False, case=False)]
                        df = df[~df['PRDLST_NM'].str.contains('|'.join(stop_words), na=False, case=False)]

                    # [필터] 사용자 지정 유형
                    if target_type:
                        df = df[df['PRDLST_DCNM'].str.contains(target_type, na=False) | 
                                df['PRDLST_NM'].str.contains(target_type, na=False)]

                    if not df.empty:
                        # 출력 항목 설정
                        cols_map = {
                            'LCNS_NO': '인허가번호', 'BSSH_NM': '업소명', 'PRDLST_REPORT_NO': '품목제조번호',
                            'PRMS_DT': '허가일자', 'PRDLST_NM': '제품명', 'PRDLST_DCNM': '유형',
                            'END_YN': '생산종료', 'POG_DAYCNT': '유통/소비기한', 'USE_METHOD': '용법'
                        }
                        
                        rename_dict = {k: v for k, v in cols_map.items() if k in df.columns}
                        final_
