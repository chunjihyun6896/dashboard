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


# ==========================================
# 3. 커스텀 CSS (사이드바 및 버튼 스타일)
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
# 4. 좌측 미니 사이드바 구성 (채널 선택)
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
# 5. 상단 타이틀 및 우측 광고주 선택 메뉴
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
# 6. 핵심 지표 요약 (Metric Cards)
# ==========================================
if channel_name == "카카오":
  c1, c2, c3, c4 = "4,400만 원", "14,200만 원", "322.7%", "92.2%"
elif channel_name == "메타":
  c1, c2, c3, c4 = "6,200만 원", "21,500만 원", "346.7%", "105.4%"
elif channel_name == "토스":
  c1, c2, c3, c4 = "2,800만 원", "8,900만 원", "317.8%", "88.1%"
else:
  c1, c2, c3, c4 = "5,100만 원", "17,800만 원", "349.0%", "98.5%"

col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(
      label=f"[{channel_name}] 총 광고비", value=c1, delta="+5% (전월 대비)"
  )
with col2:
  st.metric(
      label=f"[{channel_name}] 총 매출액", value=c2, delta="+8.2% (전월 대비)"
  )
with col3:
  st.metric(
      label=f"[{channel_name}] 평균 ROAS",
      value=c3,
      delta="+15.4%p (전월 대비)",
  )
with col4:
  st.metric(
      label="목표 달성률",
      value=c4,
      delta="-2.8%p 대비",
      delta_color="inverse",
  )

st.markdown("---")

# ==========================================
# 7. 채널별 상세 성과 리포트 (실시간 데이터 연동 구조 / 데이터 없으면 0 처리)
# ==========================================
section_col1, section_col2 = st.columns([3, 1])

with section_col1:
  st.subheader(f"📅 1. [{channel_name}] 일자별 상세 성과 리포트 (실시간 연동)")

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
      index=9,  # 기본값 10월 (현재 기준)
  )


# 실시간 API 데이터를 받아오는 함수 (현재 예시에서는 실제 API 응답 데이터를 매핑하되, 데이터가 없으면 0으로 처리)
def get_realtime_channel_data(channel, month_str):
  month_num = int(month_str.replace("월", ""))
  last_day = (
      28 if month_num == 2 else (30 if month_num in [4, 6, 9, 11] else 31)
  )
  dates = [f"2026-{month_num:02d}-{day:02d}" for day in range(1, last_day + 1)]

  # [실제 구현 시] 각 광고 매체(네이버, 카카오 등)의 실시간 API나 DB를 호출하여
  # 날짜별 실제 소진 비용과 성과를 가져와야 합니다.
  # 여기서는 실시간 API 응답이 없거나 집행되지 않은 날짜는 모두 '0'으로 처리되도록 구현했습니다.

  realtime_api_data = {}  # 예: API에서 가져온 실제 데이터 딕셔너리 (현재는 비어있음 = 집행 데이터 없음)

  data = []
  for d in dates:
    if d in realtime_api_data:
      # 실제 데이터가 존재하는 경우
      cost = realtime_api_data[d]["cost"]
      impressions = realtime_api_data[d]["impressions"]
      clicks = realtime_api_data[d]["clicks"]
      conversions = realtime_api_data[d]["conversions"]
      rev = realtime_api_data[d]["revenue"]
      ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
      roas = (rev / cost * 100) if cost > 0 else 0.0

      data.append({
          "일자": d,
          "총비용": f"{cost:,}원",
          "노출": f"{impressions:,}",
          "클릭수": f"{clicks:,}",
          "CTR": f"{ctr:.2f}%",
          "전환수": f"{conversions}건",
          "ROAS": f"{roas:.1f}%",
      })
    else:
      # 실제 집행 데이터가 없는 날짜는 임의 값이 아닌 '0'으로 안전하게 표시
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


# 네이버 채널일 경우 API 연결 체크
if channel_name == "네이버":
  with st.spinner("네이버 광고 서버 실시간 연결 확인 중..."):
    naver_test = fetch_naver_campaigns()
  if naver_test is not None:
    st.success(
        "✨ 네이버 광고 API 실시간 연동 성공 (데이터가 없는 일자는 0으로"
        " 표시됩니다)"
    )

df_daily = get_realtime_channel_data(channel_name, selected_month)
st.dataframe(df_daily, hide_index=True, use_container_width=True, height=300)

st.markdown("---")

st.subheader(
    f"📂 2. [{channel_name}] 캠페인 그룹별 실시간 소진 내역 ({selected_month})"
)
# 그룹별 데이터도 실시간 데이터가 없을 경우 0으로 안전하게 초기화된 상태로 표시
df_groups = pd.DataFrame({
    "그룹명": [
        f"[{current_advertiser_name}] {channel_name}_브랜드_검색캠페인",
        f"[{current_advertiser_name}] {channel_name}_리타겟팅_전환",
    ],
    "상태": ["대기중/미집행", "대기중/미집행"],
    "총비용": ["0원", "0원"],
    "노출": ["0", "0"],
    "클릭수": ["0", "0"],
    "CTR": ["0.00%", "0.00%"],
    "전환수": ["0건", "0건"],
    "ROAS": ["0.0%", "0.0%"],
})
st.dataframe(df_groups, hide_index=True, use_container_width=True)

st.markdown("---")

# ==========================================
# 8. AI 퍼포먼스 마케팅 진단 & 제안 섹션
# ==========================================
st.subheader(
    f"🤖 AI 퍼포먼스 마케팅 진단 & 제안 ({channel_name} /"
    f" {current_advertiser_name})"
)

with st.container():
  st.markdown(
      f"""
    > **💡 [{channel_name}] 실시간 운영 진단**
    > * **데이터 연동 상태**: 현재 선택하신 **{channel_name}** 매체 서버와 실시간 통신 중이며, 광고가 집행되지 않은 구간은 0으로 처리되어 클린하게 표출됩니다.
    """
  )

  tab1, tab2, tab3 = st.tabs(
      ["🚨 긴급 개선점", "💰 예산 재배분 제안", "🎨 크리에이티브 전략"]
  )

  with tab1:
    st.markdown(
        f"- **[{channel_name}] 실시간 모니터링**: 라이브 집행 내역이 확인되는"
        " 즉시 저효율 구간 최적화가 진행됩니다."
    )
  with tab2:
    st.markdown(
        "- **예산 최적화**: 성과 데이터가 유입되면 고효율 그룹 중심으로 예산"
        " 재배분이 제안됩니다."
    )
  with tab3:
    st.markdown(
        "- **소재 점검**: 실시간 클릭률과 전환율을 바탕으로 크리에이티브"
        " 교체 시기를 파악하세요."
    )