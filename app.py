import streamlit as st
import pandas as pd
import os
import glob
import requests
from datetime import datetime, date

# 1. 페이지 설정
st.set_page_config(page_title="음료 통합 분석 대시보드", layout="wide")

# --- [기능 1] 식약처 API 수집 (안전 장치 강화) ---
def run_collector(api_key):
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/I1250/json/1/500"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        if 'I1250' not in data: return False
        
        rows = data['I1250']['row']
        api_df = pd.DataFrame(rows)
        
        # 중복 컬럼 즉시 제거
        api_df = api_df.loc[:, ~api_df.columns.duplicated()].copy()
        
        # 기존 코드 규격(std_cols)에 맞게 매핑
        mapping = {
            'BSSH_NM': 'brand_owner', 
            'PRMS_DT': '출시년도', 
            'PRDLST_NM': 'brand_name', 
            'PRDLST_DCLS_NM': '음료유형', 
            'RAWMATERIAL_NM': '원재료표시',
            'LAST_UPDT_DT': '최종수정일자'
        }
        api_df = api_df.rename(columns=mapping)
        
        # 출시년도 추출 (앞 4자리)
        api_df['출시년도'] = api_df['출시년도'].astype(str).str[:4]
        
        if not os.path.exists('data'): os.makedirs('data')
        api_df.to_csv("data/beverage_api_data.csv", index=False, encoding='utf-8-sig')
        return True
    except:
        return False

# --- [기능 2] 데이터 로드 (에러 원천 차단 버전) ---
@st.cache_data
def load_all_data():
    possible_paths = [os.path.join("data", "*.csv"), "*.csv"]
    files = []
    for path in possible_paths:
        files.extend(glob.glob(path))
    
    if not files: return None
    
    # 분석에 필요한 표준 컬럼 (기존 코드 유지)
    std_cols = ['음료유형', 'brand_owner', 'brand_name', 'branded_food_category', '원재료표시', '주요당_감미료', '출시년도']
    df_list = []

    for f in set(files):
        try:
            try: tmp = pd.read_csv(f, encoding='utf-8-sig')
            except: tmp = pd.read_csv(f, encoding='cp949')
            
            if tmp.empty: continue

            # 1. 중복 컬럼명 제거 (InvalidIndexError 해결)
            tmp = tmp.loc[:, ~tmp.columns.duplicated()].copy()
            
            # 2. 식약처 데이터와 기존 데이터 컬럼 혼합 대응
            tmp = tmp.rename(columns={'품목유형명': '음료유형'})
            
            # 3. 없는 컬럼 생성
            for col in std_cols:
                if col not in tmp.columns: tmp[col] = "미표기"
            
            # 4. 표준 컬럼만 추출하여 리스트업
            df_list.append(tmp[std_cols].reset_index(drop=True))
        except:
            continue
            
    if not df_list: return None
    
    # 5. 안전한 병합
    full_df = pd.concat(df_list, axis=0, ignore_index=True)
    
    # 6. 데이터 전처리
    full_df['출시년도'] = pd.to_numeric(full_df['출시년도'], errors='coerce').fillna(2024).astype(int)
    
    # 감미료 자동 추출 로직 강화
    sweet_list = ['수크랄로스', '아스파탐', '아세설팜칼륨', '스테비아', '에리스리톨', '알룰로스', '설탕', '과당']
    def extract_sweets(text):
        if text == "미표기": return "미표기"
        found = [s for s in sweet_list if s in str(text)]
        return ", ".join(found) if found else "미표기"

    full_df['주요당_감미료'] = full_df['원재료표시'].apply(extract_sweets)

    return full_df

# 데이터 실행
df = load_all_data()

# --- 사이드바 제어 ---
with st.sidebar:
    st.title("🔍 검색 및 필터")
    if st.button("🔄 식약처 최신 데이터 수집"):
        if run_collector("9171f7ffd72f4ffcb62f"):
            st.cache_data.clear()
            st.rerun()

if df is not None:
    # 1. 연도 필터
    all_years = sorted(df['출시년도'].unique())
    year_range = st.sidebar.slider("1️⃣ 연도 범위", int(min(all_years)), int(max(all_years)), (2020, 2024))
    
    filtered_by_year = df[(df['출시년도'] >= year_range[0]) & (df['출시년도'] <= year_range[1])]

    # 2. 제조사 선택
    available_owners = sorted(filtered_by_year['brand_owner'].unique())
    selected_owners = st.sidebar.multiselect("2️⃣ 주요 회사 선택", available_owners)

    # 3. 제품명 선택
    temp_df = filtered_by_year[filtered_by_year['brand_owner'].isin(selected_owners)] if selected_owners else filtered_by_year
    available_brands = sorted(temp_df['brand_name'].unique())
    selected_brands = st.sidebar.multiselect("3️⃣ 제품명 검색", available_brands)

    f_df = temp_df[temp_df['brand_name'].isin(selected_brands)] if selected_brands else temp_df

    # --- 메인 화면 ---
    st.title("🥤 RTD 음료 성분 분석 대시보드")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("검색된 제품 수", f"{len(f_df)}건")
    m2.metric("고유 브랜드 수", f"{f_df['brand_name'].nunique()}개")
    m3.metric("평균 출시년도", f"{int(f_df['출시년도'].mean()) if not f_df.empty else 0}년")

    st.divider()

    # 섹션 1: 플레이버 분포
    st.header("🍋 주요 플레이버 분포")
    flavor_keywords = ['STRAWBERRY', 'MANGO', 'APPLE', 'PEACH', 'GRAPE', 'ORANGE', 'LEMON', 'LIME', 'PINEAPPLE', 'TEA']
    
    def detect_flavor(row):
        text = f"{row['brand_name']} {row['원재료표시']} {row['음료유형']}".upper()
        for k in flavor_keywords:
            if k in text: return k
        return "기타/오리지널"

    if not f_df.empty:
        f_df['Flavor'] = f_df.apply(detect_flavor, axis=1)
        st.bar_chart(f_df['Flavor'].value_counts())
    
    st.divider()

    # 섹션 2: 성분별 조회
    st.header("🧪 당/감미료 성분별 제품 조회")
    
    # 감미료 목록 추출
    all_sweets = set()
    df['주요당_감미료'].str.split(',').apply(lambda x: [all_sweets.add(s.strip()) for s in x if s.strip() and s.strip() != '미표기'])
    
    target_sweet = st.selectbox("분석할 성분 선택", ["전체"] + sorted(list(all_sweets)))
    
    display_df = f_df[f_df['주요당_감미료'].str.contains(target_sweet, na=False)] if target_sweet != "전체" else f_df

    sort_order = st.radio("정렬 기준:", ["최신순", "오래된순"], horizontal=True)
    display_df = display_df.sort_values(by='출시년도', ascending=(sort_order == "오래된순"))

    st.dataframe(
        display_df[['출시년도', 'brand_owner', 'brand_name', '주요당_감미료', '음료유형']], 
        use_container_width=True, hide_index=True
    )

    # 다운로드
    csv = display_df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button(label="📥 데이터 다운로드", data=csv, file_name='analysis.csv', mime='text/csv')
else:
    st.warning("데이터 파일(.csv)을 찾을 수 없습니다. 'data' 폴더에 파일을 넣어주세요.")
