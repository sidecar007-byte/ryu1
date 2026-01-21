import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote

# 1. 페이지 설정
st.set_page_config(page_title="식품안전 데이터 센터", layout="wide")

st.title("🍎 식품품목제조보고 최신화 목록 (ID: I1250)")
st.info("최근 3개월 내에 변경/보고된 데이터를 실시간으로 조회합니다.")

# 2. 고정 설정 (알파벳 I + 1250)
api_key = "9171f7ffd72f4ffcb62f"
service_id = "I1250" 

# 3. 사이드바 필터
st.sidebar.header("🔍 검색 필터")
target_type = st.sidebar.text_input("식품유형 (예: 주스, 향료, 소스)", value="")
search_limit = st.sidebar.slider("조회 건수", 10, 500, 100)

# 날짜 계산 (오늘 기준 3개월 전)
today = datetime.now()
three_months_ago = (today - timedelta(days=90)).strftime('%Y%m%d')

if st.sidebar.button("데이터 불러오기"):
    # URL 구성 (CHNG_DT 포함)
    base_url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={three_months_ago}"
    
    # 유형 검색어가 있는 경우 안전하게 인코딩하여 추가
    if target_type:
        base_url += f"/PRDLST_DCNM={quote(target_type)}"

    try:
        with st.spinner("식약처 서버에서 데이터를 가져오는 중..."):
            response = requests.get(base_url)
            
            # 응답이 HTML(스크립트)인지 확인하여 에러 방어
            if response.text.strip().startswith("<"):
                st.error("❌ 서버 응답 오류: 인증키가 아직 활성화되지 않았거나 ID가 올바르지 않습니다.")
                with st.expander("서버 응답 원문 확인"):
                    st.code(response.text)
                st.stop()

            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # 요청하신 상세 출력 항목 매핑
                    cols_map = {
                        'LCNS_NO': '인허가번호',
                        'BSSH_NM': '업소명',
                        'PRDLST_REPORT_NO': '품목제조번호',
                        'PRMS_DT': '허가일자',
                        'PRDLST_NM': '제품명',
                        'PRDLST_DCNM': '유형',
                        'END_YN': '생산종료여부',
                        'HI_VLT_NETRT_FOD_YN': '고열량저영양식품여부',
                        'CHLD_PRO_FOD_QUALT_CERT_YN': '어린이기호식품품질인증여부',
                        'POG_DAYCNT': '유통/소비기한',
                        'LAST_UPDT_DTM': '최종수정일자',
                        'INDUTY_NM': '업종',
                        'QLT_MAINT_TERM_DAYCNT': '품질유지기한일수',
                        'USE_METHOD': '용법',
                        'USAGE': '용도'
                    }
                    
                    # 데이터에 존재하는 컬럼만 선택 및 한글화
                    rename_dict = {k: v for k, v in cols_map.items() if k in df.columns}
                    final_df = df[list(rename_dict.keys())].rename(columns=rename_dict)
                    
                    # 결과 출력
                    st.success(f"✅ {three_months_ago} 이후 데이터 {len(final_df)}건을 조회했습니다.")
                    st.dataframe(final_df, use_container_width=True)
                    
                    # CSV 다운로드 버튼
                    csv = final_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 결과 엑셀(CSV) 저장", csv, f"food_report_{datetime.now().strftime('%y%m%d')}.csv", "text/csv")
                else:
                    st.warning(f"🔎 해당 기간 내에 '{target_type}' 관련 데이터가 없습니다.")
            else:
                st.error("⚠️ 데이터 구조를 찾을 수 없습니다. API 설정을 확인하세요.")
                st.json(data)

    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
else:
    st.info("왼쪽 사이드바에서 필터를 입력하고 [데이터 불러오기]를 클릭하세요.")
