import streamlit as st

st.set_page_config(page_title="자기소개 게임", layout="centered")
st.title("🎮 자기소개 게임: 나를 맞혀봐!")

# ---------------------------------
# 세션 초기화
# ---------------------------------
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.profile = {}

# ---------------------------------
# STEP 0: 시작
# ---------------------------------
if st.session_state.step == 0:
    st.subheader("👋 환영합니다!")
    st.write("간단한 게임을 통해 나만의 자기소개를 완성해보세요.")

    if st.button("게임 시작 ▶️"):
        st.session_state.step = 1
        st.rerun()

# ---------------------------------
# STEP 1: 이름
# ---------------------------------
elif st.session_state.step == 1:
    st.subheader("1️⃣ 이름을 입력하세요")

    name = st.text_input("이름")

    if st.button("다음"):
        if name:
            st.session_state.profile["이름"] = name
            st.session_state.step = 2
            st.rerun()
        else:
            st.warning("이름을 입력해주세요!")

# ---------------------------------
# STEP 2: 성격
# ---------------------------------
elif st.session_state.step == 2:
    st.subheader("2️⃣ 나의 성격은?")

    personality = st.radio(
        "가장 가까운 것을 선택하세요",
        ["🔥 열정형", "🧠 분석형", "🎨 창의형", "🤝 협력형"]
    )

    if st.button("다음"):
        st.session_state.profile["성격"] = personality
        st.session_state.step = 3
        st.rerun()

# ---------------------------------
# STEP 3: 관심사
# ---------------------------------
elif st.session_state.step == 3:
    st.subheader("3️⃣ 관심 있는 분야는?")

    interest = st.selectbox(
        "선택하세요",
        ["💻 IT / 개발", "📈 투자 / 경제", "🎮 게임", "🎬 콘텐츠", "🎓 공부"]
    )

    if st.button("다음"):
        st.session_state.profile["관심사"] = interest
        st.session_state.step = 4
        st.rerun()

# ---------------------------------
# STEP 4: 강점
# ---------------------------------
elif st.session_state.step == 4:
    st.subheader("4️⃣ 나의 강점은?")

    strength = st.multiselect(
        "모두 선택 가능",
        ["집중력", "끈기", "문제해결력", "소통능력", "빠른학습"]
    )

    if st.button("결과 보기"):
        st.session_state.profile["강점"] = ", ".join(strength)
        st.session_state.step = 5
        st.rerun()

# ---------------------------------
# STEP 5: 결과
# ---------------------------------
elif st.session_state.step == 5:
    st.subheader("🎉 나의 자기소개 카드")

    p = st.session_state.profile

    st.markdown(f"""
### 🙋 이름
**{p.get("이름")}**

### 🧠 성격
{p.get("성격")}

### 💡 관심사
{p.get("관심사")}

### 💪 강점
{p.get("강점")}
""")

    st.success("자기소개 완성! 🎊")

    if st.button("🔄 다시 하기"):
        st.session_state.clear()
        st.rerun()
