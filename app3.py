import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(layout="wide")
st.title("📈 26년 주식시장 분석")

# ------------------------------------
# 실시간 시세 함수
# ------------------------------------
@st.cache_data(ttl=300)
def get_realtime_price(ticker):
    try:
        t = yf.Ticker(ticker)
        h = t.history(period="2d")
        if len(h) < 2:
            return None, None
        prev = h["Close"].iloc[-2]
        curr = h["Close"].iloc[-1]
        change = round((curr - prev) / prev * 100, 2)
        return round(curr, 2), change
    except:
        return None, None

# ------------------------------------
# 테스트용 데이터
# ------------------------------------
df = pd.DataFrame({
    "code": ["AAPL", "MSFT", "NVDA"],
    "name": ["애플", "마이크로소프트", "엔비디아"],
    "icon": ["🍎", "🪟", "🎮"],
    "return_26": [120, 90, 180]
})

investment = st.number_input("투자금액", value=1_000_000, step=100_000)

# ------------------------------------
# 출력
# ------------------------------------
st.subheader("⭐ 추천 종목 TOP 5 (실시간 시세)")

for _, r in df.iterrows():
    price, change = get_realtime_price(r["code"])
    profit = int(investment * r["return_26"] / 100)
    total = investment + profit

    c1, c2, c3, c4 = st.columns([0.5, 3, 2, 2])
    c1.markdown(r["icon"])
    c2.markdown(f"**{r['code']} ({r['name']})**")

    if price:
        color = "green" if change >= 0 else "red"
        c3.markdown(
            f"<span style='color:{color}'>{price}$ ({change}%)</span>",
            unsafe_allow_html=True
        )
    else:
        c3.markdown("—")

    c4.markdown(f"**{total:,}원**")
