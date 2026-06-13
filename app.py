import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="통합관제 대시보드", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# 2. Light Theme & 모던 CSS 
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
    .stApp { background-color: #F8FAFC; font-family: 'Pretendard', sans-serif; color: #0F172A; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
    h1, h2, h3 { color: #1E293B; font-weight: 800 !important; letter-spacing: -0.5px; }
    [data-testid="stMetric"] { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); transition: all 0.3s ease; }
    [data-testid="stMetric"]:hover { box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); transform: translateY(-2px); }
    [data-testid="column"]:nth-child(1) [data-testid="stMetric"] { border-top: 4px solid #3B82F6; }
    [data-testid="column"]:nth-child(2) [data-testid="stMetric"] { border-top: 4px solid #10B981; }
    [data-testid="column"]:nth-child(3) [data-testid="stMetric"] { border-top: 4px solid #F59E0B; }
    [data-testid="column"]:nth-child(4) [data-testid="stMetric"] { border-top: 4px solid #6366F1; }
    [data-testid="stMetricLabel"] p { color: #64748B; font-weight: 600; font-size: 14px; }
    [data-testid="stMetricValue"] { color: #0F172A; font-weight: 800; font-size: 32px !important; }
    .stDataFrame { background-color: #FFFFFF; border-radius: 12px; padding: 10px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 로딩
SHEET_URL = "https://docs.google.com/spreadsheets/d/13lej_n5Zgy3JeaiYMaZUWW7Z9Uq6VGfAZ-JTeMuoaVo/export?format=xlsx"

@st.cache_data(ttl=600)
def load_data():
    return pd.read_excel(SHEET_URL, sheet_name=None, engine='openpyxl')

try:
    with st.spinner("데이터를 실시간으로 동기화하고 있습니다..."):
        all_sheets = load_data()
    
    # 4. 사이드바
    st.sidebar.title("🌐 통합 4D 관제 메뉴")
    st.sidebar.markdown("---")
    sheet_names = list(all_sheets.keys())
    selected_sheet = st.sidebar.radio("📂 분석할 카테고리 선택", sheet_names)
    
    df = all_sheets[selected_sheet].copy()
    
    if not df.empty:
        df.columns = [str(col).strip() for col in df.columns]
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        all_cols = df.columns.tolist()
    
    st.sidebar.markdown("---")
    st.sidebar.caption("업데이트 시간: 실시간 연동 중")

    # 5. 메인 화면
    st.title(f"📑 {selected_sheet} 대시보드")
    st.markdown("선택된 데이터의 핵심 지표와 **3D/4D 입체 시각화**를 분석합니다.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    if df.empty:
        st.info("💡 이 탭에는 현재 표시할 데이터가 없습니다.")
    else:
        # --- [섹션 1] 요약 지표 ---
        st.subheader("💡 Key Metrics")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("총 등록 건수", f"{len(df):,} 건")
        k2.metric("관리 항목 수", f"{len(df.columns)} 개")
        if numeric_cols:
            target_num_col = numeric_cols[0]
            total_sum = df[target_num_col].sum()
            k3.metric(f"총 {target_num_col}", f"{total_sum/10000:.1f}만" if total_sum > 10000 else f"{total_sum:,.0f}")
            k4.metric(f"평균 {target_num_col}", f"{df[target_num_col].mean():,.1f}")
        else:
            k3.metric("수치형 데이터", "없음")
            k4.metric("데이터 상태", "정상")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- [섹션 2] 3D/4D 시각화 분석 ---
        st.subheader("🚀 다차원(3D & 4D) 시각화 엔진")
        
        if len(all_cols) >= 3:
            # 컨트롤러 영역
            ctrl1, ctrl2, ctrl3 = st.columns(3)
            with ctrl1:
                chart_mode = st.selectbox("🎨 시각화 차원 선택", ["2D 평면 그래프", "🧊 3D 입체 공간", "⏳ 4D 시간 애니메이션"])
            
            with ctrl2:
                x_col = st.selectbox("📍 X축 선택", all_cols, index=0)
                y_col = st.selectbox("📍 Y축 선택", all_cols, index=1 if len(all_cols)>1 else 0)
                
            with ctrl3:
                z_col = st.selectbox("📍 Z축 선택 (3D용 높이)", all_cols, index=2 if len(all_cols)>2 else 0)
                time_col = st.selectbox("⏱️ 애니메이션 축 (4D용 시간/순서)", all_cols, index=0)

            st.markdown("---")
            
            # 차트 렌더링
            if chart_mode == "2D 평면 그래프":
                fig = px.scatter(df, x=x_col, y=y_col, color=x_col, size=z_col if z_col in numeric_cols else None, 
                                 template="plotly_white", title=f"2D 산점도: {x_col} vs {y_col}")
                                 
            elif chart_mode == "🧊 3D 입체 공간":
                fig = px.scatter_3d(df, x=x_col, y=y_col, z=z_col, color=x_col, 
                                    template="plotly_white", title=f"3D 공간 탐색: {x_col}, {y_col}, {z_col}")
                fig.update_traces(marker=dict(size=8, line=dict(width=2, color='DarkSlateGrey')))
                
            else: # 4D 시간 애니메이션
                # 데이터를 애니메이션 축 기준으로 정렬 (재생이 자연스럽게 되도록)
                df_sorted = df.sort_values(by=time_col)
                fig = px.scatter_3d(df_sorted, x=x_col, y=y_col, z=z_col, 
                                    animation_frame=time_col, animation_group=x_col,
                                    color=x_col, template="plotly_white", 
                                    title=f"4D 타임라인 분석 (시간축: {time_col})")
                fig.update_traces(marker=dict(size=10, opacity=0.8))

            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=600)
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("3차원 이상의 차트를 생성하려면 최소 3개 이상의 열(Column)이 필요합니다.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🗂️ 원본 데이터 목록")
        st.dataframe(df, use_container_width=True, height=300)

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.code(e)