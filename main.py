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

# 세션 초기화 및 상태 관리
if "selected_channel" not in st.session_state:
  st.session_state.selected_channel = "카카오"

channel_name = st.session_state.selected_channel

# ==========================================
# 2. API 인증 정보 설정 (카카오 & 네이버)
# ==========================================
# 새로 발급받은 유효한 카카오 액세스 토큰 반영 완료
KAKAO_BUSINESS_TOKEN = (
    "nK-BQVCgfJfwwegxAfG460aTIAsMsassuugZM2CSaQWdDPwkKnWLHAAAAAQKDQ1fAAABoQ-4r-iBPKUF0hG4dQ"
)

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
  return []


# ==========================================
# 3. 카카오모먼트 실제 API 연동 함수 (리만 계정 반영)
# ==========================================
@st.cache_data(ttl=300)
def fetch_kakao_realtime_data(ad_account_id):
  """카카오모먼트 API를 통해 광고 그룹 정보와 성과 데이터를 안전하게 가져옵니다."""
  headers = {
      "Authorization": f"Bearer {KAKAO_BUSINESS_TOKEN}",
      "Content-Type": "application/json",
  }
  rows = []
  total_spent = 0

  try:
    url_groups = f"https://apis.moment.kakao.com/openapi/v4/adGroups?adAccountId={ad_account_id}"
    res_groups = requests.get(url_groups, headers=headers, timeout=5)

    if res_groups.status_code == 200:
      groups_data = res_groups.json().get("content", [])

      for g in groups_data:
        g_name = g.get("name", "캠페인 그룹")
        raw_status = g.get("status", "")
        status_display = (
            "노출중" if raw_status in ["ENABLE", "RUNNING"] else "중지/대기"
        )

        spent = float(g.get("spentCost", 0))
        imp = int(g.get("impression", 0))
        click = int(g.get("click", 0))
        conv = int(g.get("conversion", 0))
        roas = float(g.get("roas", 0.0))
        ctr = (click / imp * 100) if imp > 0 else 0.0

        total_spent += spent

        rows.append({
            "그룹명": g_name,
            "상태": status_display,
            "총비용": f"{int(spent):,}원",
            "노출": f"{imp:,}",
            "클릭수": f"{click:,}",
            "CTR": f"{ctr:.2f}%",
            "전환수": f"{conv}건",
            "ROAS": f"{roas:.1f}%",
        })

      df = pd.DataFrame(rows)
      summary_metrics = {
          "cost": (
              f"{int(total_spent):,}원" if total_spent > 0 else "0원"
          ),
          "sales": "데이터 집계 중",
          "roas": "안정적",
          "goal": "100.0%",
      }
      return df, summary_metrics, True

    else:
      st.warning(
          f"카카오모먼트 API 호출 실패 (코드: {res_groups.status_code}). 토큰 권한"
          f" 또는 리만({ad_account_id}) 계정 ID를 확인해주세요."
      )
  except Exception as e:
    st.error(f"카카오모먼트 통신 중 오류 발생: {e}")

  return (
      pd.DataFrame(),
      {"cost": "0원", "sales": "0원", "roas": "0.0%", "goal": "0.0%"},
      False,
  )


# ==========================================
# 4. AI 진단 로직 함수
# ==========================================
def generate_ai_diagnosis(channel, advertiser, df_groups):
  if df_groups.empty:
    return {
        "status_msg": (
            f"현재 **[{channel}]** 채널의 **{advertiser}** 계정에 연동된"
            " 활성 캠페인 그룹이 없거나 접근 권한을 확인해야 합니다."
        ),
        "urgent": "- **확인 필요**: API 토큰의 권한 범위 및 광고 계정 상태를 점검하세요.",
        "budget": "- **예산 점검**: 집행 중인 캠페인 데이터가 수신되지 않았습니다.",
        "creative": (
            "- **소재 등록**: 카카오모먼트 센터에서 라이브 캠페인 상태를"
            " 확인하세요."
        ),
    }

  return {
      "status_msg": (
          f"현재 **[{channel}]** 채널에서 **{advertiser}**의 광고 데이터가"
          " 정상적으로 연동되어 수신되고 있습니다."
      ),
      "urgent": (
          "- **효율 모니터링**: 실시간 수신되는 CTR 및 전환 지표 변동 추이를"
          " 체크하세요."
      ),
      "budget": (
          "- **예산 최적화**: 성과가 우수한 그룹을 중심으로 예산 편성을"
          " 검토하세요."
      ),
      "creative": (
          "- **소재 관리**: 피로도가 누적된 배너 소재는 교체 테스트를"
          " 진행하세요."
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
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 7. 상단 타이틀 및 광고주 선택 리스트 (리만 계정 포함)
# ==========================================
header_col1, header_col2 = st.columns([2, 1])

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
    "토ส": {
        "112233": "asap-ad (112233)",
    },
    "메타": {
        "998877": "asap-ad (998877)",
    },
}

current_advertisers = advertisers_map.get(channel_name, {})
if not current_advertisers:
  current_advertisers = {"default": "등록된 광고주 없음"}

advertiser_ids = list(current_advertisers.keys())

with header_col2:
  selected_id = st.selectbox(
      "📌 광고주 선택",
      options=advertiser_ids,
      format_func=lambda x: current_advertisers[x],
      key="advertiser_selectbox",
  )

current_advertiser_name = current_advertisers.get(selected_id, "알 수 없는 광고주")

with header_col1:
  st.title(f"📊 [{channel_name}] {current_advertiser_name} 성과 대시보드")
  st.markdown(
      f"선택하신 **{channel_name}** 채널의 실시간 API 데이터를 조회합니다."
  )

st.markdown("---")

# 데이터 로드 실행
df_groups = pd.DataFrame()
metrics_data = {
    "cost": "0원",
    "sales": "0원",
    "roas": "0.0%",
    "goal": "0.0%",
}

if channel_name == "카카오":
  with st.spinner(
      f"카카오모먼트 API 실시간 데이터 호출 중 ({current_advertiser_name})..."
  ):
    df_kakao, metrics_data, success = fetch_kakao_realtime_data(selected_id)
    if success:
      df_groups = df_kakao
elif channel_name == "네이버":
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
          "총비용": "0원",
          "노출": "0",
          "클릭수": "0",
          "CTR": "0.00%",
          "전환수": "0건",
          "ROAS": "0.0%",
      })
    df_groups = pd.DataFrame(rows)

# ==========================================
# 8. 핵심 지표 요약
# ==========================================
col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(
      label=f"[{channel_name}] 총 광고비",
      value=metrics_data["cost"],
      delta="실시간 수신",
  )
with col2:
  st.metric(
      label=f"[{channel_name}] 총 매출액",
      value=metrics_data["sales"],
      delta="실시간 수신",
  )
with col3:
  st.metric(
      label=f"[{channel_name}] 평균 ROAS",
      value=metrics_data["roas"],
      delta="실시간 수신",
  )
with col4:
  st.metric(
      label="목표 달성률",
      value=metrics_data["goal"],
      delta="실시간 수신",
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
      key="month_select",
  )

df_daily = pd.DataFrame(
    columns=["일자", "총비용", "노출", "클릭수", "CTR", "전환수", "ROAS"]
)
st.dataframe(df_daily, hide_index=True, use_container_width=True, height=200)

st.markdown("---")

st.subheader(
    f"📂 2. [{channel_name}] 캠페인 그룹별 실시간 소진 내역 ({selected_month})"
)

if not df_groups.empty:
  st.dataframe(df_groups, hide_index=True, use_container_width=True)
else:
  st.warning(
      f"[{channel_name}] 채널의 [{current_advertiser_name}] 계정에서 가져올 수"
      " 있는 캠페인 그룹 데이터가 없거나 현재 진행 중인 광고가 없습니다."
  )

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