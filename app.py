import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정 및 레이아웃 (우주 느낌의 다크 모드 권장)
st.set_page_config(page_title="Interstellar Extinction Analyser", layout="wide", page_icon="🌌")

# 사이드바 스타일 및 메인 타이틀을 조금 더 SF/연구소 느낌으로 데코레이션
st.title("🌌 성간 소광 및 적색화 정밀 분석 시스템")
st.caption("Interstellar Extinction & Reddening Analysis Dashboard (V1.2)")

st.markdown("""
이 시뮬레이터는 우주 티끌(Interstellar Dust)로 인해 발생하는 **성간 소광(Extinction)** 및 **적색화(Reddening)** 현상을 물리적 수식에 기반하여 정밀 분석합니다. 
특히 시선 방향의 거리에 따라 누적되는 성간 물질의 밀도를 계산하여, 실제 천체 관측에서 발생하는 **거리 측정 오차를 정량적으로 추적**합니다.
""")

# 2. 데이터 로드 (실제 천체의 물리량 반영 및 가상 데이터 최적화)
@st.cache_data
def load_star_data():
    data = {
        "별 이름": ["시리우스", "베가", "알타이르", "프로키온", "카펠라"],
        "고유 색지수 (B-V)₀": [-0.05, 0.00, 0.22, 0.42, 0.80],
        "절대 등급 (M_V)": [1.4, 0.6, 2.2, 2.7, -0.5],
        "실제 거리 (pc)": [2.6, 7.7, 5.1, 3.5, 13.0]
    }
    return pd.DataFrame(data)

df = load_star_data()

# 3. 사이드바 - 전문적인 성간 물질 파라미터 조절
st.sidebar.header("🛸 성간 환경 제어 패널")
st.sidebar.markdown("---")

# 단위 거리(pc)당 소광 계수 (단위: mag/pc) - 실제 은하면 평균은 k = 0.001 ~ 0.002 mag/pc 수준이지만, 
# 가상의 짧은 거리 데이터(13pc 이내)에서 극적인 시각적 효과를 위해 단위를 조절하여 계수화합니다.
k_factor = st.sidebar.slider(
    "성간 티끌 밀도 계수 (k)", 
    min_value=0.00, max_value=0.15, value=0.05, step=0.01,
    help="값이 클수록 pc당 빛이 더 많이 차단됩니다. (은하 원반 중심 방향일수록 높은 값)"
)

# 기본 성간 적색화 법칙 R_V 값 (은하계 평균 3.1)
rv_value = st.sidebar.number_input("R_V 상수 (선택도 소광비)", min_value=2.0, max_value=5.5, value=3.1, step=0.1)

# 4. 천문학적 정밀 수식 계산 프로세스 (거리 의존성 반영)
# 거리가 멀수록 지나오는 성간 물질이 많아지므로 소광량 A_V = k * 실제거리
df["성간 소광량 (A_V)"] = np.round(k_factor * df["실제 거리 (pc)"], 3)

# R_V = A_V / E(B-V) 공식 변형 -> 색초과 E(B-V) = A_V / R_V
df["색초과 (E_B-V)"] = np.round(df["성간 소광량 (A_V)"] / rv_value, 3)

# 관측되는 색지수 계산
df["관측 색지수 (B-V)"] = np.round(df["고유 색지수 (B-V)₀"] + df["색초과 (E_B-V)"], 3)

# 포그슨 거리지수 공식 (소광 포함): V = M_V + 5 * log10(d) - 5 + A_V
df["관측 등급 (V)"] = np.round(
    df["절대 등급 (M_V)"] + 5 * np.log10(df["실제 거리 (pc)"]) - 5 + df["성간 소광량 (A_V)"], 2
)

# 성간 소광을 무시했을 때 계산되는 잘못된 거리: d_err = 10 ** ((V - M_V + 5) / 5)
df["소광 무시 겉보기 거리 (pc)"] = np.round(
    10 ** ((df["관측 등급 (V)"] - df["절대 등급 (M_V)"] + 5) / 5), 1
)

# 오차율 계산
df["거리 왜곡 오차율 (%)"] = np.round(
    ((df["소광 무시 겉보기 거리 (pc)"] - df["실제 거리 (pc)"]) / df["실제 거리 (pc)"]) * 100, 1
)


# 5. 메인 대시보드 시각화 (다크 테마 적용)
st.subheader("📊 실시간 관측 시뮬레이션 및 데이터 스트림")

# 상단 데이터 프레임 요약 데이터 제공
st.dataframe(
    df[["별 이름", "실제 거리 (pc)", "성간 소광량 (A_V)", "색초과 (E_B-V)", "관측 색지수 (B-V)", "소광 무시 겉보기 거리 (pc)", "거리 왜곡 오차율 (%)"]],
    use_container_width=True
)

st.markdown("---")

col1, col2 = st.columns([1, 1])

# 왼쪽 열: 천문학의 꽃, H-R도 상에서의 소광 효과 (Professional Vector Plot)
with col1:
    st.markdown("### 🌌 H-R도 상의 등급 및 색지수 변화 (적색화 경로)")
    st.caption("성간 물질 때문에 별이 본래 위치(공)에서 오른쪽 아래(화살표 끝)로 치우쳐 관측됩니다.")
    
    fig_hr = go.Figure()
    
    for idx, row in df.iterrows():
        # 고유 위치 (소광 전)
        fig_hr.add_trace(go.Scatter(
            x=[row["고유 색지수 (B-V)₀"]], y=[row["절대 등급 (M_V)"]],
            mode='markers', name=f"{row['별 이름']} (Original)",
            marker=dict(size=14, symbol='circle-open', line=dict(width=2, color='cyan')),
            showlegend=True
        ))
        # 관측 위치 (소광 후) -> Y축을 절대등급 대신 겉보기등급 변동 관점을 보기 위해 M_V + A_V 형태로 플롯하여 왜곡을 인지시킴
        # 여기서는 직관성을 위해 '관측으로 인해 변한 겉보기 위치 상태'를 표현하기 위해 축을 구성합니다.
        fig_hr.add_trace(go.Scatter(
            x=[row["관측 색지수 (B-V)"]], y=[row["절대 등급 (M_V)"] + row["성간 소광량 (A_V)"]],
            mode='markers', name=f"{row['별 이름']} (Observed)",
            marker=dict(size=14, color='red', symbol='cross'),
            showlegend=False
        ))
        # 이동 화살표선 (적색화 벡터)
        fig_hr.add_trace(go.Scatter(
            x=[row["고유 색지수 (B-V)₀"], row["관측 색지수 (B-V)"]],
            y=[row["절대 등급 (M_V)"], row["절대 등급 (M_V)"] + row["성간 소광량 (A_V)"]],
            mode='lines', line=dict(color='rgba(255, 255, 255, 0.4)', dash='dash'),
            showlegend=False
        ))
        
        fig_hr.update_layout(
        template="plotly_dark",
        xaxis=dict(
            title="색지수 (B-V) [우측일수록 저온/적색 별]"
        ),
        yaxis=dict(
            title="절대등급 (M_V) [위쪽일수록 고광도 별]",
            autorange="reverse"
        ),
        height=450,
        margin=dict(l=40, r=40, t=40, b=40)
    )

# 오른쪽 열: 3D 관점에서 본 거리 왜곡 현상
with col2:
    st.markdown("### 📐 시선 방향 거리 측정 왜곡 비교")
    st.caption("붉은 막대(왜곡된 거리)가 푸른 막대(실제 거리)보다 비정상적으로 길어지는 현상을 확인하세요.")
    
    fig_distance = go.Figure()
    fig_distance.add_trace(go.Bar(
        x=df["별 이름"], y=df["실제 거리 (pc)"],
        name="실제 공간 내 거리 (True Distance)", marker_color="#00CCFF"
    ))
    fig_distance.add_trace(go.Bar(
        x=df["별 이름"], y=df["소광 무시 겉보기 거리 (pc)"],
        name="소광 무시 추정 거리 (Apparent Distance)", marker_color="#FF3366"
    ))
    
    fig_distance.update_layout(
        template="plotly_dark",
        barmode='group',
        xaxis_title="관측 대상 천체",
        yaxis_title="거리 단위 (pc)",
        height=450
    )
    st.plotly_chart(fig_distance, use_container_width=True)

st.markdown("---")

# 6. 심화 물리학 및 지2 개념 연계
st.subheader("🔬 Astrophysics Core Principle (지구과학 II 심화 고찰)")

col_info1, col_info2 = st.columns([1, 1])

with col_info1:
    st.markdown("""
    ### 🌌 파장 의존적 산란과 레이리-미 산란 (Rayleigh & Mie Scattering)
    성간 적색화가 일어나는 핵심 이유는 성간 티끌의 크기가 **별빛의 파장과 비슷하거나 더 작기 때문**입니다.
    - **산란 강도 규칙**: 산란 세기는 파장의 4제곱에 반비례($I \propto \lambda^{-4}$)하는 경향을 보입니다. 즉, 푸른빛($\lambda \approx 400\text{nm}$)이 붉은빛($\lambda \approx 700\text{nm}$)보다 훨씬 강하게 산란되어 경로 이탈을 일으킵니다.
    - **색초과 수식화**: 이로 인해 관측자가 측정한 색지수는 본래의 고유 색지수보다 무조건 커지게 됩니다.
      $$E_{B-V} = (B-V)_{\text{obs}} - (B-V)_0 > 0$$
    """)

with col_info2:
    st.markdown("""
    ### 🧮 거리지수 공식의 치명적 결함과 우주 거리 사다리
    현대 천문학에서 성간 소광량($A_V$)의 보정은 우주 거리를 측정할 때 가장 핵심적인 단계입니다.
    - **오차 메커니즘**: 소광 항인 $A_V$를 식에서 누락하면 아래 수식에 의해 계산됩니다.
      $$V - M_V = 5\log_{10}d_{\text{wrong}} - 5$$
      하지만 실제 올바른 식은 $V - M_V - A_V = 5\log_{10}d_{\text{true}} - 5$ 이므로, 결국 소광량만큼 겉보기 등급 $V$가 커진 것을 별이 그냥 멀리 있어서 어두워진 것으로 오해하게 만듭니다.
    - **결론**: 본 대시보드에서 보듯, 성간 물질의 밀도 계수($k$)가 조금만 증가해도 멀리 있는 천체(예: 카펠라)일수록 오차율이 기하급수적으로 폭증하는 것을 데이터로 입증할 수 있습니다.
    """)
