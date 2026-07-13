import streamlit as st

import pandas as pd

import numpy as np

import plotly.express as px



# 1. 페이지 설정 및 레이아웃

st.set_page_config(page_title="성간 소광 분석기", layout="wide", page_icon="🌌")



st.title("🌌 성간 소광 및 적색화 분석 대시보드")

st.markdown("""

이 프로그램은 지구과학 II 천문 단원의 핵심 개념인 **성간 소광(Stellar Extinction)**과 **성간 적색화(Reddening)**가 

별의 관측 등급 및 거리 측정에 미치는 영향을 실시간으로 시각화합니다.

""")

st.markdown("---")



# 2. 고유 천문 데이터 로드 (가상의 별 5개)

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



# V 밴드 성간 소광량 A_V = R_V * E(B-V)  (일반적인 성간 물질의 R_V 평균값인 3.1 적용)

df["성간 소광량 (A_V)"] = np.round(3.1 * df["색초과 (E_B-V)"], 2)



# 관측되는 색지수 계산

df["관측 색지수 (B-V)"] = df["고유 색지수 (B-V)₀"] + df["색초과 (E_B-V)"]



# 포그슨 거리지수 공식 변형: 관측 겉보기 등급(V) 계산

# V = M_V + 5 * log10(d) - 5 + A_V

df["관측 등급 (V)"] = np.round(

    df["절대 등급 (M_V)"] + 5 * np.log10(df["실제 거리 (pc)"]) - 5 + df["성간 소광량 (A_V)"], 2

)



# 성간 소광(A_V)을 무시하고 겉보기 등급과 절대 등급으로만 잘못 계산한 거리 (왜곡된 거리)

# d_wrong = 10 ** ((V - M_V + 5) / 5)

df["소광 무시 겉보기 거리 (pc)"] = np.round(

    10 ** ((df["관측 등급 (V)"] - df["절대 등급 (M_V)"] + 5) / 5), 1

)



# 5. 메인 대시보드 시각화 (2열 구성)

col1, col2 = st.columns([1, 1])



# 왼쪽 열: 성간 적색화 그래프



with col1:

    st.subheader("📊 성간 적색화 현상 (색지수 변화)")

    st.markdown("성간 물질이 밀해질수록 별이 본래 색보다 붉게 관측되어 색지수 값이 커집니다.")

    

    # 괄호와 인자 구조를 한눈에 보이도록 재정리 (SyntaxError 방지)

    fig_reddening = px.scatter(

        df, 

        x="관측 색지수 (B-V)", 

        y="별 이름", 

        color="관측 색지수 (B-V)",

        color_continuous_scale="Bluered",

        range_color=[-0.4, 2.0],

        size=[15, 15, 15, 15, 15],  # 명시적으로 배열 크기 지정

        title="별의 관측 색지수 위치 (우측일수록 붉은 별)"

    )

    

    fig_reddening.update_layout(xaxis_range=[-0.5, 2.2])

    st.plotly_chart(fig_reddening, use_container_width=True)

