import streamlit as st
import pandas as pd
import requests
import time
import json
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo


# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(
    page_title="카카오 광고 성과 대시보드",
    page_icon="📊",
    layout="wide"
)

KST = ZoneInfo("Asia/Seoul")

KAKAO_BASE_URL = "https://apis.moment.kakao.com/openapi/v4"


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .main {
        background-color: #f7f7f7;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 1px 5px rgba(0,0,0,0.06);
        border: 1px solid #eeeeee;
        min-height: 120px;
    }

    .kpi-title {
        color: #777777;
        font-size: 14px;
        margin-bottom: 8px;
    }

    .kpi-value {
        color: #222222;
        font-size: 28px;
        font-weight: 700;
    }

    .kpi-sub {
        color: #999999;
        font-size: 12px;
        margin-top: 5px;
    }

    .status-ok {
        padding: 10px 14px;
        background: #eaf7ee;
        border: 1px solid #b7e4c7;
        border-radius: 8px;
        color: #1b6e36;
    }

    .status-error {
        padding: 10px 14px;
        background: #fff0f0;
        border: 1px solid #f0b8b8;
        border-radius: 8px;
        color: #a32929;
    }

    .status-info {
        padding: 10px 14px;
        background: #eef5ff;
        border: 1px solid #bfd5f5;
        border-radius: 8px;
        color: #245a9b;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 세션 상태
# ============================================================

if "kakao_logs" not in st.session_state:
    st.session_state.kakao_logs = []

if "kakao_raw" not in st.session_state:
    st.session_state.kakao_raw = []

if "kakao_errors" not in st.session_state:
    st.session_state.kakao_errors = []


# ============================================================
# 광고주 설정
# ============================================================

ADVERTISERS = {
    "리만": {
        "ad_account_id": "995724"
    },
    "광고주 2": {
        "ad_account_id": "558725"
    },
    "광고주 3": {
        "ad_account_id": "987505"
    }
}


# ============================================================
# Secrets
# ============================================================

try:
    KAKAO_BUSINESS_TOKEN = st.secrets["KAKAO_BUSINESS_TOKEN"]
except Exception:
    KAKAO_BUSINESS_TOKEN = ""


# ============================================================
# 유틸
# ============================================================

def now_kst():
    return datetime.now(KST)


def today_kst():
    return now_kst().date()


def money(value):
    try:
        return f"{float(value):,.0f}원"
    except Exception:
        return "0원"


def number(value):
    try:
        return f"{float(value):,.0f}"
    except Exception:
        return "0"


def percent(value):
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "0.00%"


def safe_float(value, default=0.0):
    if value is None:
        return default

    if isinstance(value, bool):
        return float(value)

    try:
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    if value is None:
        return default

    try:
        return int(float(value))
    except Exception:
        return default


def clear_debug():
    st.session_state.kakao_logs = []
    st.session_state.kakao_raw = []
    st.session_state.kakao_errors = []


# ============================================================
# Kakao Header
# ============================================================

def get_kakao_headers(ad_account_id):
    return {
        "Authorization": f"Bearer {KAKAO_BUSINESS_TOKEN}",
        "adAccountId": str(ad_account_id),
        "Accept": "application/json"
    }


# ============================================================
# 공통 API GET
# ============================================================

def kakao_get(
    endpoint,
    ad_account_id,
    params=None,
    label=""
):
    url = f"{KAKAO_BASE_URL}{endpoint}"

    headers = get_kakao_headers(ad_account_id)

    log_item = {
        "시간": now_kst().strftime("%Y-%m-%d %H:%M:%S"),
        "구분": label,
        "URL": url,
        "파라미터": params
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        log_item["HTTP"] = response.status_code

        try:
            data = response.json()
        except Exception:
            data = {
                "raw_text": response.text
            }

        log_item["응답"] = data

        st.session_state.kakao_logs.append(log_item)

        st.session_state.kakao_raw.append({
            "label": label,
            "url": response.url,
            "status": response.status_code,
            "response": data
        })

        if response.status_code != 200:
            st.session_state.kakao_errors.append({
                "label": label,
                "status": response.status_code,
                "response": data
            })

            return None

        return data

    except Exception as e:
        log_item["HTTP"] = "REQUEST ERROR"
        log_item["응답"] = str(e)

        st.session_state.kakao_logs.append(log_item)

        st.session_state.kakao_errors.append({
            "label": label,
            "status": "REQUEST ERROR",
            "response": str(e)
        })

        return None


# ============================================================
# 캠페인 목록
# ============================================================

def fetch_campaigns(ad_account_id):

    data = kakao_get(
        "/campaigns",
        ad_account_id,
        params={},
        label="캠페인 목록"
    )

    if not data:
        return []

    campaigns = data.get("data", [])

    if not isinstance(campaigns, list):
        return []

    result = []

    for item in campaigns:

        if not isinstance(item, dict):
            continue

        campaign_id = (
            item.get("id")
            or item.get("campaignId")
            or item.get("campaign_id")
        )

        campaign_name = (
            item.get("name")
            or item.get("campaignName")
            or item.get("campaign_name")
            or f"캠페인 {campaign_id}"
        )

        if campaign_id is None:
            continue

        result.append({
            "campaign_id": str(campaign_id),
            "campaign_name": str(campaign_name),
            "raw": item
        })

    return result


# ============================================================
# 광고계정 보고서
#
# 가장 중요한 부분
#
# /adAccounts/report
#
# 광고계정 전체 데이터를 가져오기 때문에
# 광고그룹별 ID를 하나하나 넘기는 방식보다 안정적임.
# ============================================================

def fetch_account_report(
    ad_account_id,
    start_date=None,
    end_date=None,
    today=False
):

    params = [
        ("timeUnit", "DAY"),
        ("metricsGroup", "BASIC"),
        ("metricsGroup", "PIXEL_SDK_CONVERSION")
    ]

    if today:
        params.append(("datePreset", "TODAY"))
        label = "광고계정 오늘 실시간 보고서"

    else:
        params.append(
            ("start", start_date.strftime("%Y%m%d"))
        )

        params.append(
            ("end", end_date.strftime("%Y%m%d"))
        )

        label = (
            f"광고계정 기간 보고서 "
            f"{start_date} ~ {end_date}"
        )

    return kakao_get(
        "/adAccounts/report",
        ad_account_id,
        params=params,
        label=label
    )


# ============================================================
# 캠페인 보고서
#
# 캠페인별 서비스신청 수량 확인용
# ============================================================

def fetch_campaign_report(
    ad_account_id,
    campaign_ids,
    start_date=None,
    end_date=None,
    today=False
):

    if not campaign_ids:
        return None

    params = [
        ("timeUnit", "DAY"),
        ("level", "CAMPAIGN"),
        ("metricsGroup", "BASIC"),
        ("metricsGroup", "PIXEL_SDK_CONVERSION")
    ]

    # 공식 API는 캠페인 ID 최대 5개
    for cid in campaign_ids:
        params.append(("campaignId", str(cid)))

    if today:
        params.append(("datePreset", "TODAY"))
        label = "캠페인 오늘 실시간 보고서"

    else:
        params.append(
            ("start", start_date.strftime("%Y%m%d"))
        )

        params.append(
            ("end", end_date.strftime("%Y%m%d"))
        )

        label = (
            f"캠페인 기간 보고서 "
            f"{start_date} ~ {end_date}"
        )

    return kakao_get(
        "/campaigns/report",
        ad_account_id,
        params=params,
        label=label
    )


# ============================================================
# API data → DataFrame
# ============================================================

def report_to_dataframe(
    report,
    report_type="account"
):

    columns = [
        "date",
        "campaign_id",
        "campaign_name",
        "cost",
        "imp",
        "click",
        "ctr",
        "signup_1d",
        "signup_7d"
    ]

    if not report:
        return pd.DataFrame(columns=columns)

    data = report.get("data", [])

    if not isinstance(data, list):
        return pd.DataFrame(columns=columns)

    rows = []

    for item in data:

        if not isinstance(item, dict):
            continue

        dimensions = item.get("dimensions") or {}
        metrics = item.get("metrics") or {}

        if not isinstance(dimensions, dict):
            dimensions = {}

        if not isinstance(metrics, dict):
            metrics = {}

        # 빈 데이터
        if not dimensions and not metrics:
            continue

        start_value = item.get("start")

        if start_value:
            try:
                report_date = pd.to_datetime(
                    start_value
                ).date()
            except Exception:
                report_date = None
        else:
            report_date = None

        campaign_id = (
            dimensions.get("campaign_id")
            or dimensions.get("campaignId")
        )

        # 기본 지표
        cost = safe_float(
            metrics.get("cost")
        )

        imp = safe_int(
            metrics.get("imp")
        )

        click = safe_int(
            metrics.get("click")
        )

        ctr = safe_float(
            metrics.get("ctr")
        )

        # 전환 지표
        signup_1d = safe_int(
            metrics.get("conv_signup_1d")
        )

        signup_7d = safe_int(
            metrics.get("conv_signup_7d")
        )

        rows.append({
            "date": report_date,
            "campaign_id": (
                str(campaign_id)
                if campaign_id is not None
                else ""
            ),
            "campaign_name": "",
            "cost": cost,
            "imp": imp,
            "click": click,
            "ctr": ctr,
            "signup_1d": signup_1d,
            "signup_7d": signup_7d
        })

    if not rows:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(rows)

    # 반드시 dtype 명시
    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["cost"] = pd.to_numeric(
        df["cost"],
        errors="coerce"
    ).fillna(0.0).astype(float)

    df["imp"] = pd.to_numeric(
        df["imp"],
        errors="coerce"
    ).fillna(0).astype(int)

    df["click"] = pd.to_numeric(
        df["click"],
        errors="coerce"
    ).fillna(0).astype(int)

    df["ctr"] = pd.to_numeric(
        df["ctr"],
        errors="coerce"
    ).fillna(0.0).astype(float)

    df["signup_1d"] = pd.to_numeric(
        df["signup_1d"],
        errors="coerce"
    ).fillna(0).astype(int)

    df["signup_7d"] = pd.to_numeric(
        df["signup_7d"],
        errors="coerce"
    ).fillna(0).astype(int)

    return df


# ============================================================
# 캠페인명 연결
# ============================================================

def attach_campaign_names(
    df,
    campaigns
):

    if df.empty:
        return df

    campaign_map = {
        str(x["campaign_id"]): x["campaign_name"]
        for x in campaigns
    }

    df = df.copy()

    df["campaign_name"] = (
        df["campaign_id"]
        .astype(str)
        .map(campaign_map)
        .fillna("")
    )

    return df


# ============================================================
# 오늘 데이터가 기간 데이터와 중복될 경우 제거
# ============================================================

def remove_today_duplicates(
    df,
    current_date
):

    if df.empty:
        return df

    df = df.copy()

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    return df[
        df["date"].dt.date != current_date
    ].copy()


# ============================================================
# 전체 날짜 만들기
#
# LossySetitemError 방지
# ============================================================

def make_full_date_dataframe(
    raw_df,
    selected_year,
    selected_month,
    today
):

    start = date(
        selected_year,
        selected_month,
        1
    )

    if selected_month == 12:
        next_month = date(
            selected_year + 1,
            1,
            1
        )
    else:
        next_month = date(
            selected_year,
            selected_month + 1,
            1
        )

    last_day = next_month - timedelta(days=1)

    # 현재 달이면 오늘까지만
    if (
        selected_year == today.year
        and selected_month == today.month
    ):
        end = today
    else:
        end = last_day

    date_range = pd.date_range(
        start=start,
        end=end,
        freq="D"
    )

    calendar_df = pd.DataFrame({
        "date": date_range
    })

    # 타입을 처음부터 정확히 설정
    calendar_df["cost"] = 0.0
    calendar_df["imp"] = 0
    calendar_df["click"] = 0
    calendar_df["signup_1d"] = 0
    calendar_df["signup_7d"] = 0

    if raw_df is None or raw_df.empty:

        calendar_df["ctr"] = 0.0

        return calendar_df

    work = raw_df.copy()

    work["date"] = pd.to_datetime(
        work["date"],
        errors="coerce"
    )

    work = work.dropna(
        subset=["date"]
    )

    # 해당 월만
    work = work[
        (
            work["date"].dt.year
            == selected_year
        )
        &
        (
            work["date"].dt.month
            == selected_month
        )
    ]

    if work.empty:

        calendar_df["ctr"] = 0.0

        return calendar_df

    # 날짜별 합계
    grouped = (
        work
        .groupby("date", as_index=False)
        .agg({
            "cost": "sum",
            "imp": "sum",
            "click": "sum",
            "signup_1d": "sum",
            "signup_7d": "sum"
        })
    )

    # 합친다
    result = calendar_df.merge(
        grouped,
        on="date",
        how="left",
        suffixes=("", "_api")
    )

    # API 데이터가 있는 경우만 교체
    result["cost"] = (
        pd.to_numeric(
            result["cost_api"],
            errors="coerce"
        )
        .fillna(0.0)
        .astype(float)
    )

    result["imp"] = (
        pd.to_numeric(
            result["imp_api"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    result["click"] = (
        pd.to_numeric(
            result["click_api"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    result["signup_1d"] = (
        pd.to_numeric(
            result["signup_1d_api"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    result["signup_7d"] = (
        pd.to_numeric(
            result["signup_7d_api"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    # CTR은 직접 계산
    result["ctr"] = 0.0

    valid_imp = result["imp"] > 0

    result.loc[
        valid_imp,
        "ctr"
    ] = (
        result.loc[
            valid_imp,
            "click"
        ].astype(float)
        /
        result.loc[
            valid_imp,
            "imp"
        ].astype(float)
        * 100.0
    )

    result["ctr"] = (
        pd.to_numeric(
            result["ctr"],
            errors="coerce"
        )
        .fillna(0.0)
        .astype(float)
    )

    result = result[
        [
            "date",
            "cost",
            "imp",
            "click",
            "ctr",
            "signup_1d",
            "signup_7d"
        ]
    ]

    return result


# ============================================================
# 캠페인별 집계
# ============================================================

def make_campaign_dataframe(
    raw_df,
    campaigns
):

    if raw_df is None or raw_df.empty:
        return pd.DataFrame()

    df = raw_df.copy()

    if "campaign_id" not in df.columns:
        return pd.DataFrame()

    df["campaign_id"] = (
        df["campaign_id"]
        .astype(str)
    )

    df = (
        df
        .groupby(
            [
                "campaign_id",
                "campaign_name"
            ],
            as_index=False
        )
        .agg({
            "cost": "sum",
            "imp": "sum",
            "click": "sum",
            "signup_1d": "sum",
            "signup_7d": "sum"
        })
    )

    df["ctr"] = 0.0

    valid = df["imp"] > 0

    df.loc[
        valid,
        "ctr"
    ] = (
        df.loc[
            valid,
            "click"
        ].astype(float)
        /
        df.loc[
            valid,
            "imp"
        ].astype(float)
        * 100
    )

    return df


# ============================================================
# 전체 데이터 수집
# ============================================================

def load_kakao_data(
    ad_account_id,
    selected_year,
    selected_month
):

    clear_debug()

    if not KAKAO_BUSINESS_TOKEN:
        return {
            "success": False,
            "message": "KAKAO_BUSINESS_TOKEN이 없습니다.",
            "daily": pd.DataFrame(),
            "campaign": pd.DataFrame(),
            "campaigns": [],
            "account_raw": None,
            "today_raw": None
        }

    today = today_kst()

    # --------------------------------------------------------
    # 캠페인 목록
    # --------------------------------------------------------

    campaigns = fetch_campaigns(
        ad_account_id
    )

    # --------------------------------------------------------
    # 선택한 월 날짜
    # --------------------------------------------------------

    month_start = date(
        selected_year,
        selected_month,
        1
    )

    if selected_month == 12:
        next_month = date(
            selected_year + 1,
            1,
            1
        )
    else:
        next_month = date(
            selected_year,
            selected_month + 1,
            1
        )

    month_end = next_month - timedelta(days=1)

    # --------------------------------------------------------
    # 과거 데이터
    #
    # 오늘은 API start/end로 조회할 수 없으므로
    # 어제까지 조회
    # --------------------------------------------------------

    historical_df = pd.DataFrame()

    historical_end = min(
        month_end,
        today - timedelta(days=1)
    )

    if month_start <= historical_end:

        account_raw = fetch_account_report(
            ad_account_id,
            start_date=month_start,
            end_date=historical_end,
            today=False
        )

        historical_df = report_to_dataframe(
            account_raw,
            report_type="account"
        )

    else:
        account_raw = None

    # --------------------------------------------------------
    # 오늘 데이터
    #
    # 핵심
    #
    # datePreset=TODAY
    # --------------------------------------------------------

    today_df = pd.DataFrame()

    today_raw = None

    if (
        selected_year == today.year
        and selected_month == today.month
    ):

        # API 요청 제한 때문에 잠깐 대기
        time.sleep(1.2)

        today_raw = fetch_account_report(
            ad_account_id,
            today=True
        )

        today_df = report_to_dataframe(
            today_raw,
            report_type="account"
        )

    # --------------------------------------------------------
    # 합치기
    # --------------------------------------------------------

    frames = []

    if (
        historical_df is not None
        and not historical_df.empty
    ):
        frames.append(historical_df)

    if (
        today_df is not None
        and not today_df.empty
    ):
        frames.append(today_df)

    if frames:
        account_df = pd.concat(
            frames,
            ignore_index=True
        )
    else:
        account_df = pd.DataFrame(
            columns=[
                "date",
                "campaign_id",
                "campaign_name",
                "cost",
                "imp",
                "click",
                "ctr",
                "signup_1d",
                "signup_7d"
            ]
        )

    # --------------------------------------------------------
    # 전체 날짜
    # --------------------------------------------------------

    daily_df = make_full_date_dataframe(
        account_df,
        selected_year,
        selected_month,
        today
    )

    # --------------------------------------------------------
    # 캠페인 보고서
    #
    # 캠페인별 데이터를 별도로 조회
    # --------------------------------------------------------

    campaign_df_list = []

    campaign_ids = [
        str(x["campaign_id"])
        for x in campaigns
    ]

    # 캠페인 API는 최대 5개씩
    chunks = [
        campaign_ids[i:i + 5]
        for i in range(
            0,
            len(campaign_ids),
            5
        )
    ]

    for index, chunk in enumerate(chunks):

        if index > 0:
            # 캠페인 보고서는 5초 제한
            time.sleep(5.2)

        # 과거
        if month_start <= historical_end:

            c_raw = fetch_campaign_report(
                ad_account_id,
                chunk,
                start_date=month_start,
                end_date=historical_end,
                today=False
            )

            c_df = report_to_dataframe(
                c_raw,
                report_type="campaign"
            )

            if not c_df.empty:
                campaign_df_list.append(
                    c_df
                )

        # 오늘
        if (
            selected_year == today.year
            and selected_month == today.month
        ):

            time.sleep(5.2)

            c_today_raw = fetch_campaign_report(
                ad_account_id,
                chunk,
                today=True
            )

            c_today_df = report_to_dataframe(
                c_today_raw,
                report_type="campaign"
            )

            if not c_today_df.empty:
                campaign_df_list.append(
                    c_today_df
                )

    if campaign_df_list:

        campaign_raw_df = pd.concat(
            campaign_df_list,
            ignore_index=True
        )

        campaign_raw_df = attach_campaign_names(
            campaign_raw_df,
            campaigns
        )

        campaign_df = make_campaign_dataframe(
            campaign_raw_df,
            campaigns
        )

    else:
        campaign_df = pd.DataFrame()

    return {
        "success": True,
        "message": "API 수신 완료",
        "daily": daily_df,
        "campaign": campaign_df,
        "campaigns": campaigns,
        "account_raw": account_raw,
        "today_raw": today_raw
    }


# ============================================================
# 사이드바
# ============================================================

with st.sidebar:

    st.markdown("## 📊 광고 성과 대시보드")

    advertiser_name = st.selectbox(
        "광고주",
        list(ADVERTISERS.keys())
    )

    ad_account_id = ADVERTISERS[
        advertiser_name
    ]["ad_account_id"]

    current_date = today_kst()

    year_options = list(
        range(
            current_date.year - 2,
            current_date.year + 1
        )
    )

    selected_year = st.selectbox(
        "연도",
        year_options,
        index=year_options.index(
            current_date.year
        )
    )

    selected_month = st.selectbox(
        "월",
        list(range(1, 13)),
        index=current_date.month - 1,
        format_func=lambda x: f"{x}월"
    )

    refresh = st.button(
        "🔄 데이터 새로고침",
        use_container_width=True
    )


# ============================================================
# 새로고침
# ============================================================

if refresh:
    st.cache_data.clear()
    st.rerun()


# ============================================================
# 제목
# ============================================================

st.title(
    f"[카카오] {advertiser_name} "
    f"({ad_account_id}) 성과 대시보드"
)

st.caption(
    f"조회기간: {selected_year}년 {selected_month}월"
)


# ============================================================
# 토큰 확인
# ============================================================

if not KAKAO_BUSINESS_TOKEN:

    st.error(
        """
        카카오 비즈니스 토큰이 없습니다.

        Streamlit Secrets에 아래와 같이 실제 토큰을 입력하세요.

        `KAKAO_BUSINESS_TOKEN = "실제 비즈니스 토큰"`

        토큰 문자열 자체를 코드에 직접 넣지는 마세요.
        """
    )

    st.stop()


# ============================================================
# 데이터 수신
# ============================================================

with st.spinner(
    "카카오 광고 데이터를 불러오는 중입니다..."
):

    result = load_kakao_data(
        ad_account_id,
        selected_year,
        selected_month
    )


# ============================================================
# API 상태
# ============================================================

if result["success"]:

    st.markdown(
        '<div class="status-ok">'
        '● 카카오 API 연결 및 수신 성공'
        '</div>',
        unsafe_allow_html=True
    )

else:

    st.markdown(
        '<div class="status-error">'
        '● 카카오 API 데이터 수신 실패'
        '</div>',
        unsafe_allow_html=True
    )

    st.error(
        result.get(
            "message",
            "알 수 없는 오류"
        )
    )

    st.stop()


daily_df = result["daily"]
campaign_df = result["campaign"]
campaigns = result["campaigns"]


# ============================================================
# KPI
# ============================================================

if daily_df.empty:

    total_cost = 0
    total_imp = 0
    total_click = 0
    total_signup = 0

else:

    total_cost = daily_df["cost"].sum()
    total_imp = daily_df["imp"].sum()
    total_click = daily_df["click"].sum()
    total_signup = daily_df["signup_7d"].sum()


if total_imp > 0:

    total_ctr = (
        total_click
        / total_imp
        * 100
    )

else:

    total_ctr = 0


if total_signup > 0:

    cpa = (
        total_cost
        / total_signup
    )

else:

    cpa = 0


st.markdown("### 📌 주요 성과")

k1, k2, k3, k4, k5 = st.columns(5)

with k1:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">광고비</div>
            <div class="kpi-value">{money(total_cost)}</div>
            <div class="kpi-sub">선택 기간</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k2:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">노출</div>
            <div class="kpi-value">{number(total_imp)}</div>
            <div class="kpi-sub">Impression</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k3:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">클릭</div>
            <div class="kpi-value">{number(total_click)}</div>
            <div class="kpi-sub">Click</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k4:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">서비스 신청 (7일)</div>
            <div class="kpi-value">{number(total_signup)}</div>
            <div class="kpi-sub">conv_signup_7d</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k5:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">CPA</div>
            <div class="kpi-value">{money(cpa)}</div>
            <div class="kpi-sub">광고비 ÷ 서비스 신청</div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.write("")


# ============================================================
# 오늘 실시간
# ============================================================

if (
    selected_year == current_date.year
    and selected_month == current_date.month
):

    today_row = daily_df[
        daily_df["date"].dt.date
        == current_date
    ]

    if not today_row.empty:

        today_cost = today_row["cost"].sum()
        today_imp = today_row["imp"].sum()
        today_click = today_row["click"].sum()
        today_signup = today_row[
            "signup_7d"
        ].sum()

    else:

        today_cost = 0
        today_imp = 0
        today_click = 0
        today_signup = 0

    if today_imp > 0:

        today_ctr = (
            today_click
            / today_imp
            * 100
        )

    else:

        today_ctr = 0

    st.markdown("### 🔴 오늘 실시간 데이터")

    t1, t2, t3, t4, t5 = st.columns(5)

    with t1:
        st.metric(
            "오늘 광고비",
            money(today_cost)
        )

    with t2:
        st.metric(
            "오늘 노출",
            number(today_imp)
        )

    with t3:
        st.metric(
            "오늘 클릭",
            number(today_click)
        )

    with t4:
        st.metric(
            "오늘 CTR",
            percent(today_ctr)
        )

    with t5:
        st.metric(
            "오늘 서비스 신청",
            number(today_signup)
        )

    st.caption(
        "※ 오늘 데이터는 카카오 API의 datePreset=TODAY 기준입니다. "
        "카카오 보고서는 당일 진행 중인 데이터이므로 이후 값이 변동될 수 있습니다."
    )


# ============================================================
# 일자별
# ============================================================

st.markdown("### 📅 일자별 성과")

if daily_df.empty:

    st.info(
        "선택한 기간에 API 데이터가 없습니다."
    )

else:

    display_daily = daily_df.copy()

    display_daily["일자"] = (
        display_daily["date"]
        .dt.strftime("%Y-%m-%d")
    )

    display_daily["광고비"] = (
        display_daily["cost"]
        .apply(money)
    )

    display_daily["노출"] = (
        display_daily["imp"]
        .apply(number)
    )

    display_daily["클릭"] = (
        display_daily["click"]
        .apply(number)
    )

    display_daily["CTR"] = (
        display_daily["ctr"]
        .apply(percent)
    )

    display_daily["서비스 신청(7일)"] = (
        display_daily["signup_7d"]
        .apply(number)
    )

    display_daily = display_daily[
        [
            "일자",
            "광고비",
            "노출",
            "클릭",
            "CTR",
            "서비스 신청(7일)"
        ]
    ]

    st.dataframe(
        display_daily,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 캠페인별
# ============================================================

st.markdown("### 📢 캠페인별 성과")

if campaign_df.empty:

    st.info(
        "캠페인별 보고서 데이터가 없습니다."
    )

else:

    display_campaign = campaign_df.copy()

    display_campaign["광고비"] = (
        display_campaign["cost"]
        .apply(money)
    )

    display_campaign["노출"] = (
        display_campaign["imp"]
        .apply(number)
    )

    display_campaign["클릭"] = (
        display_campaign["click"]
        .apply(number)
    )

    display_campaign["CTR"] = (
        display_campaign["ctr"]
        .apply(percent)
    )

    display_campaign["서비스 신청(1일)"] = (
        display_campaign["signup_1d"]
        .apply(number)
    )

    display_campaign["서비스 신청(7일)"] = (
        display_campaign["signup_7d"]
        .apply(number)
    )

    display_campaign = display_campaign[
        [
            "campaign_name",
            "광고비",
            "노출",
            "클릭",
            "CTR",
            "서비스 신청(1일)",
            "서비스 신청(7일)"
        ]
    ]

    display_campaign = display_campaign.rename(
        columns={
            "campaign_name": "캠페인"
        }
    )

    st.dataframe(
        display_campaign,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# API 데이터 확인
# ============================================================

st.markdown("### 🔎 API 데이터 확인")

with st.expander(
    "API에서 실제로 받은 데이터 확인",
    expanded=False
):

    st.write(
        f"캠페인 수: **{len(campaigns)}개**"
    )

    if campaigns:

        campaign_list_df = pd.DataFrame([
            {
                "campaign_id": x["campaign_id"],
                "campaign_name": x["campaign_name"]
            }
            for x in campaigns
        ])

        st.dataframe(
            campaign_list_df,
            use_container_width=True,
            hide_index=True
        )

    st.write(
        f"일자별 데이터 행 수: **{len(daily_df)}**"
    )

    st.write(
        f"캠페인 데이터 행 수: **{len(campaign_df)}**"
    )


# ============================================================
# API 원문 응답
# ============================================================

with st.expander(
    "🧪 카카오 API 원문 응답 보기",
    expanded=False
):

    if not st.session_state.kakao_raw:

        st.warning(
            "API 원문 응답이 없습니다."
        )

    else:

        for i, item in enumerate(
            st.session_state.kakao_raw,
            start=1
        ):

            st.markdown(
                f"#### {i}. {item['label']}"
            )

            st.write(
                f"HTTP Status: `{item['status']}`"
            )

            st.code(
                json.dumps(
                    item["response"],
                    ensure_ascii=False,
                    indent=2
                ),
                language="json"
            )


# ============================================================
# API 요청 기록
# ============================================================

with st.expander(
    "📡 API 요청 기록",
    expanded=False
):

    if not st.session_state.kakao_logs:

        st.info(
            "API 요청 기록이 없습니다."
        )

    else:

        for log in st.session_state.kakao_logs:

            st.markdown(
                f"**{log['시간']} / {log['구분']}**"
            )

            st.write(
                f"HTTP: `{log.get('HTTP')}`"
            )

            st.code(
                str(log.get("URL"))
            )

            st.json(
                log.get("파라미터")
            )


# ============================================================
# API 오류
# ============================================================

if st.session_state.kakao_errors:

    with st.expander(
        "⚠️ API 오류 상세",
        expanded=True
    ):

        for error in st.session_state.kakao_errors:

            st.error(
                f"{error['label']} "
                f"/ HTTP {error['status']}"
            )

            st.code(
                json.dumps(
                    error["response"],
                    ensure_ascii=False,
                    indent=2
                )
            )


# ============================================================
# 전환 기준
# ============================================================

with st.expander(
    "ℹ️ 서비스 신청 집계 기준",
    expanded=False
):

    st.markdown(
        """
        ### 서비스 신청 수량

        카카오모먼트 API의

        **`conv_signup_7d`**

        지표를 사용합니다.

        즉, 카카오 광고 관리자에서 표시되는

        **서비스 신청 (7일)**

        값을 기준으로 집계합니다.

        ### 주의사항

        서비스 신청(7일)은 광고 클릭 이후 최대 7일의
        어트리뷰션 기간이 적용되기 때문에 과거 날짜의
        전환수가 이후 변경될 수 있습니다.

        따라서 광고비/노출/클릭과 달리
        서비스 신청 수량은 하루가 지난 뒤에도
        숫자가 증가할 수 있습니다.
        """
    )


# ============================================================
# AI 진단
# ============================================================

st.markdown("### 🤖 광고 성과 간단 진단")

if daily_df.empty:

    st.info(
        "진단할 데이터가 없습니다."
    )

else:

    max_cost_row = daily_df.loc[
        daily_df["cost"].idxmax()
    ]

    max_click_row = daily_df.loc[
        daily_df["click"].idxmax()
    ]

    max_signup_row = daily_df.loc[
        daily_df["signup_7d"].idxmax()
    ]

    diagnosis = []

    if total_signup > 0:

        diagnosis.append(
            f"선택 기간 서비스 신청(7일)은 "
            f"총 {total_signup:,.0f}건입니다."
        )

        diagnosis.append(
            f"평균 서비스 신청당 광고비는 "
            f"{total_cost / total_signup:,.0f}원입니다."
        )

    else:

        diagnosis.append(
            "선택 기간 서비스 신청(7일)이 "
            "현재 0건으로 집계되었습니다."
        )

    diagnosis.append(
        f"광고비가 가장 많이 발생한 날짜는 "
        f"{max_cost_row['date'].strftime('%Y-%m-%d')}이며 "
        f"{max_cost_row['cost']:,.0f}원입니다."
    )

    diagnosis.append(
        f"클릭이 가장 많았던 날짜는 "
        f"{max_click_row['date'].strftime('%Y-%m-%d')}이며 "
        f"{max_click_row['click']:,.0f}회입니다."
    )

    if max_signup_row["signup_7d"] > 0:

        diagnosis.append(
            f"서비스 신청이 가장 많았던 날짜는 "
            f"{max_signup_row['date'].strftime('%Y-%m-%d')}이며 "
            f"{max_signup_row['signup_7d']:,.0f}건입니다."
        )

    for item in diagnosis:

        st.write(
            "• " + item
        )