```python
import base64
import hashlib
import hmac
from datetime import datetime, timedelta
import time

import pandas as pd
import requests
import streamlit as st


# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="멀티채널 마케팅 성과 대시보드",
    page_icon="📊",
    layout="wide"
)

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

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
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# ==========================================
# 2. 세션 상태
# ==========================================
if "selected_channel" not in st.session_state:
    st.session_state.selected_channel = "카카오"

channel_name = st.session_state.selected_channel


# ==========================================
# 3. API 인증 정보
# ==========================================

# ⚠️ 현재 전달받은 토큰
KAKAO_BUSINESS_TOKEN = (
    "dJpbpMsqnr1r9PV-cwGpbdOeimmhdwfOAAAAAwoNH9EAAAGhEBYDBlv0-avl6D9k"
)

# 네이버
NAVER_ACCESS_LICENSE = (
    "0100000000d6006534e1b94c00ea1af84cba8177cfdb1b63426ac5ccbd6b1a0065232175e8"
)

NAVER_SECRET_KEY = (
    "AQAAAADWAGU04blMAOoa+Ey6gXfPgL+rhl4UaY1olB5h2gnQWQ=="
)

NAVER_BASE_URL = "https://api.searchad.naver.com"


# 카카오 API
KAKAO_BASE_URL = "https://apis.moment.kakao.com/openapi/v4"


# ==========================================
# 4. 네이버 인증
# ==========================================

def generate_naver_signature(timestamp, method, uri, secret_key):

    message = f"{timestamp}.{method}.{uri}"

    signature = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()

    return base64.b64encode(signature).decode("utf-8")


def get_naver_header(method, uri, customer_id):

    timestamp = str(int(time.time() * 1000))

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
def fetch_naver_adgroups(customer_id):

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


# ==========================================
# 5. 카카오 공통 헤더
# ==========================================

def get_kakao_headers(ad_account_id):

    return {
        "Authorization": f"Bearer {KAKAO_BUSINESS_TOKEN}",
        "adAccountId": str(ad_account_id),
        "Content-Type": "application/json"
    }


# ==========================================
# 6. 카카오 API 공통 오류 처리
# ==========================================

def kakao_error_message(response):

    try:

        data = response.json()

        return (
            f"HTTP {response.status_code}\n"
            f"{data}"
        )

    except Exception:

        return (
            f"HTTP {response.status_code}\n"
            f"{response.text}"
        )


# ==========================================
# 7. 카카오 캠페인 조회
# ==========================================

@st.cache_data(ttl=300)
def fetch_kakao_campaigns(ad_account_id):

    url = f"{KAKAO_BASE_URL}/campaigns"

    headers = get_kakao_headers(ad_account_id)

    params = {
        "config": "ON"
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
                kakao_error_message(response)
            )

        data = response.json()

        return (
            data.get("content", []),
            True,
            ""
        )

    except Exception as e:

        return (
            [],
            False,
            str(e)
        )


# ==========================================
# 8. 카카오 광고그룹 조회
# ==========================================

@st.cache_data(ttl=300)
def fetch_kakao_adgroups(
    ad_account_id,
    campaign_id
):

    url = f"{KAKAO_BASE_URL}/adGroups"

    headers = get_kakao_headers(ad_account_id)

    params = {
        "campaignId": campaign_id,
        "config": "ON"
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
                kakao_error_message(response)
            )

        data = response.json()

        return (
            data.get("content", []),
            True,
            ""
        )

    except Exception as e:

        return (
            [],
            False,
            str(e)
        )


# ==========================================
# 9. 날짜 계산
# ==========================================

def get_month_dates(year, month):

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

    last_day = next_month - timedelta(days=1)

    # 카카오 보고서는 조회일 당일까지가 아니라
    # 조회일 전일까지 조회 가능
    yesterday = datetime.now() - timedelta(days=1)

    if last_day > yesterday:
        last_day = yesterday

    return (
        first_day.strftime("%Y%m%d"),
        last_day.strftime("%Y%m%d")
    )


# ==========================================
# 10. 카카오 광고그룹 보고서
# ==========================================

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
            False,
            "조회할 광고그룹이 없습니다."
        )

    url = f"{KAKAO_BASE_URL}/adGroups/report"

    headers = get_kakao_headers(ad_account_id)

    # 카카오 API는 한 번에 최대 40개 광고그룹
    chunks = [
        ad_group_ids[i:i + 40]
        for i in range(
            0,
            len(ad_group_ids),
            40
        )
    ]

    all_data = []

    try:

        for index, chunk in enumerate(chunks):

            # 광고계정/앱 기준 1초 제한
            if index > 0:
                time.sleep(1.1)

            params = [
                ("start", start_date),
                ("end", end_date),
                ("timeUnit", "DAY"),
                ("level", "AD_GROUP"),
                ("metricsGroup", "BASIC"),
            ]

            for ad_group_id in chunk:

                params.append(
                    ("adGroupId", str(ad_group_id))
                )

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=15
            )

            if response.status_code != 200:

                return (
                    all_data,
                    False,
                    kakao_error_message(response)
                )

            data = response.json()

            rows = data.get(
                "data",
                []
            )

            all_data.extend(rows)

        return (
            all_data,
            True,
            ""
        )

    except Exception as e:

        return (
            all_data,
            False,
            str(e)
        )


# ==========================================
# 11. 카카오 전체 데이터 조회
# ==========================================

@st.cache_data(ttl=300)
def fetch_kakao_realtime_data(
    ad_account_id,
    year,
    month
):

    # --------------------------------------
    # 1) 캠페인
    # --------------------------------------

    campaigns, success, error = fetch_kakao_campaigns(
        ad_account_id
    )

    if not success:

        return (
            pd.DataFrame(),
            {
                "cost": "0원",
                "sales": "0원",
                "roas": "0.0%",
                "goal": "0.0%"
            },
            False,
            error
        )

    if not campaigns:

        return (
            pd.DataFrame(),
            {
                "cost": "0원",
                "sales": "0원",
                "roas": "0.0%",
                "goal": "0.0%"
            },
            True,
            "활성 캠페인이 없습니다."
        )

    # --------------------------------------
    # 2) 광고그룹
    # --------------------------------------

    all_groups = []

    for campaign in campaigns:

        campaign_id = campaign.get("id")

        campaign_name = campaign.get(
            "name",
            "캠페인"
        )

        if not campaign_id:
            continue

        groups, group_success, group_error = fetch_kakao_adgroups(
            ad_account_id,
            campaign_id
        )

        if not group_success:

            return (
                pd.DataFrame(),
                {
                    "cost": "0원",
                    "sales": "0원",
                    "roas": "0.0%",
                    "goal": "0.0%"
                },
                False,
                group_error
            )

        for group in groups:

            all_groups.append({

                "campaign_id": campaign_id,

                "campaign_name": campaign_name,

                "ad_group_id": group.get(
                    "id"
                ),

                "ad_group_name": group.get(
                    "name",
                    "광고그룹"
                ),

                "config": group.get(
                    "config",
                    ""
                ),

                "systemConfig": group.get(
                    "systemConfig",
                    ""
                )
            })

    if not all_groups:

        return (
            pd.DataFrame(),
            {
                "cost": "0원",
                "sales": "0원",
                "roas": "0.0%",
                "goal": "0.0%"
            },
            True,
            "활성 광고그룹이 없습니다."
        )

    # --------------------------------------
    # 3) 조회 날짜
    # --------------------------------------

    start_date, end_date = get_month_dates(
        year,
        month
    )

    # 현재 월의 시작일보다 조회 가능한 날짜가 이전이면 종료
    if end_date < start_date:

        return (
            pd.DataFrame(),
            {
                "cost": "0원",
                "sales": "0원",
                "roas": "0.0%",
                "goal": "0.0%"
            },
            True,
            "아직 조회 가능한 날짜가 없습니다."
        )

    ad_group_ids = [
        x["ad_group_id"]
        for x in all_groups
        if x["ad_group_id"]
    ]

    # --------------------------------------
    # 4) 광고그룹 보고서
    # --------------------------------------

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
            {
                "cost": "0원",
                "sales": "0원",
                "roas": "0.0%",
                "goal": "0.0%"
            },
            False,
            report_error
        )

    # --------------------------------------
    # 5) 광고그룹 정보 + 보고서 매핑
    # --------------------------------------

    group_map = {
        str(x["ad_group_id"]): x
        for x in all_groups
    }

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

        ad_group_id = str(
            dimensions.get(
                "ad_group_id",
                ""
            )
        )

        if not ad_group_id:
            continue

        group_info = group_map.get(
            ad_group_id,
            {}
        )

        cost = float(
            metrics.get(
                "cost",
                0
            ) or 0
        )

        imp = int(
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

        rows.append({

            "일자": report.get(
                "start",
                ""
            ),

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
                if group_info.get("config") == "ON"
                else "중지/대기"
            ),

            "총비용": cost,

            "노출": imp,

            "클릭수": click,

            "CTR": ctr,

            "전환수": 0,

            "ROAS": 0.0
        })

    df = pd.DataFrame(rows)

    if df.empty:

        metrics_data = {
            "cost": "0원",
            "sales": "0원",
            "roas": "0.0%",
            "goal": "0.0%"
        }

        return (
            df,
            metrics_data,
            True,
            "보고서 데이터가 없습니다."
        )

    # ======================================
    # 6) 숫자 합계
    # ======================================

    total_cost = df["총비용"].sum()

    total_imp = df["노출"].sum()

    total_click = df["클릭수"].sum()

    total_ctr = (
        total_click / total_imp * 100
        if total_imp > 0
        else 0
    )

    # 현재 BASIC 보고서에는 매출이 없으므로
    # 실제 매출 연동 전까지 0으로 표시
    total_sales = 0

    total_roas = (
        total_sales / total_cost * 100
        if total_cost > 0
        else 0
    )

    metrics_data = {

        "cost": f"{int(total_cost):,}원",

        "sales": (
            "매출 API 필요"
        ),

        "roas": f"{total_roas:.1f}%",

        "goal": (
            f"{total_ctr:.1f}%"
        )
    }

    # 화면 표시용 포맷
    display_df = df.copy()

    display_df["총비용"] = (
        display_df["총비용"]
        .apply(
            lambda x: f"{int(x):,}원"
        )
    )

    display_df["노출"] = (
        display_df["노출"]
        .apply(
            lambda x: f"{int(x):,}"
        )
    )

    display_df["클릭수"] = (
        display_df["클릭수"]
        .apply(
            lambda x: f"{int(x):,}"
        )
    )

    display_df["CTR"] = (
        display_df["CTR"]
        .apply(
            lambda x: f"{x:.2f}%"
        )
    )

    display_df["전환수"] = (
        display_df["전환수"]
        .apply(
            lambda x: f"{int(x)}건"
        )
    )

    display_df["ROAS"] = (
        display_df["ROAS"]
        .apply(
            lambda x: f"{x:.1f}%"
        )
    )

    return (
        display_df,
        metrics_data,
        True,
        ""
    )


# ==========================================
# 12. AI 진단
# ==========================================

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
                "- **확인 필요**: 광고계정 권한, "
                "캠페인 및 광고그룹 상태를 확인하세요."
            ),

            "budget": (
                "- **예산 점검**: 현재 수신된 "
                "광고그룹 성과 데이터가 없습니다."
            ),

            "creative": (
                "- **소재 확인**: 카카오모먼트에서 "
                "광고 소재의 운영 상태를 확인하세요."
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
            "실시간 수신되는 노출·클릭·CTR 변동을 "
            "확인하세요."
        ),

        "budget": (
            "- **예산 최적화**: "
            "CTR과 광고비를 기준으로 성과가 우수한 "
            "광고그룹을 우선 관리하세요."
        ),

        "creative": (
            "- **소재 관리**: "
            "CTR이 낮아지는 소재는 새로운 배너와 "
            "A/B 테스트를 진행하세요."
        )
    }


# ==========================================
# 13. 이미지 다운로드
# ==========================================

@st.cache_data
def get_base64_image(url):

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
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


# ==========================================
# 14. 광고주 목록
# ==========================================

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


# ==========================================
# 15. 사이드바
# ==========================================

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
            <img src="{base64_logo}"
            style="
                width:100%;
                aspect-ratio:1/1;
                object-fit:contain;
                border-radius:6px;
                background:#ffffff;
                padding:4px;
                margin-bottom:5px;
            ">
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


# ==========================================
# 16. 광고주 선택
# ==========================================

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
        f"{current_advertiser_name} 성과 대시보드"
    )

    st.markdown(
        f"선택하신 **{channel_name}** 채널의 "
        "실시간 API 데이터를 조회합니다."
    )


st.markdown("---")


# ==========================================
# 17. 조회 월
# ==========================================

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


# ==========================================
# 18. 기본 데이터
# ==========================================

df_groups = pd.DataFrame()

metrics_data = {

    "cost": "0원",

    "sales": "0원",

    "roas": "0.0%",

    "goal": "0.0%"
}


api_success = False

api_error = ""


# ==========================================
# 19. 카카오 데이터 호출
# ==========================================

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
        ) = fetch_kakao_realtime_data(

            selected_id,

            datetime.now().year,

            selected_month_number
        )


# ==========================================
# 20. 네이버
# ==========================================

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

            status_display = (

                "대기중/미진행"

                if raw_status
                in [
                    "PAUSED",
                    "STOP",
                    "SUSPENDED"
                ]

                else raw_status
            )

            rows.append({

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
            })

        df_groups = pd.DataFrame(
            rows
        )


# ==========================================
# 21. 카카오 API 오류 표시
# ==========================================

if channel_name == "카카오" and not api_success:

    st.error(
        "❌ 카카오모먼트 API 연동 실패"
    )

    if api_error:

        with st.expander(
            "🔎 카카오 API 실제 응답 확인"
        ):

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


# ==========================================
# 22. 핵심 지표
# ==========================================

col1, col2, col3, col4 = st.columns(
    4
)


with col1:

    st.metric(

        label=f"[{channel_name}] 총 광고비",

        value=metrics_data["cost"],

        delta="실시간 수신"
    )


with col2:

    st.metric(

        label=f"[{channel_name}] 총 매출액",

        value=metrics_data["sales"],

        delta="현재 미연동"
    )


with col3:

    st.metric(

        label=f"[{channel_name}] 평균 ROAS",

        value=metrics_data["roas"],

        delta="현재 매출 미연동"
    )


with col4:

    st.metric(

        label="CTR",

        value=metrics_data["goal"],

        delta="실시간 수신"
    )


st.markdown("---")


# ==========================================
# 23. 일자별 데이터
# ==========================================

st.subheader(
    f"📅 [{channel_name}] "
    f"{selected_month} 일자별 성과"
)


if (
    channel_name == "카카오"
    and not df_groups.empty
):

    daily_df = df_groups.copy()

    # 일자 기준 합계
    # 문자열 포맷을 다시 숫자로 변환
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
        .agg({

            "총비용_숫자": "sum",

            "노출_숫자": "sum",

            "클릭_숫자": "sum"
        })
    )

    daily["CTR"] = daily.apply(

        lambda row:
        (
            row["클릭_숫자"]
            /
            row["노출_숫자"]
            * 100
        )
        if row["노출_숫자"] > 0
        else 0,

        axis=1
    )

    daily["총비용"] = daily[
        "총비용_숫자"
    ].apply(
        lambda x: f"{int(x):,}원"
    )

    daily["노출"] = daily[
        "노출_숫자"
    ].apply(
        lambda x: f"{int(x):,}"
    )

    daily["클릭수"] = daily[
        "클릭_숫자"
    ].apply(
        lambda x: f"{int(x):,}"
    )

    daily["CTR"] = daily[
        "CTR"
    ].apply(
        lambda x: f"{x:.2f}%"
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


# ==========================================
# 24. 캠페인 그룹별 데이터
# ==========================================

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

    if channel_name == "카카오":

        st.warning(
            f"[{channel_name}] 채널의 "
            f"[{current_advertiser_name}] 계정에서 "
            "조회할 수 있는 광고그룹 데이터가 없습니다."
        )

    else:

        st.warning(
            f"[{channel_name}] 채널의 "
            f"[{current_advertiser_name}] 계정에서 "
            "조회할 수 있는 데이터가 없습니다."
        )


st.markdown("---")


# ==========================================
# 25. AI 진단
# ==========================================

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
```
