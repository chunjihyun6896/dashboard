import time
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st


# =========================================================
# 1. 페이지 설정
# =========================================================

st.set_page_config(
    page_title="광고 성과 대시보드",
    page_icon="📊",
    layout="wide",
)


# =========================================================
# 2. CSS
# =========================================================

st.markdown(
    """
    <style>
    .main {
        padding-top: 1rem;
    }

    h1 {
        font-weight: 800;
        letter-spacing: -1px;
    }

    h2, h3 {
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .kpi-card {
        background: #ffffff;
        border: 1px solid #e8ebef;
        border-radius: 12px;
        padding: 18px 20px;
        min-height: 125px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .kpi-title {
        font-size: 14px;
        color: #555;
        margin-bottom: 10px;
    }

    .kpi-value {
        font-size: 29px;
        font-weight: 700;
        color: #17233c;
        letter-spacing: -1px;
    }

    .kpi-sub {
        margin-top: 8px;
        font-size: 12px;
        color: #159957;
    }

    .api-live {
        display: inline-block;
        background: #e8f8ee;
        color: #159957;
        border-radius: 20px;
        padding: 4px 10px;
        font-size: 12px;
        font-weight: 600;
    }

    .api-info {
        display: inline-block;
        background: #f1f4f7;
        color: #667085;
        border-radius: 20px;
        padding: 4px 10px;
        font-size: 12px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 3. 카카오 설정
# =========================================================

KAKAO_BASE_URL = (
    "https://apis.moment.kakao.com/openapi/v4"
)


# Streamlit Secrets
try:
    KAKAO_BUSINESS_TOKEN = st.secrets[
        "KAKAO_BUSINESS_TOKEN"
    ]
except Exception:
    KAKAO_BUSINESS_TOKEN = ""


# =========================================================
# 4. 광고주
# =========================================================

KAKAO_ADVERTISERS = {
    "995724": "리만 (995724)",
    "558725": "asap-ad (558725)",
    "987505": "GHB (987505)",
}

NAVER_ADVERTISERS = {
    "2274356": "리만",
    "987505": "GHB",
    "1001864": "기타",
}

TOSS_ADVERTISERS = {
    "112233": "토스",
}

META_ADVERTISERS = {
    "998877": "Meta",
}


# =========================================================
# 5. 세션
# =========================================================

if "selected_channel" not in st.session_state:
    st.session_state.selected_channel = "카카오"

if "selected_advertiser" not in st.session_state:
    st.session_state.selected_advertiser = "995724"

if "kakao_debug" not in st.session_state:
    st.session_state.kakao_debug = []


# =========================================================
# 6. 공통 함수
# =========================================================

def safe_float(value):
    try:
        if value is None:
            return 0.0

        if isinstance(value, str):
            value = value.replace(",", "")

        return float(value)

    except Exception:
        return 0.0


def safe_int(value):
    try:
        if value is None:
            return 0

        if isinstance(value, str):
            value = value.replace(",", "")

        return int(float(value))

    except Exception:
        return 0


def format_won(value):
    return f"{safe_float(value):,.0f}원"


def format_number(value):
    return f"{safe_int(value):,}"


def format_percent(value):
    return f"{safe_float(value):.2f}%"


# =========================================================
# 7. 카카오 헤더
# =========================================================

def get_kakao_headers(ad_account_id):

    return {
        "Authorization": (
            f"Bearer {KAKAO_BUSINESS_TOKEN}"
        ),
        "adAccountId": str(ad_account_id),
        "Content-Type": "application/json",
    }


# =========================================================
# 8. 카카오 GET
# =========================================================

def kakao_get(
    endpoint,
    ad_account_id,
    params=None,
    timeout=30,
):

    if not KAKAO_BUSINESS_TOKEN:

        return {
            "ok": False,
            "status_code": 0,
            "response": {
                "code": -1,
                "message": (
                    "KAKAO_BUSINESS_TOKEN이 설정되지 않았습니다."
                ),
                "detail": (
                    "Streamlit Secrets에 "
                    "KAKAO_BUSINESS_TOKEN을 등록하세요."
                ),
            },
        }

    url = f"{KAKAO_BASE_URL}{endpoint}"

    try:

        response = requests.get(
            url,
            headers=get_kakao_headers(
                ad_account_id
            ),
            params=params,
            timeout=timeout,
        )

        try:
            body = response.json()
        except Exception:
            body = response.text

        return {
            "ok": response.ok,
            "status_code": response.status_code,
            "response": body,
        }

    except requests.RequestException as e:

        return {
            "ok": False,
            "status_code": 0,
            "response": {
                "code": -1,
                "message": "카카오 API 요청 오류",
                "detail": str(e),
            },
        }


# =========================================================
# 9. 캠페인 조회
# =========================================================

def fetch_kakao_campaigns(
    ad_account_id
):

    result = kakao_get(
        "/campaigns",
        ad_account_id,
    )

    if not result["ok"]:
        return [], result

    body = result["response"]

    if not isinstance(body, dict):
        return [], result

    data = body.get("data", [])

    if not isinstance(data, list):
        return [], result

    return data, None


# =========================================================
# 10. 광고그룹 조회
# =========================================================

def fetch_kakao_adgroups(
    ad_account_id,
    campaign_id,
):

    result = kakao_get(
        "/adGroups",
        ad_account_id,
        params={
            "campaignId": str(campaign_id)
        },
    )

    if not result["ok"]:
        return [], result

    body = result["response"]

    if not isinstance(body, dict):
        return [], result

    data = body.get("data", [])

    if not isinstance(data, list):
        return [], result

    return data, None


# =========================================================
# 11. 광고그룹 전체 수집
# =========================================================

def collect_kakao_adgroups(
    ad_account_id
):

    campaigns, error = (
        fetch_kakao_campaigns(
            ad_account_id
        )
    )

    if error:
        return [], [], error

    all_adgroups = []

    for campaign in campaigns:

        campaign_id = (
            campaign.get("id")
            or campaign.get("campaignId")
        )

        campaign_name = (
            campaign.get("name")
            or campaign.get("campaignName")
            or f"캠페인 {campaign_id}"
        )

        if not campaign_id:
            continue

        adgroups, error = (
            fetch_kakao_adgroups(
                ad_account_id,
                campaign_id,
            )
        )

        if error:
            return [], [], error

        for group in adgroups:

            group_id = (
                group.get("id")
                or group.get("adGroupId")
            )

            group_name = (
                group.get("name")
                or group.get("adGroupName")
                or f"광고그룹 {group_id}"
            )

            if not group_id:
                continue

            all_adgroups.append(
                {
                    "ad_group_id": str(
                        group_id
                    ),
                    "ad_group_name": group_name,
                    "campaign_id": str(
                        campaign_id
                    ),
                    "campaign_name": campaign_name,
                    "status": (
                        group.get(
                            "adGroupStatus"
                        )
                        or group.get(
                            "status"
                        )
                        or ""
                    ),
                }
            )

    return (
        all_adgroups,
        campaigns,
        None,
    )


# =========================================================
# 12. 광고그룹 보고서
# =========================================================

def fetch_kakao_report(
    ad_account_id,
    ad_group_ids,
    start=None,
    end=None,
    date_preset=None,
):

    if not ad_group_ids:
        return [], None

    all_data = []

    # 최대 40개
    chunks = [
        ad_group_ids[i:i + 40]
        for i in range(
            0,
            len(ad_group_ids),
            40,
        )
    ]

    for index, chunk in enumerate(
        chunks
    ):

        # 카카오 공식 예제의 Long[] 형태
        ad_group_string = ",".join(
            str(x)
            for x in chunk
        )

        # metricsGroup 복수 선택
        params = [
            (
                "adGroupId",
                ad_group_string,
            ),
            (
                "timeUnit",
                "DAY",
            ),
            (
                "level",
                "AD_GROUP",
            ),
            (
                "metricsGroup",
                "BASIC",
            ),
            (
                "metricsGroup",
                "PIXEL_SDK_CONVERSION",
            ),
        ]

        if date_preset:

            params.append(
                (
                    "datePreset",
                    date_preset,
                )
            )

        else:

            params.append(
                (
                    "start",
                    start,
                )
            )

            params.append(
                (
                    "end",
                    end,
                )
            )

        result = kakao_get(
            "/adGroups/report",
            ad_account_id,
            params=params,
        )

        # 디버그 기록
        st.session_state.kakao_debug.append(
            {
                "endpoint": (
                    "/adGroups/report"
                ),
                "params": params,
                "status_code": (
                    result["status_code"]
                ),
                "ok": result["ok"],
            }
        )

        if not result["ok"]:
            return [], result

        body = result["response"]

        if isinstance(body, dict):

            data = body.get(
                "data",
                []
            )

            if isinstance(
                data,
                list
            ):
                all_data.extend(
                    data
                )

        # 카카오 광고그룹 보고서
        # 요청 제한 대응
        if index < len(chunks) - 1:
            time.sleep(1.1)

    return all_data, None


# =========================================================
# 13. 월 날짜
# =========================================================

def get_month_dates(
    year,
    month,
):

    first_day = date(
        year,
        month,
        1,
    )

    if month == 12:

        next_month = date(
            year + 1,
            1,
            1,
        )

    else:

        next_month = date(
            year,
            month + 1,
            1,
        )

    last_day = (
        next_month
        - timedelta(days=1)
    )

    today = date.today()

    # 현재 월이면 오늘까지만
    if (
        year == today.year
        and month == today.month
    ):

        last_day = today

    dates = []

    current = first_day

    while current <= last_day:

        dates.append(current)

        current += timedelta(
            days=1
        )

    return dates


# =========================================================
# 14. 과거 조회 기간
# =========================================================

def get_historical_range(
    year,
    month,
):

    first_day = date(
        year,
        month,
        1,
    )

    today = date.today()

    # 현재 월
    if (
        year == today.year
        and month == today.month
    ):

        yesterday = (
            today
            - timedelta(days=1)
        )

        if yesterday < first_day:
            return None, None

        return (
            first_day,
            yesterday,
        )

    # 과거 월
    if month == 12:

        next_month = date(
            year + 1,
            1,
            1,
        )

    else:

        next_month = date(
            year,
            month + 1,
            1,
        )

    last_day = (
        next_month
        - timedelta(days=1)
    )

    return (
        first_day,
        last_day,
    )


# =========================================================
# 15. API 보고서 → DataFrame
# =========================================================

def report_to_dataframe(
    report_data,
    adgroup_meta,
):

    rows = []

    meta_map = {
        str(x["ad_group_id"]): x
        for x in adgroup_meta
    }

    for item in report_data:

        if not isinstance(
            item,
            dict
        ):
            continue

        dimensions = item.get(
            "dimensions",
            {},
        ) or {}

        metrics = item.get(
            "metrics",
            {},
        ) or {}

        ad_group_id = str(
            dimensions.get(
                "ad_group_id",
                "",
            )
        )

        if not ad_group_id:
            continue

        meta = meta_map.get(
            ad_group_id,
            {},
        )

        start_date = (
            item.get("start")
            or item.get("date")
            or ""
        )

        # -------------------------
        # BASIC
        # -------------------------

        cost = safe_float(
            metrics.get("cost")
        )

        imp = safe_int(
            metrics.get("imp")
        )

        click = safe_int(
            metrics.get("click")
        )

        # -------------------------
        # SERVICE SIGNUP
        # -------------------------

        signup_1d = safe_int(
            metrics.get(
                "conv_signup_1d"
            )
        )

        signup_7d = safe_int(
            metrics.get(
                "conv_signup_7d"
            )
        )

        # -------------------------
        # 기타 전환
        # -------------------------

        purchase_7d = safe_int(
            metrics.get(
                "conv_purchase_7d"
            )
        )

        purchase_amount_7d = (
            safe_float(
                metrics.get(
                    "conv_purchase_p_7d"
                )
            )
        )

        # -------------------------
        # ROAS
        # -------------------------

        roas_7d = safe_float(
            metrics.get(
                "conv_purchase_p_per_cost_7d"
            )
        )

        rows.append(
            {
                "date": start_date,
                "ad_group_id": ad_group_id,
                "campaign_id": meta.get(
                    "campaign_id",
                    "",
                ),
                "campaign_name": meta.get(
                    "campaign_name",
                    "",
                ),
                "ad_group_name": meta.get(
                    "ad_group_name",
                    "",
                ),
                "status": meta.get(
                    "status",
                    "",
                ),
                "cost": cost,
                "imp": imp,
                "click": click,
                "signup_1d": signup_1d,
                "signup_7d": signup_7d,
                "purchase_7d": purchase_7d,
                "purchase_amount_7d": (
                    purchase_amount_7d
                ),
                "roas_7d": roas_7d,
            }
        )

    return pd.DataFrame(rows)


# =========================================================
# 16. 일별 데이터 생성
# =========================================================

def make_daily_dataframe(
    year,
    month,
    report_df,
):

    dates = get_month_dates(
        year,
        month,
    )

    full_df = pd.DataFrame(
        {
            "date": [
                x.strftime(
                    "%Y-%m-%d"
                )
                for x in dates
            ]
        }
    )

    if (
        report_df is None
        or report_df.empty
    ):

        daily = pd.DataFrame(
            columns=[
                "date",
                "cost",
                "imp",
                "click",
                "signup_7d",
                "purchase_amount_7d",
            ]
        )

    else:

        daily = report_df.copy()

        # 날짜
        daily["date"] = (
            pd.to_datetime(
                daily["date"],
                errors="coerce",
            )
            .dt.strftime(
                "%Y-%m-%d"
            )
        )

        # 숫자형
        numeric_columns = [
            "cost",
            "imp",
            "click",
            "signup_7d",
            "purchase_amount_7d",
        ]

        for col in numeric_columns:

            if col not in daily.columns:
                daily[col] = 0.0

            daily[col] = pd.to_numeric(
                daily[col],
                errors="coerce",
            ).fillna(0.0)

        daily = (
            daily
            .groupby(
                "date",
                as_index=False,
            )
            .agg(
                {
                    "cost": "sum",
                    "imp": "sum",
                    "click": "sum",
                    "signup_7d": "sum",
                    "purchase_amount_7d": "sum",
                }
            )
        )

    # 전체 날짜와 병합
    result = full_df.merge(
        daily,
        on="date",
        how="left",
    )

    # 숫자형
    for col in [
        "cost",
        "imp",
        "click",
        "signup_7d",
        "purchase_amount_7d",
    ]:

        if col not in result.columns:
            result[col] = 0.0

        result[col] = pd.to_numeric(
            result[col],
            errors="coerce",
        ).fillna(0.0)

    # CTR
    result["ctr"] = 0.0

    for i in range(
        len(result)
    ):

        imp = float(
            result.at[i, "imp"]
        )

        click = float(
            result.at[i, "click"]
        )

        if imp > 0:

            result.at[i, "ctr"] = (
                click
                / imp
                * 100
            )

    # CPA
    result["cpa"] = 0.0

    for i in range(
        len(result)
    ):

        cost = float(
            result.at[i, "cost"]
        )

        signup = float(
            result.at[i, "signup_7d"]
        )

        if signup > 0:

            result.at[i, "cpa"] = (
                cost
                / signup
            )

    return result


# =========================================================
# 17. 광고그룹 데이터
# =========================================================

def make_group_dataframe(
    report_df,
    adgroup_meta,
):

    meta_df = pd.DataFrame(
        adgroup_meta
    )

    if meta_df.empty:
        return pd.DataFrame()

    if (
        report_df is None
        or report_df.empty
    ):

        group_df = pd.DataFrame(
            columns=[
                "ad_group_id",
                "cost",
                "imp",
                "click",
                "signup_7d",
                "purchase_amount_7d",
            ]
        )

    else:

        temp = report_df.copy()

        for col in [
            "cost",
            "imp",
            "click",
            "signup_7d",
            "purchase_amount_7d",
        ]:

            temp[col] = pd.to_numeric(
                temp[col],
                errors="coerce",
            ).fillna(0.0)

        group_df = (
            temp
            .groupby(
                "ad_group_id",
                as_index=False,
            )
            .agg(
                {
                    "cost": "sum",
                    "imp": "sum",
                    "click": "sum",
                    "signup_7d": "sum",
                    "purchase_amount_7d": "sum",
                }
            )
        )

    result = meta_df.merge(
        group_df,
        on="ad_group_id",
        how="left",
    )

    for col in [
        "cost",
        "imp",
        "click",
        "signup_7d",
        "purchase_amount_7d",
    ]:

        if col not in result.columns:
            result[col] = 0.0

        result[col] = pd.to_numeric(
            result[col],
            errors="coerce",
        ).fillna(0.0)

    result["ctr"] = 0.0

    for i in range(
        len(result)
    ):

        imp = float(
            result.at[i, "imp"]
        )

        click = float(
            result.at[i, "click"]
        )

        if imp > 0:

            result.at[i, "ctr"] = (
                click
                / imp
                * 100
            )

    result["cpa"] = 0.0

    for i in range(
        len(result)
    ):

        cost = float(
            result.at[i, "cost"]
        )

        signup = float(
            result.at[i, "signup_7d"]
        )

        if signup > 0:

            result.at[i, "cpa"] = (
                cost
                / signup
            )

    return result


# =========================================================
# 18. 전체 카카오 데이터
# =========================================================

@st.cache_data(ttl=60)
def fetch_kakao_data(
    ad_account_id,
    year,
    month,
):

    # 디버그 초기화
    st.session_state.kakao_debug = []

    # -----------------------------------------------------
    # 광고그룹
    # -----------------------------------------------------

    (
        adgroup_meta,
        campaigns,
        error,
    ) = collect_kakao_adgroups(
        ad_account_id
    )

    if error:

        return {
            "success": False,
            "error": error,
        }

    if not adgroup_meta:

        return {
            "success": True,
            "adgroup_meta": [],
            "campaigns": campaigns,
            "report_df": pd.DataFrame(),
        }

    ad_group_ids = [
        x["ad_group_id"]
        for x in adgroup_meta
    ]

    # -----------------------------------------------------
    # 과거 날짜
    # -----------------------------------------------------

    (
        start_day,
        end_day,
    ) = get_historical_range(
        year,
        month,
    )

    historical_data = []

    if (
        start_day is not None
        and end_day is not None
    ):

        data, error = (
            fetch_kakao_report(
                ad_account_id,
                ad_group_ids,
                start=start_day.strftime(
                    "%Y%m%d"
                ),
                end=end_day.strftime(
                    "%Y%m%d"
                ),
            )
        )

        if error:

            return {
                "success": False,
                "error": error,
            }

        historical_data = data

        # 다음 TODAY 요청과 간격
        time.sleep(1.1)

    # -----------------------------------------------------
    # 오늘
    # -----------------------------------------------------

    today = date.today()

    today_data = []

    if (
        year == today.year
        and month == today.month
    ):

        data, error = (
            fetch_kakao_report(
                ad_account_id,
                ad_group_ids,
                date_preset="TODAY",
            )
        )

        if error:

            return {
                "success": False,
                "error": error,
            }

        today_data = data

    # -----------------------------------------------------
    # 합치기
    # -----------------------------------------------------

    all_data = (
        historical_data
        + today_data
    )

    report_df = report_to_dataframe(
        all_data,
        adgroup_meta,
    )

    return {
        "success": True,
        "adgroup_meta": adgroup_meta,
        "campaigns": campaigns,
        "report_df": report_df,
    }


# =========================================================
# 19. 사이드바
# =========================================================

with st.sidebar:

    st.markdown(
        "## 📌 광고 채널"
    )

    channel = st.selectbox(
        "채널 선택",
        [
            "카카오",
            "네이버",
            "토스",
            "Meta",
        ],
        index=0,
    )

    st.session_state.selected_channel = (
        channel
    )

    st.divider()

    if channel == "카카오":

        options = list(
            KAKAO_ADVERTISERS.keys()
        )

        current = (
            st.session_state
            .selected_advertiser
        )

        index = (
            options.index(current)
            if current in options
            else 0
        )

        advertiser_id = st.selectbox(
            "광고주 선택",
            options,
            format_func=lambda x:
                KAKAO_ADVERTISERS[x],
            index=index,
        )

        st.session_state.selected_advertiser = (
            advertiser_id
        )

    elif channel == "네이버":

        advertiser_id = st.selectbox(
            "광고주 선택",
            list(
                NAVER_ADVERTISERS.keys()
            ),
            format_func=lambda x:
                NAVER_ADVERTISERS[x],
        )

    elif channel == "토스":

        advertiser_id = st.selectbox(
            "광고주 선택",
            list(
                TOSS_ADVERTISERS.keys()
            ),
            format_func=lambda x:
                TOSS_ADVERTISERS[x],
        )

    else:

        advertiser_id = st.selectbox(
            "광고주 선택",
            list(
                META_ADVERTISERS.keys()
            ),
            format_func=lambda x:
                META_ADVERTISERS[x],
        )


# =========================================================
# 20. 다른 채널
# =========================================================

if channel != "카카오":

    st.title(
        f"📊 [{channel}] 성과 대시보드"
    )

    st.info(
        f"{channel} API 연동 영역입니다."
    )

    st.stop()


# =========================================================
# 21. 카카오 헤더
# =========================================================

ad_account_id = str(
    advertiser_id
)

advertiser_name = (
    KAKAO_ADVERTISERS.get(
        ad_account_id,
        ad_account_id,
    )
)

st.title(
    f"📊 [카카오] {advertiser_name} 성과 대시보드"
)

st.write(
    "선택하신 카카오 채널의 API 데이터를 조회합니다."
)


# =========================================================
# 22. 월 선택
# =========================================================

today = date.today()

month_options = []

for i in range(12):

    month_index = (
        today.year * 12
        + today.month
        - 1
        - i
    )

    y = month_index // 12
    m = month_index % 12 + 1

    month_options.append(
        (y, m)
    )

month_labels = [
    f"{y}년 {m}월"
    for y, m in month_options
]

col1, col2 = st.columns(
    [1, 1]
)

with col1:

    selected_month_label = (
        st.selectbox(
            "조회 월",
            month_labels,
            index=0,
        )
    )

selected_index = (
    month_labels.index(
        selected_month_label
    )
)

selected_year, selected_month = (
    month_options[selected_index]
)

with col2:

    st.write("")

    if st.button(
        "🔄 데이터 새로고침",
        use_container_width=True,
    ):

        st.cache_data.clear()

        st.session_state.kakao_debug = []

        st.rerun()


# =========================================================
# 23. 데이터 조회
# =========================================================

with st.spinner(
    "카카오 API 데이터를 조회하고 있습니다..."
):

    result = fetch_kakao_data(
        ad_account_id,
        selected_year,
        selected_month,
    )


# =========================================================
# 24. 오류
# =========================================================

if not result.get(
    "success",
    False,
):

    st.error(
        "카카오 API 조회에 실패했습니다."
    )

    st.code(
        str(
            result.get(
                "error"
            )
        ),
        language="json",
    )

    st.stop()


# =========================================================
# 25. 데이터
# =========================================================

report_df = result.get(
    "report_df",
    pd.DataFrame(),
)

adgroup_meta = result.get(
    "adgroup_meta",
    [],
)


# =========================================================
# 26. 일별
# =========================================================

daily_df = make_daily_dataframe(
    selected_year,
    selected_month,
    report_df,
)


# =========================================================
# 27. 그룹별
# =========================================================

group_df = make_group_dataframe(
    report_df,
    adgroup_meta,
)


# =========================================================
# 28. KPI
# =========================================================

total_cost = safe_float(
    daily_df["cost"].sum()
)

total_imp = safe_int(
    daily_df["imp"].sum()
)

total_click = safe_int(
    daily_df["click"].sum()
)

total_signup = safe_int(
    daily_df["signup_7d"].sum()
)

if total_imp > 0:

    total_ctr = (
        total_click
        / total_imp
        * 100
    )

else:

    total_ctr = 0.0

if total_signup > 0:

    total_cpa = (
        total_cost
        / total_signup
    )

else:

    total_cpa = 0.0


# =========================================================
# 29. 현재월 여부
# =========================================================

is_current_month = (
    selected_year == today.year
    and selected_month == today.month
)


# =========================================================
# 30. 제목
# =========================================================

st.divider()

st.subheader(
    f"📋 1. [카카오] {selected_month}월 일자별 상세 성과 리포트"
)


# =========================================================
# 31. KPI
# =========================================================

k1, k2, k3, k4, k5 = st.columns(
    5
)


with k1:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">
                [카카오] 총 광고비
            </div>
            <div class="kpi-value">
                {format_won(total_cost)}
            </div>
            <div class="kpi-sub">
                ↑ API 수신
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with k2:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">
                [카카오] 서비스 신청
            </div>
            <div class="kpi-value">
                {format_number(total_signup)}건
            </div>
            <div class="kpi-sub">
                ↑ 서비스 신청 7일
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with k3:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">
                [카카오] 전환당 비용
            </div>
            <div class="kpi-value">
                {format_won(total_cpa)}
            </div>
            <div class="kpi-sub">
                ↑ 광고비 ÷ 서비스 신청
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with k4:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">
                [카카오] CTR
            </div>
            <div class="kpi-value">
                {format_percent(total_ctr)}
            </div>
            <div class="kpi-sub">
                ↑ API 수신
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with k5:

    st.markdown(
        """
        <div class="kpi-card">
            <div class="kpi-title">
                [카카오] ROAS
            </div>
            <div class="kpi-value">
                매출 미연동
            </div>
            <div class="kpi-sub">
                ↑ 매출 데이터 연동 필요
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 32. 실시간 표시
# =========================================================

if is_current_month:

    st.markdown(
        """
        <span class="api-live">
            ● 오늘 데이터 실시간 조회
        </span>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "오늘은 카카오 API의 TODAY 기준으로 조회합니다."
    )

else:

    st.markdown(
        """
        <span class="api-info">
            과거 월 데이터
        </span>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 33. 일별 표
# =========================================================

st.markdown(
    f"### 📊 [카카오] {selected_month}월 일자별 성과"
)

display_daily = daily_df.copy()

display_daily["총비용"] = (
    display_daily["cost"]
    .apply(format_won)
)

display_daily["노출"] = (
    display_daily["imp"]
    .apply(format_number)
)

display_daily["클릭수"] = (
    display_daily["click"]
    .apply(format_number)
)

display_daily["CTR"] = (
    display_daily["ctr"]
    .apply(format_percent)
)

display_daily["전환수"] = (
    display_daily["signup_7d"]
    .apply(
        lambda x:
        f"{safe_int(x):,}건"
    )
)

display_daily["CPA"] = (
    display_daily["cpa"]
    .apply(format_won)
)

display_daily = display_daily[
    [
        "date",
        "총비용",
        "노출",
        "클릭수",
        "CTR",
        "전환수",
        "CPA",
    ]
]

display_daily = display_daily.rename(
    columns={
        "date": "일자"
    }
)

st.dataframe(
    display_daily,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# 34. 광고그룹
# =========================================================

st.divider()

st.subheader(
    "📊 [카카오] 광고그룹별 성과"
)

if group_df.empty:

    st.info(
        "조회된 광고그룹 데이터가 없습니다."
    )

else:

    display_group = group_df.copy()

    display_group["광고비"] = (
        display_group["cost"]
        .apply(format_won)
    )

    display_group["노출"] = (
        display_group["imp"]
        .apply(format_number)
    )

    display_group["클릭"] = (
        display_group["click"]
        .apply(format_number)
    )

    display_group["CTR"] = (
        display_group["ctr"]
        .apply(format_percent)
    )

    display_group["서비스 신청"] = (
        display_group["signup_7d"]
        .apply(
            lambda x:
            f"{safe_int(x):,}건"
        )
    )

    display_group["CPA"] = (
        display_group["cpa"]
        .apply(format_won)
    )

    display_group = display_group[
        [
            "campaign_name",
            "ad_group_name",
            "광고비",
            "노출",
            "클릭",
            "CTR",
            "서비스 신청",
            "CPA",
        ]
    ]

    display_group = display_group.rename(
        columns={
            "campaign_name": "캠페인",
            "ad_group_name": "광고그룹",
        }
    )

    st.dataframe(
        display_group,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# 35. 오늘 데이터 별도 표시
# =========================================================

if is_current_month:

    st.divider()

    st.subheader(
        "🟢 오늘 실시간 데이터"
    )

    today_string = (
        today.strftime(
            "%Y-%m-%d"
        )
    )

    today_row = daily_df[
        daily_df["date"]
        == today_string
    ]

    if not today_row.empty:

        row = today_row.iloc[0]

        t1, t2, t3, t4 = st.columns(
            4
        )

        with t1:
            st.metric(
                "오늘 광고비",
                format_won(
                    row["cost"]
                ),
            )

        with t2:
            st.metric(
                "오늘 노출",
                format_number(
                    row["imp"]
                ),
            )

        with t3:
            st.metric(
                "오늘 클릭",
                format_number(
                    row["click"]
                ),
            )

        with t4:
            st.metric(
                "오늘 서비스 신청",
                f"{safe_int(row['signup_7d']):,}건",
            )


# =========================================================
# 36. 데이터 확인
# =========================================================

st.divider()

with st.expander(
    "🔎 API 데이터 확인"
):

    st.write(
        f"광고계정: {ad_account_id}"
    )

    st.write(
        f"광고그룹 수: {len(adgroup_meta)}"
    )

    st.write(
        f"보고서 데이터 행 수: {len(report_df)}"
    )

    if report_df.empty:

        st.warning(
            "카카오 API에서 보고서 데이터가 들어오지 않았습니다."
        )

    else:

        st.dataframe(
            report_df,
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# 37. API 요청 기록
# =========================================================

with st.expander(
    "🛠 API 요청 기록"
):

    debug = st.session_state.get(
        "kakao_debug",
        [],
    )

    if debug:

        for item in debug:

            st.json(item)

    else:

        st.info(
            "API 요청 기록이 없습니다."
        )


# =========================================================
# 38. 전환 기준
# =========================================================

with st.expander(
    "ℹ️ 전환수 집계 기준"
):

    st.write(
        """
        전환수는 카카오모먼트의
        `서비스 신청 (7일)` 기준입니다.

        API 지표:
        `conv_signup_7d`

        즉 카카오 관리자 화면의
        서비스 신청 (7일) 지표를
        대시보드의 전환수로 사용합니다.
        """
    )

    st.write(
        """
        오늘 데이터는 `datePreset=TODAY`
        기준으로 별도 조회합니다.
        """
    )


# =========================================================
# 39. AI 진단
# =========================================================

st.divider()

st.subheader(
    "🤖 AI 성과 진단"
)

if total_cost == 0:

    st.info(
        "현재 조회된 광고비 데이터가 없습니다."
    )

else:

    if total_signup > 0:

        st.write(
            f"• 현재 서비스 신청은 "
            f"**{total_signup:,}건**입니다."
        )

        st.write(
            f"• 서비스 신청당 비용(CPA)은 "
            f"**{total_cpa:,.0f}원**입니다."
        )

    else:

        st.write(
            "• 현재 서비스 신청 전환이 확인되지 않습니다."
        )

    st.write(
        f"• 현재 CTR은 **{total_ctr:.2f}%**입니다."
    )

    st.write(
        "• ROAS는 매출 데이터가 연결되면 계산하도록 구성되어 있습니다."
    )