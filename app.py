import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote

# 페이지 설정
st.set_page_config(page_title="식품품목제조보고 최신화 목록", layout="wide")

st.title("📂 식품품목제조보고 최신화 내역 (ID: 11250)")
st.info("관리자 지정 ID 11250을 기반으로 최근 3개월간의 데이터를 조회합니다.")

# 1. 고정 설정 및 입력
api_key = "9171f7ffd72f4ffcb62f"
service_id = "11250"  # 요청하신 대로 숫자로 고정

st.sidebar.header("🔍 검색 필터")
target_type = st.sidebar.text_input("조회할 식품유형 (예: 주스, 향료, 소스)", value="")
search_limit = st.sidebar.slider("한 번에 불러올 데이터 양", 10, 1000, 100)

# 2. 날짜 계산 (오늘부터 3개월 전)
today = datetime.now()
three_months_ago = (today - timedelta(days=90)).strftime('%Y%m%d')

if st.sidebar.button("데이터 동기화 및 조회"):
    # URL 구성 (CHNG_DT 포함)
    base_url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={three_months_ago}"
    
    # 식품유형 입력값이 있는 경우 URL에 추가
    if target_type:
        base_url += f"/PRDLST_DCNM={quote(target_type)}"

    try:
        with st.spinner("식약처 서버에서 최신 정보를 가져오는 중..."):
            response = requests.get(base_url)
            
            # HTML 응답(에러 메시지) 여부 체크
            if response.text.strip().startswith("<"):
                st.error("❌ 서버 응답 에러: 데이터 대신 시스템 메시지가 수신되었습니다.")
                if "인증키" in response.text:
                    st.warning("인증키 활성화 대기 중이거나 호출 한도가 초과되었을 수 있습니다.")
                st.stop()

            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # 출력 형식에 맞춘 컬럼명 변경 (이미지/명세서 기준)
                    cols_map = {
                        'LCNS_NO': '인허가번호',
                        'BSSH_NM': '업소명',
                        'PRDLST_REPORT_NO': '품목제조번호',
                        'PRMS_DT': '허가일자',
                        'PRDLST_NM': '제품명',
                        'PRDLST_DCNM': '유형',
                        'POG_DAYCNT': '유통/소비기한',
                        'LAST_UPDT_DTM': '최종수정일자',
                        'USE_METHOD': '용법'
                    }
                    
                    # 존재하는 컬럼만 필터링하여 출력
                    final_df = df.
