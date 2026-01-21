import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote

# 1. 페이지 설정 및 제목 (괄호 삭제)
st.set_page_config(page_title="식품품목제조보고 최신화 내역", layout="wide")
st.title("🍎 식품품목제조보고 최신화 내역")

# 2. 사이드바 검색 조건 설정
st.sidebar.header("🔍 검색 조건 설정")

# 기간 설정 (기본값: 최근 3개월)
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
with col2:
    end_date = st.date_input("종료일", datetime.now())

start_date_str = start_date.strftime('%Y%m%d')
end_date_str = end_date.strftime('%Y%m%d')

# 유형 설정
target_type = st.sidebar.text_input("조회할 식품유형 (예: 음료, 과자, 주스)", value="")

# 첨가물 제외 옵션 및 호출량
exclude_additive = st.sidebar.checkbox("향료 및 첨가물 제외", value=True)
search_limit = st.sidebar.slider("데이터 호출량", 100, 1000, 500)

# API 기본 정보
api_key = "9171f7ffd72f4ffcb62f"
service_id = "I1250"

if st.sidebar.button("데이터 조회 시작"):
    # 기간별 조회를 위해 변경일자(CHNG_DT) 기준 URL 구성
    # 시작일부터 종료일까지 범위를 지정하여 호출 (식약처 API 특성상 시작일 기준 호출 후 파이썬 필터링)
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/{search_limit}/CHNG_DT={start_date_str}"

    try:
        with st.spinner("데이터를 분석 중입니다..."):
            response = requests.get(url)
            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # [필터 1] 설정한 종료일까지만 데이터 남기기
                    df = df[df['CHNG_DT'] <= end_date_str]

                    # [필터 2] 향료 및 첨가물 제외
                    if exclude_additive:
                        stop_words = ['향료', '첨가물', '혼합제제', '후레바', '에센스', '천연향료', '합성향료']
                        df = df[~df['PRDLST_DCNM'].str.contains('|'.join(stop_words), na=False)]
                        df = df[~df['PRDLST_NM'].str.contains('|'.join(stop_words), na=False)]

                    # [필터 3] 사용자 지정 유형 필터링
                    if target_type:
                        df = df[df['PRDLST_DCNM'].str.contains(target_type, na=False) | 
                                df['PRDLST_NM'].str.contains(target_type, na=False)]

                    if not df.empty:
                        # 출력 항목 매핑
                        cols_map = {
                            'LCNS_NO': '인허가번호', 'BSSH_NM': '업소명', 'PRDLST_REPORT_NO': '품목제조번호',
                            'PRMS_DT': '허가일자', 'PRDLST_NM': '제품명', 'PRDLST_DCNM': '유형',
                            'END_YN': '생산종료', 'POG_DAYCNT': '유통/소비기한', 'LAST_UPDT_DTM': '최종수정일자',
                            'USE_METHOD': '용법', 'USAGE': '용도'
                        }
                        
                        rename_dict = {k: v for k, v in cols_map.items() if k in df.columns}
                        final_df = df[list(rename_dict.keys())].rename(columns=rename_dict)
                        
                        st.success(f"✅ {start_date} ~ {end_date} 기간 동안 '{target_type}' 관련 {len(final_df)}건의 데이터를 조회했습니다.")
                        
                        # 3. 표 설정 (색대비 강화 및 진하게 설정)
                        st.markdown("""
                            <style>
                            .stDataFrame {
                                border: 2px solid #4B4B4B;
                                border-radius: 5px;
                            }
                            </style>
                        """, unsafe_allow_html=True)
                        
                        # 표 출력
                        st.dataframe(final_df.style.set_properties(**{
                            'background-color': 'white',
                            'color': 'black',
                            'border-color': '#D3D3D3'
                        }), use_container_width=True)
                        
                        # CSV 다운로드
                        csv = final_df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📥 결과 CSV 저장", csv, f"food_report_{start_date_str}_{end_date_str}.csv", "text/csv")
                    else:
                        st.warning("🔎 설정한 조건(기간/유형/첨가물 제외)에 맞는 데이터가 없습니다.")
                else:
                    st.info("해당 기간에 보고된 데이터가 없습니다.")
            else:
                st.error("API 호출 실패. 인증키나 서비스 권한을 확인하세요.")

    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
else:
    st.info("왼쪽 사이드바에서 기간과 유형을 설정한 후 [데이터 조회 시작] 버튼을 눌러주세요.")
