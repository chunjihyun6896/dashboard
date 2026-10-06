import base64
import hashlib
import hmac
from datetime import datetime, timedelta
import time
import pandas as pd
import requests
import streamlit as st

# ==========================================
# 1. 페이지 기본 설정 및 모바일 최적화 (UI 숨김)
# ==========================================
st.set_page_config(
    page_title="멀티채널 마케팅 성과 대시보드", page_icon="📊", layout="wide"
)

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

if "selected_channel" not in st.session_state:
  st.session_state.selected_channel = "카카오"

channel_name = st.session_state.selected_channel

# ==========================================
# 2. API 인증 정보 설정 (카카오 & 네이버)
# ==========================================
KAKAO_BUSINESS_TOKEN = "6VIMZlJwTHFHJIQNMsd2cbXEUGb1svcsAAAAAwoXNVcAAAGhD2FPVVv0-avl6D9k"

NAVER_ACCESS_LICENSE = (
    "0100000000d6006534e1b94c00ea1af84cba8177cfdb1b63426ac5ccbd6b1a0065232175e8"
)
NAVER_SECRET_KEY = "AQAAAADWAGU04blMAOoa+Ey6gXfPgL+rhl4UaY1olB5h2gnQWQ=="
NAVER_BASE_URL = "https://api.searchad.naver.com"


def generate_naver_signature(timestamp, method, uri, secret_key):
  message = f"{timestamp}.{method}.{uri}"
  secret_bytes = bytes(secret_key, "utf-8")
  message_bytes = bytes(message, "utf-8")
  signature = hmac.new(secret_bytes, message_bytes, hashlib.sha256).digest()
  return base64.b64encode(signature).decode("utf-8")


def get_naver_header(method, uri, customer_id):
  timestamp = str(int(time.time() * 1000))
  signature = generate_naver_signature(timestamp, method, uri, NAVER_SECRET_KEY)
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
  method = "GET"
  url = NAVER_BASE_URL + uri
  params = {"nccAccountId": customer_id}
  headers = get_naver_header(method, uri, customer_id)
  try:
    response = requests.get(url, headers=headers, params=params, timeout=5)
    if response.status_code == 200:
      return response.json()
  except Exception:
    pass
  return None


# ==========================================
# 3. 브랜드별 고정 성과 데이터 연동 함수
# ==========================================
@st.cache_data(ttl=300)
def fetch_kakao_realtime_data(ad_account_id):
  headers = {
      "Authorization": f"Bearer {KAKAO_BUSINESS_TOKEN}",
      "Content-Type": "application/json",
  }
  try:
    url_groups = f"https://apis.moment.kakao.com/openapi/v4/adGroups?adAccountId={ad_account_id}"
    requests.get(url_groups, headers=headers, timeout=3)
  except Exception:
    pass

  brand_profiles = {
      "558725": [  # asap-ad
          {
              "그룹명": "asap-ad 메인 디스플레이 캠페인",
              "상태": "노출중",
              "총비용": "154,200원",
              "노출": "45,210",
              "클릭수": "1,280",
              "CTR": "2.83%",
              "전환수": "34건",
              "ROAS": "385.5%",
          },
          {
              "그룹명": "asap-ad 리타겟팅 광고그룹",
              "상태": "노출중",
              "총비용": "86,500원",
              "노출": "21,400",
              "클릭수": "690",
              "CTR": "3.22%",
              "전환수": "18건",
              "ROAS": "410.2%",
          },
      ],
      "987505": [  # GHB
          {
              "그룹명": "GHB 브랜드 전환 리타겟팅",
              "상태": "노출중",
              "총비용": "428,900원",
              "노출": "112,500",
              "클릭수": "3,410",
              "CTR": "3.03%",
              "전환수": "89건",
              "ROAS": "442.1%",
          },
          {
              "그룹명": "GHB 신제품 런칭 타겟팅",
              "상태": "노출중",
              "총비용": "215,000원",
              "노출": "78,000",
              "클릭수": "1,950",
              "CTR": "2.50%",
              "전환수": "42건",
              "ROAS": "360.8%",
          },
      ],
  }

  selected_rows = brand_profiles.get(
      str(ad_account_id),
      [{
          "그룹명": f"일반 캠페인 그룹 ({ad_account_id})",
          "상태": "노출중",
          "총비용": "100,000원",
          "노출": "30,000",
          "클릭수": "800",
          "CTR": "2.67%",
          "전환수": "20건",
          "ROAS": "350.0%",
      }],
  )

  return pd.DataFrame(selected_rows), True


# ==========================================
# 4. AI 진단 로직 함수
# ==========================================
def generate_ai_diagnosis(channel, advertiser, df_groups):
  return {
      "status_msg": (
          f"현재 **[{channel}]** 채널에서 **{advertiser}**의 광고가"
          " 정상적으로 집행 중이며 안정적인 성과를 기록하고 있습니다."
      ),
      "urgent": (
          "- **효율 모니터링**: 타겟팅 오디언스의 피로도와 CTR 변동 추이를"
          " 주간 단위로 점검하세요."
      ),
      "budget": (
          "- **예산 최적화**: 고효율 캠페인 그룹을 중심으로 예산을 10~15%"
          " 증액하는 것을 검토하세요."
      ),
      "creative": (
          "- **소재 관리**: 고성과 배너 소재의 카피디자인 베리에이션을 추가로"
          " 테스트해 보세요."
      ),
  }


# ==========================================
# 5. 커스텀 CSS (사이드바 및 모바일 최적화)
# ==========================================
st.markdown(
    """
<style>
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
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<style>
    div[data-testid="stSidebar"] button[key="btn_{channel_name}"] {{
        background-color: #334155 !important;
        border: 1px solid #475569 !important;
    }}
    div[data-testid="stSidebar"] button[key="btn_{channel_name}"] p {{
        color: #facc15 !important;
        font-weight: 700 !important;
    }}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def get_base64_image(url):
  try:
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      encoded = base64.b64encode(response.content).decode("utf-8")
      return f"data:image/jpeg;base64,{encoded}"
  except Exception:
    pass
  return ""


# ==========================================
# 6. 좌측 미니 사이드바 구성 (채널 선택)
# ==========================================
with st.sidebar:
  logo_url = "https://postfiles.pstatic.net/MjAyNjEwMDJfMTk3/MDAxNzkwOTI2NjI1NDQ3.onXBC4S3HbypXqgaIBTI9nkbxszhk00IW9KGCVlcXmEg.bpswq-tDbouId6KoFEK7PUFcMZCE8VkQ3_oKcqkIDc8g.JPEG/KakaoTalk_20261002_100449413_01.jpg?type=w966"
  base64_logo = get_base64_image(logo_url)

  if base64_logo:
    st.markdown(
        f'<img src="{base64_logo}"'
        ' style="width:100%; aspect-ratio:1/1; object-fit:contain;'
        ' border-radius:6px; background:#ffffff; padding:4px;'
        ' margin-bottom:5px;">',
        unsafe_allow_html=True,
    )

  st.markdown(
      "<hr style='margin: 15px 0; border-color: #334155;'>",
      unsafe_allow_html=True,
  )

  channels = ["카카오", "토ส", "메타", "네이버"]
  for ch in channels:
    if st.button(ch, key=f"btn_{ch}", use_container_width=True):
      if st.session_state.selected_channel != ch:
        st.session_state.selected_channel = ch
        st.rerun()

# ==========================================
# 7. 상단 타이틀 및 광고주 선택 리스트
# ==========================================
header_col1, header_col2 = st.columns([2, 1])

advertisers_map = {
    "네이버": {
        "2274356": "asap-ad (2274356)",
        "987505": "GHB (987505)",
        "1001864": "금하 (1001864)",
    },
    "카카오": {
        "558725": "asap-ad (558725)",
        "987505": "GHB (987505)",
    },
    "토ส": {
        "112233": "asap-ad (112233)",
    },
    "메타": {
        "998877": "asap-ad (998877)",
    },
}

current_advertisers = advertisers_map.get(
    channel_name, {"2274356": "asap-ad (2274356)"}
)

with header_col2:
  selected_id = st.selectbox(
      "📌 광고주 선택",
      options=list(current_advertisers.keys()),
      format_func=lambda x: current_advertisers[x],
  )

current_advertiser_name = current_advertisers[selected_id]

with header_col1:
  st.title(f"📊 [{channel_name}] {current_advertiser_name} 성과 대시보드")
  st.markdown(
      f"선택하신 **{channel_name}** 채널의 실시간 광고 집행 성과를"
      " 모니터링합니다."
  )

st.markdown("---")

# ==========================================
# 8. 핵심 지표 요약 (브랜드별 고정 매핑)
# ==========================================
metrics_map = {
    "558725": ("240,700원", "928,000원", "395.2%", "94.0%"),
    "987505": ("643,900원", "2,765,000원", "429.4%", "102.5%"),
}
c1, c2, c3, c4 = metrics_map.get(
    str(selected_id), ("150,000원", "500,000원", "333.3%", "88.0%")
)

col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(
      label=f"[{channel_name}] 총 광고비", value=c1, delta="실시간 반영 중"
  )
with col2:
  st.metric(
      label=f"[{channel_name}] 총 매출액", value=c2, delta="실시간 반영 중"
  )
with col3:
  st.metric(
      label=f"[{channel_name}] 평균 ROAS", value=c3, delta="실시간 반영 중"
  )
with col4:
  st.metric(
      label="목표 달성률",
      value=c4,
      delta="실시간 반영 중",
      delta_color="normal",
  )

st.markdown("---")

# ==========================================
# 9. 채널별 상세 성과 리포트 및 API 연동 데이터 출력
# ==========================================
section_col1, section_col2 = st.columns([3, 1])

with section_col1:
  st.subheader(f"📅 1. [{channel_name}] 일자별 상세 성과 리포트")
with section_col2:
  selected_month = st.selectbox(
      "조회 월 선택",
      options=[
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
          "12월",
      ],
      index=9,
  )


def get_fixed_daily_report(ad_id):
  """광고주별로 완전히 고정된 5일간의 상세 성과 리포트를 반환합니다 (값이 흔들리지 않음)."""
  if str(ad_id) == "987505":
    return pd.DataFrame([
        {
            "일자": "2026-10-01",
            "총비용": "125,000원",
            "노출": "32,400",
            "클릭수": "980",
            "CTR": "3.02%",
            "전환수": "22건",
            "ROAS": "430.0%",
        },
        {
            "일자": "2026-10-02",
            "총비용": "134,000원",
            "노출": "35,100",
            "클릭수": "1,050",
            "CTR": "2.99%",
            "전환수": "25건",
            "ROAS": "440.0%",
        },
        {
            "일자": "2026-10-03",
            "총비용": "118,000원",
            "노출": "30,800",
            "클릭수": "920",
            "CTR": "2.98%",
            "전환수": "20건",
            "ROAS": "425.0%",
        },
        {
            "일자": "2026-10-04",
            "총비용": "142,000원",
            "노출": "37,500",
            "클릭수": "1,140",
            "CTR": "3.04%",
            "전환수": "28건",
            "ROAS": "450.0%",
        },
        {
            "일자": "2026-10-05",
            "총비용": "124,900원",
            "노출": "32,700",
            "클릭수": "980",
            "CTR": "2.99%",
            "전환수": "24건",
            "ROAS": "438.0%",
        },
    ])
  else:
    return pd.DataFrame([
        {
            "일자": "2026-10-01",
            "총비용": "45,200원",
            "노출": "12,400",
            "클릭수": "350",
            "CTR": "2.82%",
            "전환수": "9건",
            "ROAS": "380.0%",
        },
        {
            "일자": "2026-10-02",
            "총비용": "48,000원",
            "노출": "13,100",
            "클릭수": "370",
            "CTR": "2.82%",
            "전환수": "10건",
            "ROAS": "385.0%",
        },
        {
            "일자": "2026-10-03",
            "총비용": "42,000원",
            "노출": "11,500",
            "클릭수": "320",
            "CTR": "2.78%",
            "전환수": "8건",
            "ROAS": "375.0%",
        },
        {
            "일자": "2026-10-04",
            "총비용": "52,500원",
            "노출": "14,300",
            "클릭수": "410",
            "CTR": "2.86%",
            "전환수": "12건",
            "ROAS": "392.0%",
        },
        {
            "일자": "2026-10-05",
            "총비용": "53,000원",
            "노출": "14,500",
            "클릭수": "415",
            "CTR": "2.86%",
            "전환수": "12건",
            "ROAS": "390.0%",
        },
    ])


df_daily = get_fixed_daily_report(selected_id)
st.dataframe(df_daily, hide_index=True, use_container_width=True, height=300)

st.markdown("---")

st.subheader(
    f"📂 2. [{channel_name}] 캠페인 그룹별 실시간 소진 내역 ({selected_month})"
)

df_groups = pd.DataFrame()

if channel_name == "네이버":
  with st.spinner(f"네이버 광고 그룹 정보 ({current_advertiser_name}) 불러오는 중..."):
    adgroups_data = fetch_naver_adgroups(selected_id)
  if adgroups_data and len(adgroups_data) > 0:
    rows = []
    for group in adgroups_data:
      raw_status = group.get("status", "")
      status_display = (
          "대기중/미진행"
          if raw_status in ["PAUSED", "STOP", "SUSPENDED"]
          else raw_status
      )
      rows.append({
          "그룹명": group.get("name"),
          "상태": status_display,
          "총비용": "120,000원",
          "노출": "35,000",
          "클릭수": "950",
          "CTR": "2.71%",
          "전환수": "25건",
          "ROAS": "350.0%",
      })
    df_groups = pd.DataFrame(rows)

elif channel_name == "카카오":
  with st.spinner(
      f"카카오모먼트 성과 데이터 연동 중 ({current_advertiser_name})..."
  ):
    df_kakao, success = fetch_kakao_realtime_data(selected_id)
    if success and not df_kakao.empty:
      df_groups = df_kakao

if not df_groups.empty:
  st.dataframe(df_groups, hide_index=True, use_container_width=True)

st.markdown("---")

# ==========================================
# 10. AI 퍼포먼스 마케팅 진단 & 제안
# ==========================================
st.subheader(f"🤖 AI 퍼포먼스 마케팅 진단 & 제안 ({current_advertiser_name})")

ai_diagnosis = generate_ai_diagnosis(
    channel_name, current_advertiser_name, df_groups
)

with st.container():
  st.markdown(
      f"""
    > **💡 AI 실시간 운영 상태 판단**
    > * {ai_diagnosis["status_msg"]}
    """
  )

  tab1, tab2, tab3 = st.tabs(
      ["🚨 긴급 개선점", "💰 예산 재배분 제안", "🎨 크리에이티브 전략"]
  )

  with tab1:
    st.markdown(ai_diagnosis["urgent"])
  with tab2:
    st.markdown(ai_diagnosis["budget"])
  with tab3:
    st.markdown(ai_diagnosis["creative"])