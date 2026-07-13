import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정 및 레이아웃
st.set_page_config(page_title="성간 소광 분석기", layout="wide", page_icon="🌌")

# 대시보드 메인 타이틀
st.title("🌌 성간 소광 및 적색화 정밀 분석 대시보드")
st.caption("Interstellar Extinction & Reddening Analysis Dashboard (V1.3)")

# 소개글 및 물리적 원리 설명
st.markdown("""
이 프로그램은 지구과학 II 천문 단원의 핵심 개념인 **"성간 소광"**과 **"성간 적색화"**가 별의 관측 등급 및 거리 측정에 미치는 영향을 실시간으로 시각화하고 정량적으로 분석합니다.

### 🔍 왜 이런 현상이 나타날까요? (물리적 원리)
우주 공간의 **"성간 티끌(Interstellar Dust)"**은 빛을 흡수하거나 사방으로 흩어지게 만드는 **"산란"** 현상을 일으킵니다. 
이때 파장이 긴 붉은빛보다 파장이 짧은 푸른빛이 훨씬 더 강하게 산란됩니다 (파장의 4제곱에 반비례하는 경향). 

결과적으로 지구에 도달하는 별빛은 푸른빛을 많이 잃어 **본래보다 어둡게 보이고(성간 소광)**, 상대적으로 **붉은색을 띠게 됩니다(성간 적색화)**.
""")
st.markdown("---")

# 2. 고유 천문 데이터 로드 (실제/가상 천체 데이터 통합 최적화)
@st.cache_data
def load_star_data():
    data = {
        "별 이름": ["알타이르", "시리우스", "베가", "프로키온", "카펠라"],
        "고유 색지수 (B-V)₀": [-0.20, -0.05, 0.00, 0.30, 0.80],
        "절대 등급 (M_V)": [2.2, 1.4, 0.6, 2.7, -0.5],
        "실제 거리 (pc)": [5.1, 2.6, 7.7, 3.5, 13.0]
    }
    return pd.DataFrame(data)

df = load_star_data()

# 3. 사이드바 - 성간 물질 파라미터 조절
st.sidebar.header("🛠️ 성간 물질 설정")
st.sidebar.markdown("우주 공간에 존재하는 성간 티끌의 밀도를 조절하여 소광 효과를 확인하세요.")

# 성간 티끌 밀도 가중치 스케일러
dust_density = st.sidebar.slider("성간 티끌 밀도 가중치", min_value=0.0, max_value=3.0, value=1.0, step=0.1)

# 4. 천문학적 수식 계산 프로세스
# 색초과 E(B-V) = 관측 색지수 - 고유 색지수 (밀도에 비례한다고 가정)
df["색초과 (E_B-V)"] = np.round(0.25 * dust_density, 2)

# V 밴드 성간 소광량 A_V = R_V * E(B-V) (일반적인 성간 물질의 R_V 평균값인 3.1 적용)
df["성간 소광량 (A_V)"] = np.round(3.1 * df["색초과 (E_B-V)"], 2)

# 관측되는 색지수 계산
df["관측 색지수 (B-V)"] = np.round(df["고유 색지수 (B-V)₀"] + df["색초과 (E_B-V)"], 3)

# 포그슨 거리지수 공식 변형: 관측 겉보기 등급(V) 계산 (V = M_V + 5 * log10(d) - 5 + A_V)
df["관측 등급 (V)"] = np.round(
    df["절대 등급 (M_V)"] + 5 * np.log10(df["실제 거리 (pc)"]) - 5 + df["성간 소광량 (A_V)"], 2
)

# 성간 소광(A_V)을 무시하고 겉보기 등급과 절대 등급으로만 잘못 계산한 거리 (왜곡된 거리)
df["소광 무시 겉보기 거리 (pc)"] = np.round(
    10 ** ((df["관측 등급 (V)"] - df["절대 등급 (M_V)"] + 5) / 5), 1
)

# 오차율 추가 산출
df["거리 왜곡 오차율 (%)"] = np.round(
    ((df["소광 무시 겉보기 거리 (pc)"] - df["실제 거리 (pc)"]) / df["실제 거리 (pc)"]) * 100, 1
)


# 5. 메인 대시보드 데이터 테이블 출력
st.subheader("📊 실시간 관측 데이터 분석 스트림")
st.dataframe(
    df[["별 이름", "실제 거리 (pc)", "성간 소광량 (A_V)", "색초과 (E_B-V)", "관측 색지수 (B-V)", "관측 등급 (V)", "소광 무시 겉보기 거리 (pc)", "거리 왜곡 오차율 (%)"]],
    use_container_width=True
)

st.markdown("---")


# 6. 메인 대시보드 시각화 (2열 구성)
col1, col2 = st.columns([1, 1])

# 왼쪽 열: 성간 적색화 그래프 (오류가 없도록 고정된 표준 마커 방식 사용)
with col1:
    st.subheader("📊 성간 적색화 현상 (색지수 변화)")
    st.markdown("성간 물질이 밀해질수록 별이 본래 색보다 붉게 관측되어 색지수 값이 오른쪽으로 이동합니다.")
    
    fig_reddening = px.scatter(
        df, 
        x="관측 색지수 (B-V)", 
        y="별 이름", 
        color="관측 색지수 (B-V)",
        color_continuous_scale="Bluered",
        range_color=[-0.4, 2.0],
        title="별의 관측 색지수 위치 (우측일수록 붉은 별)"
    )
    
    # 안정적인 마커 크기 및 레이아웃 조정 (autorange 문법 에러 원천 차단)
    fig_reddening.update_traces(marker=dict(size=14, symbol='circle'))
    fig_reddening.update_layout(
        paper_bgcolor='rgba(15, 15, 20, 1)',
        plot_bgcolor='rgba(15, 15, 20, 1)',
        font=dict(color='white'),
        xaxis=dict(
            title="관측 색지수 (B-V)",
            range=[-0.6, 2.2],
            gridcolor='rgba(255, 255, 255, 0.1)'
        ),
        yaxis=dict(
            title="천체 이름",
            gridcolor='rgba(255, 255, 255, 0.1)'
        ),
        height=450
    )
    st.plotly_chart(fig_reddening, use_container_width=True)

# 오른쪽 열: 거리 왜곡 비교 그래프
with col2:
    st.subheader("📐 성간 소광으로 인한 거리 측정 왜곡")
    st.markdown("소광량($A_V$)을 보정하지 않으면 별이 실제보다 어둡게 보여 거리가 비정상적으로 길게 계산됩니다.")
    
    fig_distance = go.Figure()
    fig_distance.add_trace(go.Bar(
        x=df["별 이름"], y=df["실제 거리 (pc)"],
        name="실제 거리 (True)", marker_color="#00CCFF"
    ))
    fig_distance.add_trace(go.Bar(
        x=df["별 이름"], y=df["소광 무시 겉보기 거리 (pc)"],
        name="소광 무시 거리 (Apparent)", marker_color="#FF3366"
    ))
    
    fig_distance.update_layout(
        paper_bgcolor='rgba(15, 15, 20, 1)',
        plot_bgcolor='rgba(15, 15, 20, 1)',
        font=dict(color='white'),
        barmode='group',
        title="실제 거리 vs 소광을 무시하고 계산한 거리",
        xaxis=dict(title="별 이름", gridcolor='rgba(255, 255, 255, 0.1)'),
        yaxis=dict(title="거리 (pc)", gridcolor='rgba(255, 255, 255, 0.1)'),
        height=450
    )
    st.plotly_chart(fig_distance, use_container_width=True)

st.markdown("---")


# 7. 탐구 목적 및 지2 개념 정리 (가독성을 극대화한 배치)
st.subheader("💡 탐구 목적 및 지구과학 II 핵심 개념 정리")

col_info1, col_info2 = st.columns([1, 1])

with col_info1:
    st.markdown("""
    ### 🎯 탐구 목적
    1. **다양한 천체 데이터 분석:** 고유 색지수, 절대 등급, 실제 거리 등 **다양한 속성을 가진 천체 데이터를 연계 처리**하여 다각적인 데이터 분석 역량을 기릅니다.
    2. **정량적 오차 분석:** 성간 물질 효과를 보정하지 않았을 때 발생하는 우주 거리 측정의 치명적인 왜곡 오류를 수치와 그래프로 직접 비교·분석합니다.
    3. **천문학 수식의 시각화:** 지구과학 II 교과과정의 거리지수 공식을 코드로 구현함으로써 복잡한 천문 데이터 정제 과정을 직관적으로 이해합니다.
    """)

with col_info2:
    st.markdown("""
    ### 📖 지구과학 II 핵심 개념
    - **성간 소광 ($A_V$):** 성간 티끌이 빛을 흡수·산란시켜 별이 본래보다 어둡게 보이는 현상입니다. (겉보기 등급 $V$가 증가함)
    - **성간 적색화 & 색초과 ($E_{B-V}$):** 푸른빛이 더 강하게 산란되므로 관측 색지수가 고유 색지수보다 커져 별이 붉게 보입니다. 
      $$E_{B-V} = (B-V) - (B-V)_0$$
    - **거리 측정 오차 공식:** 소광량($A_V$)을 누락하면 거리지수 공식에 의해 **실제 거리보다 더 멀리 있는 것으로 오인**하게 됩니다.
      $$V - M_V = 5\\log_{10}d - 5$$
    """)
