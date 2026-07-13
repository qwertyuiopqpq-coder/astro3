import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정 및 레이아웃
st.set_page_config(page_title="성간 소광 분석기", layout="wide", page_icon="🌌")

st.title("🌌 성간 소광 및 적색화 분석 대시보드")
st.markdown("""
이 프로그램은 지구과학 II 천문 단원의 핵심 개념인 **성간 소광(Stellar Extinction)**과 **성간 적색화(Reddening)**가 
별의 관측 등급 및 거리 측정에 미치는 영향을 실시간으로 시각화합니다.
""")
st.markdown("---")

# 2. 고유 천문 데이터 로드 (가상의 별 5개 - 거리를 다양하게 배치)
@st.cache_data
def load_star_data():
    data = {
        "별 이름": ["알타이르", "시리우스", "베가", "프로키온", "카펠라"],
        "고유 색지수 (B-V)₀": [-0.20, -0.05, 0.00, 0.30, 0.80],
        "절대 등급 (M_V)": [2.2, 1.4, 0.6, 2.7, -0.5],
        "실제 거리 (pc)": [5.1, 2.6, 7.7, 3.5, 13.0]
    }
    return pd.DataFrame(data)

df = load_star_data().copy()

# 3. 사이드바 - 성간 물질 파라미터 조절
st.sidebar.header("🛠️ 성간 물질 설정")
st.sidebar.markdown("우주 공간에 존재하는 성간 티끌의 밀도를 조절하여 소광 효과를 확인하세요.")

# 성간 티끌 밀도 가중치 스케일러 (단위 거리당 소광 계수 개념 도입)
dust_density = st.sidebar.slider("성간 티끌 밀도 가중치", min_value=0.0, max_value=3.0, value=1.0, step=0.1)

# 4. 천문학적 수식 계산 프로세스
# [수정] 거리가 멀수록 성간 물질을 많이 통과하므로 색초과가 누적되도록 변경
# 단위 거리(1pc)당 평균 색초과를 0.02로 가정하고 밀도 가중치와 실제 거리를 곱함
df["색초과 (E_B-V)"] = np.round(0.02 * dust_density * df["실제 거리 (pc)"], 2)

# V 밴드 성간 소광량 A_V = R_V * E(B-V)  (R_V = 3.1 적용)
df["성간 소광량 (A_V)"] = np.round(3.1 * df["색초과 (E_B-V)"], 2)

# 관측되는 색지수 계산: (B-V) = (B-V)₀ + E(B-V)
df["관측 색지수 (B-V)"] = df["고유 색지수 (B-V)₀"] + df["색초과 (E_B-V)"]

# 포그슨 거리지수 공식 변형: 관측 겉보기 등급(V) 계산
# V = M_V + 5 * log10(d) - 5 + A_V
df["관측 등급 (V)"] = np.round(
    df["절대 등급 (M_V)"] + 5 * np.log10(df["실제 거리 (pc)"]) - 5 + df["성간 소광량 (A_V)"], 2
)

# 성간 소광(A_V)을 무시하고 계산한 왜곡된 거리 (d_wrong = 10 ** ((V - M_V + 5) / 5))
df["소광 무시 겉보기 거리 (pc)"] = np.round(
    10 ** ((df["관측 등급 (V)"] - df["절대 등급 (M_V)"] + 5) / 5), 1
)

# 거리 왜곡 오차 (%)
df["거리 오차율 (%)"] = np.round(((df["소광 무시 겉보기 거리 (pc)"] - df["실제 거리 (pc)"]) / df["실제 거리 (pc)"]) * 100, 1)


# 5. 메인 대시보드 시각화 (2열 구성)
col1, col2 = st.columns([1, 1])

# 왼쪽 열: 성간 적색화 그래프
with col1:
    st.subheader("📊 성간 적색화 현상 (색지수 변화)")
    st.markdown("성간 물질이 밀해질수록 별이 본래 색보다 붉게 관측되어 색지수($B-V$) 값이 커집니다.")
    
    fig_reddening = px.scatter(
        df, 
        x="관측 색지수 (B-V)", 
        y="별 이름", 
        color="관측 색지수 (B-V)",
        color_continuous_scale="Bluered",
        range_color=[-0.4, 2.5],
        size=[20] * len(df),
        title="별의 관측 색지수 (우측일수록 붉게 보임)",
        hover_data=["고유 색지수 (B-V)₀", "색초과 (E_B-V)"]
    )
    
    fig_reddening.update_layout(xaxis_range=[-0.5, 2.7], yaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig_reddening, use_container_width=True)

# 오른쪽 열: 거리 왜곡 분석 그래프 (신규 추가)
with col2:
    st.subheader("📐 성간 소광으로 인한 거리 측정 왜곡")
    st.markdown("소광량($A_V$)을 무시하면 별이 실제보다 **더 어둡게 보여 훨씬 멀리 있는 것으로 오인**합니다.")
    
    # 실제 거리와 소광 무시 거리를 비교하는 그룹 바 차트
    fig_distance = go.Figure()
    fig_distance.add_trace(go.Bar(
        x=df["별 이름"], y=df["실제 거리 (pc)"],
        name="실제 거리 (pc)", marker_color="royalblue"
    ))
    fig_distance.add_trace(go.Bar(
        x=df["별 이름"], y=df["소광 무시 겉보기 거리 (pc)"],
        name="소광 무시 거리 (pc)", marker_color="crimson"
    ))
    
    fig_distance.update_layout(
        barmode='group',
        title="실제 거리 vs 소광을 무시하고 계산한 거리",
        xaxis_title="별 이름",
        yaxis_title="거리 (pc)"
    )
    st.plotly_chart(fig_distance, use_container_width=True)

st.markdown("---")

# 6. 데이터 분석 테이블 요약
st.subheader("📋 데이터 요약 및 분석 결과")
st.markdown("슬라이더를 움직이면 아래 테이블의 관측 데이터와 거리 오차율이 실시간으로 계산됩니다.")

# 화면에 보여줄 필드만 선택 및 정리
display_df = df[[
    "별 이름", "실제 거리 (pc)", "고유 색지수 (B-V)₀", 
    "색초과 (E_B-V)", "성간 소광량 (A_V)", "관측 등급 (V)", 
    "소광 무시 겉보기 거리 (pc)", "거리 오차율 (%)"
]]

st.dataframe(display_df.style.background_gradient(subset=["거리 오차율 (%)"], cmap="Reds"), use_container_width=True)

# 7. 핵심 개념 정리 요약 인터랙션
with st.expander("💡 지구과학 II 핵심 개념 체크 (시험 문제 빈출 포인트)"):
    st.markdown("""
    - **성간 소광($A_V$):** 성간 물질에 의해 별빛이 흡수되거나 산란되어 **본래보다 어둡게(겉보기 등급 $V$가 크게)** 보이는 현상입니다.
    - **성간 적색화($E_{B-V}$):** 파장이 짧은 푸른빛이 붉은빛보다 산란이 잘 되기 때문에, 별이 **본래보다 붉게(관측 색지수가 크게)** 보이는 현상입니다.
    - **거리 측정의 왜곡:** 성간 소광을 고려하지 않고 거리지수 공식($m-M = 5\log_{10}d - 5$)을 그대로 사용하면, 별이 실제보다 어둡기 때문에 **거리를 실제보다 더 멀리 있는 것으로 잘못 판단**하게 됩니다.
    """)
