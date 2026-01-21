import requests
import pandas as pd
from datetime import datetime, timedelta

def get_food_report_final_format():
    # 1. 기본 설정 (ID 11250 고정)
    api_key = "9171f7ffd72f4ffcb62f"
    service_id = "I1250"
    file_type = "json"
    
    # 2. 날짜 설정 (최근 3개월)
    today = datetime.now()
    three_months_ago = (today - timedelta(days=90)).strftime('%Y%m%d')
    
    # API URL 구성 (CHNG_DT 인자 포함)
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{service_id}/{file_type}/1/100/CHNG_DT={three_months_ago}"

    print(f"📂 작업명: 식품품목제조보고 최신화 목록 (최근 3개월)")
    print(f"📅 조회 기준: {three_months_ago} 이후 변경 자료\n")

    try:
        response = requests.get(url)
        data = response.json()
        
        if service_id in data:
            rows = data[service_id].get("row", [])
            if not rows:
                print("⚠️ 해당 기간 내 데이터가 없습니다.")
                return

            # 데이터프레임 생성
            df = pd.DataFrame(rows)

            # 3. 요청하신 출력 형식에 맞춰 컬럼 매칭 및 이름 변경
            # 명세서 변수명과 요청 한글명을 매핑합니다.
            column_mapping = {
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

            # 존재하는 컬럼만 필터링하여 재정렬
            available_cols = [col for col in column_mapping.keys() if col in df.columns]
            final_df = df[available_cols].rename(columns=column_mapping)

            # 4. 결과 출력 (가로로 길기 때문에 표 형식으로 출력)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
            
            print(f"✅ 총 {len(final_df)}건의 데이터를 출력합니다.")
            print("-" * 150)
            print(final_df.to_string(index=False))
            print("-" * 150)

            # 필요시 엑셀 저장
            # final_df.to_excel("식품품목제조보고_최신화.xlsx", index=False)
            
        else:
            print("⚠️ API 응답에 해당 서비스 ID가 없습니다. (인증키 활성화 확인 필요)")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    get_food_report_final_format()
