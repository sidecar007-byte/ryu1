import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote # 한글 검색어 안전 처리를 위해 필요

# 페이지 설정
st.set_page_config(page_title="식품안전 데이터 대시보드", layout="wide")

st.title("🍎 식품품목제조보고 최신화 목록 (ID: I1250)")
st.sidebar.header("🔍 필터 설정")

# 기본 설정
api_key = "9171f7ffd72f4ffcb62f"
service_id = "I1250"
today = datetime.now()
three_months_ago = (today - timedelta(days=90)).strftime('%Y%m%d')

# 사이드바 입력창
target_category = st.sidebar.text_input("조회할 식품유형 (예: 향료, 과자, 음료)", value="향료")
search_limit = st.sidebar.slider("최대 조회 건수", 10, 500, 100)

if st.sidebar.button("데이터 조회 시작"):
    # 한글 검색어 인코딩 처리
    safe_category = quote(target_category)
    
    # URL 구성 (CHNG_DT와 PRDLST_DCNM 결합)
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={three_months_ago}/PRDLST_DCNM={safe_category}"

    with st.spinner(f"'{target_category}' 데이터를 불러오는 중..."):
        try:
            response = requests.get(url)
            
            # 1. 응답 텍스트가 HTML(스크립트)인지 먼저 확인
            if "<script>" in response.text or "인증키가 유효하지 않습니다" in response.text:
                st.error("❌ 식약처 서버 에러: 인증키가 일시적으로 거부되었습니다.")
                st.info("💡 원인: 키 발급 후 1시간 미만 혹은 서버의 일시적인 과부하입니다. 잠시 후 다시 시도해 주세요.")
                st.stop() # 실행 중단

            # 2. JSON 파싱 시도
            try:
                data = response.json()
            except Exception:
                st.error("❌ 데이터 형식 오류: 서버가 비정상적인 응답을 보냈습니다.")
                st.code(response.text[:200]) # 받은 내용 일부 출력
                st.stop()

            # 3. 데이터 출력 로직
            if service_id in data:
                rows = data[service_id].get("row", [])
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # 요청하신 15개 항목 매핑 (데이터에 존재하는 것 위주)
                    column_mapping = {
                        'LCNS_NO': '인허가번호', 'BSSH_NM': '업소명', 'PRDLST_REPORT_NO': '품목제조번호',
                        'PRMS_DT': '허가일자', 'PRDLST_NM': '제품명', 'PRDLST_DCNM': '유형',
                        'END_YN': '생산종료', 'POG_DAYCNT': '유통/소비기한', 'LAST_UPDT_DTM': '최종수정일'
                    }
                    
                    final_df = df.rename(columns=column_mapping)
                    st.success(f"✅ 최근 3개월 내 '{target_category}' 관련 데이터 {len(final_df)}건 발견")
                    st.dataframe(final_df, use_container_width=True)
                else:
                    st.warning(f"⚠️ '{target_category}' 유형에 해당하는 최근 3개월 데이터가 없습니다.")
            else:
                st.error("⚠️ 서버 응답에 데이터가 포함되어 있지 않습니다.")

        except Exception as e:
            st.error(f"⚠️ 연결 오류: {e}")

else:
    st.info("사이드바에 검색어를 입력하고 버튼을 눌러주세요.")
