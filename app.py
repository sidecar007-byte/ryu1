 import streamlit as st

import pandas as pd

import os

import glob



# 1. 페이지 설정

st.set_page_config(page_title="음료 데이터 통합 분석기", layout="wide")



@st.cache_data

def load_data():

    # 파일 탐색 로직

    possible_paths = [os.path.join("data", "*.csv"), "*.csv"]

    csv_files = []

    for path in possible_paths:

        csv_files.extend(glob.glob(path))

    

    if not csv_files:

        return None



    file_path = csv_files[0]

    try:

        df = pd.read_csv(file_path, encoding='utf-8-sig')

    except:

        df = pd.read_csv(file_path, encoding='cp949')



    # 컬럼 표준화 (순서 기반 강제 매핑)

    std_cols = ['음료유형', 'brand_owner', 'brand_name', 'branded_food_category', '원재료표시', '주요당_감미료', '출시년도']

    current_cols = list(df.columns)

    df.rename(columns={current_cols[i]: std_cols[i] for i in range(min(len(current_cols), len(std_cols)))}, inplace=True)



    # 데이터 전처리

    df['출시년도'] = pd.to_numeric(df['출시년도'], errors='coerce')

    df = df.dropna(subset=['출시년도'])

    df['출시년도'] = df['출시년도'].astype(int)

    

    for col in std_cols:

        if col != '출시년도':

            df[col] = df[col].astype(str).str.strip().replace(['nan', 'None', ''], '미표기')

    

    return df



df = load_data()



if df is not None:

    # --- 사이드바: 연동형 검색 시스템 ---

    st.sidebar.title("🔍 검색 및 필터")

    

    # 1. 연도 필터

    all_years = sorted(df['출시년도'].unique())

    year_range = st.sidebar.slider("1️⃣ 연도 범위", int(min(all_years)), int(max(all_years)), (int(min(all_years)), int(max(all_years))))

    

    # 연도 1차 필터링

    filtered_by_year = df[(df['출시년도'] >= year_range[0]) & (df['출시년도'] <= year_range[1])]



    # 2. 제조사 선택

    available_owners = sorted(filtered_by_year['brand_owner'].unique())

    selected_owners = st.sidebar.multiselect("2️⃣ 주요 회사 선택", available_owners)



    # 3. 제품명 선택 (제조사와 연동)

    if selected_owners:

        temp_df = filtered_by_year[filtered_by_year['brand_owner'].isin(selected_owners)]

    else:

        temp_df = filtered_by_year



    available_brands = sorted(temp_df['brand_name'].unique())

    selected_brands = st.sidebar.multiselect("3️⃣ 제품명 검색", available_brands)



    # 최종 필터링 데이터

    if selected_brands:

        f_df = temp_df[temp_df['brand_name'].isin(selected_brands)]

    else:

        f_df = temp_df



    # --- 메인 화면 구성 ---

    st.title("🥤 RTD 음료 성분 분석 대시보드")

    

    # 지표 요약

    m1, m2, m3 = st.columns(3)

    m1.metric("검색된 제품 수", f"{len(f_df)}건")

    m2.metric("고유 브랜드 수", f"{f_df['brand_name'].nunique()}개")

    m3.metric("평균 출시년도", f"{int(f_df['출시년도'].mean()) if not f_df.empty else 0}년")



    st.divider()



    # --- 섹션 1: 플레이버 분포 ---

    st.header("🍋 주요 플레이버 분포")

    flavor_keywords = ['STRAWBERRY', 'MANGO', 'APPLE', 'PEACH', 'GRAPE', 'ORANGE', 'LEMON', 'LIME', 'PINEAPPLE', 'TEA']

    

    def detect_flavor(row):

        text = f"{row['brand_name']} {row['원재료표시']} {row['branded_food_category']}".upper()

        for k in flavor_keywords:

            if k in text: return k

        return "기타/오리지널"



    if not f_df.empty:

        f_df['Flavor'] = f_df.apply(detect_flavor, axis=1)

        flavor_counts = f_df['Flavor'].value_counts()

        st.bar_chart(flavor_counts)

    

    st.divider()



    # --- 섹션 2: 당 및 감미료 성분별 정렬 및 조회 (추가됨!) ---

    st.header("🧪 당/감미료 성분별 제품 조회")

    

    # 전체 데이터에서 감미료 목록 추출 (검색용)

    all_sweets = set()

    df['주요당_감미료'].str.split(',').apply(lambda x: [all_sweets.add(s.strip()) for s in x if s.strip() and s.strip() != '미표기'])

    

    col_s1, col_s2 = st.columns([1, 3])

    with col_s1:

        target_sweet = st.selectbox("분석할 성분 선택", ["전체"] + sorted(list(all_sweets)))

    

    # 감미료 필터 적용

    if target_sweet != "전체":

        display_df = f_df[f_df['주요당_감미료'].str.contains(target_sweet, na=False)]

        st.info(f"🔍 **'{target_sweet}'** 성분이 포함된 제품 리스트 (총 {len(display_df)}건)")

    else:

        display_df = f_df

        st.info(f"💡 현재 필터링된 전체 제품 리스트 (총 {len(display_df)}건)")



    # 정렬 기능 추가 (출시년도 최신순 기본)

    sort_order = st.radio("정렬 기준:", ["최신순", "오래된순"], horizontal=True)

    if sort_order == "최신순":

        display_df = display_df.sort_values(by='출시년도', ascending=False)

    else:

        display_df = display_df.sort_values(by='출시년도', ascending=True)



    # 데이터 테이블 출력

    st.dataframe(

        display_df[['출시년도', 'brand_owner', 'brand_name', '주요당_감미료', '음료유형']], 

        use_container_width=True,

        hide_index=True

    )



    # --- 다운로드 버튼 ---

    csv = display_df.to_csv(index=False).encode('utf-8-sig')

    st.sidebar.download_button(

        label="📥 현재 데이터 결과 다운로드",

        data=csv,

        file_name='beverage_analysis_result.csv',

        mime='text/csv',

    )
