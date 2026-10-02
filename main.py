import base64
import hashlib
import hmac
import time
import pandas as pd
import requests
import streamlit as st

# ==========================================
# 1. 페이지 기본 설정 (와이드 모드)
# ==========================================
st.set_page_config(
    page_title="멀티채널 마케팅 성과 대시보드", page_icon="📊", layout="wide"
)

# 세션 스테이트를 이용해 현재 선택된 채널 관리 (기본값: 카카오)
if "selected_channel" not in st.session_state:
  st.session_state.selected_channel = "카카오"

channel_name = st.session_state.selected_channel

# ==========================================
# 2. 네이버 검색광고 API 설정 및 연동 함수
# ==========================================
CUSTOMER_ID = "2274356"
ACCESS_LICENSE = (
    "0100000000d6006534e1b94c00ea1af84cba8177cfdb1b63426ac5ccbd6b1a0065232175e8"
)
SECRET_KEY = "AQAAAADWAGU04blMAOoa+Ey6gXfPgL+rhl4UaY1olB5h2gnQWQ=="
BASE_URL = "https://api.searchad.naver.com"


def generate_signature(timestamp, method, uri, secret_key):
  message = f"{timestamp}.{method}.{uri}"
  secret_bytes = bytes(secret_key, "utf-8")
  message_bytes = bytes(message, "utf-8")
  signature = hmac.new(secret_bytes, message_bytes, hashlib.sha256).digest()
  return base64.b64encode(signature).decode("utf-8")


def get_naver_header(method, uri):
  timestamp = str(int(time.time() * 1000))
  signature = generate_signature(timestamp, method, uri, SECRET_KEY)
  return {
      "Content-Type": "application/json; charset=UTF-8",
      "X-Timestamp": timestamp,
      "X-API-KEY": ACCESS_LICENSE,
      "X-Customer": str(CUSTOMER_ID),
      "X-Signature": signature,
  }


# 네이버 계정(고객) 정보 실시간 조회 함수 (광고주명 자동 인식)
@st.cache_data(ttl=600)
def fetch_naver_customer_info(customer_id):
  uri = f"/customers/{customer_id}"
  method = "GET"
  url = BASE_URL + uri
  headers = get_naver_header(method, uri)

  try:
    response = requests.get(url, headers=headers, timeout=5)
    if response.status_code == 200:
      data = response.json()
      # 네이버 API 응답 구조에 따라 업체명(name 또는 companyName 등) 추출
      return data.get("name") or data.get("companyName")
    else:
      return None
  except Exception:
    return None


@st.cache_data(ttl=600)
def fetch_naver_campaigns():
  uri = "/ncc/campaigns"
  method = "GET"
  url = BASE_URL + uri
  params = {"nccAccountId": CUSTOMER_ID}
  headers = get_naver_header(method, uri)

  try:
    response = requests.get(url, headers=headers, params=params, timeout=5)
    if response.status_code == 200:
      return response.json()
    else:
      return None
  except Exception:
    return None


@st.cache_data(ttl=600)
def fetch_naver_adgroups():
  uri = "/ncc/adgroups"
  method = "GET"
  url = BASE_URL + uri
  params = {"nccAccountId": CUSTOMER_ID}
  headers = get_naver_header(method, uri)

  try:
    response = requests.get(url, headers=headers, params=params, timeout=5)
    if response.status_code == 200:
      return response.json()
    else:
      return None
  except Exception:
    return None


# ==========================================
# 3. AI 진단 로직 함수 (미진행 상태 정밀 판별)
# ==========================================
def generate_ai_diagnosis(channel, advertiser, df_groups):
  is_running = True

  if df_groups.empty:
    is_running = False
  else:
    stopped_rows = df_groups[
        df_groups["상태"].str.contains("미진행|대기중|중지|PAUSED|STOP", na=False)
    ]
    if len(stopped_rows) == len(df_groups):
      is_running = False

  diagnosis_dict = {}

  if not is_running:
    diagnosis_dict["status_msg"] = (
        f"현재 **[{channel}]** 채널은 등록된 광고가 **미진행** 상태이며, 정상적으로"
        " 집행되고 있지 않습니다."
    )
    diagnosis_dict["urgent"] = (
        f"- **[미진행 안내]** 현재 **{advertiser}** 계정의 {channel}"
        " 캠페인/그룹이 일시정지 또는 대기 상태입니다.\n- **조치 제안**: 네이버"
        " 광고 시스템에서 해당 캠페인 및 광고 그룹의 상태를 '노출중'으로"
        " 전환하고, 비즈채널 및 소재 검수 상태를 확인해 주세요."
    )
    diagnosis_dict["budget"] = (
        "- **예산 재배분 불가**: 광고가 집행 중이지 않아 소진 비용 및 전환"
        " 데이터가 존재하지 않습니다. 광고 집행 개시 후 데이터를 바탕으로 예산"
        " 최적화를 진행할 수 있습니다."
    )
    diagnosis_dict["creative"] = (
        "- **소재 점검 안내**: 현재 노출 중인 광고가 없으므로, 등록된 키워드와"
        " 랜딩페이지, 이미지/텍스트 소재의 사전 검수 완료 여부를 점검하세요."
    )
  else:
    diagnosis_dict["status_msg"] = (
        f"현재 **[{channel}]** 채널에서 광고가 **정상적으로 진행 중**이며"
        " 실시간 성과가 수집되고 있습니다."
    )
    diagnosis_dict["urgent"] = (
        "- **효율 모니터링**: 라이브 중인 그룹의 클릭률(CTR)과 전환율을"
        " 점검하여 저효율 세부 요소를 관리하세요."
    )
    diagnosis_dict["budget"] = (
        "- **예산 최적화**: 성과가 우수한 그룹에 예산을 증액하고, 효율이"
        " 저조한 그룹은 입찰가를 조정하세요."
    )
    diagnosis_dict["creative"] = (
        "- **소재 교체 제안**: 노출 피로도가 높은 소재는 새로운 메시지나"
        " 디자인으로 교체 테스트를 권장합니다."
    )

  return diagnosis_dict


# ==========================================
# 4. 커스텀 CSS (사이드바 및 버튼 스타일)
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
# 5. 좌측 미니 사이드바 구성 (채널 선택)
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

  channels = ["카카오", "토스", "메타", "네이버"]

  for ch in channels:
    if st.button(ch, key=f"btn_{ch}", use_container_width=True):
      if st.session_state.selected_channel != ch:
        st.session_state.selected_channel = ch
        st.rerun()

# ==========================================
# 6. 상단 타이틀 및 광고주 자동 인식 메뉴
# ==========================================
header_col1, header_col2 = st.columns([2, 1])

# 네이버 채널일 경우 API로 실제 광고주명을 실시간 가져옴 (실패 시 기본값 사용)
if channel_name == "네이버":
  api_advertiser_name = fetch_naver_customer_info(CUSTOMER_ID)
  current_advertiser_name = (
      api_advertiser_name
      if api_advertiser_name
      else f"네이버 광고주 ({CUSTOMER_ID})"
  )
  with header_col2:
    st.info(
        f"📌 **현재 연동된 네이버 계정**\n- ID: `{CUSTOMER_ID}`\n- 인식된"
        f" 업체명: **{current_advertiser_name}**"
    )
else:
  # 타 채널의 경우 기존 선택형태 유지
  advertisers = {
      "558725": "A 브랜드 (주력 상품군)",
      "889922": "B 브랜드 (신규 런칭군)",
      "774411": "C 브랜드 (글로벌 라인)",
  }
  with header_col2:
    selected_id = st.selectbox(
        "📌 광고주 선택",
        options=list(advertisers.keys()),
        format_func=lambda x: f"{advertisers[x]} ({x})",
    )
  current_advertiser_name = advertisers[selected_id]

with header_col1:
  st.title(f"📊 [{channel_name}] {current_advertiser_name} 성과 대시보드")
  st.markdown(
      f"선택하신 **{channel_name}** 채널의 광고 집행 성과 및 실시간 데이터를"
      " 모니터링합니다."
  )

st.markdown("---")

# ==========================================
# 7. 핵심 지표 요약 (Metric Cards)
# ==========================================
c1, c2, c3, c4 = "0원", "0원", "0.0%", "0.0%"

col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(
      label=f"[{channel_name}] 총 광고비", value=c1, delta="0% (전월 대비)"
  )
with col2:
  st.metric(
      label=f"[{channel_name}] 총 매출액", value=c2, delta="0% (전월 대비)"
  )
with col3:
  st.metric(
      label=f"[{channel_name}] 평균 ROAS", value=c3, delta="0.0%p (전월 대비)"
  )
with col4:
  st.metric(
      label="목표 달성률",
      value=c4,
      delta="0.0%p 대비",
      delta_color="inverse",
  )

st.markdown("---")

# ==========================================
# 8. 채널별 상세 성과 리포트
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


def get_zero_channel_data(month_str):
  month_num = int(month_str.replace("월", ""))
  last_day = (
      28 if month_num == 2 else (30 if month_num in [4, 6, 9, 11] else 31)
  )
  dates = [f"2026-{month_num:02d}-{day:02d}" for day in range(1, last_day + 1)]

  data = []
  for d in dates:
    data.append({
        "일자": d,
        "총비용": "0원",
        "노출": "0",
        "클릭수": "0",
        "CTR": "0.00%",
        "전환수": "0건",
        "ROAS": "0.0%",
    })
  return pd.DataFrame(data)


df_daily = get_zero_channel_data(selected_month)
st.dataframe(df_daily, hide_index=True, use_container_width=True, height=300)

st.markdown("---")

st.subheader(
    f"📂 2. [{channel_name}] 캠페인 그룹별 실시간 소진 내역 ({selected_month})"
)

# 네이버 채널 데이터 연동
if channel_name == "네이버":
  with st.spinner("네이버 광고 그룹 정보를 실시간 불러오는 중..."):
    adgroups_data = fetch_naver_adgroups()

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
  else:
    df_groups = pd.DataFrame(columns=[
        "그룹명",
        "상태",
        "총비용",
        "노출",
        "클릭수",
        "CTR",
        "전환수",
        "ROAS",
    ])
    st.info(
        "현재 네이버 계정에 등록된 광고 그룹이 없거나 데이터를 불러오지"
        " 못했습니다."
    )
else:
  df_groups = pd.DataFrame(columns=[
      "그룹명",
      "상태",
      "총비용",
      "노출",
      "클릭수",
      "CTR",
      "전환수",
      "ROAS",
  ])
  st.info(f"현재 [{channel_name}] 채널에 집행된 실시간 그룹 데이터가 없습니다.")

if not df_groups.empty:
  st.dataframe(df_groups, hide_index=True, use_container_width=True)

st.markdown("---")

# ==========================================
# 9. AI 퍼포먼스 마케팅 진단 & 제안
# ==========================================
st.subheader(
    f"🤖 AI 퍼포먼스 마케팅 진단 & 제안 ({channel_name} /"
    f" {current_advertiser_name})"
)

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