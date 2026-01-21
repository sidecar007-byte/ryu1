import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="식품품목제조보고 최신화 내역", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stDataFrame { border: 3px solid #333333; border-radius: 5px; background-color: white; }
    h1 { color: #1E3A8A; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍎 식품품목제조보고 최신화 내역")

# 2. 사이드바 검색 조건
st.sidebar.header("🔍 검색 필터 설정")

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
with col2:
    end_date = st.date_input("종료일", datetime.now())

# 검색 키워드
target_type = st.sidebar.text_input("식품유형 입력 (예: 음료, 과자, 캔디)", value="")
search_limit = st.sidebar.slider("데이터 호출량", 100, 1000, 600)

# API 정보
api_key = "9171f7ffd72f4ffcb62f"
service_id = "I1250"
data_type = "json"

if st.sidebar.button("데이터 조회 시작"):
    # [명세서 반영] 추가 요청인자가 있을 경우 & 기호 사용
    # 형식: .../시작/종료/변수명1=값1&변수명2=값2
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    # 기본 URL (변경일자 기준)
    base_url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/{data_type}/1/{search_limit}"
    params = f"/CHNG_DT={start_str}"
    
    # 유형 검색어가 있는 경우 명세서 규칙(&)에 따라 추가
    if target_type:
        params += f"&PRDLST_DCNM={target_type}"

    full_url = base_url + params

    try:
        with st.spinner("식약처 서버에서 데이터를 불러오는 중..."):
            response = requests.get(full_url)
            
            # 응답이 비정상(HTML 등)일 경우 처리
            if response.text.startswith("<"):
                st.error("❌ 서버 응답 오류: 요청 주소 형식을 확인하세요.")
                st.code(full_url)
                st.stop()

            data = response.json()
            
            if service_id in data:
                rows = data[service_id].get("row", [])
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # 1. 종료일 기준 필터링 (서버는 시작일 이후만 주므로 종료일은 직접 거름)
                    date_col = next((c for c in ['CHNG_DT', 'PRMS_DT', 'LAST_UPDT_DTM'] if c in df.columns), None)
                    if date_col:
                        df['clean_date'] = df[date_col].str.replace(r'[^0-9]', '', regex=True).str[:8]
                        df = df[(df['clean_date'] >= start_str) & (df['clean_date'] <= end_str)]

                    # 2. 향료 등 불필요 항목 필터링 (사용자가 직접 입력한 경우가 아니면 제외)
                    if not target_type:
                        stop_words = ['향료', '첨가물', '혼합제제', '후레바']
                        df = df[~df['PRDLST_DCNM'].str.contains('|'.join(stop_words), na=False)]

                    if not df.empty:
                        # 한글 컬럼 매핑
                        cols_map = {
                            'LCNS_NO': '인허가번호', 'BSSH_NM': '업소명', 'PRDLST_REPORT_NO': '품목제조번호',
                            'PRMS_DT': '허가일자', 'PRDLST_NM': '제품명', 'PRDLST_DCNM': '유형',
                            'POG_DAYCNT': '유통/소비기한', 'USE_METHOD': '용법'
                        }
                        
                        rename_dict = {k: v for k, v in cols_map.items() if k in df.columns}
                        final_df = df[list(rename_dict.keys())].rename(columns=rename_dict)
                        
                        st.success(f"✅ {start_date} ~ {end_date} 기간 내 {len(final_df)}건 조회 완료")
                        st.dataframe(final_df, use_container_width=True)
                        
                        # 엑셀 다운로드
                        csv = final_df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📥 결과 CSV 저장", csv, f"food_list.csv", "text/csv")
                    else:
                        st.warning("🔎 조건에 맞는 데이터가 없습니다. 호출량을 늘리거나 기간을 조정해 보세요.")
                else:
                    st.info("해당 기간에 등록된 데이터가 없습니다.")
            else:
                st.error("⚠️ 데이터 구조를 찾을 수 없습니다. 서비스 ID를 확인하세요.")
                
    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
