import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 페이지 설정
st.set_page_config(page_title="Streamlit 데이터 시각화", layout="wide")

st.title("📊 Streamlit 데이터 시각화 앱")

# 파일 업로드
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("데이터 미리보기")
    st.dataframe(df)

    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns

    if len(numeric_cols) >= 2:
        x_col = numeric_cols[0]
        y_col = numeric_cols[1]

        st.subheader("자동 생성 그래프")

        fig, ax = plt.subplots()
        ax.plot(df[x_col], df[y_col])
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(f"{x_col} vs {y_col}")

        st.pyplot(fig)
    else:
        st.warning("숫자형 컬럼이 2개 이상 필요")
        

