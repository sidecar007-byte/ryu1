import streamlit as st
st.title("*류지성의 첫 웹앱*!")
st.write('안녕하세요! 반갑습니다. :)')
st.write('초록색버튼따라가기!')
st.button("버튼누르기")
def main():
    st.title("비밀번호 입력창 토글 예제")

    # 1. 세션 상태 초기화 (버튼 상태를 기억하기 위함)
    if 'show_input' not in st.session_state:
        st.session_state['show_input'] = False

    # 2. 버튼 클릭 시 상태를 변경하는 콜백 함수
    def toggle_input():
        st.session_state['show_input'] = not st.session_state['show_input']

    # 3. 버튼 생성 (누르면 toggle_input 함수 실행)
    btn_label = "비밀번호 입력창 닫기" if st.session_state['show_input'] else "비밀번호 입력창 열기"
    st.button(btn_label, on_click=toggle_input)

    # 4. 상태에 따라 입력창 표시
    if st.session_state['show_input']:
        st.divider() # 구분선
        password = st.text_input("비밀번호를 입력하세요", type="password")
        
        # 비밀번호 확인 로직 (예시)
        if password:
            if password == "1234":
                st.success("✅ 인증되었습니다!")
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")
