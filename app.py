import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote

st.set_page_config(page_title="식품안전 데이터 진단 도구", layout="wide")

st.title("📂 식품품목제조보고 최신화 (ID: 11250)")

# 설정값
api_key = "9171f7ffd72f4ffcb62f"
service_id = "11250"
today = datetime.now()
three_months_ago = (today - timedelta(days=90)).strftime('%Y%m%d')

# 사이드바
st.sidebar.header("조회 필터")
target_type = st.sidebar.text_input("식품유형 (예: 주스, 향료)", value="")

if st.sidebar.button("데이터 동기화 및 진단"):
    # URL 생성
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/json/1/100/CHNG_DT={three_months_ago}"
    if target_type:
        url += f"/PRDLST_DCNM={quote(target_type)}"
    
    try:
        response = requests.get(url)
        
        # 1. 원시 응답 확인 (HTML인지 JSON인지 판별)
        content = response.text.strip()
        
        if content.startswith("<script") or "alert" in content:
            st.error("❌ 식약처 서버에서 접근을 거부했습니다.")
            st.warning("⚠️ 원인: 인증키가 '11250' 서비스에 대해 아직 승인되지 않았거나 활성화 대기 중입니다.")
            with st.expander("서버에서 보내온 실제 메시지 확인"):
                st.code(content)
            st.stop()
            
        # 2. JSON 파싱
        data = response.json()
        
        if service_id in data:
            rows = data[service_id].get("row", [])
            if rows:
                df = pd.DataFrame(rows)
                st.success(f"✅ 데이터 호출 성공! (총 {len(df)}건)")
                st.dataframe(df, use_container_width=True)
            else:
                st.info(f"🔎 {three_months_ago} 이후 해당 조건의 데이터가 없습니다.")
        else:
            # 서비스 ID 자체가 틀렸을 경우 나오는 결과 출력
            st.error(f"⚠️ 서비스 ID({service_id}) 호출 실패")
            st.json(data)

    except Exception as e:
        st.error(f"🔌 시스템 오류: {e}")
