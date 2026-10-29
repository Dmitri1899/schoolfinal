import calendar
from datetime import date

import holidays
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="SchoolMove | 통학비 분석", page_icon="🚌", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1100px; padding-top: 2rem; padding-bottom: 3rem;}
div[data-testid="stMetric"] {background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:16px;}
div.stButton > button {width:100%; min-height:65px; border-radius:10px; font-size:17px; font-weight:600;}
</style>
""", unsafe_allow_html=True)

st.title("🚌 SchoolMove")
st.write("등하교 일수와 달력을 분석해 예상 교통비를 계산하는 통학비 관리 앱입니다.")

if "analysis_mode" not in st.session_state:
    st.session_state.analysis_mode = "등교일 수 기준"

st.subheader("분석 방식 선택")
st.caption("원하는 방식을 선택하면 필요한 입력 항목만 표시됩니다.")
b1, b2 = st.columns(2)
with b1:
    if st.button("📅 등교일 수 기준", type="primary" if st.session_state.analysis_mode == "등교일 수 기준" else "secondary", key="mode_manual", use_container_width=True):
        st.session_state.analysis_mode = "등교일 수 기준"
with b2:
    if st.button("🗓️ 월별 등교일 분석", type="primary" if st.session_state.analysis_mode == "월별 등교일 분석" else "secondary", key="mode_calendar", use_container_width=True):
        st.session_state.analysis_mode = "월별 등교일 분석"

mode = st.session_state.analysis_mode
if mode == "등교일 수 기준":
    st.info("월간 등교 일수를 직접 입력해 간편하게 교통비를 계산합니다.")
else:
    st.info("선택한 연도의 달력을 분석해 월별 평일·주말·공휴일을 기준으로 계산합니다.")

st.divider()
st.subheader("1. 교통 조건 설정")
c1, c2 = st.columns(2)
with c1:
    transport = st.selectbox("주로 이용하는 교통수단", ["버스", "지하철", "버스 + 지하철 환승", "기타 교통수단"])
with c2:
    fare = st.number_input("편도 교통요금 (원)", min_value=0, value=1500, step=50)

c3, c4 = st.columns(2)
with c3:
    weekday_trips = st.selectbox("평일 하루 이용 횟수", [1, 2, 3, 4], index=1,
        format_func=lambda x: {1: "편도 1회", 2: "왕복 2회", 3: "3회", 4: "4회"}[x])
with c4:
    budget = st.number_input("월간 교통비 예산 (원)", min_value=0, value=70000, step=5000)

st.divider()

if mode == "등교일 수 기준":
    st.subheader("2. 등교일 정보")
    school_days = st.number_input("월간 등교 일수", min_value=1, max_value=31, value=20, step=1)

    weekday_cost = school_days * weekday_trips * fare
    weekend_cost = 0
    monthly_cost = weekday_cost
    annual_cost = monthly_cost * 12

    df = pd.DataFrame([{
        "월": f"{month}월",
        "평일 교통비": weekday_cost,
        "주말 교통비": weekend_cost,
        "월간 예상 교통비": monthly_cost
    } for month in range(1, 13)])

    st.caption("입력한 등교 일수가 매월 동일하다고 가정합니다. 이 방식에서는 주말 교통비를 계산하지 않습니다.")
    st.divider()
    st.subheader("3. 계산 결과")
    a, b, c = st.columns(3)
    a.metric("하루 평일 교통비", f"{weekday_trips * fare:,}원")
    b.metric("월간 예상 교통비", f"{monthly_cost:,}원")
    c.metric("연간 예상 교통비", f"{annual_cost:,}원")

else:
    st.subheader("2. 분석할 연도 및 주말 설정")
    c1, c2 = st.columns(2)
    with c1:
        year = st.number_input("분석 연도", min_value=2020, max_value=2100, value=date.today().year, step=1)
    with c2:
        include_weekends = st.checkbox("주말 교통비 포함", value=False)

    weekend_trips = 2
    if include_weekends:
        weekend_trips = st.selectbox("주말 하루 이용 횟수", [1, 2, 3, 4], index=1,
            format_func=lambda x: {1: "편도 1회", 2: "왕복 2회", 3: "3회", 4: "4회"}[x])

    exclude_holidays = st.checkbox("평일 공휴일을 등교일에서 제외", value=True)
    st.caption("한국 공휴일은 holidays 라이브러리 기준입니다. 학교 방학과 재량휴업일은 자동으로 반영되지 않습니다.")

    kr_holidays = holidays.country_holidays("KR", years=[int(year)])
    records = []
    for month in range(1, 13):
        days_in_month = calendar.monthrange(int(year), month)[1]
        weekdays, weekends, weekday_holidays = 0, 0, 0
        for day in range(1, days_in_month + 1):
            current_date = date(int(year), month, day)
            holiday_name = kr_holidays.get(current_date)
            if current_date.weekday() < 5:
                weekdays += 1
                if holiday_name:
                    weekday_holidays += 1
            else:
                weekends += 1

        commute_days = weekdays - weekday_holidays if exclude_holidays else weekdays
        weekday_cost = commute_days * weekday_trips * fare
        weekend_cost = weekends * weekend_trips * fare if include_weekends else 0
        records.append({
            "월": f"{month}월",
            "평일 수": weekdays,
            "평일 공휴일 수": weekday_holidays,
            "주말 수": weekends,
            "예상 등교일": commute_days,
            "평일 교통비": weekday_cost,
            "주말 교통비": weekend_cost,
            "월간 예상 교통비": weekday_cost + weekend_cost
        })

    df = pd.DataFrame(records)
    total_weekdays = int(df["평일 수"].sum())
    total_weekends = int(df["주말 수"].sum())
    total_holidays = int(df["평일 공휴일 수"].sum())
    total_school_days = int(df["예상 등교일"].sum())
    annual_cost = int(df["월간 예상 교통비"].sum())

    st.divider()
    st.subheader(f"3. {int(year)}년 달력 분석 결과")
    a, b, c, d = st.columns(4)
    a.metric("연간 평일", f"{total_weekdays:,}일")
    b.metric("연간 주말", f"{total_weekends:,}일")
    c.metric("평일 공휴일", f"{total_holidays:,}일")
    d.metric("예상 등교일", f"{total_school_days:,}일")
    st.metric("연간 예상 교통비", f"{annual_cost:,}원")

st.divider()
st.subheader("📈 월별 예상 교통비")
fig = px.bar(df, x="월", y="월간 예상 교통비", text="월간 예상 교통비", title="월별 교통비 비교")
fig.update_traces(texttemplate="%{text:,}원", textposition="outside", cliponaxis=False)
fig.update_layout(xaxis_title="월", yaxis_title="예상 교통비 (원)", yaxis_rangemode="tozero")
st.plotly_chart(fig, use_container_width=True)

st.subheader("평일·주말 교통비 비교")
cost_df = df[["월", "평일 교통비", "주말 교통비"]].melt(id_vars="월", var_name="구분", value_name="교통비")
fig2 = px.bar(cost_df, x="월", y="교통비", color="구분", barmode="group", title="월별 평일 및 주말 교통비")
fig2.update_layout(xaxis_title="월", yaxis_title="교통비 (원)", yaxis_rangemode="tozero")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("📊 월별 상세 데이터")
display_df = df.copy()
for column in ["평일 교통비", "주말 교통비", "월간 예상 교통비"]:
    display_df[column] = display_df[column].map(lambda x: f"{x:,}원")
st.dataframe(display_df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("💳 예산 분석")
average_cost = annual_cost / 12
remaining = budget - average_cost
a, b, c = st.columns(3)
a.metric("월간 예산", f"{budget:,}원")
b.metric("월평균 교통비", f"{average_cost:,.0f}원")
c.metric("평균 예산 잔액", f"{remaining:,.0f}원")

if budget > 0:
    usage = average_cost / budget
    st.write(f"월평균 예산 사용률: {usage * 100:.1f}%")
    st.progress(min(usage, 1.0))
    if average_cost > budget:
        st.warning("월평균 교통비가 설정한 예산을 초과합니다.")
    else:
        st.success("월평균 교통비가 설정한 예산 이내입니다.")
else:
    st.info("예산을 0원보다 크게 설정하면 예산 사용률을 확인할 수 있습니다.")

st.divider()
st.subheader("📥 분석 결과 다운로드")
csv_data = df.to_csv(index=False).encode("utf-8-sig")
st.download_button("월별 교통비 분석 CSV 다운로드", data=csv_data, file_name="schoolmove_analysis.csv", mime="text/csv")

st.caption("모든 결과는 입력한 요금에 따른 예상치입니다. 달력 분석은 평일·주말·공휴일을 기준으로 하며, 학교 방학, 재량휴업일, 결석, 실제 환승 할인 등은 자동 반영되지 않습니다.")
