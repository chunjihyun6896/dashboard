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
      st.error(
          f"네이버 API 오류 발생! (상태 코드: {response.status_code})"
      )
      st.code(response.text)
      return None
  except Exception as e:
    st.error(f"네트워크 예외 발생: {e}")
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
      f"선택하신 **{channel_name}** 채널의 광고 집행 성과 및 상세 데이터를"
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
# 7. 채널별 상세 성과 리포트
# ==========================================
section_col1, section_col2 = st.columns([3, 1])

with section_col1:
  if channel_name == "네이버":
    st.subheader("📅 1. [네이버 API 연동] 실시간 캠페인 목록 정보")
  else:
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
      index=0,
  )

# 네이버 채널일 경우: 실제 API 응답 데이터만 테이블에 반영 (데이터가 없으면 안내 문구 출력)
if channel_name == "네이버":
  with st.spinner("네이버 광고 서버에서 캠페인 데이터를 불러오는 중..."):
    naver_data = fetch_naver_campaigns()

  if naver_data:
    st.success("✨ 네이버 광고 API 연동 성공!")

    rows = []
    for camp in naver_data:
      rows.append({
          "캠페인 ID": camp.get("nccCampaignId"),
          "캠페인명": camp.get("name"),
          "상태": camp.get("status"),
          "캠페인 유형": camp.get("campaignTp"),
          "일예산": (
              f"{camp.get('dailyBudget', 0):,}원"
              if camp.get("dailyBudget", 0) > 0
              else "제한없음"
          ),
          "총 소진비용": f"{camp.get('totalChargeCost', 0):,}원",
      })

    df_naver = pd.DataFrame(rows)
    st.dataframe(df_naver, hide_index=True, use_container_width=True)
  else:
    st.warning(
        "불러올 네이버 캠페인 데이터가 없거나 API 응답이 비어 있습니다."
    )

# 카카오, 메타, 토스 채널일 경우: 기존 샘플 리포트 출력
else:


  def generate_channel_daily_data(month_str):
    month_num = int(month_str.replace("월", ""))
    last_day = (
        28 if month_num == 2 else (30 if month_num in [4, 6, 9, 11] else 31)
    )
    dates = [f"2026-{month_num:02d}-{day:02d}" for day in range(1, last_day + 1)]

    data = []
    for i, d in enumerate(dates):
      cost_val = 150000 + (i * 4000)
      rev_val = cost_val * (3.2 + (i % 5) * 0.1)
      roas_val = (rev_val / cost_val) * 100

      data.append({
          "일자": d,
          "총비용": f"{cost_val:,}원",
          "노출": f"{1200000 + (i * 10000):,}",
          "클릭수": f"{3500 + (i * 40):,}",
          "CTR": f"{2.5 + (i * 0.01):.2f}%",
          "전환수": f"{40 + (i % 6)}건",
          "ROAS": f"{roas_val:.1f}%",
      })
    return pd.DataFrame(data)


  df_daily = generate_channel_daily_data(selected_month)
  st.dataframe(df_daily, hide_index=True, use_container_width=True, height=300)

  st.markdown("---")
  st.subheader(
      f"📂 2. [{channel_name}] 캠페인 그룹별 소진 내역 ({selected_month})"
  )
  df_groups = pd.DataFrame({
      "그룹명": [
          f"[{current_advertiser_name}] {channel_name}_브랜드_검색캠페인",
          f"[{current_advertiser_name}] {channel_name}_리타겟팅_전환",
      ],
      "상태": ["진행중", "진행중"],
      "총비용": ["15,000,000원", "12,500,000원"],
      "노출": ["45,000,000", "32,000,000"],
      "클릭수": ["125,000", "98,000"],
      "CTR": ["2.78%", "3.06%"],
      "전환수": ["1,420건", "1,250건"],
      "ROAS": ["325.0%", "315.5%"],
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
    > **💡 [{channel_name}] 운영 진단 요약**
    > * **채널 특화 분석**: 현재 선택하신 **{channel_name}** 매체는 실시간 데이터 기반으로 고효율 캠페인이 집중 관리되고 있습니다.
    """
  )

  tab1, tab2, tab3 = st.tabs(
      ["🚨 긴급 개선점", "💰 예산 재배분 제안", "🎨 크리에이티브 전략"]
  )

  with tab1:
    st.markdown(
        f"- **[{channel_name}] 저효율 캠페인 점검**: 소진 비용 대비 전환"
        " 단가(CPA)가 높은 그룹의 입찰 전략을 최적화하세요."
    )
  with tab2:
    st.markdown(
        "- **고성과 그룹 예산 상향**: ROAS가 보장되는 메인 캠페인 그룹에 예산을"
        " 추가 배분하여 볼륨을 극대화하세요."
    )
  with tab3:
    st.markdown(
        "- **소재 리프레시**: 피로도가 누적된 크리에이티브는 중단하고 신규 소스를"
        " 투입하세요."
    )