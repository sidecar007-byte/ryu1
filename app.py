import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote

st.set_page_config(page_title="완제품 품목제조보고 조회", layout="wide")
st.title("🍹 완제품 식품품목제조보고 최신화 내역")

st.sidebar.header("🔍 검색 조건 설정")

# 1. 서비스 ID 설정 (완제품용 I2790으로 변경 시도)
api_key = "9171f7ffd72f4ffcb62f"
service_id = "I2790"  # 완제품(음료, 과자 등) 전용 ID

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
with col2:
    end_date = st.date_input("종료일", datetime.now())

start_date_str = start_date.strftime('%Y%m%d')
end_date_str = end_date.strftime('%Y%m%d')

# 기본 검색어를 '음료'로 설정
target_type = st.sidebar.text_input("조회할 식품유형", value="음료")
search_limit = st.sidebar.slider("데이터 호출량", 100, 1000, 500)

if st.sidebar.button("실시간 데이터 조회"):
    # I2790 서비스 호출 주소
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={start_date_str}"

    try:
        with st.spinner("완제품 데이터를 불러오는 중..."):
            response = requests.get(url)
            
            # 권한이 없는 ID일 경우 에러 처리
            if "인증키가 유효하지 않습니다" in response.text or response.status_code != 200:
                st.error(f"❌ '{service_id}' 서비스에 대한 접근 권한이 없습니다.")
                st.info("💡 관리자에게 'I2790' 서비스 권한 승인을 요청하시거나, 현재 승인된 ID가 무엇인지 확인해 보세요.")
                st.stop()

            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # 날짜 필터링
                    date_col = next((c for c in ['CHNG_DT', 'PRMS_DT', 'LAST_UPDT_DTM'] if c in df.columns), None)
                    if date_col:
                        df['temp_date'] = df[date_col].str.replace(r'[^0-9]', '', regex=True).str[:8]
                        df = df[(df['temp_date'] >= start_date_str) & (df['temp_date'] <= end_date_str)]
                    
                    # 검색어 필터링 (음료, 과자 등)
                    if target_type:
                        df = df[df['PRDLST_DCNM'].str.contains(target_type, na=False) | 
                                df['PRDLST_NM'].str.contains(target_type, na=False)]

                    if not df.empty:
                        cols_map = {
                            'BSSH_NM': '업소명', 'PRDLST_NM': '제품명', 'PRDLST_DCNM': '유형',
                            'PRMS_DT': '허가일자', 'POG_DAYCNT': '유통기한'
                        }
                        rename_dict = {k: v for k, v in cols_map.items() if k in df.columns}
                        final_df = df[list(rename_dict.keys())].rename(columns=rename_dict)
                        
                        st.success(f"✅ 최근 3개월 내 '{target_type}' 데이터 {len(final_df)}건을 발견했습니다.")
                        st.markdown("""<style> .stDataFrame { border: 3px solid #333333; } </style>""", unsafe_allow_html=True)
                        st.dataframe(final_df, use_container_width=True)
                    else:
                        st.warning(f"🔎 '{target_type}' 키워드가 포함된 완제품이 없습니다.")
                else:
                    st.info("해당 기간에 등록된 데이터가 없습니다.")
    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
