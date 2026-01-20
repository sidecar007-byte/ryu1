import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="26년 주식시장 분석", layout="wide")
st.title("📈 26년 주식시장 분석")

# 1. Ticker 입력란
tickers = st.text_input("종목 코드 입력 (쉼표 구분, 예: AAPL,MSFT,TSLA)", "AAPL,MSFT,TSLA")
ticker_list = [t.strip() for t in tickers.split(",")]

# 2. 수익률 드롭다운
target = st.selectbox("🎯 목표 수익률 (%)", list(range(20, 210, 10)))

# fetch function
def fetch_history(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=3y&interval=1mo"
    res = requests.get(url).json()
    try:
        prices = res["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"]
        dates = [x["fmt"] for x in res["chart"]["result"][0]["timestamp"]]
        df = pd.DataFrame({"date": dates, "adjclose": prices})
        df["year"] = pd.to_datetime(df["date"]).dt.year
        return df
    except:
        return pd.DataFrame()

# 3. 수익률 계산
results = []
for t in ticker_list:
    df = fetch_history(t)
    if df.empty:
        continue

    # 연도별 종가만 추림
    yearly = df.groupby("year").last()["adjclose"]
    if 2024 in yearly and 2025 in yearly and 2026 in yearly:
        r24 = (yearly[2025] - yearly[2024]) / yearly[2024] * 100
        r25 = (yearly[2026] - yearly[2025]) / yearly[2025] * 100
        r26 = (yearly[2026] - yearly[2025]) / yearly[2025] * 100
        if r26 >= target:
            results.append((t, r24, r25, r26))

# 출력
df_out = pd.DataFrame(results, columns=["Ticker", "24년", "25년", "26년"])
df_out = df_out.sort_values(by="26년", ascending=False).head(5)

st.subheader("⭐ 추천 종목")
st.dataframe(df_out)
