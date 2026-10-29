
import calendar
from datetime import date

import holidays
import pandas as pd
import plotly.express as px
import streamlit as st

# =====================================
# 페이지 설정
# =====================================
st.set_page_config(
    page_title="SchoolMove | 통학비 분석",
    page_icon="🚌",
    layout="wide"
)

st.markdown("""
<style>
    .block-container {
        max-width: 1150px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    div[data-testid="stMetric"] {
        background: #f8fafc;
        padding: 14px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚌 SchoolMove")
st.write("나의 등하교 교통비를 계산하고 월별 지출을 분석하세요.")

# =====================================
# 분석 방식 선택
# =====================================
st.sidebar.header("📊 분석 방식")

mode = st.sidebar.radio(
    "원하는 분석 방법을 선택하세요.",
    [
        "등교일 수 기준",
        "월별 등교일 분석"
    ]
)

st.sidebar.divider()
st.sidebar.header("⚙️ 통학 조건")

fare = st.sidebar.number_input(
    "편도 교통요금 (원)",
    min_value=0,
    value=1500,
    step=50
)

weekday_trips = st.sidebar.selectbox(
    "평일 하루 이용 횟수",
    [1, 2, 3, 4],
    index=1,
    format_func=lambda x: {
        1: "편도 1회",
        2: "왕복 2회",
        3: "3회",
        4: "4회"
    }[x]
)

include_weekends = st.sidebar.checkbox(
    "주말 교통비 포함",
    value=False
)

weekend_trips = st.sidebar.selectbox(
    "주말 하루 이용 횟수",
    [1, 2, 3, 4],
    index=1,
    format_func=lambda x: {
        1: "편도 1회",
        2: "왕복 2회",
        3: "3회",
        4: "4회"
    }[x],
    disabled=not include_weekends
)

budget = st.sidebar.number_input(
    "월간 교통비 예산 (원)",
    min_value=0,
    value=70000,
    step=5000
)

# =====================================
# 교통수단별 비교 요금
# =====================================
st.subheader("교통수단별 요금 설정")
st.caption("기본 요금은 예시입니다. 실제 결제 요금에 맞게 수정하세요.")

col1, col2 = st.columns(2)

with col1:
    bus_fare = st.number_input(
        "버스 편도 요금 (원)",
        min_value=0,
        value=1500,
        step=50
    )
    subway_fare = st.number_input(
        "지하철 편도 요금 (원)",
        min_value=0,
        value=1500,
        step=50
    )

with col2:
    transfer_fare = st.number_input(
        "환승 편도 요금 (원)",
        min_value=0,
        value=1600,
        step=50
    )
    other_fare = st.number_input(
        "기타 교통수단 편도 요금 (원)",
        min_value=0,
        value=2000,
        step=50
    )

fares = {
    "버스": bus_fare,
    "지하철": subway_fare,
    "버스 + 지하철 환승": transfer_fare,
    "기타 교통수단": other_fare
}

# =====================================
# 분석 방식 1: 등교일 수 직접 입력
# =====================================
if mode == "등교일 수 기준":

    st.header("📅 등교일 수 기준 분석")
    st.write("한 달 등교 일수를 직접 입력해 예상 교통비를 계산합니다.")

    col1, col2 = st.columns(2)

    with col1:
        school_days = st.number_input(
            "월간 등교 일수",
            min_value=1,
            max_value=31,
            value=20,
            step=1
        )

    with col2:
        selected_transport = st.selectbox(
            "주로 이용하는 교통수단",
            list(fares.keys())
        )

    selected_fare = fares[selected_transport]

    weekday_cost = (
        school_days * weekday_trips * selected_fare
    )

    # 주말 이용은 등교일과 별도로 추가
    weekend_days = 0

    if include_weekends:
        weekend_days = st.number_input(
            "한 달 주말 이용 일수",
            min_value=0,
            max_value=10,
            value=4,
            step=1
        )

    weekend_cost = (
        weekend_days * weekend_trips * selected_fare
        if include_weekends else 0
    )

    monthly_cost = weekday_cost + weekend_cost
    annual_cost = monthly_cost * 12

    result_df = pd.DataFrame({
        "구분": ["평일", "주말"],
        "이용 일수": [school_days, weekend_days],
        "교통비": [weekday_cost, weekend_cost]
    })

    st.divider()
    st.subheader("계산 결과")

    c1, c2, c3 = st.columns(3)

    c1.metric("하루 평일 교통비",
              f"{weekday_trips * selected_fare:,}원")
    c2.metric("월간 예상 교통비",
              f"{monthly_cost:,}원")
    c3.metric("연간 예상 교통비",
              f"{annual_cost:,}원")

    monthly_data = []

    for month in range(1, 13):
        monthly_data.append({
            "월": f"{month}월",
            "평일 교통비": weekday_cost,
            "주말 교통비": weekend_cost,
            "월간 예상 교통비": monthly_cost
        })

    df = pd.DataFrame(monthly_data)

    st.info(
        "이 방식은 매월 입력한 등교 일수가 동일하다고 가정해 "
        "연간 비용을 추정합니다."
    )

# =====================================
# 분석 방식 2: 실제 달력 기준
# =====================================
else:

    st.header("🗓️ 월별 등교일 분석")
    st.write("선택한 연도의 달력을 이용해 월별 평일과 주말을 분석합니다.")

    year = st.number_input(
        "분석 연도",
        min_value=2020,
        max_value=2100,
        value=date.today().year,
        step=1
    )

    exclude_holidays = st.checkbox(
        "평일 공휴일을 등교일에서 제외",
        value=True
    )

    kr_holidays = holidays.country_holidays(
        "KR",
        years=[int(year)]
    )

    records = []

    for month in range(1, 13):

        days_in_month = calendar.monthrange(
            int(year), month
        )[1]

        weekdays = 0
        weekends = 0
        weekday_holidays = 0

        for day in range(1, days_in_month + 1):

            current_date = date(
                int(year), month, day
            )

            holiday_name = kr_holidays.get(current_date)

            if current_date.weekday() < 5:
                weekdays += 1

                if holiday_name:
                    weekday_holidays += 1
            else:
                weekends += 1

        if exclude_holidays:
            commute_days = weekdays - weekday_holidays
        else:
            commute_days = weekdays

        weekday_cost = (
            commute_days * weekday_trips * fare
        )

        weekend_cost = (
            weekends * weekend_trips * fare
            if include_weekends else 0
        )

        total_cost = weekday_cost + weekend_cost

        records.append({
            "월": f"{month}월",
            "평일 수": weekdays,
            "평일 공휴일 수": weekday_holidays,
            "주말 수": weekends,
            "예상 등교일": commute_days,
            "평일 교통비": weekday_cost,
            "주말 교통비": weekend_cost,
            "월간 예상 교통비": total_cost
        })

    df = pd.DataFrame(records)

    total_weekdays = int(df["평일 수"].sum())
    total_weekends = int(df["주말 수"].sum())
    total_holidays = int(df["평일 공휴일 수"].sum())
    total_school_days = int(df["예상 등교일"].sum())

    st.subheader(f"{int(year)}년 달력 분석 결과")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("연간 평일", f"{total_weekdays:,}일")
    c2.metric("연간 주말", f"{total_weekends:,}일")
    c3.metric("평일 공휴일", f"{total_holidays:,}일")
    c4.metric("예상 등교일", f"{total_school_days:,}일")

    annual_cost = int(df["월간 예상 교통비"].sum())

    st.metric("연간 예상 교통비", f"{annual_cost:,}원")

# =====================================
# 공통: 월별 비용 그래프
# =====================================
st.divider()
st.subheader("📈 월별 예상 교통비")

fig = px.bar(
    df,
    x="월",
    y="월간 예상 교통비",
    text="월간 예상 교통비",
    title="월별 교통비 비교"
)

fig.update_traces(
    texttemplate="%{text:,}원",
    textposition="outside",
    cliponaxis=False
)

fig.update_layout(
    yaxis_title="예상 교통비 (원)",
    xaxis_title="월",
    yaxis_rangemode="tozero"
)

st.plotly_chart(fig, use_container_width=True)

# =====================================
# 공통: 평일 / 주말 그래프
# =====================================
st.subheader("평일과 주말 교통비 비교")

cost_df = df[
    ["월", "평일 교통비", "주말 교통비"]
].melt(
    id_vars="월",
    var_name="구분",
    value_name="교통비"
)

fig2 = px.bar(
    cost_df,
    x="월",
    y="교통비",
    color="구분",
    barmode="group",
    title="월별 평일·주말 교통비"
)

fig2.update_layout(
    yaxis_title="예상 교통비 (원)",
    yaxis_rangemode="tozero"
)

st.plotly_chart(fig2, use_container_width=True)

# =====================================
# 공통: 비용 비교표
# =====================================
st.subheader("월별 비용 상세")

display_df = df.copy()

money_columns = [
    "평일 교통비",
    "주말 교통비",
    "월간 예상 교통비"
]

for column in money_columns:
    display_df[column] = display_df[column].map(
        lambda x: f"{x:,}원"
    )

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

# =====================================
# 공통: 예산 분석
# =====================================
st.divider()
st.subheader("💳 월간 예산 분석")

average_cost = annual_cost / 12
remaining = budget - average_cost

c1, c2, c3 = st.columns(3)

c1.metric("월간 예산", f"{budget:,}원")
c2.metric("월평균 예상 교통비", f"{average_cost:,.0f}원")
c3.metric("평균 예산 잔액", f"{remaining:,.0f}원")

if budget > 0:

    usage = average_cost / budget

    st.write(f"월평균 예산 사용률: {usage * 100:.1f}%")
    st.progress(min(usage, 1.0))

    if average_cost > budget:
        st.warning("월평균 예상 교통비가 예산을 초과합니다.")
    else:
        st.success("월평균 예상 교통비가 예산 이내입니다.")

else:
    st.info("예산을 0원보다 크게 설정하면 예산 사용률을 확인할 수 있습니다.")

# =====================================
# CSV 다운로드
# =====================================
st.divider()
st.subheader("📥 분석 결과 다운로드")

csv_data = df.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="월별 교통비 분석 CSV 다운로드",
    data=csv_data,
    file_name="schoolmove_analysis.csv",
    mime="text/csv"
)

st.caption(
    "계산 결과는 입력한 요금과 설정을 바탕으로 한 예상치입니다. "
    "월별 분석은 평일·주말·공휴일을 기준으로 하며, "
    "학교 방학, 재량휴업일, 결석, 실제 환승 할인 등은 "
    "자동 반영되지 않습니다."
)
