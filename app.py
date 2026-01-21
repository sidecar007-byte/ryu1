import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote

# 1. 페이지 기본 설정
st.set_page_config(page_title="식품품목제조보고 조회 시스템", layout="wide")

st.title("📂 식품품목제조보고 최신화 목록 (ID: 11250)")
st.caption("관리자 지정 ID 11250 기반 | 최근 3개월 데이터 실시간 조회")

# 2. 사이드바 설정
api_key = "9171f7ffd72f4ffcb62f"
service_id = "11250"  # 고정된 서비스 ID

st.sidebar.header("🔍 검색 필터")
target_type = st.sidebar.text_input("식품유형 입력 (예: 주스, 소스, 과자)", value="")
search_limit = st.sidebar.slider("최대 호출 건수", 10, 1000, 100)

# 3. 날짜 계산 (오늘 기준 3개월 전)
today = datetime.now()
three_months_ago = (today - timedelta(days=90)).strftime('%Y%m%d')

# 4. 조회 버튼 클릭 시 로직 시작
if st.sidebar.button("데이터 불러오기"):
    # URL 구성 (CHNG_DT 포함)
    base_url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={three_months_ago}"
    
    # 검색어가 있을 경우 인코딩하여 추가
    if target_type:
        base_url += f"/PRDLST_DCNM={quote(target_type)}"

    try:
        with st.spinner("식약처 데이터를 동기화 중입니다..."):
            response = requests.get(base_url)
            
            # 응답이 HTML(에러 메시지)인 경우 처리
            if response.text.strip().startswith("<"):
                st.error("❌ 서버 응답 에러: 데이터 대신 시스템 메시지가 수신되었습니다.")
                st.info("💡 해결 방법: 인증키가 아직 활성화되지 않았거나 서버 통신 오류일 수 있습니다. 잠시 후 다시 시도해 주세요.")
                st.stop()

            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # 요청하신 상세 항목 매핑
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
                    
                    # 컬럼 이름 변경 (데이터에 존재하는 항목만)
                    rename_dict = {k: v for k, v in cols_map.items() if k in df.columns}
                    final_df = df.rename(columns=rename_dict)
                    
                    # 결과 요약 및 표 출력
                    st.success(f"✅ {three_months_ago} 이후 등록된 데이터 {len(final_df)}건을 조회했습니다.")
                    st.dataframe(final_df, use_container_width=True)
                    
                    # CSV 다운로드 버튼
                    csv = final_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 결과 CSV 다운로드",
                        data=csv,
                        file_name=f"report_11250_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime='text/csv'
                    )
                else:
                    st.warning(f"🔎 해당 기간 내에 '{target_type}' 관련 데이터가 없습니다.")
            else:
                st.error(f"⚠️ API 호출 실패: 서비스 ID {service_id}를 확인하세요.")
                
    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")

else:
    st.info("왼쪽 사이드바에서 필터를 입력하고 [데이터 불러오기] 버튼을 눌러주세요.")
