st.subheader("⭐ 추천 종목 TOP 5 (실시간 시세)")

if top.empty:
    st.warning("조건을 만족하는 종목이 없습니다.")
else:
    for _, r in top.iterrows():
        profit = int(investment * r["return_26"] / 100)
        total = investment + profit

        # 미국주식만 실시간
        price, change = (None, None)
        if market == "미국 주식":
            price, change = get_realtime_price(r["code"])

        cols = st.columns([0.4, 2.8, 1, 1, 1, 1.4, 1.4])

        cols[0].markdown(r["icon"])
        cols[1].markdown(f"**{r['code']} ({r['name']})**")
        cols[2].markdown(f"{r['return_24']}%")
        cols[3].markdown(f"{r['return_25']}%")
        cols[4].markdown(f"**{r['return_26']}%**")

        if price:
            color = "green" if change >= 0 else "red"
            cols[5].markdown(
                f"<span style='color:{color}'>{price}$ ({change}%)</span>",
                unsafe_allow_html=True
            )
        else:
            cols[5].markdown("—")

        cols[6].markdown(f"**{total:,}원**")
