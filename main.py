import streamlit as st
import pandas as pd
import requests
import time
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
        margin-bottom: 15px;
    }

    .diagnosis-card {
        background: white;
        border-radius: 12px;
        padding: 20px 22px;
        border: 1px solid #eeeeee;
        margin-bottom: 12px;
    }

    .diagnosis-title {
        font-size: 17px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .diagnosis-text {
        font-size: 14px;
        line-height: 1.7;
        color: #444444;
    }

    .improvement-card {
        background: white;
        border-radius: 12px;
        padding: 20px 22px;
        border: 1px solid #eeeeee;
        margin-bottom: 12px;
    }

    .priority-high {
        color: #d32f2f;
        font-weight: 700;
    }

    .priority-medium {
        color: #ed8b00;
        font-weight: 700;
    }

    .priority-good {
        color: #188038;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 광고주 설정
# ============================================================

ADVERTISERS = {
    "리만": {
        "ad_account_id": "995724"
    },

    "구피디": {
        "ad_account_id": "558725"
    },

    "GHB": {
        "ad_account_id": "987505"
    },

    "법률사무소 금하": {
        "ad_account_id": "1001864"
    },

    "법무법인 대한": {
        "ad_account_id": "996079"
    },

    "노빌리언": {
        "ad_account_id": "996206"
    },

    "따뜻한하루": {
        "ad_account_id": "958077"
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
# Kakao API GET
# ============================================================

def kakao_get(
    endpoint,
    ad_account_id,
    params=None
):

    url = f"{KAKAO_BASE_URL}{endpoint}"

    headers = get_kakao_headers(
        ad_account_id
    )

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        if response.status_code != 200:

            try:
                error_data = response.json()
            except Exception:
                error_data = response.text

            st.error(
                f"카카오 API 오류 "
                f"(HTTP {response.status_code})"
            )

            with st.expander(
                "오류 내용 확인"
            ):
                st.write(error_data)

            return None

        try:
            return response.json()

        except Exception:
            return None

    except Exception as e:

        st.error(
            f"카카오 API 연결 오류: {e}"
        )

        return None


# ============================================================
# 캠페인 목록
# ============================================================

def fetch_campaigns(ad_account_id):

    data = kakao_get(
        "/campaigns",
        ad_account_id,
        params={}
    )

    if not data:
        return []

    campaigns = data.get(
        "data",
        []
    )

    if not isinstance(
        campaigns,
        list
    ):
        return []

    result = []

    for item in campaigns:

        if not isinstance(
            item,
            dict
        ):
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
            "campaign_id": str(
                campaign_id
            ),
            "campaign_name": str(
                campaign_name
            )
        })

    return result


# ============================================================
# 광고계정 보고서
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
        (
            "metricsGroup",
            "PIXEL_SDK_CONVERSION"
        )
    ]

    if today:

        params.append(
            ("datePreset", "TODAY")
        )

    else:

        params.append(
            (
                "start",
                start_date.strftime("%Y%m%d")
            )
        )

        params.append(
            (
                "end",
                end_date.strftime("%Y%m%d")
            )
        )

    return kakao_get(
        "/adAccounts/report",
        ad_account_id,
        params=params
    )


# ============================================================
# API → DataFrame
# ============================================================

def report_to_dataframe(report):

    columns = [
        "date",
        "cost",
        "imp",
        "click",
        "ctr",
        "signup_1d",
        "signup_7d"
    ]

    if not report:

        return pd.DataFrame(
            columns=columns
        )

    data = report.get(
        "data",
        []
    )

    if not isinstance(
        data,
        list
    ):

        return pd.DataFrame(
            columns=columns
        )

    rows = []

    for item in data:

        if not isinstance(
            item,
            dict
        ):
            continue

        dimensions = (
            item.get("dimensions")
            or {}
        )

        metrics = (
            item.get("metrics")
            or {}
        )

        if not isinstance(
            dimensions,
            dict
        ):
            dimensions = {}

        if not isinstance(
            metrics,
            dict
        ):
            metrics = {}

        if not dimensions and not metrics:
            continue

        start_value = item.get(
            "start"
        )

        report_date = None

        if start_value:

            try:

                report_date = pd.to_datetime(
                    start_value
                ).date()

            except Exception:

                report_date = None

        rows.append({

            "date": report_date,

            "cost": safe_float(
                metrics.get("cost")
            ),

            "imp": safe_int(
                metrics.get("imp")
            ),

            "click": safe_int(
                metrics.get("click")
            ),

            "ctr": safe_float(
                metrics.get("ctr")
            ),

            "signup_1d": safe_int(
                metrics.get(
                    "conv_signup_1d"
                )
            ),

            "signup_7d": safe_int(
                metrics.get(
                    "conv_signup_7d"
                )
            )
        })

    if not rows:

        return pd.DataFrame(
            columns=columns
        )

    df = pd.DataFrame(
        rows
    )

    # --------------------------------------------------------
    # dtype 명시
    # --------------------------------------------------------

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
# 전체 날짜 DataFrame
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

    last_day = (
        next_month
        - timedelta(days=1)
    )

    # 현재 월이면 오늘까지만
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

    # dtype 미리 지정
    calendar_df["cost"] = 0.0
    calendar_df["imp"] = 0
    calendar_df["click"] = 0
    calendar_df["ctr"] = 0.0
    calendar_df["signup_1d"] = 0
    calendar_df["signup_7d"] = 0

    if (
        raw_df is None
        or raw_df.empty
    ):

        return calendar_df

    work = raw_df.copy()

    work["date"] = pd.to_datetime(
        work["date"],
        errors="coerce"
    )

    work = work.dropna(
        subset=["date"]
    )

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

        return calendar_df

    grouped = (
        work
        .groupby(
            "date",
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

    result = calendar_df.merge(
        grouped,
        on="date",
        how="left",
        suffixes=(
            "",
            "_api"
        )
    )

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

    # CTR 직접 계산
    result["ctr"] = 0.0

    valid = (
        result["imp"] > 0
    )

    result.loc[
        valid,
        "ctr"
    ] = (
        result.loc[
            valid,
            "click"
        ].astype(float)
        /
        result.loc[
            valid,
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

    return result[
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


# ============================================================
# 데이터 전체 수집
# ============================================================

def load_kakao_data(
    ad_account_id,
    selected_year,
    selected_month
):

    today = today_kst()

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

    month_end = (
        next_month
        - timedelta(days=1)
    )

    # --------------------------------------------------------
    # 과거 데이터
    # --------------------------------------------------------

    historical_df = pd.DataFrame()

    historical_end = min(
        month_end,
        today - timedelta(days=1)
    )

    if month_start <= historical_end:

        historical_raw = fetch_account_report(
            ad_account_id,
            start_date=month_start,
            end_date=historical_end,
            today=False
        )

        historical_df = report_to_dataframe(
            historical_raw
        )

    # --------------------------------------------------------
    # 오늘 데이터
    # --------------------------------------------------------

    today_df = pd.DataFrame()

    if (
        selected_year == today.year
        and selected_month == today.month
    ):

        time.sleep(1.2)

        today_raw = fetch_account_report(
            ad_account_id,
            today=True
        )

        today_df = report_to_dataframe(
            today_raw
        )

    # --------------------------------------------------------
    # 합치기
    # --------------------------------------------------------

    frames = []

    if not historical_df.empty:
        frames.append(
            historical_df
        )

    if not today_df.empty:
        frames.append(
            today_df
        )

    if frames:

        raw_df = pd.concat(
            frames,
            ignore_index=True
        )

    else:

        raw_df = pd.DataFrame(
            columns=[
                "date",
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
        raw_df,
        selected_year,
        selected_month,
        today
    )

    return daily_df


# ============================================================
# AI 마케팅 진단
# ============================================================

def generate_marketing_diagnosis(
    df,
    today
):

    if df is None or df.empty:

        return {
            "summary": (
                "현재 분석할 광고 데이터가 없습니다."
            ),
            "diagnosis": [],
            "improvements": []
        }

    work = df.copy()

    # --------------------------------------------------------
    # 전체 지표
    # --------------------------------------------------------

    total_cost = float(
        work["cost"].sum()
    )

    total_imp = int(
        work["imp"].sum()
    )

    total_click = int(
        work["click"].sum()
    )

    total_signup = int(
        work["signup_7d"].sum()
    )

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

    if total_click > 0:

        click_to_signup = (
            total_signup
            / total_click
            * 100
        )

    else:

        click_to_signup = 0

    # --------------------------------------------------------
    # 데이터 발생일
    # --------------------------------------------------------

    active_days = work[
        work["cost"] > 0
    ]

    active_day_count = len(
        active_days
    )

    if active_day_count > 0:

        avg_daily_cost = (
            total_cost
            / active_day_count
        )

    else:

        avg_daily_cost = 0

    # --------------------------------------------------------
    # 신청 발생일
    # --------------------------------------------------------

    signup_days = work[
        work["signup_7d"] > 0
    ]

    signup_day_count = len(
        signup_days
    )

    # --------------------------------------------------------
    # 최대 광고비 날짜
    # --------------------------------------------------------

    if not work.empty:

        max_cost_row = work.loc[
            work["cost"].idxmax()
        ]

    else:

        max_cost_row = None

    # --------------------------------------------------------
    # 최대 CTR 날짜
    # --------------------------------------------------------

    if not work.empty:

        max_ctr_row = work.loc[
            work["ctr"].idxmax()
        ]

    else:

        max_ctr_row = None

    # --------------------------------------------------------
    # 오늘 데이터
    # --------------------------------------------------------

    today_rows = work[
        work["date"].dt.date
        == today
    ]

    if not today_rows.empty:

        today_cost = float(
            today_rows["cost"].sum()
        )

        today_imp = int(
            today_rows["imp"].sum()
        )

        today_click = int(
            today_rows["click"].sum()
        )

        today_signup = int(
            today_rows["signup_7d"].sum()
        )

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

    # ========================================================
    # 진단 생성
    # ========================================================

    diagnosis = []

    improvements = []

    # --------------------------------------------------------
    # 1. CTR 진단
    # --------------------------------------------------------

    if total_ctr < 0.5:

        diagnosis.append({
            "level": "high",
            "title": "클릭 유도력이 낮습니다",
            "text": (
                f"현재 CTR은 {total_ctr:.2f}%로 "
                "광고가 노출되는 것에 비해 클릭을 충분히 "
                "끌어내지 못하고 있습니다."
            )
        })

        improvements.append({
            "level": "high",
            "title": "광고 소재 개선",
            "text": (
                "현재 소재의 첫 문장과 핵심 혜택을 "
                "다시 검토하는 것이 우선입니다. "
                "고객이 광고를 보는 즉시 "
                "'내가 받을 수 있는 혜택'이 보이도록 "
                "메인 문구를 더 직접적으로 구성하는 것을 권장합니다."
            )
        })

    elif total_ctr < 1.0:

        diagnosis.append({
            "level": "medium",
            "title": "CTR이 보통 수준입니다",
            "text": (
                f"CTR은 {total_ctr:.2f}%입니다. "
                "기본적인 클릭은 발생하고 있지만 "
                "소재 개선을 통해 추가적인 클릭 확보가 가능한 구간입니다."
            )
        })

        improvements.append({
            "level": "medium",
            "title": "소재 A/B 테스트",
            "text": (
                "현재 소재를 유지하면서 제목, 핵심 혜택, "
                "CTA 문구를 각각 다르게 만든 소재를 추가해 "
                "클릭률 차이를 비교하는 것을 권장합니다."
            )
        })

    else:

        diagnosis.append({
            "level": "good",
            "title": "클릭 유도력은 양호합니다",
            "text": (
                f"CTR {total_ctr:.2f}%로 "
                "광고 노출 대비 클릭 반응은 양호한 편입니다."
            )
        })

        improvements.append({
            "level": "good",
            "title": "현재 소재의 강점 유지",
            "text": (
                "CTR이 양호하므로 소재를 급격하게 변경하기보다 "
                "현재 잘 작동하는 소재를 기준으로 "
                "세부적인 A/B 테스트를 진행하는 것이 좋습니다."
            )
        })

    # --------------------------------------------------------
    # 2. 전환 진단
    # --------------------------------------------------------

    if total_click > 0 and total_signup == 0:

        diagnosis.append({
            "level": "high",
            "title": "클릭은 발생하지만 서비스 신청으로 연결되지 않습니다",
            "text": (
                f"총 {total_click:,}회의 클릭이 발생했지만 "
                "현재 서비스 신청(7일)은 0건입니다. "
                "광고 소재보다는 랜딩페이지, 상담 신청 과정, "
                "고객의 구매/신청 의도에서 이탈이 발생하고 있을 가능성이 높습니다."
            )
        })

        improvements.append({
            "level": "high",
            "title": "랜딩페이지와 신청 과정 점검",
            "text": (
                "광고 클릭 후 실제 신청까지의 과정을 확인하세요. "
                "페이지 로딩속도, 신청 버튼 위치, 전화번호/상담폼, "
                "신청 절차가 복잡하지 않은지 우선적으로 확인하는 것을 권장합니다."
            )
        })

    elif total_signup > 0:

        diagnosis.append({
            "level": "good",
            "title": "광고가 실제 신청으로 연결되고 있습니다",
            "text": (
                f"서비스 신청(7일) {total_signup:,}건이 발생했으며 "
                f"클릭 대비 신청 전환율은 약 {click_to_signup:.2f}%입니다."
            )
        })

        if cpa > 0:

            improvements.append({
                "level": "medium",
                "title": "CPA 중심으로 효율 최적화",
                "text": (
                    f"현재 평균 CPA는 약 {cpa:,.0f}원입니다. "
                    "신청이 발생하는 소재와 시간대에 예산을 집중하고 "
                    "신청 없이 광고비만 사용하는 구간의 비중을 줄이는 방향으로 "
                    "최적화하는 것을 권장합니다."
                )
            })

    # --------------------------------------------------------
    # 3. 광고비 진단
    # --------------------------------------------------------

    if (
        total_cost > 0
        and total_signup == 0
    ):

        diagnosis.append({
            "level": "high",
            "title": "광고비 대비 전환 성과가 확인되지 않습니다",
            "text": (
                f"현재까지 {total_cost:,.0f}원의 광고비가 사용되었지만 "
                "서비스 신청(7일)이 발생하지 않았습니다."
            )
        })

        improvements.append({
            "level": "high",
            "title": "무전환 구간의 예산 점검",
            "text": (
                "광고비가 지속적으로 발생하는데 신청이 없다면 "
                "예산을 바로 늘리기보다 소재·타겟·랜딩페이지 중 "
                "어느 단계에서 문제가 발생하는지 먼저 확인하는 것이 좋습니다."
            )
        })

    # --------------------------------------------------------
    # 4. 광고비 집중도
    # --------------------------------------------------------

    if (
        max_cost_row is not None
        and total_cost > 0
    ):

        max_cost = float(
            max_cost_row["cost"]
        )

        max_cost_ratio = (
            max_cost
            / total_cost
            * 100
        )

        if max_cost_ratio >= 40:

            diagnosis.append({
                "level": "medium",
                "title": "특정 날짜에 광고비가 집중되어 있습니다",
                "text": (
                    f"{max_cost_row['date'].strftime('%m월 %d일')}에 "
                    f"{max_cost:,.0f}원이 사용되어 "
                    f"전체 광고비의 약 {max_cost_ratio:.1f}%가 "
                    "하루에 집중되었습니다."
                )
            })

            improvements.append({
                "level": "medium",
                "title": "예산 분산 및 효율 확인",
                "text": (
                    "특정 날짜에 예산이 집중되어 있다면 "
                    "해당 날짜의 신청 수와 CPA를 함께 확인하고 "
                    "성과가 좋은 날짜에 의도적으로 예산을 집중할지 판단하세요."
                )
            })

    # --------------------------------------------------------
    # 5. 오늘 성과
    # --------------------------------------------------------

    if today_cost > 0:

        if (
            total_cost > 0
            and active_day_count > 1
        ):

            avg_before_today = (
                total_cost
                - today_cost
            ) / max(
                active_day_count - 1,
                1
            )

            if today_cost > (
                avg_before_today * 1.5
            ):

                diagnosis.append({
                    "level": "medium",
                    "title": "오늘 광고비 지출이 평소보다 높습니다",
                    "text": (
                        f"오늘 광고비는 {today_cost:,.0f}원으로 "
                        "기존 활성일 평균보다 높은 수준입니다. "
                        "오늘 발생한 클릭과 신청을 함께 확인할 필요가 있습니다."
                    )
                })

    # --------------------------------------------------------
    # 6. 신청 발생 빈도
    # --------------------------------------------------------

    if (
        total_signup > 0
        and active_day_count > 0
    ):

        signup_rate_days = (
            signup_day_count
            / active_day_count
            * 100
        )

        if signup_rate_days < 30:

            diagnosis.append({
                "level": "medium",
                "title": "신청 발생이 특정 날짜에 편중되어 있습니다",
                "text": (
                    f"광고가 집행된 {active_day_count}일 중 "
                    f"{signup_day_count}일에서만 신청이 발생했습니다. "
                    "일부 날짜나 조건에서 성과가 집중되고 있을 가능성이 있습니다."
                )
            })

            improvements.append({
                "level": "medium",
                "title": "성과 발생 조건 분석",
                "text": (
                    "신청이 발생한 날짜의 광고비, 클릭량, CTR을 비교해 "
                    "성과가 좋은 패턴을 찾아 예산 배분 기준으로 활용하는 것이 좋습니다."
                )
            })

    # --------------------------------------------------------
    # 7. 전체 요약
    # --------------------------------------------------------

    if total_signup > 0:

        summary = (
            f"현재까지 광고비 {total_cost:,.0f}원으로 "
            f"서비스 신청 {total_signup:,}건을 확보하고 있습니다. "
            f"CTR은 {total_ctr:.2f}%, 평균 CPA는 "
            f"{cpa:,.0f}원입니다. "
            "현재는 전환을 유지하면서 광고 소재와 예산 배분을 "
            "세밀하게 최적화하는 방향이 적절합니다."
        )

    elif total_click > 0:

        summary = (
            f"현재 광고비 {total_cost:,.0f}원, "
            f"클릭 {total_click:,}회가 발생하고 있지만 "
            "서비스 신청으로 이어지는 성과가 부족합니다. "
            "예산 확대보다는 전환 과정과 랜딩페이지를 먼저 점검하는 것이 우선입니다."
        )

    elif total_cost > 0:

        summary = (
            f"현재 광고비 {total_cost:,.0f}원이 집행되고 있습니다. "
            "아직 클릭 및 전환 데이터가 충분하지 않기 때문에 "
            "추가 데이터를 확보하면서 소재와 타겟 반응을 확인하는 단계입니다."
        )

    else:

        summary = (
            "현재 광고 집행 데이터가 없어 "
            "구체적인 성과 진단이 어렵습니다."
        )

    return {
        "summary": summary,
        "diagnosis": diagnosis,
        "improvements": improvements
    }


# ============================================================
# 사이드바
# ============================================================

with st.sidebar:

    st.markdown(
        "## 📊 광고 성과 대시보드"
    )

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

        Streamlit Secrets에서

        `KAKAO_BUSINESS_TOKEN`

        항목을 확인해주세요.
        """
    )

    st.stop()


# ============================================================
# 데이터 수신
# ============================================================

with st.spinner(
    "카카오 광고 데이터를 불러오는 중입니다..."
):

    daily_df = load_kakao_data(
        ad_account_id,
        selected_year,
        selected_month
    )


# ============================================================
# API 상태
# ============================================================

st.markdown(
    '<div class="status-ok">'
    '● 카카오 광고 데이터 정상 수신'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# KPI 계산
# ============================================================

total_cost = float(
    daily_df["cost"].sum()
)

total_imp = int(
    daily_df["imp"].sum()
)

total_click = int(
    daily_df["click"].sum()
)

total_signup = int(
    daily_df["signup_7d"].sum()
)


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



# ============================================================
# 오늘 실시간 데이터
# ============================================================

st.markdown("## 🔴 오늘 실시간 데이터")

today_row = daily_df[
    daily_df["date"].dt.date == current_date
]

yesterday_date = current_date - timedelta(days=1)

yesterday_row = daily_df[
    daily_df["date"].dt.date == yesterday_date
]


# ------------------------------------------------------------
# 증감률 계산
# ------------------------------------------------------------

def calc_change(today_value, yesterday_value):

    if yesterday_value is None or yesterday_value == 0:
        return None

    return (
        (today_value - yesterday_value)
        / yesterday_value
        * 100
    )


def delta_percent(value):

    if value is None:
        return None

    return f"{value:+.1f}% 어제 대비"


def delta_ctr(value):

    if value is None:
        return None

    return f"{value:+.2f}%p 어제 대비"


# ============================================================
# 카드 디자인
# ============================================================

st.markdown(
    """
    <style>

    /* 카드 기본 */
    div[data-testid="stMetric"] {
        position: relative;
        overflow: hidden;

        min-height: 165px;
        padding: 22px 20px 24px 20px;

        border-radius: 22px;

        border: 1px solid rgba(225, 228, 235, 0.55);

        box-shadow:
            0 8px 24px rgba(44, 62, 90, 0.055);

        transition:
            transform 0.20s ease,
            box-shadow 0.20s ease;
    }


    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);

        box-shadow:
            0 13px 30px rgba(44, 62, 90, 0.09);
    }


    /* =========================================
       카드별 파스텔 컬러
       ========================================= */


    /* 광고비 - 핑크 */

    div[data-testid="column"]:nth-of-type(1)
    div[data-testid="stMetric"] {

        background:
            linear-gradient(
                155deg,
                #ffffff 0%,
                #fffafa 42%,
                #fff0f2 100%
            );

        border-color: #ffe3e6;
    }


    div[data-testid="column"]:nth-of-type(1)
    div[data-testid="stMetric"]::after {
        background: #ffdfe3;
    }


    /* 노출 - 블루 */

    div[data-testid="column"]:nth-of-type(2)
    div[data-testid="stMetric"] {

        background:
            linear-gradient(
                155deg,
                #ffffff 0%,
                #f8fbff 42%,
                #edf5ff 100%
            );

        border-color: #dceaff;
    }


    div[data-testid="column"]:nth-of-type(2)
    div[data-testid="stMetric"]::after {
        background: #dcecff;
    }


    /* 클릭 - 그린 */

    div[data-testid="column"]:nth-of-type(3)
    div[data-testid="stMetric"] {

        background:
            linear-gradient(
                155deg,
                #ffffff 0%,
                #f8fdf9 42%,
                #ecf9f1 100%
            );

        border-color: #d8f0e1;
    }


    div[data-testid="column"]:nth-of-type(3)
    div[data-testid="stMetric"]::after {
        background: #d9f1e1;
    }


    /* CTR - 퍼플 */

    div[data-testid="column"]:nth-of-type(4)
    div[data-testid="stMetric"] {

        background:
            linear-gradient(
                155deg,
                #ffffff 0%,
                #fbf9ff 42%,
                #f2edff 100%
            );

        border-color: #e8dfff;
    }


    div[data-testid="column"]:nth-of-type(4)
    div[data-testid="stMetric"]::after {
        background: #e7ddff;
    }


    /* 서비스 신청 - 오렌지 */

    div[data-testid="column"]:nth-of-type(5)
    div[data-testid="stMetric"] {

        background:
            linear-gradient(
                155deg,
                #ffffff 0%,
                #fffdf8 42%,
                #fff4df 100%
            );

        border-color: #f8e7c8;
    }


    div[data-testid="column"]:nth-of-type(5)
    div[data-testid="stMetric"]::after {
        background: #ffebc5;
    }


    /* CPA - 민트 */

    div[data-testid="column"]:nth-of-type(6)
    div[data-testid="stMetric"] {

        background:
            linear-gradient(
                155deg,
                #ffffff 0%,
                #f7fdfb 42%,
                #e9f9f5 100%
            );

        border-color: #d4eee8;
    }


    div[data-testid="column"]:nth-of-type(6)
    div[data-testid="stMetric"]::after {
        background: #d3f0e9;
    }


    /* =========================================
       카드 하단 부드러운 물결
       ========================================= */

    div[data-testid="stMetric"]::after {

        content: "";

        position: absolute;

        width: 135%;
        height: 80px;

        left: -18%;
        bottom: -52px;

        border-radius:
            48% 52% 0 0 /
            70% 70% 0 0;

        opacity: 0.72;

        transform: rotate(-2deg);

        pointer-events: none;

        z-index: 0;
    }


    div[data-testid="stMetric"]::before {

        content: "";

        position: absolute;

        width: 90%;
        height: 55px;

        right: -25%;
        bottom: -39px;

        border-radius: 50%;

        background:
            rgba(255,255,255,0.48);

        transform: rotate(5deg);

        pointer-events: none;

        z-index: 1;
    }


    /* =========================================
       카드 제목
       ========================================= */

    div[data-testid="stMetricLabel"] {

        position: relative;

        z-index: 5;

        font-size: 14px;

        font-weight: 650;

        color: #505a6d;

        margin-bottom: 10px;
    }


    /* =========================================
       숫자
       ========================================= */

    div[data-testid="stMetricValue"] {

        position: relative;

        z-index: 5;

        font-size: 29px;

        font-weight: 750;

        color: #172033;

        letter-spacing: -0.7px;
    }


    div[data-testid="stMetricValue"] > div {

        white-space: nowrap;
    }


    /* =========================================
       어제 대비 배지
       ========================================= */

    div[data-testid="stMetricDelta"] {

        position: relative;

        z-index: 5;

        width: fit-content;

        margin-top: 12px;

        padding: 5px 10px;

        border-radius: 999px;

        background:
            rgba(255,255,255,0.75);

        box-shadow:
            0 2px 8px
            rgba(30,41,59,0.035);

        font-size: 12px;

        font-weight: 650;
    }


    /* 모바일 */

    @media (max-width: 1000px) {

        div[data-testid="stMetric"] {

            min-height: 145px;

            padding:
                18px
                15px
                20px
                15px;
        }


        div[data-testid="stMetricValue"] {

            font-size: 23px;
        }

    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 오늘 데이터가 있을 경우
# ============================================================

if not today_row.empty:

    # 오늘
    today_cost = float(
        today_row["cost"].sum()
    )

    today_imp = int(
        today_row["imp"].sum()
    )

    today_click = int(
        today_row["click"].sum()
    )

    today_signup = int(
        today_row["signup_7d"].sum()
    )


    today_ctr = (
        today_click / today_imp * 100
        if today_imp > 0
        else 0.0
    )


    today_cpa = (
        today_cost / today_signup
        if today_signup > 0
        else 0.0
    )


    # ========================================================
    # 어제 데이터
    # ========================================================

    if not yesterday_row.empty:

        yesterday_cost = float(
            yesterday_row["cost"].sum()
        )

        yesterday_imp = int(
            yesterday_row["imp"].sum()
        )

        yesterday_click = int(
            yesterday_row["click"].sum()
        )

        yesterday_signup = int(
            yesterday_row["signup_7d"].sum()
        )

    else:

        yesterday_cost = 0.0
        yesterday_imp = 0
        yesterday_click = 0
        yesterday_signup = 0


    yesterday_ctr = (
        yesterday_click / yesterday_imp * 100
        if yesterday_imp > 0
        else 0.0
    )


    yesterday_cpa = (
        yesterday_cost / yesterday_signup
        if yesterday_signup > 0
        else 0.0
    )


    # ========================================================
    # 어제 대비
    # ========================================================

    cost_change = calc_change(
        today_cost,
        yesterday_cost
    )

    imp_change = calc_change(
        today_imp,
        yesterday_imp
    )

    click_change = calc_change(
        today_click,
        yesterday_click
    )

    signup_change = calc_change(
        today_signup,
        yesterday_signup
    )

    cpa_change = calc_change(
        today_cpa,
        yesterday_cpa
    )


    ctr_change = (
        today_ctr - yesterday_ctr
        if yesterday_imp > 0
        else None
    )


    # ========================================================
    # 6개 카드 생성
    # ========================================================

    col1, col2, col3, col4, col5, col6 = st.columns(
        6,
        gap="medium"
    )


    with col1:

        st.metric(
            label="💳 오늘 광고비",
            value=f"{today_cost:,.0f}원",
            delta=delta_percent(
                cost_change
            )
        )


    with col2:

        st.metric(
            label="👁️ 오늘 노출",
            value=f"{today_imp:,.0f}",
            delta=delta_percent(
                imp_change
            )
        )


    with col3:

        st.metric(
            label="🖱️ 오늘 클릭",
            value=f"{today_click:,.0f}",
            delta=delta_percent(
                click_change
            )
        )


    with col4:

        st.metric(
            label="📊 오늘 CTR",
            value=f"{today_ctr:.2f}%",
            delta=delta_ctr(
                ctr_change
            )
        )


    with col5:

        st.metric(
            label="👥 오늘 서비스 신청",
            value=f"{today_signup:,.0f}",
            delta=delta_percent(
                signup_change
            )
        )


    with col6:

        st.metric(
            label="🎯 오늘 CPA",

            value=(
                f"{today_cpa:,.0f}원"
                if today_signup > 0
                else "-"
            ),

            delta=(
                delta_percent(cpa_change)
                if (
                    today_signup > 0
                    and yesterday_signup > 0
                )
                else None
            ),

            # CPA는 낮아질수록 좋음
            delta_color="inverse"
        )


    # ========================================================
    # 업데이트 안내
    # ========================================================

    st.caption(
        f"● 실시간 업데이트 · "
        f"{current_date.strftime('%Y년 %m월 %d일')} 기준"
    )


else:

    st.info(
        "오늘 광고 데이터가 아직 없습니다."
    )
# ============================================================
# 일자별 성과
# ============================================================

st.markdown(
    "### 📅 일자별 성과"
)

if daily_df.empty:

    st.info(
        "선택한 기간에 데이터가 없습니다."
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
# AI 마케팅 진단
# ============================================================

st.markdown("### 🤖 마케팅 진단")

ai_result = generate_marketing_diagnosis(
    daily_df,
    current_date
)

# ------------------------------------------------------------
# 종합 진단
# ------------------------------------------------------------

st.info(
    f"**종합 진단**  \n"
    f"{ai_result['summary']}"
)


# ------------------------------------------------------------
# 세부 진단
# ------------------------------------------------------------

if ai_result["diagnosis"]:

    for item in ai_result["diagnosis"]:

        if item["level"] == "high":

            st.warning(
                f"🔴 **{item['title']}**  \n"
                f"{item['text']}"
            )

        elif item["level"] == "medium":

            st.info(
                f"🟠 **{item['title']}**  \n"
                f"{item['text']}"
            )

        else:

            st.success(
                f"🟢 **{item['title']}**  \n"
                f"{item['text']}"
            )


# ============================================================
# 개선 방향
# ============================================================

st.markdown("### 🚀 개선 방향")

if ai_result["improvements"]:

    for index, item in enumerate(
        ai_result["improvements"],
        start=1
    ):

        if item["level"] == "high":

            st.warning(
                f"**{index}순위 · {item['title']}**  \n"
                f"{item['text']}"
            )

        elif item["level"] == "medium":

            st.info(
                f"**{index}순위 · {item['title']}**  \n"
                f"{item['text']}"
            )

        else:

            st.success(
                f"**{index}순위 · {item['title']}**  \n"
                f"{item['text']}"
            )


# ============================================================
# 하단 안내
# ============================================================

st.caption(
    "※ 서비스 신청(7일)은 카카오 전환 어트리뷰션 기준으로 "
    "이후 수치가 변경될 수 있습니다."
)