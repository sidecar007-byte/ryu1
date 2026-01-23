import streamlit as st
import pandas as pd
import os
import glob
import requests
from datetime import datetime, date

# 1. 페이지 설정
st.set_page_config(page_title="연도별 음료 분석 대시보드", layout="wide")

# --- [데이터 수집] ---
def run_collector(api_key):
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/I1250/json/1/500"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        if 'I1250' not in data: return False
        rows = data['I1250']['row']
        api_df = pd.DataFrame(rows)
        api_df = api_df.loc[:, ~api_df.columns.duplicated()].copy()
        mapping = {
            'BSSH_NM': 'brand_owner', 'PRMS_DT': '출시년도', 
            'PRDLST_NM': 'brand_name', 'PRDLST_DCLS_NM': '음료유형', 
            'RAWMATERIAL_NM': '원재료표시', 'LAST_UPDT_DT': '최종수정일자'
        }
        api_df = api_df.rename(columns=mapping)
        api_df['최종수정일자'] = pd.to_datetime(api_df['최종수정일자'], errors='coerce').dt.strftime('%Y-%m-%d')
        api_df['출시년도'] = api_df['출시년도'].astype(str).str[:4]
        if not os.path.exists('data'): os.makedirs('data')
        api_df.to_csv("data/beverage_api_data.csv", index=False, encoding='utf-8-sig')
        return True
    except: return False

# --- [데이터 로드] ---
@st.cache_data
def load_all_data():
    files = glob.glob(os.path.join("data", "*.csv")) + glob.glob("*.csv")
    if not files: return None
    std_cols = ['음료유형', 'brand_owner', 'brand_name', '원재료표시', '출시년도', '최종수정일자']
    df_list = []
    for f in set(files):
        try:
            try: tmp = pd.read_csv(f, encoding='utf-8-sig')
            except: tmp = pd.read_csv(f, encoding='cp949')
            tmp = tmp.loc[:, ~tmp.columns.duplicated()].copy()
            tmp = tmp.rename(columns={'품목유형명': '음료유형', '업소명': 'brand_owner', '제품명': 'brand_name'})
            for col in std_cols:
                if col not in tmp.columns: tmp[col] = "미표기"
            df_list.append(tmp[std_cols].reset_index(drop=True))
        except: continue
    full_df = pd.concat(df_list, axis=0, ignore_index=True)
    full_df['출시년도'] = pd.to_numeric(full_df['출시년도'], errors='coerce').fillna(2024).astype(int)
    full_df['수정일_dt'] = pd.to_datetime(full_df['최종수정일자'], errors='coerce').dt.date
    
    # 감미료 추출 로직
    sweets = ['수크랄로스', '아스파탐', '아세설팜칼륨', '스테비아', '에리스리톨', '알룰로스', '설탕']
    full_df['주요당_감미료'] = full_df['원재료표시'].apply(lambda x: ", ".join([s for s in sweets if s in str(x)]) or "미표기")
    return full_df

df = load_all_data()

# --- [사이드바 필터: 연도 검색 핵심] ---
with st.sidebar:
    st.title("🔎 제품 연도 검색")
    if st.button("🔄 최신 데이터 수집"):
        if run_collector("9171f7ffd72f4ffcb62f"):
            st.cache_data.clear()
            st.rerun()

    if df is not None:
        st.divider()
        # [요청사항 반영] 연도 검색 슬라이더
        min_y, max_y = int(df['출시년도'].min()), int(df['출시년도'].max())
        search_year = st.slider("📅 출시년도 범위 검색", min_y, max_y, (2020, 2024))
        
        # [식약처 수정일자 필터]
        valid_dates = df['수정일_dt'].dropna().unique()
        if len(valid_dates) > 0:
            date_range = st.slider("🗓️ 식약처 수정일자 범위", min(valid_dates), max(valid_dates), (min(valid_dates), max(valid_dates)))
        else:
            date_range = (date.today(), date.today())

# --- [메인 화면: 검색된 제품만 출력] ---
if df is not None:
    # 1. 연도 기반 필터링 (메인 데이터)
    filtered_df = df[(df['출시년도'] >= search_year[0]) & (df['출시년도'] <= search_year[1])]
    
    # 2. 식약처 수정일자 기반 필터링
    api_filtered_df = df[(df['수정일_dt'] >= date_range[0]) & (df['수정일_dt'] <= date_range[1])]

    tab1, tab2 = st.tabs(["📊 연도별 출시제품 분석", "🔍 식약처 날짜별 상세조회"])

    with tab1:
        st.header(f"🥤 {search_year[0]}년 ~ {search_year[1]}년 출시 제품")
        
        if not filtered_df.empty:
            m1, m2 = st.columns(2)
            with m1:
                st.subheader("🏢 브랜드별 출시 순위")
                st.bar_chart(filtered_df['brand_owner'].value_counts().head(10))
            with m2:
                st.subheader("🍋 제품별 플레이버 분포")
                flavor_list = ['APPLE', 'PEACH', 'LEMON', 'GRAPE', 'STRAWBERRY']
                filtered_df['Flavor'] = filtered_df['brand_name'].apply(lambda x: next((f for f in flavor_list if f in str(x).upper()), "기타"))
                st.bar_chart(filtered_df['Flavor'].value_counts())
            
            st.subheader(f"📋 {search_year[0]}~{search_year[1]} 출시 제품 리스트")
            st.dataframe(
                filtered_df.sort_values('출시년도', ascending=False)[['출시년도', 'brand_owner', 'brand_name', '음료유형', '주요당_감미료']], 
                use_container_width=True, hide_index=True
            )
        else:
            st.warning("선택한 연도에 출시된 제품이 없습니다.")

    with tab2:
        st.header("📅 식약처 업데이트 현황")
        st.write(f"조회 범위: {date_range[0]} ~ {date_range[1]}")
        st.dataframe(
            api_filtered_df.sort_values('최종수정일자', ascending=False)[['최종수정일자', 'brand_owner', 'brand_name', '음료유형']], 
            use_container_width=True, hide_index=True
        )
else:
    st.info("데이터가 없습니다. 업데이트 버튼을 눌러주세요.")
