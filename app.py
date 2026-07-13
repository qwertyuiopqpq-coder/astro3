import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="성간 소광 분석기", layout="wide", page_icon="✨")

st.title("🌌 성간 소광 및 적색화 분석 대시보드")
st.markdown("""
지구과학 II 천문 단원의 **성간 소광(Stellar Extinction)**과 **적색화(Reddening)** 개념을 시각적으로 탐구하는 프로그램입니다.
성간 물질의 양을 조절하며 별의 관측 등급과 실제 거리의 변화를 분석해 보세요.
""")
st.markdown("---")

# 2. 가상의 관측 별 데이터 준비 (고유 특성)
@st.cache_data
def load_star_data():
    # 별 이름, 고유 색지수(B-V)0, 절대등급(M_V), 실제 거리(pc)
    data = {
        "별 이름": ["알타이르", "시리우스", "베가", "프로키온", "카펠라"],
        "고유 색지수 (B-V)₀": [-0.20, -0.05, 0.00, 0.30, 0.80],
        "절대 등급 (M_V)": [2.2, 1.4, 0.6, 2.7, -0.5],
        "실제 거리 (pc)": [5.1, 2.6, 7.7, 3.5, 13.0]
    }
    return pd.DataFrame(data)

df_base = load_star_data()

# 3. 사이드바 컨트롤러 (성간 물질 조건 설정)
st.sidebar.header("🛠️ 성간 물질 파라미터")
st.sidebar.markdown("우주 공간에 존재하는 성간 티끌의 밀도를 조절합니다.")

# 성간 물질 밀도 가중치 (0 = 진공, 3 = 매우 밀도가 높음)
dust_density = st.sidebar.slider("성간 티끌 밀도 가중치", 0.0, 3.0, 1.0, 0.1)

# 4. 데이터 계산 프로세스
df = df_base.copy()

# 성간 물질에 의한 색초과(E)와 소광량(A_V) 계산 (밀도에 비례한다고 가정)
df["색초과 (E_B-V)"] = np.round(0.25 * dust_density, 2)
df["성간 소광량 (A_V)"] = np.round(3.1 * df["색초과 (E_B-V)"], 2)

# 관측되는 색지수 및 겉보기 등급 역산
df["관측 색지수 (B-V)"] = df["고유 색지수 (B-V)₀"] + df["색초과 (E_B-V)"]
# 포그슨 방정식: V = M_V + 5*log10(d) - 5 + A_V
df["관측 등급 (V)"] = np.round(df["절대 등급 (M_V)"] + 5 * np.log10(df["실제 거리 (pc)"]) - 5 + df["성간 소광량 (A_V)"], 2)

# 보정 전 겉보기 거리 (성간 소광을 무시했을 때 어둡게 보여서 멀리 있다고 착각하는 거리)
df["소광 무시 분석 거리 (pc)"] = np.round(10 ** ((df["관측 등급 (V)"] - df["절대 등급 (M_V)"] + 5) / 5), 1)

# 5. 메인 화면 시각화 및 결과
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 성간 적색화 현상 (색지수 변화)")
    st.markdown("성간 물질이 많아질수록 별의 색지수가 오른쪽(적색)으로 이동합니다.")
    
    # Plotly를 이용한 색지수 변화 차트
    fig_reddening = px.scatter(
        df, 
        x="관측 색지수 (B-V)", 
        y="별 이름", 
        color="관측 색지수 (B-V)",
        color_continuous_scale="Bluered", # 파란색에서 빨간색으로 변하는 스케일
        range_color=[-0.4, 2.0],
        size=[15]*len(df),
        title="별의 관측 색지수 (오른쪽일수록 붉게 보임)"
    )
    fig_reddening.update_layout(xaxis_range=[-0.5, 2.0])
    st.plotly_chart(fig_reddening, use_container_width=True)

with col2:
    st.subheader("📐 거리 왜곡 분석 (소광의 영향)")
    st.markdown("성간 소광을 고려하지 않으면, 별이 실제보다 **훨씬 멀리 있는 것으로 오해**하게 됩니다.")
    
    # 실제 거리 vs 왜곡된 거리 비교 그래프를 위한 데이터 재구성
    df_melted = df.melt(
        id_vars=["별 이름"], 
        value_vars=["실제 거리 (pc)", "소광 무시 분석 거리 (pc)"],
        var_name="거리 종류", 
        value_name="거리"
    )
    
    fig_distance = px.bar(
        df_melted, 
        x="별 이름", 
        y="거리", 
        color="거리 종류", 
        barmode="group",
        title="실제 거리 vs 소광을 무시하고 계산한 거리"
    )
    st.plotly_chart(fig_distance, use_container_width=True)

# 6. 데이터 테이블 표시
st.subheader("📋 실시간 천문 분석 데이터 테이블")
st.dataframe(df.style.background_gradient(subset=["성간 소광량 (A_V)"], cmap="Reds"))

# 데이터 다운로드 기능
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="데이터를 CSV로 내보내기",
    data=csv,
    file_name='interstellar_extinction_data.csv',
    mime='text/csv',
)
