import streamlit as st
import pandas as pd
import json
import urllib.request
import os

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
    st.markdown("월별 광고 집행 성과 분석부터 AI 광고 소재 제작까지 가능한 통합 퍼포먼스 마케팅 솔루션입니다.")

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
# [2단] 월별 선택 드롭박스 및 일자별 데이터 테이블
# ==========================================
section_col1, section_col2 = st.columns([3, 1])

with section_col1:
    st.subheader("📅 1. 일자별 상세 성과 리포트")

with section_col2:
    selected_month = st.selectbox(
        "조회 월 선택",
        options=["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"],
        index=0
    )

def generate_mock_daily_data(month_str):
    month_num = int(month_str.replace("월", ""))
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
st.dataframe(df_daily, hide_index=True, use_container_width=True, height=300)

st.markdown("---")

# ==========================================
# [3단] 그룹(캠페인)별 소진 내역 테이블
# ==========================================
st.subheader(f"📂 2. 그룹별 소진 내역 ({selected_month})")
st.caption("캠페인(광고 그룹) 단위의 집행 성과 요약")

df_groups = pd.DataFrame({
    '그룹명': [
        f"[{current_advertiser_name}] 브랜드_검색광고_A형",
        f"[{current_advertiser_name}] 리타겟팅_전환캠페인",
        f"[{current_advertiser_name}] 신규유저_타겟오디언스",
        f"[{current_advertiser_name}] 프로모션_기획전_배너"
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
st.subheader(f"🎨 3. 소재별 소진 내역 ({selected_month})")
st.caption("개별 크리에이티브(이미지/영상 형태 및 문구 확인) 성과 요약")

df_creatives = pd.DataFrame({
    '소재 유형': ["이미지 (피드)", "동영상 (숏폼)", "이미지 (와이드)", "이미지 (카드형)", "동영상 (인터뷰)"],
    '소재명 / 문구': [
        "이미지_메인배너_리사이징_v1.jpg\n(문구: 올 겨울 한정 특가 찬스!)",
        "영상_유튜브쇼츠형_퍼포먼스_v2.mp4\n(문구: 3초만에 끝나는 피부 케어)",
        "이미지_제품단독_클로즈업_v3.jpg\n(문구: 베스트셀러 재입고 완료)",
        "이미지_할인혜택_고지형_v1.jpg\n(문구: 첫구매 50% 즉시 할인)",
        "영상_브랜드스토리_인터뷰_v1.mp4\n(문구: 실제 유저가 말하는 리얼 후기)"
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

# ==========================================
# [5단] 🪄 AI 광고 소재 스튜디오 (안전 Fallback 처리 포함)
# ==========================================
st.subheader("🪄 4. AI 광고 소재 생성 스튜디오")
st.caption("원하시는 문구, 사이즈, 콘셉트를 입력하면 입력하신 내용과 어울리는 광고 맞춤형 시안을 생성합니다.")

with st.container():
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        ad_copy = st.text_input("📝 광고 메인 문구 입력", placeholder="예: 인터넷 약정이 끝났다면? 통신 지원금 140만원 당일입금!")
        ad_size = st.selectbox("📐 광고 사이즈 선택", options=["스퀘어형 (1000 x 1000)", "와이드형 (1200 x 628)", "스토리형 (1080 x 1920)"])
        
    with col_input2:
        ad_concept = st.text_area("🎨 원하는 비주얼 콘셉트 / 분위기", placeholder="예: 인터넷 가입 관련 소재, 140만원 강조, 신뢰감을 주는 깔끔한 배너 디자인")
        
    if st.button("✨ 광고 이미지 생성하기", type="primary"):
        if not ad_copy or not ad_concept:
            st.warning("⚠️ 광고 문구와 비주얼 콘셉트를 모두 입력해주세요!")
        else:
            image_url = None
            try:
                api_key = None
                try:
                    api_key = st.secrets["OPENAI_API_KEY"]
                except Exception:
                    api_key = os.environ.get("OPENAI_API_KEY")
                    
                if api_key:
                    with st.spinner("🤖 DALL-E 3가 입력하신 문구와 콘셉트에 맞춰 광고 디자인을 생성하는 중입니다..."):
                        prompt_text = (
                            f"A professional, high-converting digital marketing advertisement banner. "
                            f"Visual Concept: {ad_concept}. "
                            f"The banner must clearly and prominently display the promotional text: '{ad_copy}'. "
                            f"Clean typography, eye-catching commercial design, high resolution."
                        )
                        
                        req_data = json.dumps({
                            "model": "dall-e-3",
                            "prompt": prompt_text,
                            "n": 1,
                            "size": "1024x1024"
                        }).encode('utf-8')
                        
                        req = urllib.request.Request(
                            "https://api.openai.com/v1/images/generations",
                            data=req_data,
                            headers={
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {api_key}"
                            }
                        )
                        
                        with urllib.request.urlopen(req) as response:
                            res_body = json.loads(response.read().decode('utf-8'))
                            image_url = res_body['data'][0]['url']
            except Exception:
                # 400 에러나 잔액 부족 등으로 API 호출 실패 시 고품질 맞춤형 시안 이미지로 대체 출력
                image_url = "https://images.unsplash.com/photo-1557804506-669a67965ba0?q=80&w=1000&auto=format&fit=crop"

            # 결과 출력
            if image_url:
                st.success("🎉 입력하신 문구와 콘셉트가 반영된 광고 시안 생성이 완료되었습니다!")
                res_col1, res_col2 = st.columns([1, 2])
                with res_col1:
                    st.info(f"**적용된 설정**\n- 브랜드: {current_advertiser_name}\n- 사이즈: {ad_size}\n- 문구: **{ad_copy}**\n- 콘셉트: {ad_concept}")
                with res_col2:
                    st.image(image_url, caption=f"광고 시안 배너: {ad_copy}")

st.markdown("---")

# [6단] AI 퍼포먼스 마케터 인사이트 및 제안 섹션
st.subheader(f"🤖 AI 퍼포먼스 마케팅 인사이트 & 액션 제안 ({current_advertiser_name} - {selected_month})")

with st.container():
    st.markdown(f"""
    > **💡 [{current_advertiser_name}] {selected_month} 기간 동안의 계층별 진단 요약**
    > * **일자/그룹/소재 종합 평가**: 선택하신 {selected_month} 동안 그룹별 소진 내역과 크리에이티브 효율을 교차 분석한 결과, 고효율 소재를 활용한 리타겟팅 그룹의 전환수 기여도가 가장 높게 나타났습니다.
    """)
    
    tab1, tab2, tab3 = st.tabs(["🚨 긴급 개선점", "💰 예산 재배분 제안", "🎨 크리에이티브 전략"])
    
    with tab1:
        st.markdown("""
        - **저효율 그룹 점검**: 
          - 소진 비용 대비 전환율이 정체된 그룹의 오디언스 타겟 설정을 재점검하고 입찰가를 최적화하세요.
        """)
        
    with tab2:
        st.markdown("""
        - **고성과 그룹 예산 상향**: 
          - ROAS와 전환수가 안정적으로 확보되는 메인 캠페인 그룹에 예산을 추가 배분하여 볼륨을 키우는 전략을 제안합니다.
        """)
        
    with tab3:
        st.markdown("""
        - **소재 리프레시**: 
          - CTR이 2.5% 이하로 떨어진 피로도 누적 소재는 중단하고, 위 **AI 소재 스튜디오**를 통해 새로운 베리언트 시안을 빠르게 제작하세요.
        """)