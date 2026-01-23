import streamlit as st
import pandas as pd
import os
import glob
import requests
from datetime import datetime, date

# 1. 페이지 설정
st.set_page_config(page_title="음료 통합 분석 대시보드", layout="wide")

# --- [기능 1] 식약처 API 수집 및 표준화 ---
def run_collector(api_key):
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/I1250/json/1/500"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        if 'I1250' not in data: return False
        
        rows = data['I1250']['row']
        api_df = pd.DataFrame(rows)
        
        # 중복 컬럼 제거 (에러 방지 핵심)
        api_df = api_df.loc[:, ~api_df.columns.duplicated()].copy()
        
        # 기존 CSV 규격에 맞게 컬럼명 매핑
        mapping = {
            'BSSH_NM': 'brand_owner', 
            'PRMS_DT': '출시년도', 
            'PRDLST_NM': 'brand_name', 
            'PRDLST_DCLS_NM': '음료유형', 
            'RAWMATERIAL_NM': '원재료표시'
        }
        api_df = api_df.rename(columns=mapping)
        api_df['출시년도'] = api_df['출시년도'].astype(str).str[:4] # '20240101' -> '2024'
        
        if not os.path.exists('data'): os.makedirs('data')
        api_df.to_csv("data/beverage_api_data.csv", index=False, encoding='utf-8-sig')
        return True
    except:
        return False

# --- [기능 2] 데이터 통합 로드 (에러 원천 차단) ---
@st.cache_data
def load_all_data():
    # 모든 CSV 파일 탐색
    files = glob.glob(os.path.join("data", "*.csv")) + glob.glob("*.csv")
    if not files: return None
    
    # 분석에 필요한 7개 핵심 컬럼 표준 정의
    std_cols = ['음료유형', 'brand_owner', 'brand_name', 'branded_food_category', '원재료표시', '주요당_감미료', '출시년도']
    df_list = []

    for f in set(files):
        try:
            try: tmp = pd.read_csv(f, encoding='utf-8-sig')
            except: tmp = pd.read_csv(f, encoding='cp949')
            
            if tmp.empty: continue

            # [해결] 중복 컬럼 이름 제거 (InvalidIndexError 방지)
            tmp = tmp.loc[:, ~tmp.columns.duplicated()].copy()
            
            # 컬럼 이름 유연하게 매핑
            tmp = tmp.rename(columns={'품목유형명': '음료유형', '업소명': 'brand_owner', '제품명': 'brand_name'})
            
            # 표준 컬럼 중 없는 것은 생성
            for col in std_cols:
                if col not in tmp.columns: tmp[col] = "미표기"
            
            # 딱 정해진 표준 컬럼만 추출 (병합 시 충돌 방지)
            df_list.append(tmp[std_cols].reset_index(drop=True))
        except:
            continue
            
    if not df_list: return None
    
    # 데이터 병합
    full_df = pd.concat(df_list, axis=0, ignore_index=True)
    
    # 전처리: 출시년도 숫자화
    full_df['출시년도'] = pd.to_numeric(full_df['출시년도'], errors='coerce').fillna(2024).astype(int)
    
    # [만족 기능] 감미료 자동 추출 로직
    sweet_list = ['수크랄로스', '아스파탐', '아세설팜칼륨', '스테비아', '에리스리톨', '알룰로스', '설탕', '과당']
    def extract_sweets(row):
        # 이미 추출된 값이 있으면 사용, 없으면 원재료에서 추출
        existing = str(row['주요당_감미료'])
        if existing != "미표기" and len(existing) > 1: return existing
        
        text = str(row['원재료표시'])
        found = [s for s in sweet_list if s in text]
        return ", ".join(found) if found else "미표기"

    full_df['주요당_감미료'] = full_df.apply(extract_sweets, axis=1)

    return full_df

# 데이터 실행
df = load_all_data()

# --- 사이드바: 필터 및 제어 ---
with st.sidebar:
    st.title("🥤 대시보드 제어")
    if st.button("🔄 식약처 데이터 업데이트"):
        if run_collector("9171f7ffd72f4ffcb62f"):
            st.cache_data.clear()
            st.rerun()

    if df is not None:
        st.divider()
        # 연도 필터
        all_years = sorted(df['출시년도'].unique())
        year_range = st.slider("1️⃣ 출시 연도 선택", int(min(all_years)), int(max(all_years)), (2020, 2024))
        
        # 제조사 선택 (연동형)
        filtered_by_year = df[(df['출시년도'] >= year_range[0]) & (df['출시년도'] <= year_range[1])]
        available_owners = sorted(filtered_by_year['brand_owner'].unique())
        selected_owners = st.multiselect("2️⃣ 주요 제조사 선택", available_owners)

# --- 메인 대시보드 화면 ---
if df is not None:
    # 데이터 필터링 적용
    temp_df = filtered_by_year[filtered_by_year['brand_owner'].isin(selected_owners)] if selected_owners else filtered_by_year
    
    st.title("📊 RTD 음료 통합 트렌드 분석")
    
    # 핵심 지표 (KPI)
    m1, m2, m3 = st.columns(3)
    m1.metric("분석 대상 제품 수", f"{len(temp_df)}건")
    m2.metric("참여 브랜드 수", f"{temp_df['brand_owner'].nunique()}개")
    m3.metric("최신 업데이트", f"{temp_df['출시년도'].max()}년")

    st.divider()

    # 섹션 1: 시각화 분석
    tab1, tab2 = st.tabs(["📈 시장 현황 분석", "🔍 제품 성분 검색"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏢 제조사별 출시 비중")
            st.bar_chart(temp_df['brand_owner'].value_counts().head(10))
            
        with col2:
            st.subheader("🍋 인기 플레이버 분포")
            flavor_keywords = ['STRAWBERRY', 'MANGO', 'APPLE', 'PEACH', 'GRAPE', 'LEMON', 'LIME', 'TEA', 'SODA']
            def detect_flavor(row):
                text = f"{row['brand_name']} {row['원재료표시']}".upper()
                for k in flavor_keywords:
                    if k in text: return k
                return "기타/오리지널"
            
            temp_df['Flavor'] = temp_df.apply(detect_flavor, axis=1)
            st.bar_chart(temp_df['Flavor'].value_counts())

    with tab2:
        st.header("🧪 성분 및 감미료 상세 조회")
        
        # 감미료 필터
        all_sweets = set()
        df['주요당_감미료'].str.split(',').apply(lambda x: [all_sweets.add(s.strip()) for s in x if s.strip() and s.strip() != '미표기'])
        target_sweet = st.selectbox("특정 감미료 포함 제품 찾기", ["전체"] + sorted(list(all_sweets)))
        
        display_df = temp_df[temp_df['주요당_감미료'].str.contains(target_sweet, na=False)] if target_sweet != "전체" else temp_df
        
        # 최신순 정렬 및 출력
        st.dataframe(
            display_df.sort_values('출시년도', ascending=False)[['출시년도', 'brand_owner', 'brand_name', '주요당_감미료', '음료유형']], 
            use_container_width=True, hide_index=True
        )

    # 데이터 다운로드 버튼
    csv = temp_df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button(label="📥 분석 결과 다운로드 (CSV)", data=csv, file_name=f'drink_analysis_{date.today()}.csv')

else:
    st.info("데이터 파일이 없습니다. 사이드바에서 업데이트 버튼을 눌러주세요.")
