import base64
import hashlib
import hmac
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st


# =========================================================
# 1. 페이지 설정
# =========================================================

st.set_page_config(
    page_title="멀티채널 마케팅 성과 대시보드",
    page_icon="📊",
    layout="wide"
)


# =========================================================
# 2. 기본 CSS
# =========================================================

st.markdown(
    """
    <style>
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    [data-testid="stSidebar"] {
        background-color: #1e293b;
        min-width: 90px !important;
        max-width: 90px !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }

    [data-testid="stSidebar"] img {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        object-fit: contain !important;
        border-radius: 6px;
        background-color: #ffffff;
        padding: 4px;
    }

    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        width: 100% !important;
        text-align: center !important;
        padding: 10px 0 !important;
        margin-bottom: 6px;
        border-radius: 6px;
    }

    [data-testid="stSidebar"] div.stButton > button p {
        color: #ffffff !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }

    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 3. 세션 상태
# =========================================================

if "selected_channel" not in st.session_state:
    st.session_state.selected_channel = "카카오"

channel_name = st.session_state.selected_channel


# =========================================================
# 4. API 인증 정보
# =========================================================

# 카카오모먼트 비즈니스 토큰
KAKAO_BUSINESS_TOKEN = (
    "dJpbpMsqnr1r9PV-cwGpbdOeimmhdwfOAAAAAwoNH9EAAAGhEBYDBlv0-avl6D9k"
)

KAKAO_BASE_URL = (
    "https://apis.moment.kakao.com/openapi/v4"
)


# 네이버
NAVER_ACCESS_LICENSE = (
    "0100000000d6006534e1b94c00ea1af84cba8177cfdb1b63426ac5ccbd6b1a0065232175e8"
)

NAVER_SECRET_KEY = (
    "AQAAAADWAGU04blMAOoa+Ey6gXfPgL+rhl4UaY1olB5h2gnQWQ=="
)

NAVER_BASE_URL = (
    "https://api.searchad.naver.com"
)


# =========================================================
# 5. 광고주 목록
# =========================================================

advertisers_map = {
    "네이버": {
        "2274356": "asap-ad (2274356)",
        "987505": "GHB (987505)",
        "1001864": "금하 (1001864)",
    },

    "카카오": {
        "995724": "리만 (995724)",
        "558725": "asap-ad (558725)",
        "987505": "GHB (987505)",
    },

    "토스": {
        "112233": "asap-ad (112233)",
    },

    "메타": {
        "998877": "asap-ad (998877)",
    },
}


# =========================================================
# 6. 네이버 API
# =========================================================

def generate_naver_signature(
    timestamp,
    method,
    uri,
    secret_key
):
    message = f"{timestamp}.{method}.{uri}"

    signature = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()

    return base64.b64encode(signature).decode("utf-8")


def get_naver_header(
    method,
    uri,
    customer_id
):

    timestamp = str(
        int(time.time() * 1000)
    )

    signature = generate_naver_signature(
        timestamp,
        method,
        uri,
        NAVER_SECRET_KEY
    )

    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": NAVER_ACCESS_LICENSE,
        "X-Customer": str(customer_id),
        "X-Signature": signature,
    }


@st.cache_data(ttl=600)
def fetch_naver_adgroups(
    customer_id
):

    uri = "/ncc/adgroups"

    url = NAVER_BASE_URL + uri

    headers = get_naver_header(
        "GET",
        uri,
        customer_id
    )

    params = {
        "nccAccountId": customer_id
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()

        return []

    except Exception:

        return []


# =========================================================
# 7. 카카오 API 공통 헤더
# =========================================================

def get_kakao_headers(
    ad_account_id
):

    return {
        "Authorization": (
            f"Bearer {KAKAO_BUSINESS_TOKEN}"
        ),
        "adAccountId": str(ad_account_id),
        "Content-Type": "application/json",
    }


# =========================================================
# 8. 카카오 API 오류 내용 추출
# =========================================================

def get_kakao_error(
    response
):

    try:

        data = response.json()

        return (
            f"HTTP 상태코드: {response.status_code}\n\n"
            f"카카오 응답:\n"
            f"{data}"
        )

    except Exception:

        return (
            f"HTTP 상태코드: {response.status_code}\n\n"
            f"카카오 응답:\n"
            f"{response.text}"
        )


# =========================================================
# 9. 카카오 캠페인 조회
#
# 공식 API
# GET /openapi/v4/campaigns
#
# adAccountId = Header
# =========================================================

@st.cache_data(ttl=300)
def fetch_kakao_campaigns(
    ad_account_id
):

    url = (
        f"{KAKAO_BASE_URL}/campaigns"
    )

    headers = get_kakao_headers(
        ad_account_id
    )

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:

            return (
                [],
                False,
                get_kakao_error(response)
            )

        data = response.json()

        campaigns = data.get(
            "content",
            []
        )

        return (
            campaigns,
            True,
            ""
        )

    except Exception as e:

        return (
            [],
            False,
            f"카카오 캠페인 조회 오류: {e}"
        )


# =========================================================
# 10. 카카오 광고그룹 조회
#
# 공식 API
# GET /openapi/v4/adGroups
#
# campaignId = 필수
# adAccountId = Header
# =========================================================

@st.cache_data(ttl=300)
def fetch_kakao_adgroups(
    ad_account_id,
    campaign_id
):

    url = (
        f"{KAKAO_BASE_URL}/adGroups"
    )

    headers = get_kakao_headers(
        ad_account_id
    )

    params = {
        "campaignId": str(campaign_id)
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code != 200:

            return (
                [],
                False,
                get_kakao_error(response)
            )

        data = response.json()

        groups = data.get(
            "content",
            []
        )

        return (
            groups,
            True,
            ""
        )

    except Exception as e:

        return (
            [],
            False,
            f"카카오 광고그룹 조회 오류: {e}"
        )


# =========================================================
# 11. 조회 날짜
# =========================================================

def get_report_dates(
    year,
    month
):

    first_day = datetime(
        year,
        month,
        1
    )

    if month == 12:

        next_month = datetime(
            year + 1,
            1,
            1
        )

    else:

        next_month = datetime(
            year,
            month + 1,
            1
        )

    last_day = (
        next_month
        - timedelta(days=1)
    )

    # 카카오 API는 오늘 데이터가 아니라
    # 조회일 전일까지 기간 조회 가능
    yesterday = (
        datetime.now()
        - timedelta(days=1)
    )

    if last_day > yesterday:

        last_day = yesterday

    if first_day > last_day:

        return None, None

    return (
        first_day.strftime("%Y%m%d"),
        last_day.strftime("%Y%m%d")
    )


# =========================================================
# 12. 카카오 광고그룹 보고서
#
# 공식 API
# GET /openapi/v4/adGroups/report
#
# adGroupId 최대 40개
# timeUnit = DAY
# level = AD_GROUP
# metricsGroup = BASIC
# =========================================================

@st.cache_data(ttl=300)
def fetch_kakao_adgroup_report(
    ad_account_id,
    ad_group_ids,
    start_date,
    end_date
):

    if not ad_group_ids:

        return (
            [],
            True,
            "조회할 광고그룹이 없습니다."
        )

    url = (
        f"{KAKAO_BASE_URL}/adGroups/report"
    )

    headers = get_kakao_headers(
        ad_account_id
    )

    all_report_data = []

    # 공식 최대 40개
    chunks = []

    for i in range(
        0,
        len(ad_group_ids),
        40
    ):

        chunks.append(
            ad_group_ids[i:i + 40]
        )

    try:

        for chunk_index, chunk in enumerate(
            chunks
        ):

            # 요청 제한
            if chunk_index > 0:
                time.sleep(1.1)

            params = [
                ("start", start_date),
                ("end", end_date),
                ("timeUnit", "DAY"),
                ("level", "AD_GROUP"),
                ("metricsGroup", "BASIC"),
            ]

            # Long[] 형식
            for ad_group_id in chunk:

                params.append(
                    (
                        "adGroupId",
                        str(ad_group_id)
                    )
                )

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=20
            )

            if response.status_code != 200:

                return (
                    all_report_data,
                    False,
                    get_kakao_error(response)
                )

            data = response.json()

            report_rows = data.get(
                "data",
                []
            )

            all_report_data.extend(
                report_rows
            )

        return (
            all_report_data,
            True,
            ""
        )

    except Exception as e:

        return (
            all_report_data,
            False,
            f"카카오 보고서 조회 오류: {e}"
        )


# =========================================================
# 13. 카카오 전체 데이터
# =========================================================

@st.cache_data(ttl=300)
def fetch_kakao_data(
    ad_account_id,
    year,
    month
):

    # -----------------------------------------------------
    # A. 날짜
    # -----------------------------------------------------

    start_date, end_date = (
        get_report_dates(
            year,
            month
        )
    )

    if not start_date:

        return (
            pd.DataFrame(),
            {},
            False,
            "현재 월은 아직 조회 가능한 날짜가 없습니다."
        )

    # -----------------------------------------------------
    # B. 캠페인 조회
    # -----------------------------------------------------

    campaigns, success, error = (
        fetch_kakao_campaigns(
            ad_account_id
        )
    )

    if not success:

        return (
            pd.DataFrame(),
            {},
            False,
            error
        )

    # -----------------------------------------------------
    # C. 광고그룹 조회
    # -----------------------------------------------------

    all_groups = []

    for campaign in campaigns:

        campaign_id = campaign.get(
            "id"
        )

        campaign_name = campaign.get(
            "name",
            "캠페인"
        )

        campaign_config = campaign.get(
            "config",
            ""
        )

        if not campaign_id:
            continue

        groups, group_success, group_error = (
            fetch_kakao_adgroups(
                ad_account_id,
                campaign_id
            )
        )

        if not group_success:

            return (
                pd.DataFrame(),
                {},
                False,
                group_error
            )

        for group in groups:

            group_id = group.get(
                "id"
            )

            if not group_id:
                continue

            all_groups.append(
                {
                    "campaign_id": campaign_id,

                    "campaign_name": campaign_name,

                    "campaign_config": campaign_config,

                    "ad_group_id": group_id,

                    "ad_group_name": group.get(
                        "name",
                        "광고그룹"
                    ),

                    "group_config": group.get(
                        "config",
                        ""
                    ),

                    "system_config": group.get(
                        "systemConfig",
                        ""
                    ),
                }
            )

    # -----------------------------------------------------
    # D. 광고그룹이 없는 경우
    # -----------------------------------------------------

    if not all_groups:

        return (
            pd.DataFrame(),
            {
                "cost": "0원",
                "sales": "매출 미연동",
                "roas": "0.0%",
                "ctr": "0.00%"
            },
            True,
            "캠페인은 확인되지만 광고그룹이 없습니다."
        )

    # -----------------------------------------------------
    # E. 광고그룹 ID
    # -----------------------------------------------------

    ad_group_ids = []

    for group in all_groups:

        group_id = group.get(
            "ad_group_id"
        )

        if group_id:

            ad_group_ids.append(
                group_id
            )

    # 중복 제거
    ad_group_ids = list(
        dict.fromkeys(
            ad_group_ids
        )
    )

    # -----------------------------------------------------
    # F. 보고서 조회
    # -----------------------------------------------------

    report_data, report_success, report_error = (
        fetch_kakao_adgroup_report(
            ad_account_id,
            ad_group_ids,
            start_date,
            end_date
        )
    )

    if not report_success:

        return (
            pd.DataFrame(),
            {},
            False,
            report_error
        )

    # -----------------------------------------------------
    # G. 광고그룹 정보 매핑
    # -----------------------------------------------------

    group_map = {}

    for group in all_groups:

        group_map[
            str(group["ad_group_id"])
        ] = group

    rows = []

    for report in report_data:

        dimensions = report.get(
            "dimensions",
            {}
        )

        metrics = report.get(
            "metrics",
            {}
        )

        ad_group_id = dimensions.get(
            "ad_group_id"
        )

        if not ad_group_id:
            continue

        group_info = group_map.get(
            str(ad_group_id),
            {}
        )

        # 기본 지표
        cost = float(
            metrics.get(
                "cost",
                0
            ) or 0
        )

        impression = int(
            metrics.get(
                "imp",
                0
            ) or 0
        )

        click = int(
            metrics.get(
                "click",
                0
            ) or 0
        )

        ctr = float(
            metrics.get(
                "ctr",
                0
            ) or 0
        )

        # 날짜
        report_date = report.get(
            "start",
            ""
        )

        rows.append(
            {
                "일자": report_date,

                "캠페인명": group_info.get(
                    "campaign_name",
                    "-"
                ),

                "그룹명": group_info.get(
                    "ad_group_name",
                    "-"
                ),

                "상태": (
                    "노출중"
                    if group_info.get(
                        "group_config"
                    ) == "ON"
                    else "중지/대기"
                ),

                "총비용": cost,

                "노출": impression,

                "클릭수": click,

                "CTR": ctr,

                "전환수": 0,

                "ROAS": 0.0,
            }
        )

    # -----------------------------------------------------
    # H. 데이터 없음
    # -----------------------------------------------------

    if not rows:

        return (
            pd.DataFrame(),
            {
                "cost": "0원",
                "sales": "매출 미연동",
                "roas": "0.0%",
                "ctr": "0.00%"
            },
            True,
            "선택한 기간에 광고 성과 데이터가 없습니다."
        )

    # -----------------------------------------------------
    # I. DataFrame
    # -----------------------------------------------------

    df = pd.DataFrame(
        rows
    )

    # -----------------------------------------------------
    # J. 전체 지표
    # -----------------------------------------------------

    total_cost = df[
        "총비용"
    ].sum()

    total_imp = df[
        "노출"
    ].sum()

    total_click = df[
        "클릭수"
    ].sum()

    total_ctr = (
        total_click
        / total_imp
        * 100
        if total_imp > 0
        else 0
    )

    # 현재는 BASIC만 조회
    # 매출/전환은 이후 별도 지표 연결
    total_sales = 0

    total_roas = (
        total_sales
        / total_cost
        * 100
        if total_cost > 0
        else 0
    )

    metrics_data = {
        "cost": f"{int(total_cost):,}원",

        "sales": "매출 미연동",

        "roas": f"{total_roas:.1f}%",

        "ctr": f"{total_ctr:.2f}%"
    }

    # -----------------------------------------------------
    # K. 화면 표시용 DataFrame
    # -----------------------------------------------------

    display_df = df.copy()

    display_df["총비용"] = (
        display_df["총비용"]
        .apply(
            lambda x:
            f"{int(x):,}원"
        )
    )

    display_df["노출"] = (
        display_df["노출"]
        .apply(
            lambda x:
            f"{int(x):,}"
        )
    )

    display_df["클릭수"] = (
        display_df["클릭수"]
        .apply(
            lambda x:
            f"{int(x):,}"
        )
    )

    display_df["CTR"] = (
        display_df["CTR"]
        .apply(
            lambda x:
            f"{x:.2f}%"
        )
    )

    display_df["전환수"] = (
        display_df["전환수"]
        .apply(
            lambda x:
            f"{int(x)}건"
        )
    )

    display_df["ROAS"] = (
        display_df["ROAS"]
        .apply(
            lambda x:
            f"{x:.1f}%"
        )
    )

    return (
        display_df,
        metrics_data,
        True,
        ""
    )


# =========================================================
# 14. AI 진단
# =========================================================

def generate_ai_diagnosis(
    channel,
    advertiser,
    df_groups
):

    if df_groups.empty:

        return {
            "status_msg": (
                f"현재 **[{channel}]** 채널의 "
                f"**{advertiser}** 계정에서 "
                "조회 가능한 광고 데이터가 없습니다."
            ),

            "urgent": (
                "- **확인 필요**: "
                "광고계정 권한, 캠페인, "
                "광고그룹 상태를 확인하세요."
            ),

            "budget": (
                "- **예산 점검**: "
                "현재 수신된 성과 데이터가 없습니다."
            ),

            "creative": (
                "- **소재 확인**: "
                "카카오모먼트에서 광고 소재 상태를 확인하세요."
            )
        }

    return {
        "status_msg": (
            f"현재 **[{channel}]** 채널에서 "
            f"**{advertiser}**의 광고 데이터가 "
            "정상적으로 연동되고 있습니다."
        ),

        "urgent": (
            "- **효율 모니터링**: "
            "노출, 클릭, CTR 변동을 확인하세요."
        ),

        "budget": (
            "- **예산 최적화**: "
            "CTR과 광고비가 우수한 그룹을 중심으로 "
            "예산을 검토하세요."
        ),

        "creative": (
            "- **소재 관리**: "
            "CTR이 낮은 소재는 새로운 소재와 "
            "A/B 테스트를 진행하세요."
        )
    }


# =========================================================
# 15. 이미지
# =========================================================

@st.cache_data
def get_base64_image(
    url
):

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10
        )

        if response.status_code == 200:

            encoded = base64.b64encode(
                response.content
            ).decode("utf-8")

            return (
                f"data:image/jpeg;base64,{encoded}"
            )

    except Exception:
        pass

    return ""


# =========================================================
# 16. 사이드바
# =========================================================

with st.sidebar:

    logo_url = (
        "https://postfiles.pstatic.net/"
        "MjAyNjEwMDJfMTk3/"
        "MDAxNzkwOTI2NjI1NDQ3."
        "onXBC4S3HbypXqgaIBTI9nkbxszhk00IW9KGCVlcXmEg."
        "bpswq-tDbouId6KoFEK7PUFcMZCE8VkQ3_oKcqkIDc8g."
        "JPEG/"
        "KakaoTalk_20261002_100449413_01.jpg"
        "?type=w966"
    )

    base64_logo = get_base64_image(
        logo_url
    )

    if base64_logo:

        st.markdown(
            f"""
            <img
                src="{base64_logo}"
                style="
                    width:100%;
                    aspect-ratio:1/1;
                    object-fit:contain;
                    border-radius:6px;
                    background:#ffffff;
                    padding:4px;
                    margin-bottom:5px;
                "
            >
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        "<hr style='margin:15px 0;border-color:#334155;'>",
        unsafe_allow_html=True
    )

    channels = [
        "카카오",
        "토스",
        "메타",
        "네이버"
    ]

    for ch in channels:

        if st.button(
            ch,
            key=f"btn_{ch}",
            use_container_width=True
        ):

            if (
                st.session_state.selected_channel
                != ch
            ):

                st.session_state.selected_channel = ch

                st.cache_data.clear()

                st.rerun()


# =========================================================
# 17. 광고주 선택
# =========================================================

current_advertisers = advertisers_map.get(
    channel_name,
    {}
)

if not current_advertisers:

    current_advertisers = {
        "default": "등록된 광고주 없음"
    }

advertiser_ids = list(
    current_advertisers.keys()
)


header_col1, header_col2 = st.columns(
    [2, 1]
)


with header_col2:

    selected_id = st.selectbox(
        "📌 광고주 선택",
        options=advertiser_ids,
        format_func=lambda x:
            current_advertisers[x],
        key="advertiser_selectbox"
    )


current_advertiser_name = (
    current_advertisers.get(
        selected_id,
        "알 수 없는 광고주"
    )
)


with header_col1:

    st.title(
        f"📊 [{channel_name}] "
        f"{current_advertiser_name} "
        "성과 대시보드"
    )

    st.markdown(
        f"선택하신 **{channel_name}** 채널의 "
        "API 데이터를 조회합니다."
    )


st.markdown("---")


# =========================================================
# 18. 월 선택
# =========================================================

section_col1, section_col2 = st.columns(
    [3, 1]
)


with section_col1:

    st.subheader(
        f"📅 1. [{channel_name}] "
        "일자별 상세 성과 리포트"
    )


with section_col2:

    month_options = [
        "1월",
        "2월",
        "3월",
        "4월",
        "5월",
        "6월",
        "7월",
        "8월",
        "9월",
        "10월",
        "11월",
        "12월"
    ]

    current_month = datetime.now().month

    selected_month = st.selectbox(
        "조회 월",
        options=month_options,
        index=current_month - 1,
        key="month_select"
    )


selected_month_number = (
    month_options.index(
        selected_month
    ) + 1
)


# =========================================================
# 19. 기본값
# =========================================================

df_groups = pd.DataFrame()

metrics_data = {
    "cost": "0원",
    "sales": "0원",
    "roas": "0.0%",
    "ctr": "0.00%"
}

api_success = True
api_error = ""


# =========================================================
# 20. 카카오
# =========================================================

if channel_name == "카카오":

    with st.spinner(
        f"카카오모먼트 API 호출 중 "
        f"({current_advertiser_name})..."
    ):

        (
            df_groups,
            metrics_data,
            api_success,
            api_error
        ) = fetch_kakao_data(
            selected_id,
            datetime.now().year,
            selected_month_number
        )


# =========================================================
# 21. 네이버
# =========================================================

elif channel_name == "네이버":

    with st.spinner(
        f"네이버 광고 그룹 정보 "
        f"({current_advertiser_name}) "
        "불러오는 중..."
    ):

        adgroups_data = (
            fetch_naver_adgroups(
                selected_id
            )
        )

    if adgroups_data:

        rows = []

        for group in adgroups_data:

            raw_status = group.get(
                "status",
                ""
            )

            if raw_status in [
                "PAUSED",
                "STOP",
                "SUSPENDED"
            ]:

                status_display = (
                    "대기중/미진행"
                )

            else:

                status_display = raw_status

            rows.append(
                {
                    "그룹명": group.get(
                        "name",
                        "-"
                    ),

                    "상태": status_display,

                    "총비용": "0원",

                    "노출": "0",

                    "클릭수": "0",

                    "CTR": "0.00%",

                    "전환수": "0건",

                    "ROAS": "0.0%"
                }
            )

        df_groups = pd.DataFrame(
            rows
        )


# =========================================================
# 22. API 오류 표시
# =========================================================

if (
    channel_name == "카카오"
    and not api_success
):

    st.error(
        "❌ 카카오모먼트 API 호출에 실패했습니다."
    )

    st.markdown(
        "### 🔎 카카오 서버가 반환한 실제 오류"
    )

    st.code(
        api_error,
        language="text"
    )

elif (
    channel_name == "카카오"
    and api_success
    and api_error
):

    st.info(
        f"ℹ️ {api_error}"
    )


# =========================================================
# 23. 핵심 지표
# =========================================================

col1, col2, col3, col4 = st.columns(
    4
)


with col1:

    st.metric(
        label=f"[{channel_name}] 총 광고비",
        value=metrics_data["cost"],
        delta="API 수신"
    )


with col2:

    st.metric(
        label=f"[{channel_name}] 총 매출액",
        value=metrics_data["sales"],
        delta="추후 연동"
    )


with col3:

    st.metric(
        label=f"[{channel_name}] 평균 ROAS",
        value=metrics_data["roas"],
        delta="매출 연동 후 계산"
    )


with col4:

    st.metric(
        label=f"[{channel_name}] CTR",
        value=metrics_data["ctr"],
        delta="API 수신"
    )


st.markdown("---")


# =========================================================
# 24. 일자별 성과
# =========================================================

st.subheader(
    f"📅 [{channel_name}] "
    f"{selected_month} 일자별 성과"
)


if (
    channel_name == "카카오"
    and not df_groups.empty
):

    daily_df = df_groups.copy()

    daily_df["총비용_숫자"] = (
        daily_df["총비용"]
        .astype(str)
        .str.replace(
            ",",
            "",
            regex=False
        )
        .str.replace(
            "원",
            "",
            regex=False
        )
        .astype(float)
    )

    daily_df["노출_숫자"] = (
        daily_df["노출"]
        .astype(str)
        .str.replace(
            ",",
            "",
            regex=False
        )
        .astype(float)
    )

    daily_df["클릭_숫자"] = (
        daily_df["클릭수"]
        .astype(str)
        .str.replace(
            ",",
            "",
            regex=False
        )
        .astype(float)
    )

    daily = (
        daily_df
        .groupby(
            "일자",
            as_index=False
        )
        .agg(
            {
                "총비용_숫자": "sum",
                "노출_숫자": "sum",
                "클릭_숫자": "sum"
            }
        )
    )

    daily["CTR_숫자"] = daily.apply(
        lambda row:
        (
            row["클릭_숫자"]
            / row["노출_숫자"]
            * 100
        )
        if row["노출_숫자"] > 0
        else 0,
        axis=1
    )

    daily["총비용"] = (
        daily["총비용_숫자"]
        .apply(
            lambda x:
            f"{int(x):,}원"
        )
    )

    daily["노출"] = (
        daily["노출_숫자"]
        .apply(
            lambda x:
            f"{int(x):,}"
        )
    )

    daily["클릭수"] = (
        daily["클릭_숫자"]
        .apply(
            lambda x:
            f"{int(x):,}"
        )
    )

    daily["CTR"] = (
        daily["CTR_숫자"]
        .apply(
            lambda x:
            f"{x:.2f}%"
        )
    )

    daily["전환수"] = "미연동"

    daily["ROAS"] = "미연동"

    daily = daily[
        [
            "일자",
            "총비용",
            "노출",
            "클릭수",
            "CTR",
            "전환수",
            "ROAS"
        ]
    ]

    st.dataframe(
        daily,
        hide_index=True,
        use_container_width=True,
        height=300
    )

else:

    empty_df = pd.DataFrame(
        columns=[
            "일자",
            "총비용",
            "노출",
            "클릭수",
            "CTR",
            "전환수",
            "ROAS"
        ]
    )

    st.dataframe(
        empty_df,
        hide_index=True,
        use_container_width=True,
        height=200
    )


st.markdown("---")


# =========================================================
# 25. 광고그룹별 성과
# =========================================================

st.subheader(
    f"📂 2. [{channel_name}] "
    f"캠페인 그룹별 실시간 소진 내역 "
    f"({selected_month})"
)


if not df_groups.empty:

    st.dataframe(
        df_groups,
        hide_index=True,
        use_container_width=True
    )

else:

    st.warning(
        f"[{channel_name}] "
        f"[{current_advertiser_name}] 계정에서 "
        "조회 가능한 광고그룹 데이터가 없습니다."
    )


st.markdown("---")


# =========================================================
# 26. AI 진단
# =========================================================

st.subheader(
    f"🤖 AI 퍼포먼스 마케팅 진단 & 제안 "
    f"({current_advertiser_name})"
)


ai_diagnosis = generate_ai_diagnosis(
    channel_name,
    current_advertiser_name,
    df_groups
)


with st.container():

    st.markdown(
        f"""
> **💡 AI 실시간 운영 상태 판단**
>
> * {ai_diagnosis["status_msg"]}
"""
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🚨 긴급 개선점",
            "💰 예산 재배분 제안",
            "🎨 크리에이티브 전략"
        ]
    )

    with tab1:

        st.markdown(
            ai_diagnosis["urgent"]
        )

    with tab2:

        st.markdown(
            ai_diagnosis["budget"]
        )

    with tab3:

        st.markdown(
            ai_diagnosis["creative"]
        )