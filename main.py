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
# 3. AI 진단 로직 함수 (데이터 기반 동적 생성)
# ==========================================
def generate_ai_diagnosis(channel, advertiser, df_groups):
  # 실제 데이터 집행 여부 확인 (그룹 데이터가 존재하고 상태가 'UP' 또는 'ELIGIBLE' 등이거나 비용이 발생하는지 체크)
  is_running = False
  if not df_groups.empty:
    # 예시로 상태 항목에 대기중/미집행이 아닌 항목이 포함되어 있는지 혹은 데이터가 있는지 확인
    active_check = df_groups[~df_groups["상태"].str.contains("대기|미진행|중지", na=False)]
    if len(active_check) > 0:
      is_running = True

  diagnosis_dict = {}

  if not is_running:
    diagnosis_dict["status_msg"] = (
        f"현재 **[{channel}]** 채널은 등록된 광고가 **미진행** 상태이거나 집행"
        " 이력이 확인되지 않습니다."
    )
    diagnosis_dict["urgent"] = (
        f"- **[미진행 안내]** 현재 **{advertiser}** 계정의 {channel}"
        " 캠페인/그룹이 활성화되지 않았거나 소진 비용이 0원입니다.\n- **조치"
        " 제안**: 캠페인 및 광고 그룹의 상태를 '노출중'으로 변경하고, 예산 및"
        " 입찰가 설정 상태를 점검해 주세요."
    )
    diagnosis_dict["budget"] = (
        "- **예산 배분 불가**: 현재 광고가 집행되고 있지 않아 유의미한 소진"
        " 데이터가 없으므로 예산 재배분을 산출할 수 없습니다. 광고 집행 개시"
        " 후 다시 진단해 주세요."
    )
    diagnosis_dict["creative"] = (
        "- **소재 점검**: 등록된 광고 소재(이미지/문구)의 검수 상태를"
        " 확인하시고, 노출 전 타겟팅 및 키워드/소재 세팅을 완료해 주세요."
    )
  else:
    diagnosis_dict["status_msg"] = (
        f"현재 **[{channel}]** 채널에서 광고가 **정상적으로 진행 중**이며"
        " 실시간 성과가 수집되고 있습니다."
    )
    diagnosis_dict["urgent"] = (
        "- **효율 모니터링**: 일부 그룹의 클릭률(CTR)과 전환율을 점검하여"
        " 저효율 소재를 필터링하세요."
    )
    diagnosis_dict["budget"] = (
        "- **예산 최적화**: 전환율이 높은 상위 그룹에 예산을 집중하고, 소진이"
        " 더딘 캠페인은 입찰가를 조정하세요."
    )
    diagnosis_dict["creative"] = (
        "- **소재 교체 제안**: 피로도가 높아진 소재는 새로운 후크 메시지나"
        " 배너로 교체 테스트를 권장합니다."
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
# 6. 상단 타이틀 및 우측 광고주 선택 메뉴
# ==========================================
advertisers = {
    "558725": "A 브랜드 (주력 상품군)",
    "889922": "B 브랜드 (신규 런칭군)",
    "774411": "C 브랜드 (글로벌 라인)",
}

header_col1, header_col2 = st.columns([2, 1])

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
      rows.append({
          "그룹명": group.get("name"),
          "상태": group.get("status"),
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
# 9. AI 퍼포먼스 마케팅 진단 & 제안 (실시간 판단 반영)
# ==========================================
st.subheader(
    f"🤖 AI 퍼포먼스 마케팅 진단 & 제안 ({channel_name} /"
    f" {current_advertiser_name})"
)

# AI 진단 결과 동적 생성 호출
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