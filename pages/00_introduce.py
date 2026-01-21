import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="식품품목제조보고 최신화 현황", layout="wide")

st.title("🍎 식품품목제조보고 최신화 목록 (최근 3개월)")
st.sidebar.header("조회 조건 설정")

# 1. 사용자 입력 부분
api_key = "9171f7ffd72f4ffcb62f"
service_id = "I1250"

# 검색어 입력 (예: 주스, 향료, 소스 등)
target_category = st.sidebar.text_input("원하는 식품유형을 입력하세요", value="향료")
search_limit = st.sidebar.slider("조회 건수", 10, 500, 100)

# 날짜 계산
today = datetime.now()
three_months_ago = (today - timedelta(days=90)).strftime('%Y%m%d')

if st.sidebar.button("데이터 불러오기"):
    # API URL 구성
    # 사용자 입력값을 PRDLST_DCNM 인자에 포함하여 요청 가능
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={three_months_ago}/PRDLST_DCNM={target_category}"

    with st.spinner('식약처 데이터를 불러오는 중...'):
        try:
            response = requests.get(url)
            data = response.json()

            if service_id in data:
                rows = data[service_id].get("row", [])
                if rows:
                    df = pd.DataFrame(rows)

                    # 항목 한글화 매핑
                    column_mapping = {
                        'LCNS_NO': '인허가번호',
                        'BSSH_NM': '업소명',
                        'PRDLST_REPORT_NO': '품목제조번호',
                        'PRMS_DT': '허가일자',
                        'PRDLST_NM': '제품명',
                        'PRDLST_DCNM': '유형',
                        'END_YN': '생산종료',
                        'HI_VLT_NETRT_FOD_YN': '고열량저영양',
                        'POG_DAYCNT': '유통/소비기한',
                        'LAST_UPDT_DTM': '최종수정일',
                        'USE_METHOD': '용법'
                    }
                    
                    # 데이터 정리
                    available_cols = [col for col in column_mapping.keys() if col in df.columns]
                    display_df = df[available_cols].rename(columns=column_mapping)
                    
                    # 결과 요약
                    st.success(f"✅ '{target_category}' 관련 최신 데이터 {len(display_df)}건을 찾았습니다.")
                    
                    # 데이터 표 출력 (필터링, 정렬 가능한 인터랙티브 표)
                    st.dataframe(display_df, use_container_width=True)
                    
                    # 엑셀 다운로드 버튼
                    csv = display_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="결과를 CSV 파일로 저장",
                        data=csv,
                        file_name=f"food_list_{target_category}.csv",
                        mime='text/csv',
                    )
                else:
                    st.warning(f"⚠️ 해당 기간 내에 '{target_category}' 유형의 데이터가 없습니다.")
            else:
                st.error("API 응답 오류: 인증키가 아직 활성화되지 않았거나 서버 점검 중일 수 있습니다.")
        
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
else:
    st.info("왼쪽 사이드바에서 조건을 입력하고 [데이터 불러오기] 버튼을 눌러주세요.")
