import time
from datetime import date, datetime, timedelta

import pandas as pd
import requests
import streamlit as st


# =========================================================
# 1. 페이지 기본 설정
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

    h2 {
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
        font-size: 30px;
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

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e8ebef;
        border-radius: 12px;
        padding: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 3. 기본 설정
# =========================================================

KAKAO_BASE_URL = "https://apis.moment.kakao.com/openapi/v4"


# ---------------------------------------------------------
# Streamlit Secrets 사용
#
# .streamlit/secrets.toml 예:
#
# KAKAO_BUSINESS_TOKEN = "새로운_토큰"
#
# 필요하면 아래처럼 광고계정도 설정 가능
# KAKAO_AD_ACCOUNT_ID = "995724"
# ---------------------------------------------------------

try:
    KAKAO_BUSINESS_TOKEN = st.secrets["KAKAO_BUSINESS_TOKEN"]
except Exception:
    KAKAO_BUSINESS_TOKEN = ""


# =========================================================
# 4. 광고주 목록
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
# 5. 세션 상태
# =========================================================

if "selected_channel" not in st.session_state:
    st.session_state.selected_channel = "카카오"

if "selected_advertiser" not in st.session_state:
    st.session_state.selected_advertiser = "995724"


# =========================================================
# 6. 공통 함수
# =========================================================

def format_won(value):
    """원화 표시"""
    try:
        value = float(value or 0)
        return f"{value:,.0f}원"
    except Exception:
        return "0원"


def format_number(value):
    """숫자 표시"""
    try:
        return f"{float(value or 0):,.0f}"
    except Exception:
        return "0"


def format_percent(value):
    """퍼센트 표시"""
    try:
        return f"{float(value or 0):.2f}%"
    except Exception:
        return "0.00%"


def safe_float(value):
    try:
        if value is None:
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def safe_int(value):
    try:
        if value is None:
            return 0
        return int(float(value))
    except Exception:
        return 0


# =========================================================
# 7. 카카오 API 헤더
# =========================================================

def get_kakao_headers(ad_account_id):
    return {
        "Authorization": f"Bearer {KAKAO_BUSINESS_TOKEN}",
        "adAccountId": str(ad_account_id),
        "Content-Type": "application/json",
    }


# =========================================================
# 8. 카카오 API 공통 GET
# =========================================================

def kakao_get(endpoint, ad_account_id, params=None, timeout=30):
    """
    카카오 API GET 요청.

    실패할 경우 HTTP 상태코드와 카카오 응답을 그대로 반환.
    """

    if not KAKAO_BUSINESS_TOKEN:
        return {
            "ok": False,
            "status_code": 0,
            "response": {
                "code": -1,
                "message": "KAKAO_BUSINESS_TOKEN이 설정되지 않았습니다.",
                "detail": "Streamlit Secrets에 KAKAO_BUSINESS_TOKEN을 등록하세요.",
            },
        }

    url = f"{KAKAO_BASE_URL}{endpoint}"

    try:
        response = requests.get(
            url,
            headers=get_kakao_headers(ad_account_id),
            params=params,
            timeout=timeout,
        )

        try:
            body = response.json()
        except Exception:
            body = response.text

        if response.ok:
            return {
                "ok": True,
                "status_code": response.status_code,
                "response": body,
            }

        return {
            "ok": False,
            "status_code": response.status_code,
            "response": body,
        }

    except requests.RequestException as e:
        return {
            "ok": False,
            "status_code": 0,
            "response": {
                "code": -1,
                "message": "카카오 API 요청 중 네트워크 오류",
                "detail": str(e),
            },
        }


# =========================================================
# 9. 캠페인 목록 조회
# =========================================================

def fetch_kakao_campaigns(ad_account_id):
    result = kakao_get(
        "/campaigns",
        ad_account_id,
        params=None,
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
# 10. 광고그룹 목록 조회
# =========================================================

def fetch_kakao_adgroups(ad_account_id, campaign_id):
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
# 11. 광고그룹 ID를 Long[] 형태로 전달
# =========================================================

def build_adgroup_params(ad_group_ids):
    """
    카카오 공식 API 문서의 Long[] 예시에 맞춰
    adGroupId를 comma-separated 형태로 전달.

    예:
    adGroupId=123,456,789
    """

    ids = [str(x) for x in ad_group_ids]

    return ",".join(ids)


# =========================================================
# 12. 광고그룹 보고서 조회
# =========================================================

def fetch_kakao_adgroup_report(
    ad_account_id,
    ad_group_ids,
    start=None,
    end=None,
    date_preset=None,
    metrics_group="BASIC",
):
    """
    광고그룹 보고서.

    BASIC
      - 광고비
      - 노출
      - 클릭
      - CTR

    PIXEL_SDK_CONVERSION
      - 서비스 신청(1일)
      - 서비스 신청(7일)
      - 기타 픽셀/SDK 전환

    광고그룹 최대 40개.
    """

    if not ad_group_ids:
        return [], None

    all_data = []

    # 카카오 API는 광고그룹 최대 40개
    chunks = [
        ad_group_ids[i:i + 40]
        for i in range(0, len(ad_group_ids), 40)
    ]

    for chunk_index, chunk in enumerate(chunks):

        params = {
            "adGroupId": build_adgroup_params(chunk),
            "timeUnit": "DAY",
            "level": "AD_GROUP",
            "metricsGroup": metrics_group,
        }

        if date_preset:
            params["datePreset"] = date_preset
        else:
            params["start"] = start
            params["end"] = end

        result = kakao_get(
            "/adGroups/report",
            ad_account_id,
            params=params,
        )

        if not result["ok"]:
            return [], result

        body = result["response"]

        if isinstance(body, dict):
            data = body.get("data", [])

            if isinstance(data, list):
                all_data.extend(data)

        # 카카오 광고그룹 보고서 API 호출 제한 대응
        if chunk_index < len(chunks) - 1:
            time.sleep(1.1)

    return all_data, None


# =========================================================
# 13. 월별 조회 날짜 생성
# =========================================================

def get_month_dates(year, month):
    """
    선택한 월의 전체 날짜 생성.

    현재 월이면:
        1일 ~ 오늘

    지난 월이면:
        1일 ~ 말일
    """

    first_day = date(year, month, 1)

    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)

    last_day = next_month - timedelta(days=1)

    today = date.today()

    if year == today.year and month == today.month:
        last_day = today

    dates = []

    current = first_day

    while current <= last_day:
        dates.append(current)
        current += timedelta(days=1)

    return dates


# =========================================================
# 14. 과거 조회 기간
# =========================================================

def get_historical_range(year, month):
    """
    오늘을 제외한 과거 데이터 범위.

    카카오 API의 start/end 조회는 오늘을 포함할 수 없기 때문에
    현재 월이면 어제까지 조회.
    """

    first_day = date(year, month, 1)
    today = date.today()

    if year == today.year and month == today.month:
        end_day = today - timedelta(days=1)

        if end_day < first_day:
            return None, None

        return first_day, end_day

    # 과거 월
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)

    last_day = next_month - timedelta(days=1)

    return first_day, last_day


# =========================================================
# 15. 광고그룹 메타 정보 만들기
# =========================================================

def collect_kakao_adgroups(ad_account_id):
    """
    모든 캠페인 → 모든 광고그룹을 수집.

    반환:
        adgroups
        campaigns
        error
    """

    campaigns, error = fetch_kakao_campaigns(ad_account_id)

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

        adgroups, error = fetch_kakao_adgroups(
            ad_account_id,
            campaign_id,
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
                    "ad_group_id": str(group_id),
                    "ad_group_name": group_name,
                    "campaign_id": str(campaign_id),
                    "campaign_name": campaign_name,
                    "status": (
                        group.get("adGroupStatus")
                        or group.get("status")
                        or ""
                    ),
                }
            )

    return all_adgroups, campaigns, None


# =========================================================
# 16. BASIC 보고서 → DataFrame
# =========================================================

def basic_report_to_df(report_data, adgroup_meta):
    rows = []

    meta_map = {
        str(x["ad_group_id"]): x
        for x in adgroup_meta
    }

    for item in report_data:

        dimensions = item.get("dimensions", {}) or {}
        metrics = item.get("metrics", {}) or {}

        ad_group_id = str(
            dimensions.get("ad_group_id", "")
        )

        if not ad_group_id:
            continue

        meta = meta_map.get(
            ad_group_id,
            {}
        )

        report_date = (
            item.get("start")
            or item.get("date")
            or ""
        )

        rows.append(
            {
                "date": report_date,
                "campaign_id": meta.get("campaign_id", ""),
                "campaign_name": meta.get("campaign_name", ""),
                "ad_group_id": ad_group_id,
                "ad_group_name": meta.get("ad_group_name", ""),
                "status": meta.get("status", ""),
                "cost": safe_float(metrics.get("cost")),
                "imp": safe_int(metrics.get("imp")),
                "click": safe_int(metrics.get("click")),
                "ctr": safe_float(metrics.get("ctr")),
            }
        )

    return pd.DataFrame(rows)


# =========================================================
# 17. 전환 보고서 → DataFrame
# =========================================================

def conversion_report_to_df(report_data):
    rows = []

    for item in report_data:

        dimensions = item.get("dimensions", {}) or {}
        metrics = item.get("metrics", {}) or {}

        ad_group_id = str(
            dimensions.get("ad_group_id", "")
        )

        if not ad_group_id:
            continue

        rows.append(
            {
                "date": (
                    item.get("start")
                    or item.get("date")
                    or ""
                ),
                "ad_group_id": ad_group_id,

                # ★ 핵심
                # 카카오 관리자에서 보는
                # "서비스 신청 (7일)"
                "service_signup_7d": safe_int(
                    metrics.get("conv_signup_7d")
                ),

                # 참고용 1일 서비스 신청
                "service_signup_1d": safe_int(
                    metrics.get("conv_signup_1d")
                ),

                # 기타 전환
                "complete_registration_7d": safe_int(
                    metrics.get("conv_cmpt_reg_7d")
                ),

                "purchase_7d": safe_int(
                    metrics.get("conv_purchase_7d")
                ),

                "participation_7d": safe_int(
                    metrics.get("conv_participation_7d")
                ),
            }
        )

    return pd.DataFrame(rows)


# =========================================================
# 18. 날짜 전체 채우기
# =========================================================

def make_full_date_dataframe(
    year,
    month,
    basic_df,
    conversion_df,
    adgroup_meta,
):
    """
    광고가 실제로 집행된 날짜만 API에서 내려오더라도
    선택한 월의 날짜를 모두 만들어준다.

    광고가 없는 날 = 0
    """

    dates = get_month_dates(year, month)

    full_dates = pd.DataFrame(
        {
            "date": [
                d.strftime("%Y-%m-%d")
                for d in dates
            ]
        }
    )

    # -----------------------------------------
    # BASIC
    # -----------------------------------------

    if basic_df.empty:
        basic_daily = pd.DataFrame(
            columns=[
                "date",
                "cost",
                "imp",
                "click",
            ]
        )
    else:

        basic_df["date"] = pd.to_datetime(
            basic_df["date"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

        basic_daily = (
            basic_df
            .groupby("date", as_index=False)
            .agg(
                {
                    "cost": "sum",
                    "imp": "sum",
                    "click": "sum",
                }
            )
        )

    # -----------------------------------------
    # 전환
    # -----------------------------------------

    if conversion_df.empty:
        conversion_daily = pd.DataFrame(
            columns=[
                "date",
                "service_signup_7d",
            ]
        )
    else:

        conversion_df["date"] = pd.to_datetime(
            conversion_df["date"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

        conversion_daily = (
            conversion_df
            .groupby("date", as_index=False)
            .agg(
                {
                    "service_signup_7d": "sum",
                }
            )
        )

    # -----------------------------------------
    # 날짜 병합
    # -----------------------------------------

    result = full_dates.merge(
        basic_daily,
        on="date",
        how="left",
    )

    result = result.merge(
        conversion_daily,
        on="date",
        how="left",
    )

    # -----------------------------------------
    # 빈 날짜 = 0
    # -----------------------------------------

    for col in [
        "cost",
        "imp",
        "click",
        "service_signup_7d",
    ]:
        if col in result.columns:
            result[col] = result[col].fillna(0)

    result["ctr"] = 0.0

    mask = result["imp"] > 0

    result.loc[mask, "ctr"] = (
        result.loc[mask, "click"]
        / result.loc[mask, "imp"]
        * 100
    )

    result["cpa"] = 0.0

    mask_conversion = result["service_signup_7d"] > 0

    result.loc[mask_conversion, "cpa"] = (
        result.loc[mask_conversion, "cost"]
        / result.loc[mask_conversion, "service_signup_7d"]
    )

    return result


# =========================================================
# 19. 광고그룹별 데이터 만들기
# =========================================================

def make_adgroup_dataframe(
    basic_df,
    conversion_df,
    adgroup_meta,
):
    meta_df = pd.DataFrame(adgroup_meta)

    if meta_df.empty:
        return pd.DataFrame()

    # BASIC
    if basic_df.empty:
        basic_group = pd.DataFrame(
            columns=[
                "ad_group_id",
                "cost",
                "imp",
                "click",
            ]
        )
    else:
        basic_group = (
            basic_df
            .groupby("ad_group_id", as_index=False)
            .agg(
                {
                    "cost": "sum",
                    "imp": "sum",
                    "click": "sum",
                }
            )
        )

    # CONVERSION
    if conversion_df.empty:
        conversion_group = pd.DataFrame(
            columns=[
                "ad_group_id",
                "service_signup_7d",
            ]
        )
    else:
        conversion_group = (
            conversion_df
            .groupby("ad_group_id", as_index=False)
            .agg(
                {
                    "service_signup_7d": "sum",
                }
            )
        )

    result = meta_df.merge(
        basic_group,
        on="ad_group_id",
        how="left",
    )

    result = result.merge(
        conversion_group,
        on="ad_group_id",
        how="left",
    )

    for col in [
        "cost",
        "imp",
        "click",
        "service_signup_7d",
    ]:
        if col in result.columns:
            result[col] = result[col].fillna(0)

    result["ctr"] = 0.0

    mask = result["imp"] > 0

    result.loc[mask, "ctr"] = (
        result.loc[mask, "click"]
        / result.loc[mask, "imp"]
        * 100
    )

    result["cpa"] = 0.0

    mask = result["service_signup_7d"] > 0

    result.loc[mask, "cpa"] = (
        result.loc[mask, "cost"]
        / result.loc[mask, "service_signup_7d"]
    )

    return result


# =========================================================
# 20. 카카오 전체 데이터 조회
# =========================================================

@st.cache_data(ttl=60)
def fetch_kakao_data(ad_account_id, year, month):
    """
    카카오 전체 조회.

    ① 과거 데이터
       start ~ yesterday

    ② 오늘 데이터
       datePreset=TODAY

    ③ BASIC
       광고비 / 노출 / 클릭

    ④ PIXEL_SDK_CONVERSION
       서비스 신청(7일)
    """

    # -----------------------------------------
    # 광고그룹 수집
    # -----------------------------------------

    adgroup_meta, campaigns, error = collect_kakao_adgroups(
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
            "basic_df": pd.DataFrame(),
            "conversion_df": pd.DataFrame(),
            "today": date.today(),
        }

    ad_group_ids = [
        x["ad_group_id"]
        for x in adgroup_meta
    ]

    # -----------------------------------------
    # 과거 기간
    # -----------------------------------------

    start_day, end_day = get_historical_range(
        year,
        month,
    )

    historical_basic = []
    historical_conversion = []

    if start_day and end_day:

        # BASIC
        report, error = fetch_kakao_adgroup_report(
            ad_account_id=ad_account_id,
            ad_group_ids=ad_group_ids,
            start=start_day.strftime("%Y%m%d"),
            end=end_day.strftime("%Y%m%d"),
            metrics_group="BASIC",
        )

        if error:
            return {
                "success": False,
                "error": error,
            }

        historical_basic = report

        # API rate limit
        time.sleep(1.1)

        # 서비스 신청
        report, error = fetch_kakao_adgroup_report(
            ad_account_id=ad_account_id,
            ad_group_ids=ad_group_ids,
            start=start_day.strftime("%Y%m%d"),
            end=end_day.strftime("%Y%m%d"),
            metrics_group="PIXEL_SDK_CONVERSION",
        )

        if error:
            return {
                "success": False,
                "error": error,
            }

        historical_conversion = report

    # -----------------------------------------
    # 오늘
    # -----------------------------------------

    today_basic = []
    today_conversion = []

    today = date.today()

    # 선택한 월이 현재 월이면 TODAY 호출
    if year == today.year and month == today.month:

        # BASIC
        report, error = fetch_kakao_adgroup_report(
            ad_account_id=ad_account_id,
            ad_group_ids=ad_group_ids,
            date_preset="TODAY",
            metrics_group="BASIC",
        )

        if error:
            return {
                "success": False,
                "error": error,
            }

        today_basic = report

        # API rate limit
        time.sleep(1.1)

        # 서비스 신청
        report, error = fetch_kakao_adgroup_report(
            ad_account_id=ad_account_id,
            ad_group_ids=ad_group_ids,
            date_preset="TODAY",
            metrics_group="PIXEL_SDK_CONVERSION",
        )

        if error:
            return {
                "success": False,
                "error": error,
            }

        today_conversion = report

    # -----------------------------------------
    # DataFrame 변환
    # -----------------------------------------

    all_basic = historical_basic + today_basic
    all_conversion = (
        historical_conversion
        + today_conversion
    )

    basic_df = basic_report_to_df(
        all_basic,
        adgroup_meta,
    )

    conversion_df = conversion_report_to_df(
        all_conversion
    )

    return {
        "success": True,
        "adgroup_meta": adgroup_meta,
        "campaigns": campaigns,
        "basic_df": basic_df,
        "conversion_df": conversion_df,
        "today": today,
    }


# =========================================================
# 21. 사이드바
# =========================================================

with st.sidebar:

    st.markdown("## 📌 광고 채널")

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

    st.session_state.selected_channel = channel

    st.markdown("---")

    if channel == "카카오":

        advertiser_options = list(
            KAKAO_ADVERTISERS.keys()
        )

        advertiser_id = st.selectbox(
            "광고주 선택",
            advertiser_options,
            format_func=lambda x:
                KAKAO_ADVERTISERS[x],
            index=(
                advertiser_options.index(
                    st.session_state.selected_advertiser
                )
                if st.session_state.selected_advertiser
                in advertiser_options
                else 0
            ),
        )

        st.session_state.selected_advertiser = advertiser_id

    elif channel == "네이버":

        advertiser_id = st.selectbox(
            "광고주 선택",
            list(NAVER_ADVERTISERS.keys()),
            format_func=lambda x:
                NAVER_ADVERTISERS[x],
        )

    elif channel == "토스":

        advertiser_id = st.selectbox(
            "광고주 선택",
            list(TOSS_ADVERTISERS.keys()),
            format_func=lambda x:
                TOSS_ADVERTISERS[x],
        )

    else:

        advertiser_id = st.selectbox(
            "광고주 선택",
            list(META_ADVERTISERS.keys()),
            format_func=lambda x:
                META_ADVERTISERS[x],
        )


# =========================================================
# 22. 메인
# =========================================================

if channel != "카카오":

    st.title(
        f"📊 [{channel}] {advertiser_id} 성과 대시보드"
    )

    st.info(
        f"{channel} API 연동 영역입니다. "
        "현재 카카오 API 연동을 우선 완성한 상태입니다."
    )

    st.stop()


# =========================================================
# 23. 카카오 메인 화면
# =========================================================

ad_account_id = str(advertiser_id)
advertiser_name = KAKAO_ADVERTISERS.get(
    ad_account_id,
    ad_account_id,
)

st.title(
    f"📊 [카카오] {advertiser_name} 성과 대시보드"
)

st.write(
    "선택하신 카카오 채널의 API 데이터를 조회합니다."
)


# =========================================================
# 24. 조회 월
# =========================================================

col1, col2 = st.columns([1, 1])

with col1:

    today = date.today()

    month_options = []

    for i in range(12):

        # 월 계산
        month_offset = (
            today.year * 12
            + today.month
            - 1
            - i
        )

        y = month_offset // 12
        m = month_offset % 12 + 1

        month_options.append(
            (y, m)
        )

    month_labels = [
        f"{y}년 {m}월"
        for y, m in month_options
    ]

    selected_month_label = st.selectbox(
        "조회 월",
        month_labels,
        index=0,
    )

selected_index = month_labels.index(
    selected_month_label
)

selected_year, selected_month = (
    month_options[selected_index]
)


# =========================================================
# 25. 새로고침
# =========================================================

with col2:

    st.write("")

    if st.button(
        "🔄 데이터 새로고침",
        use_container_width=True,
    ):
        st.cache_data.clear()
        st.rerun()


# =========================================================
# 26. 데이터 조회
# =========================================================

with st.spinner(
    "카카오 광고 데이터를 조회하고 있습니다..."
):

    result = fetch_kakao_data(
        ad_account_id,
        selected_year,
        selected_month,
    )


# =========================================================
# 27. API 오류
# =========================================================

if not result.get("success"):

    st.error("카카오 API 조회에 실패했습니다.")

    st.code(
        str(result.get("error")),
        language="json",
    )

    st.stop()


basic_df = result.get(
    "basic_df",
    pd.DataFrame(),
)

conversion_df = result.get(
    "conversion_df",
    pd.DataFrame(),
)

adgroup_meta = result.get(
    "adgroup_meta",
    [],
)


# =========================================================
# 28. 일별 데이터
# =========================================================

daily_df = make_full_date_dataframe(
    selected_year,
    selected_month,
    basic_df.copy(),
    conversion_df.copy(),
    adgroup_meta,
)


# =========================================================
# 29. 광고그룹 데이터
# =========================================================

group_df = make_adgroup_dataframe(
    basic_df.copy(),
    conversion_df.copy(),
    adgroup_meta,
)


# =========================================================
# 30. KPI 계산
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
    daily_df["service_signup_7d"].sum()
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
    total_cpa = (
        total_cost
        / total_signup
    )
else:
    total_cpa = 0


# =========================================================
# 31. 오늘 실시간 여부
# =========================================================

is_current_month = (
    selected_year == today.year
    and selected_month == today.month
)


# =========================================================
# 32. KPI
# =========================================================

st.divider()

st.subheader(
    f"📋 1. [카카오] {selected_month}월 일자별 상세 성과 리포트"
)


kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)


with kpi1:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">[카카오] 총 광고비</div>
            <div class="kpi-value">{format_won(total_cost)}</div>
            <div class="kpi-sub">
                ↑ API 수신
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with kpi2:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">[카카오] 서비스 신청</div>
            <div class="kpi-value">{format_number(total_signup)}건</div>
            <div class="kpi-sub">
                ↑ 서비스 신청 7일
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with kpi3:

    if total_signup > 0:
        cpa_text = format_won(total_cpa)
    else:
        cpa_text = "0원"

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">[카카오] 전환당 비용</div>
            <div class="kpi-value">{cpa_text}</div>
            <div class="kpi-sub">
                ↑ 광고비 ÷ 서비스 신청
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with kpi4:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">[카카오] CTR</div>
            <div class="kpi-value">{format_percent(total_ctr)}</div>
            <div class="kpi-sub">
                ↑ API 수신
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with kpi5:

    # 서비스 신청은 전환이므로
    # 매출액이 없으면 ROAS 계산 불가
    st.markdown(
        """
        <div class="kpi-card">
            <div class="kpi-title">[카카오] ROAS</div>
            <div class="kpi-value">매출 미연동</div>
            <div class="kpi-sub">
                ↑ 매출 연동 후 계산
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 33. 실시간 상태 표시
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
        "오늘 데이터는 카카오 API의 TODAY 기준으로 조회됩니다."
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
# 34. 일별 성과 표
# =========================================================

st.markdown(
    f"### 📊 [카카오] {selected_month}월 일자별 성과"
)

display_daily = daily_df.copy()

display_daily["총비용"] = display_daily["cost"].apply(
    format_won
)

display_daily["노출"] = display_daily["imp"].apply(
    format_number
)

display_daily["클릭수"] = display_daily["click"].apply(
    format_number
)

display_daily["CTR"] = display_daily["ctr"].apply(
    format_percent
)

display_daily["서비스 신청"] = (
    display_daily["service_signup_7d"]
    .apply(
        lambda x:
        f"{int(x):,}건"
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
        "서비스 신청",
        "CPA",
    ]
]

display_daily = display_daily.rename(
    columns={
        "date": "일자",
    }
)

st.dataframe(
    display_daily,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# 35. 광고그룹별 성과
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
        display_group[
            "service_signup_7d"
        ]
        .apply(
            lambda x:
            f"{int(x):,}건"
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
# 36. 핵심 안내
# =========================================================

st.divider()

with st.expander(
    "ℹ️ 전환수 집계 기준"
):

    st.write(
        """
        **전환수는 카카오모먼트의 `서비스 신청(7일)` 기준입니다.**

        카카오 API의 `PIXEL_SDK_CONVERSION` 지표 중
        `conv_signup_7d`를 사용합니다.

        따라서 카카오 관리자 화면에서 보이는
        `서비스 신청 (7일)`과 동일한 기준으로
        대시보드의 전환수를 표시합니다.
        """
    )

    st.write(
        """
        **오늘 데이터**

        오늘은 카카오 API의 `datePreset=TODAY`를
        별도로 호출합니다.

        따라서 오늘 광고비/노출/클릭/서비스 신청은
        전날까지 확정된 월간 데이터가 아니라
        현재 시점의 실시간성 데이터입니다.
        """
    )


# =========================================================
# 37. API 데이터 디버그
# =========================================================

with st.expander(
    "🔧 API 원본 데이터 확인"
):

    st.write(
        f"광고계정 ID: {ad_account_id}"
    )

    st.write(
        f"광고그룹 수: {len(adgroup_meta)}"
    )

    st.write(
        f"기본 보고서 행 수: {len(basic_df)}"
    )

    st.write(
        f"전환 보고서 행 수: {len(conversion_df)}"
    )

    if not basic_df.empty:

        st.write("BASIC 원본 변환 데이터")

        st.dataframe(
            basic_df,
            use_container_width=True,
            hide_index=True,
        )

    if not conversion_df.empty:

        st.write(
            "PIXEL_SDK_CONVERSION 원본 변환 데이터"
        )

        st.dataframe(
            conversion_df,
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# 38. AI 진단
# =========================================================

st.divider()

st.subheader(
    "🤖 AI 성과 진단"
)

if total_cost == 0 and total_signup == 0:

    st.info(
        "현재 조회된 광고 집행 데이터가 없습니다."
    )

else:

    diagnosis = []

    if total_ctr < 1:
        diagnosis.append(
            "CTR이 1% 미만으로 상대적으로 낮습니다. "
            "소재의 첫 화면 메시지와 클릭 유도 문구를 점검해보세요."
        )

    if total_signup > 0:

        diagnosis.append(
            f"현재 서비스 신청은 총 {total_signup:,}건이며 "
            f"CPA는 {total_cpa:,.0f}원입니다."
        )

    else:

        diagnosis.append(
            "현재 서비스 신청 전환이 확인되지 않습니다. "
            "픽셀/SDK 및 서비스 신청 전환 설정을 확인해보세요."
        )

    diagnosis.append(
        "ROAS는 현재 매출 데이터가 연결되지 않아 계산하지 않습니다."
    )

    for item in diagnosis:
        st.write(
            f"• {item}"
        )