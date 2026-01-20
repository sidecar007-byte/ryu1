import streamlit as st
import pandas as pd
import requests
from pykrx import stock
from datetime import datetime

st.set_page_config(page_title="26년 주식시장 분석", layout="wide")
st.title("📈 26년 주식시장 분석")

# ==================================================
# 1. 목표 수익률 선택 (20%~200%)
# ==================================================
target = st.selectbox("🎯 목표 수익률 (%)", list(range(20, 210, 10)))

# ==================================================
# 2. 미국 주식 (Yahoo Finance)
# ==================================================
HEADERS = {"User-Agent": "Mozilla/5.0"}

US_STOCKS = {
    "AAPL": "애플",
    "MSFT": "마이크로소프트",
    "NVDA": "엔비디아",
    "META": "메타",
    "AMZN": "아마존",
    "TSLA": "테슬라"
}

def fetch_yahoo(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=3y&interval=1mo"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        result = data.get("chart", {}).get("result")
        if not result:
            return None

        ts = result[0]["timestamp"]
        prices = result[0]["indicators"]["adjclose"][0]["adjclose"]

        df = pd.DataFrame({
            "date": pd.to_datetime(ts, unit="s"),
            "price": prices
        }).dropna()

        df["year"] = df["date"].dt.year
        return df
    except:
        return None

# ==================================================
# 3. 한국 주식 (KRX, pykrx)  ⭐ 강력추천
# ==================================================
KOSPI_CODES = stock.get_market_ticker_list(market="KOSPI")[:50]  # 대표 50종목

def fetch_krx(code):
    try:
        df = stock.get_market_ohlcv_by_date(
            fromdate="20240101",
            todate=datetime.today().strftime("%Y%m%d"),
            ticker=code
        )
        if df.empty:
            return None
        df = df.reset_index()
        df["year"] = df["날짜"].dt.year
        return df
    except:
        return None

# ==================================================
# 4. 수익률 계산
# ==================================================
results = []

# 🇺🇸 미국 주식
for code, name in US_STOCKS.items():
    df = fetch_yahoo(code)
    if df is None:
        continue

    yearly = df.groupby("year").last()["price"]
    if all(y in yearly for y in [2024, 2025, 2026]):
        r25 = (yearly[2026] - yearly[2025]) / yearly[2025] * 100
        if r25 >= target:
            results.append({
                "종목": f"{code} ({name})",
                "시장": "미국",
                "26년 수익률(%)": round(r25, 1)
            })

# 🇰🇷 한국 주식
for code in KOSPI_CODES:
    df = fetch_krx(code)
    if df is None:
        continue

    yearly = df.groupby("year").last()["종가"]
    if all(y in yearly for y in [2024, 2025, 2026]):
        r25 = (yearly[2026] - yearly[2025]) / yearly[2025] * 100
        if r25 >= target:
            results.append({
                "종목": f"{code} ({stock.get_market_ticker_name(code)})",
                "시장": "한국",
                "26년 수익률(%)": round(r25, 1)
            })

# ==================================================
# 5. 결과 출력
# ==================================================
st.subheader("⭐ 추천 종목 TOP 5")

if not results:
    st.warning("조건을 만족하는 종목이 없습니다. 수익률 기준을 낮춰보세요.")
else:
    df_out = pd.DataFrame(results).sort_values("26년 수익률(%)", ascending=False)
    st.dataframe(df_out.head(5), use_container_width=True)

# ==================================================
# 6. 뉴스 링크
# ==================================================
st.divider()
st.subheader("📰 관련 뉴스")

for stock_name in df_out.head(5)["종목"]:
    link = f"https://www.google.com/search?q={stock_name}+주식+뉴스"
    st.markdown(f"- **{stock_name}** → [뉴스 보기]({link})")
