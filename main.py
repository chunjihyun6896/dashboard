import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 기본 설정 (와이드 모드)
st.set_page_config(
    page_title="마케팅 성과 대시보드",
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

with header_col1:
    st.title("📊 통합 마케팅 성과 대시보드")
    st.markdown("매체별 ROAS 성과 및 광고비 집행 현황을 모니터링하는 대시보드입니다.")

with header_col2:
    # 우측 상단에 셀렉트박스 배치
    selected_id = st.selectbox(
        "📌 광고주 선택",
        options=list(advertisers.keys()),
        format_func=lambda x: f"{advertisers[x]} ({x})"
    )

current_advertiser_name = advertisers[selected_id]

st.markdown("---")
st.markdown(f"**현재 선택된 계정**: `{current_advertiser_name}` (카카오모먼트 계정 ID: `{selected_id}`)")
st.markdown("---")

# [1단] 핵심 지표 요약 (Metric Cards)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="총 광고비", value="440만 원", delta="-5% (전주 대비)")
with col2:
    st.metric(label="총 매출액", value="1,420만 원", delta="+8.2% (전주 대비)")
with col3:
    st.metric(label="평균 ROAS", value="322.7%", delta="+15.4%p (전주 대비)")
with col4:
    st.metric(label="목표 달성률", value="92.2%", delta="-2.8%p (목표 350% 대비)", delta_color="inverse")

st.markdown("---")

# [2단] 시각화 및 비중 분석 섹션
chart_col1, chart_col2 = st.columns([2, 1])

with chart_col1:
    st.subheader("📈 매체별 ROAS")
    st.caption("빨간 막대는 목표 미달 · 옅은 세로선은 지난주 기준")

    df_roas = pd.DataFrame({
        '매체': ['Meta', 'Google', '네이버', '카카오*'],
        'ROAS': [306.3, 296.0, 355.9, 173.5],
        '지난주ROAS': [398.7, 292.9, 387.5, 187.7],
        '예산소진율': ['예산 100%', '예산 85%', '예산 82%', '예산 80%'],
        '상태': ['미달', '미달', '달성', '미달']
    })

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_roas['ROAS'],
        y=df_roas['매체'],
        orientation='h',
        marker_color=['#E54B4B' if s == '미달' else '#2ECC71' for s in df_roas['상태']],
        text=[f"{val}%" for val in df_roas['ROAS']],
        textposition='outside',
        hoverinfo='skip'
    ))

    fig.add_vline(x=350, line_dash="dash", line_color="gray", annotation_text="목표 350%", annotation_position="bottom right")

    fig.update_layout(
        xaxis=dict(range=[0, 450], showgrid=True, fixedrange=True),
        yaxis=dict(autorange="reversed", fixedrange=True),
        margin=dict(l=10, r=10, t=10, b=10),
        height=250,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    config_settings = {'displayModeBar': False}
    st.plotly_chart(fig, use_container_width=True, config=config_settings)
    
    st.info("ℹ️ *카카오는 지난주 전환값이 2일 비어 있어 지난주 값이 실제보다 낮을 수 있습니다. 빈 날을 빼면 지난주 211.8%입니다.")

with chart_col2:
    st.subheader("🥧 이번 주 매체별 광고비 비중")
    media_share = pd.DataFrame({
        '매체': ['Meta', 'Google', '네이버', '카카오'],
        '광고비': ['200만원', '110만원', '90만원', '40만원'],
        '비중': ['45%', '25%', '20%', '9%']
    })
    st.dataframe(media_share, hide_index=True, use_container_width=True)

st.markdown("---")

# [3단] 상세 데이터 테이블 섹션
st.subheader("📋 매체별 상세 성과 데이터")
raw_data = pd.DataFrame({
    '매체': ['Meta', 'Google', '네이버', '카카오', '합계 / 평균'],
    '광고비': ['2,000,000원', '1,100,000원', '1,000,000원', '400,000원', '4,500,000원'],
    '매출액': ['6,126,000원', '3,256,000원', '3,559,000원', '694,000원', '13,635,000원'],
    'ROAS': ['306.3%', '296.0%', '355.9%', '173.5%', '303.0%'],
    '전환수': ['142건', '88건', '95건', '22건', '347건']
})

st.dataframe(raw_data, hide_index=True, use_container_width=True)

st.markdown("---")

# [4단] AI 퍼포먼스 마케터 인사이트 및 제안 섹션
st.subheader(f"🤖 AI 퍼포먼스 마케팅 인사이트 & 액션 제안 ({current_advertiser_name})")

with st.container():
    st.markdown(f"""
    > **💡 [{current_advertiser_name}] 이번 주 핵심 진단 요약**
    > * **종합 평가**: 목표 ROAS(350%) 대비 현재 평균 ROAS(303.0%)는 다소 미달 상태이나, 네이버 매체가 355.9%로 유일하게 목표선을 방어하고 있습니다.
    > * **매체별 특이사항**: 카카오모먼트 계정(`{selected_id}`)의 데이터 누락일(2일 공백)을 보정할 경우 실제 효율은 약 **211.8%** 수준으로 추정됩니다.
    """)
    
    tab1, tab2, tab3 = st.tabs(["🚨 긴급 개선점", "💰 예산 재배분 제안", "🎨 크리에이티브 전략"])
    
    with tab1:
        st.markdown("""
        - **카카오/메타 타겟 오디언스 점검**: 
          - 효율이 저조한 카카오 및 메타 캠페인의 맞춤 타겟 모수 피로도를 진단하고 신규 타겟군 확장이 필요합니다.
        - **전환 추적(Pixel/SDK) 데이터 누락 검수**: 
          - 광고 계정 내 전환 태그 누락 일자가 발생하지 않도록 연동 상태를 재확인해 주세요.
        """)
        
    with tab2:
        st.markdown("""
        - **고효율 매체 집중 집행**: 
          - 목표 ROAS를 달성 중인 **네이버** 채널의 예산 소진율을 상향 조정하여 전체 평균 ROAS를 끌어올리는 방안을 제안합니다.
        - **저효율 매체 다각화**: 
          - 카카오 및 구글은 예산을 소폭 동결하거나 타겟 단가를 조절하여 효율 안정화를 도모해야 합니다.
        """)
        
    with tab3:
        st.markdown("""
        - **소재 교체 주기 도래 광고 그룹 식별**: 
          - CTR이 하락세를 보이는 소재들은 후킹 소구점을 변경한 신규 이미지/영상 소재로 즉시 교체 권장.
        """)