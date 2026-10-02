import streamlit as st
import pandas as pd

# 1. 페이지 기본 설정 (와이드 모드)
st.set_page_config(
    page_title="카카오 마케팅 성과 대시보드",
    page_icon="📊",
    layout="wide"
)

# 관리 중인 광고주 리스트
advertisers = {
    "558725": "A 브랜드 (주력 상품군)",
    "889922": "B 브랜드 (신규 런칭군)",
    "774411": "C 브랜드 (글로벌 라인)"
}

# ==========================================
# 2. 상단 타이틀 및 우측 광고주 선택 메뉴 배치
# ==========================================
header_col1, header_col2 = st.columns([2, 1])

with header_col2:
    selected_id = st.selectbox(
        "📌 광고주 선택",
        options=list(advertisers.keys()),
        format_func=lambda x: f"{advertisers[x]} ({x})"
    )

current_advertiser_name = advertisers[selected_id]

with header_col1:
    st.title(f"📊 {current_advertiser_name} ({selected_id}) 카카오 대시보드")
    st.markdown("월별 광고 집행 성과 및 일자별 상세 데이터를 모니터링하는 대시보드입니다.")

st.markdown("---")

# [1단] 핵심 지표 요약 (Metric Cards)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="총 광고비", value="4,400만 원", delta="+5% (전월 대비)")
with col2:
    st.metric(label="총 매출액", value="14,200만 원", delta="+8.2% (전월 대비)")
with col3:
    st.metric(label="평균 ROAS", value="322.7%", delta="+15.4%p (전월 대비)")
with col4:
    st.metric(label="목표 달성률", value="92.2%", delta="-2.8%p (목표 350% 대비)", delta_color="inverse")

st.markdown("---")

# ==========================================
# [2단] 월별 선택 드롭박스 및 일자별 데이터 테이블 섹션
# ==========================================
section_col1, section_col2 = st.columns([3, 1])

with section_col1:
    st.subheader("📅 일자별 상세 성과 리포트")

with section_col2:
    # 우측 상단 월 선택 드롭박스
    selected_month = st.selectbox(
        "조회 월 선택",
        options=["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"],
        index=0  # 기본 1월 선택
    )

# 예시용 샘플 데이터 생성 (실제 API 연동 시 해당 월 데이터로 교체됨)
# 1월 선택 시 1월 1일 ~ 1월 31일 데이터 시뮬레이션
def generate_mock_daily_data(month_str):
    month_num = int(month_str.replace("월", ""))
    # 월에 따른 마지막 날짜 대략 설정 (2월은 28일, 31일 달 등)
    last_day = 28 if month_num == 2 else (30 if month_num in [4, 6, 9, 11] else 31)
    
    dates = [f"2026-{month_num:02d}-{day:02d}" for day in range(1, last_day + 1)]
    
    data = []
    for i, d in enumerate(dates):
        cost = f"{(150000 + (i * 5000)):,}원"
        imp = f"{(1200000 + (i * 12000)):,}"
        click = f"{(3500 + (i * 45)):,}"
        ctr = f"{2.8 + (i * 0.02):.2f}%"
        conv = f"{45 + (i % 5)}"
        
        data.append({
            "일자": d,
            "총비용": cost,
            "노출": imp,
            "클릭수": click,
            "CTR": ctr,
            "전환수": conv
        })
    return pd.DataFrame(data)

df_daily = generate_mock_daily_data(selected_month)

# 테이블 출력 (항목: 일자 / 총비용 / 노출 / 클릭수 / ctr / 전환수)
st.dataframe(
    df_daily, 
    hide_index=True, 
    use_container_width=True,
    height=400
)

st.markdown("---")

# [3단] AI 퍼포먼스 마케터 인사이트 및 제안 섹션
st.subheader(f"🤖 AI 퍼포먼스 마케팅 인사이트 & 액션 제안 ({current_advertiser_name} - {selected_month})")

with st.container():
    st.markdown(f"""
    > **💡 [{current_advertiser_name}] {selected_month} 성과 진단 요약**
    > * **종합 평가**: 선택하신 {selected_month} 기간 동안의 일자별 트래픽과 비용 소진 추이를 분석한 결과, 안정적인 유입과 전환 효율을 보이고 있습니다.
    > * **효율 최적화 포인트**: 중순 이후 클릭수와 CTR이 상승하는 구간의 크리에이티브 집행 방식을 타 기간에도 확대 적용하는 것을 권장합니다.
    """)
    
    tab1, tab2, tab3 = st.tabs(["🚨 긴급 개선점", "💰 예산 재배분 제안", "🎨 크리에이티브 전략"])
    
    with tab1:
        st.markdown("""
        - **일자별 예산 소진 모니터링**: 
          - 특정 주말 기간 동안 노출 대비 클릭 효율이 일시적으로 낮아지는 현상이 관측되어 타겟 입찰가 조정을 검토해야 합니다.
        """)
        
    with tab2:
        st.markdown("""
        - **효율 우수 일자 예산 집중**: 
          - 전환수가 높게 집계된 일자 패턴을 분석하여 해당 요일/시간대에 예산을 집중 배분하는 전략이 유효합니다.
        """)
        
    with tab3:
        st.markdown("""
        - **고성과 소재 유지**: 
          - CTR이 꾸준히 3% 이상 유지되는 상위 광고 소재의 노출 볼륨을 유지하고, 피로도가 쌓이는 시점의 대체 소재를 준비하세요.
        """)