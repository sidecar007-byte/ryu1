import streamlit as st

st.set_page_config(page_title="MBTI 추천 앱", layout="centered")
st.title("🧠 MBTI 성향 분석 & 추천")

st.write("각 문항에서 더 가까운 쪽을 선택하세요.")

# 점수 저장
scores = {"E":0, "I":0, "S":0, "N":0, "T":0, "F":0, "J":0, "P":0}

def question(q, a1, t1, a2, t2):
    choice = st.radio(q, [a1, a2], index=0)
    if choice == a1:
        scores[t1] += 1
    else:
        scores[t2] += 1

# 질문
question("1️⃣ 사람들과 함께 있을 때 에너지가 생긴다",
         "그렇다", "E", "아니다", "I")

question("2️⃣ 사실과 경험이 더 중요하다",
         "그렇다", "S", "아니다", "N")

question("3️⃣ 결정할 때 논리가 더 중요하다",
         "그렇다", "T", "아니다", "F")

question("4️⃣ 계획된 일정이 편하다",
         "그렇다", "J", "아니다", "P")

question("5️⃣ 새로운 사람 만나는 걸 좋아한다",
         "그렇다", "E", "아니다", "I")

question("6️⃣ 상상보단 현실이 중요하다",
         "그렇다", "S", "아니다", "N")

question("7️⃣ 감정보다 결과가 우선이다",
         "그렇다", "T", "아니다", "F")

question("8️⃣ 즉흥적인 선택이 좋다",
         "그렇다", "P", "아니다", "J")

# 결과 버튼
if st.button("🔍 MBTI 결과 보기"):
    mbti = ""
    mbti += "E" if scores["E"] >= scores["I"] else "I"
    mbti += "S" if scores["S"] >= scores["N"] else "N"
    mbti += "T" if scores["T"] >= scores["F"] else "F"
    mbti += "J" if scores["J"] >= scores["P"] else "P"

    st.success(f"당신의 MBTI는 **{mbti}** 입니다!")

    recommendations = {
        "INTJ": "📊 전략기획, 데이터 분석, 연구직",
        "INTP": "🧪 개발자, 연구원, 문제 해결 전문가",
        "ENTJ": "👔 경영, 리더, 프로젝트 매니저",
        "ENTP": "🚀 창업, 마케팅, 기획",
        "INFJ": "🧠 상담가, 심리학, 작가",
        "INFP": "🎨 예술가, 콘텐츠 크리에이터",
        "ENFJ": "🤝 교육, 코칭, 인사",
        "ENFP": "🌈 크리에이티브 디렉터, 방송",
        "ISTJ": "📁 회계, 행정, 관리",
        "ISFJ": "🏥 간호, 복지, 지원",
        "ESTJ": "🏢 조직관리, 운영",
        "ESFJ": "🎓 교육, 서비스",
        "ISTP": "🔧 엔지니어, 기술직",
        "ISFP": "🎵 디자이너, 음악",
        "ESTP": "🏎 영업, 트레이더",
        "ESFP": "🎤 연예, 이벤트"
    }

    st.subheader("✨ 추천 분야")
    st.write(recommendations.get(mbti, "추천 정보를 준비 중입니다."))
