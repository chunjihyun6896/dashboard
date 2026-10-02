import base64
import pandas as pd
import requests
import streamlit as st

# 1. 페이지 기본 설정 (와이드 모드)
st.set_page_config(
    page_title="멀티채널 마케팅 성과 대시보드", page_icon="📊", layout="wide"
)

# 세션 스테이트를 이용해 현재 선택된 채널 관리 (기본값: 카카오)
if "selected_channel" not in st.session_state:
  st.session_state.selected_channel = "카카오"

channel_name = st.session_state.selected_channel

# ==========================================
# 2. 커스텀 CSS (기본 흰색 텍스트, 선택된 항목만 노란색 볼드체)
# ==========================================
st.markdown(
    """
<style>
    /* 기본 사이드바 너비를 좁게 설정 및 어두운 남색 배경 적용 */
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        min-width: 90px !important;
        max-width: 90px !important;
    }
    /* 사이드바 내부 여백 및 패딩 최소화 */
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    /* 사이드바 로고 이미지를 1:1 비율 및 규격에 맞게 조정 */
    [data-testid="stSidebar"] img {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        object-fit: contain !important;
        border-radius: 6px;
        background-color: #ffffff;
        padding: 4px;
    }
    
    /* Streamlit 기본 버튼 스타일 초기화 (배경 없음, 박스 없음) */
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
    
    /* 기본 버튼 안의 텍스트 색상을 흰색으로 설정 */
    [data-testid="stSidebar"] div.stButton > button p {
        color: #ffffff !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }
    
    /* 마우스 올렸을 때 살짝 밝은 배경 효과 */
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 선택된 메뉴 버튼만 '노란색 볼드체'로 동적 변경
# ==========================================
st.markdown(
    f"""
<style>
    div[data-testid="stSidebar"] button[key="btn_{channel_name}"] p {{
        color: #facc15 !important; /* 선명한 노란색 */
        font-weight: 700 !important;
    }}
</style>
""",
    unsafe_allow_html=True,
)


# 외부 이미지 보안 차단 방지 및 Base64 변환 함수
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
# 3. 좌측 미니 사이드바 구성 (로고 + 텍스트 메뉴)
# ==========================================
with st.sidebar:
  # 1) 자사 로고 이미지 배치
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

  # 2) 채널 목록 버튼 렌더링
  channels = ["카카오", "토스", "메타"]

  for ch in channels:
    if st.button(ch, key=f"btn_{ch}", use_container_width=True):
      if st.session_state.selected_channel != ch:
        st.session_state.selected_channel = ch
        st.rerun()

# ==========================================
# 4. 상단 타이틀 및 우측 광고주 선택 메뉴 배치
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

# [1단] 핵심 지표 요약 (Metric Cards) - 채널별 수치 분기
if channel_name == "카카오":
  c1, c2, c3, c4 = "4,400만 원", "14,200만 원", "322.7%", "92.2%"
elif channel_name == "메타":
  c1, c2, c3, c4 = "6,200만 원", "21,500만 원", "346.7%", "105.4%"
else:  # 토스
  c1, c2, c3, c4 = "2,800만 원", "8,900만 원", "317.8%", "88.1%"

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
# [2단] 월별 선택 드롭박스 및 일자별 데이터 테이블
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
      index=0,
  )


def generate_mock_daily_data(month_str, prefix):
  month_num = int(month_str.replace("월", ""))
  last_day = (
      28
      if month_num == 2
      else (30 if month_num in [4, 6, 9, 11] else 31)
  )
  dates = [
      f"2026-{month_num:02d}-{day:02d}" for day in range(1, last_day + 1)
  ]

  data = []
  for i, d in enumerate(dates):
    cost = f"{(150000 + (i * 4000)):,}원"
    imp = f"{(1200000 + (i * 10000)):,}"
    click = f"{(3500 + (i * 40)):,}"
    ctr = f"{2.5 + (i * 0.01):.2f}%"
    conv = f"{40 + (i % 6)}"

    data.append({
        "일자": d,
        "매체": prefix,
        "총비용": cost,
        "노출": imp,
        "클릭수": click,
        "CTR": ctr,
        "전환수": conv,
    })
  return pd.DataFrame(data)


df_daily = generate_mock_daily_data(selected_month, channel_name)
st.dataframe(df_daily, hide_index=True, use_container_width=True, height=300)

st.markdown("---")

# ==========================================
# [3단] 그룹(캠페인)별 소진 내역 테이블
# ==========================================
st.subheader(f"📂 2. [{channel_name}] 캠페인 그룹별 소진 내역 ({selected_month})")
st.caption(f"{channel_name} 광고 플랫폼 내 캠페인 단위 집행 성과 요약")

df_groups = pd.DataFrame({
    "그룹명": [
        f"[{current_advertiser_name}] {channel_name}_브랜드_검색캠페인",
        f"[{current_advertiser_name}] {channel_name}_리타겟팅_전환",
        f"[{current_advertiser_name}] {channel_name}_신규유저_확장오디언스",
        f"[{current_advertiser_name}] {channel_name}_프로모션_기획전",
    ],
    "상태": ["진행중", "진행중", "일시정지", "진행중"],
    "총비용": [
        "15,000,000원",
        "12,500,000원",
        "8,000,000원",
        "8,500,000원",
    ],
    "노출": ["45,000,000", "32,000,000", "15,000,000", "22,000,000"],
    "클릭수": ["125,000", "98,000", "34,000", "67,000"],
    "CTR": ["2.78%", "3.06%", "2.26%", "3.04%"],
    "전환수": ["1,420건", "1,250건", "410건", "890건"],
})

st.dataframe(df_groups, hide_index=True, use_container_width=True)

st.markdown("---")

# ==========================================
# [4단] 소재별 소진 내역 테이블
# ==========================================
st.subheader(f"🎨 3. [{channel_name}] 소재별 소진 내역 ({selected_month})")
st.caption("개별 크리에이티브 형태 및 문구별 성과 요약")

df_creatives = pd.DataFrame({
    "소재 유형": [
        "이미지 (피드)",
        "동영상 (숏폼)",
        "이미지 (와이드)",
        "이미지 (카드형)",
        "동영상 (인터뷰)",
    ],
    "소재명 / 문구": [
        f"[{channel_name}] 메인배너_v1.jpg\n(문구: 시즌 한정 특가 찬스!)",
        f"[{channel_name}] 쇼츠형_퍼포먼스_v2.mp4\n(문구: 3초만에 끝나는 간편"
        " 가입)",
        f"[{channel_name}] 제품단독_클로즈업_v3.jpg\n(문구: 베스트셀러 재입고"
        " 완료)",
        f"[{channel_name}] 할인혜택_고지형_v1.jpg\n(문구: 첫구매 50% 즉시 할인)",
        f"[{channel_name}] 스토리_인터뷰_v1.mp4\n(문구: 실제 유저 리얼 후기)",
    ],
    "집행기간": [
        "01.01 ~ 01.31",
        "01.05 ~ 01.25",
        "01.10 ~ 01.31",
        "01.15 ~ 01.31",
        "01.01 ~ 01.15",
    ],
    "총비용": [
        "12,000,000원",
        "10,500,000원",
        "9,000,000원",
        "7,500,000원",
        "6,000,000원",
    ],
    "노출": ["38,000,000", "28,000,000", "21,000,000", "18,000,000", "9,500,000"],
    "클릭수": ["110,000", "92,000", "58,000", "49,000", "21,000"],
    "CTR": ["2.89%", "3.28%", "2.76%", "2.72%", "2.21%"],
    "전환수": ["1,200건", "1,150건", "620건", "510건", "200건"],
})

st.dataframe(df_creatives, hide_index=True, use_container_width=True)

st.markdown("---")

# [5단] AI 퍼포먼스 마케터 인사이트 및 제안 섹션
st.subheader(
    f"🤖 AI 퍼포먼스 마케팅 진단 & 제안 ({channel_name} /"
    f" {current_advertiser_name})"
)

with st.container():
  st.markdown(
      f"""
    > **💡 [{channel_name}] {selected_month} 기간 동안의 매체별 운영 진단 요약**
    > * **채널 특화 분석**: 현재 선택하신 **{channel_name}** 매체는 타 채널 대비 클릭률(CTR)과 전환 효율이 안정적으로 유지되고 있습니다.
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