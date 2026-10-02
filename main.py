import streamlit as st
import pandas as pd

# 1. 페이지 기본 설정 (와이드 모드)
st.set_page_config(
    page_title="멀티채널 마케팅 성과 대시보드",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# 2. 좌측 사이드바 구성 (로고 및 매체 선택)
# ==========================================
with st.sidebar:
    # 자사 로고 이미지 배치
    logo_url = "https://postfiles.pstatic.net/MjAyNjEwMDJfMjk4/MDAxNzkwOTAzOTM5MzYz.TuL0H-S5UJ3hzhRb7hJLmt_Ze1U6QLqbva_vU6jeFsAg.5eVyYnQJTMkoNvS-OHY6TyepB4kuOwDtWfu1JvPa1XIg.JPEG/%EB%A1%9C%EA%B3%A0.jpg?type=w966"
    st.image(logo_url, use_container_width=True)
    
    st.markdown("---")
    
    # 광고 매체 선택 라디오 버튼 (카카오, 메타, 토스)
    st.subheader("📢 광고 매체 선택")
    selected_channel = st.radio(
        "확인할 채널을 선택하세요",
        options=["카카오 (Kakao)", "메타 (Meta)", "토스 (Toss)"],
        index=0
    )
    
    # 채널별 심볼 추출
    channel_name = selected_channel.split(" ")[0]
    
    st.markdown("---")
    
    # 관리 중인 광고주 리스트
    advertisers = {
        "558725": "A 브랜드 (주력 상품군)",
        "889922": "B 브랜드 (신규 런칭군)",
        "774411": "C 브랜드 (글로벌 라인)"
    }
    
    selected_id = st.selectbox(
        "📌 광고주 선택",
        options=list(advertisers.keys()),
        format_func=lambda x: f"{advertisers[x]} ({x})"
    )

current_advertiser_name = advertisers[selected_id]

# ==========================================
# 3. 메인 대시보드 영역
# ==========================================
st.title(f"📊 [{channel_name}] {current_advertiser_name} ({selected_id}) 성과 대시보드")
st.markdown(f"선택하신 **{channel_name}** 매체의 광고 집행 성과 및 상세 데이터를 모니터링하는 통합 퍼포먼스 솔루션입니다.")

st.markdown("---")

# [1단] 핵심 지표 요약 (Metric Cards) - 채널별로 수치가 살짝 다르게 연동되도록 구성
if channel_name == "카카오":
    c1, c2, c3, c4 = "4,400만 원", "14,200만 원", "322.7%", "92.2%"
elif channel_name == "메타":
    c1, c2, c3, c4 = "6,200만 원", "21,500만 원", "346.7%", "105.4%"
else:  # 토스
    c1, c2, c3, c4 = "2,800만 원", "8,900만 원", "317.8%", "88.1%"

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label=f"[{channel_name}] 총 광고비", value=c1, delta="+5% (전월 대비)")
with col2:
    st.metric(label=f"[{channel_name}] 총 매출액", value=c2, delta="+8.2% (전월 대비)")
with col3:
    st.metric(label=f"[{channel_name}] 평균 ROAS", value=c3, delta="+15.4%p (전월 대비)")
with col4:
    st.metric(label="목표 달성률", value=c4, delta="-2.8%p 대비", delta_color="inverse")

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
        options=["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"],
        index=0
    )

def generate_mock_daily_data(month_str, prefix):
    month_num = int(month_str.replace("월", ""))
    last_day = 28 if month_num == 2 else (30 if month_num in [4, 6, 9, 11] else 31)
    dates = [f"2026-{month_num:02d}-{day:02d}" for day in range(1, last_day + 1)]
    
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
            "전환수": conv
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
    '그룹명': [
        f"[{current_advertiser_name}] {channel_name}_브랜드_검색캠페인",
        f"[{current_advertiser_name}] {channel_name}_리타겟팅_전환",
        f"[{current_advertiser_name}] {channel_name}_신규유저_확장오디언스",
        f"[{current_advertiser_name}] {channel_name}_프로모션_기획전"
    ],
    '상태': ["진행중", "진행중", "일시정지", "진행중"],
    '총비용': ["15,000,000원", "12,500,000원", "8,000,000원", "8,500,000원"],
    '노출': ["45,000,000", "32,000,000", "15,000,000", "22,000,000"],
    '클릭수': ["125,000", "98,000", "34,000", "67,000"],
    'CTR': ["2.78%", "3.06%", "2.26%", "3.04%"],
    '전환수': ["1,420건", "1,250건", "410건", "890건"]
})

st.dataframe(df_groups, hide_index=True, use_container_width=True)

st.markdown("---")

# ==========================================
# [4단] 소재별 소진 내역 테이블
# ==========================================
st.subheader(f"🎨 3. [{channel_name}] 소재별 소진 내역 ({selected_month})")
st.caption("개별 크리에이티브 형태 및 문구별 성과 요약")

df_creatives = pd.DataFrame({
    '소재 유형': ["이미지 (피드)", "동영상 (숏폼)", "이미지 (와이드)", "이미지 (카드형)", "동영상 (인터뷰)"],
    '소재명 / 문구': [
        f"[{channel_name}] 메인배너_v1.jpg\n(문구: 시즌 한정 특가 찬스!)",
        f"[{channel_name}] 쇼츠형_퍼포먼스_v2.mp4\n(문구: 3초만에 끝내는 간편 가입)",
        f"[{channel_name}] 제품단독_클로즈업_v3.jpg\n(문구: 베스트셀러 재입고 완료)",
        f"[{channel_name}] 할인혜택_고지형_v1.jpg\n(문구: 첫구매 50% 즉시 할인)",
        f"[{channel_name}] 스토리_인터뷰_v1.mp4\n(문구: 실제 유저 리얼 후기)"
    ],
    '집행기간': ["01.01 ~ 01.31", "01.05 ~ 01.25", "01.10 ~ 01.31", "01.15 ~ 01.31", "01.01 ~ 01.15"],
    '총비용': ["12,000,000원", "10,500,000원", "9,000,000원", "7,500,000원", "6,000,000원"],
    '노출': ["38,000,000", "28,000,000", "21,000,000", "18,000,000", "9,500,000"],
    '클릭수': ["110,000", "92,000", "58,000", "49,000", "21,000"],
    'CTR': ["2.89%", "3.28%", "2.76%", "2.72%", "2.21%"],
    '전환수': ["1,200건", "1,150건", "620건", "510건", "200건"]
})

st.dataframe(df_creatives, hide_index=True, use_container_width=True)

st.markdown("---")

# [5단] AI 퍼포먼스 마케터 인사이트 및 제안 섹션
st.subheader(f"🤖 AI 퍼포먼스 마케팅 진단 & 제안 ({channel_name} / {current_advertiser_name})")

with st.container():
    st.markdown(f"""
    > **💡 [{channel_name}] {selected_month} 기간 동안의 매체별 운영 진단 요약**
    > * **채널 특화 분석**: 현재 선택하신 **{channel_name}** 매체는 타 채널 대비 클릭률(CTR)과 전환 효율이 안정적으로 유지되고 있습니다. 고효율 소재 중심의 예산 집중을 권장합니다.
    """)
    
    tab1, tab2, tab3 = st.tabs(["🚨 긴급 개선점", "💰 예산 재배분 제안", "🎨 크리에이티브 전략"])
    
    with tab1:
        st.markdown(f"""
        - **[{channel_name}] 저효율 캠페인 점검**: 
          - 소진 비용 대비 전환 단가(CPA)가 높은 오디언스 그룹의 입찰 전략을 최적화하세요.
        """)
        
    with tab2:
        st.markdown("""
        - **고성과 그룹 예산 상향**: 
          - ROAS가 보장되는 메인 캠페인 그룹에 예산을 추가 배분하여 볼륨을 극대화하세요.
        """)
        
    with tab3:
        st.markdown("""
        - **소재 리프레시**: 
          - 피로도가 누적된 크리에이티브는 중단하고 신규 소스를 투입하세요.
        """)