# -*- coding: utf-8 -*-
"""
안전공급팀 통합관제 대시보드 (Streamlit)
- 디자인: 통합관제_대시보드.html 의 네온 글래스모피즘 테마 이식 (다크/라이트 토글)
- 데이터: Google Sheets(전체 시트) 실시간 연동
- 수정사항: 데이터 유실 방지(원본 표 분리), 캐시 시간 단축, 엑셀 에러값 방어
실행:  streamlit run app.py
"""

import re
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ──────────────────────────────────────────────────────────────────────────
# 0. 기본 설정
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="안전공급팀 통합관제 대시보드",
                   page_icon="🛰️", layout="wide",
                   initial_sidebar_state="expanded")

SHEET_URL = "https://docs.google.com/spreadsheets/d/13lej_n5Zgy3JeaiYMaZUWW7Z9Uq6VGfAZ-JTeMuoaVo/export?format=xlsx"

# 네온 팔레트 (다크 / 라이트)
PALETTE = {
    "dark":  ["#00f0ff", "#3b82f6", "#b53cff", "#ffaa00", "#ff3366", "#00e676", "#e2e8f0"],
    "light": ["#0284c7", "#2563eb", "#9333ea", "#d97706", "#e11d48", "#059669", "#64748b"],
}

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ──────────────────────────────────────────────────────────────────────────
# 1. 테마 CSS
# ──────────────────────────────────────────────────────────────────────────
def inject_css(theme: str):
    if theme == "dark":
        v = dict(bg="#060913", grad1="rgba(0,240,255,.05)", grad2="rgba(181,60,255,.05)",
                 grad3="#03050a", panel="rgba(16,22,36,.65)", border="rgba(255,255,255,.08)",
                 light="rgba(255,255,255,.15)", txt="#f8fafc", muted="#94a3b8", dark="#64748b",
                 th="rgba(16,22,36,.95)", rowh="rgba(255,255,255,.04)",
                 cyan="#00f0ff", blue="#3b82f6", purple="#b53cff", amber="#ffaa00",
                 red="#ff3366", green="#00e676", glow="0 0 18px")
    else:
        v = dict(bg="#f1f5f9", grad1="rgba(2,132,199,.05)", grad2="rgba(147,51,234,.05)",
                 grad3="#e2e8f0", panel="rgba(255,255,255,.9)", border="rgba(0,0,0,.1)",
                 light="rgba(0,0,0,.06)", txt="#0f172a", muted="#475569", dark="#94a3b8",
                 th="rgba(255,255,255,.97)", rowh="rgba(0,0,0,.03)",
                 cyan="#0284c7", blue="#2563eb", purple="#9333ea", amber="#d97706",
                 red="#e11d48", green="#059669", glow="0 2px 8px")

    st.markdown(f"""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&display=swap');

    .stApp {{
        background:
            radial-gradient(circle at 15% 50%, {v['grad1']} 0%, transparent 50%),
            radial-gradient(circle at 85% 30%, {v['grad2']} 0%, transparent 50%),
            linear-gradient(180deg, {v['bg']} 0%, {v['grad3']} 100%);
        background-attachment: fixed;
        font-family: 'Pretendard', sans-serif;
        color: {v['txt']};
    }}
    /* 사이드바 */
    [data-testid="stSidebar"] {{
        background: {v['panel']}; backdrop-filter: blur(20px);
        border-right: 1px solid {v['border']};
    }}
    [data-testid="stSidebar"] * {{ color: {v['txt']}; }}

    h1,h2,h3,h4 {{ color: {v['txt']}; font-weight: 800 !important; letter-spacing:-.4px; }}
    p, span, label, div {{ color: {v['txt']}; }}

    /* 글래스 카드 = st.container(border=True) */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: {v['panel']}; backdrop-filter: blur(16px);
        border: 1px solid {v['border']} !important; border-radius: 18px;
        box-shadow: 0 8px 32px rgba(0,0,0,.18); padding: 6px 10px;
    }}

    /* 헤더 배너 */
    .hero {{
        display:flex; justify-content:space-between; align-items:center; gap:18px; flex-wrap:wrap;
        background:{v['panel']}; backdrop-filter:blur(20px);
        border:1px solid {v['border']}; border-radius:20px; padding:18px 26px;
        box-shadow:0 10px 40px rgba(0,0,0,.15); margin-bottom:14px;
    }}
    .hero .brand {{ display:flex; align-items:center; gap:16px; }}
    .hero .logo {{
        width:54px;height:54px;border-radius:15px;display:grid;place-items:center;
        background:linear-gradient(135deg,{v['amber']},{v['red']});
        box-shadow:0 0 22px rgba(255,170,0,.35); font-size:26px;
    }}
    .hero h1 {{ font-size:21px; margin:0; line-height:1.2; }}
    .hero .sub {{ display:block; font-size:11px; font-weight:700; color:{v['amber']};
        letter-spacing:2.5px; margin-top:5px; text-transform:uppercase; }}
    .live {{ display:inline-flex; align-items:center; gap:7px; font-size:13px;
        color:{v['green']}; font-weight:800; }}
    .live .dot {{ width:9px;height:9px;border-radius:50%;background:{v['green']};
        box-shadow:0 0 10px {v['green']}; animation:pulse 2s infinite; }}
    .live .clock {{ font-family:'JetBrains Mono',monospace; color:{v['txt']}; font-size:15px; }}
    @keyframes pulse {{0%{{box-shadow:0 0 0 0 rgba(0,230,118,.6)}}70%{{box-shadow:0 0 0 9px rgba(0,230,118,0)}}100%{{box-shadow:0 0 0 0 rgba(0,230,118,0)}}}}

    /* KPI 카드 그리드 */
    .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin:4px 0 8px; }}
    .kpi {{ position:relative; overflow:hidden; padding:18px 20px; border-radius:18px;
        background:{v['panel']}; backdrop-filter:blur(16px); border:1px solid {v['border']};
        box-shadow:0 8px 32px rgba(0,0,0,.1); }}
    .kpi .lab {{ font-size:12.5px; color:{v['muted']}; font-weight:700; margin-bottom:9px; }}
    .kpi .val {{ font-family:'JetBrains Mono',monospace; font-size:33px; font-weight:800;
        line-height:1; letter-spacing:-1px; }}
    .kpi .unit {{ font-size:13px; font-weight:700; margin-left:4px; opacity:.7; }}
    .kpi::after {{ content:""; position:absolute; right:-22px; bottom:-22px; width:90px;height:90px;
        border-radius:50%; opacity:.12; filter:blur(16px); }}
    .k-cyan .val{{color:{v['cyan']}}} .k-cyan::after{{background:{v['cyan']}}}
    .k-blue .val{{color:{v['blue']}}} .k-blue::after{{background:{v['blue']}}}
    .k-purple .val{{color:{v['purple']}}} .k-purple::after{{background:{v['purple']}}}
    .k-amber .val{{color:{v['amber']}}} .k-amber::after{{background:{v['amber']}}}
    .k-red .val{{color:{v['red']}}} .k-red::after{{background:{v['red']}}}
    .k-green .val{{color:{v['green']}}} .k-green::after{{background:{v['green']}}}

    /* 카드 제목 바 */
    .ctitle {{ display:flex; align-items:center; gap:10px; font-size:15px; font-weight:800;
        margin:2px 0 2px 2px; color:{v['txt']}; }}
    .ctitle .bar {{ width:4px; height:15px; border-radius:4px; box-shadow:0 0 8px currentColor; }}
    .cdesc {{ font-size:12px; color:{v['muted']}; margin:0 0 6px 18px; font-weight:500; }}

    /* 섹션 헤더 */
    .sect {{ font-size:17px; font-weight:800; margin:18px 0 6px; color:{v['txt']};
        display:flex; align-items:center; gap:9px; }}
    .sect .ico {{ font-size:18px; }}

    /* 데이터프레임 */
    [data-testid="stDataFrame"] {{ border:1px solid {v['border']}; border-radius:14px; }}

    /* 라디오(시트 선택) 버튼화 */
    [data-testid="stSidebar"] [role="radiogroup"] label {{
        background:{v['rowh']}; border:1px solid {v['border']}; border-radius:11px;
        padding:9px 12px; margin-bottom:6px; transition:.2s; font-weight:700; font-size:13.5px;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {{ border-color:{v['cyan']}; }}

    /* 다운로드 버튼 */
    .stDownloadButton button, .stButton button {{
        background:{v['panel']}; border:1px solid {v['cyan']}; color:{v['cyan']};
        border-radius:11px; font-weight:800;
    }}
    .stDownloadButton button:hover, .stButton button:hover {{
        border-color:{v['cyan']}; box-shadow:0 0 14px {v['grad1']};
    }}
    [data-testid="stMetricValue"] {{ font-family:'JetBrains Mono',monospace; }}
    #MainMenu, footer {{ visibility:hidden; }}
    </style>
    """, unsafe_allow_html=True)


inject_css(st.session_state.theme)
IS_DARK = st.session_state.theme == "dark"
COLORS = PALETTE[st.session_state.theme]
GRID = "rgba(255,255,255,.07)" if IS_DARK else "rgba(0,0,0,.07)"
TXT = "#f8fafc" if IS_DARK else "#0f172a"


# ──────────────────────────────────────────────────────────────────────────
# 2. 데이터 로딩 (ttl 축소)
# ──────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)  # 1분 주기로 캐시 (수정 시 빠른 갱신)
def load_data():
    return pd.read_excel(SHEET_URL, sheet_name=None, engine="openpyxl")


# ──────────────────────────────────────────────────────────────────────────
# 3. 데이터 정리 / 컬럼 분류 헬퍼
# ──────────────────────────────────────────────────────────────────────────
FREETEXT_HINT = ("내용", "메모", "공사명", "비고", "조치", "원문", "위치", "장소", "주소",
                 "구분", "분야")  
DATE_HINT = ("날짜", "일자", "일시", "시간", "접수일", "시작일", "종료일", "완료일", "점검일", "참관일")


def dedupe_cols(cols):
    seen, out = {}, []
    for c in cols:
        c = str(c).strip()
        if c == "" or c.lower().startswith("unnamed"):
            c = "열"
        if c in seen:
            seen[c] += 1
            c = f"{c}_{seen[c]}"
        else:
            seen[c] = 0
        out.append(c)
    return out


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """데이터 유실을 막기 위해 안전하게 빈칸 및 오류값을 제거합니다."""
    df = df.copy()
    df.columns = dedupe_cols(df.columns)
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
    
    # 엑셀 에러값 방어 및 문자열 정리
    for c in df.columns:
        if df[c].dtype == object:
            s = df[c].astype(str).str.strip()
            # pandas의 nan, None 처리 및 엑셀 수식 에러 처리
            s = s.replace({
                "nan": np.nan, "NaN": np.nan, "None": np.nan, "": np.nan,
                "#DIV/0!": np.nan, "#N/A": np.nan, "#VALUE!": np.nan, "#REF!": np.nan
            })
            df[c] = s
    
    df = df.dropna(axis=0, how="all")
    return df.reset_index(drop=True)


def parse_dates(s: pd.Series) -> pd.Series:
    raw = s.astype(str)
    ext = raw.str.extract(r"(\d{2,4}\s*[.\-/]\s*\d{1,2}\s*[.\-/]\s*\d{1,2})", expand=False)
    norm = ext.str.replace(r"\s*[.\-/]\s*", "-", regex=True).str.rstrip("-")
    dt = pd.to_datetime(norm, errors="coerce", format="mixed")
    dt = dt.fillna(pd.to_datetime(raw, errors="coerce", format="mixed"))
    return dt


def to_numeric(s: pd.Series) -> pd.Series:
    cleaned = (s.astype(str)
               .str.replace(r"[₩,%\s]", "", regex=True)
               .str.replace("−", "-", regex=False))
    return pd.to_numeric(cleaned, errors="coerce")


def classify(df: pd.DataFrame):
    """차트 분석을 위해 컬럼 타입을 캐스팅합니다. 원본 df는 변형하지 않고 복사본(out)을 사용합니다."""
    out = df.copy()
    dates, nums, cats, texts = [], [], [], []
    n = len(out)
    for c in out.columns:
        s = out[c]
        name = str(c)
        is_date_name = any(h in name for h in DATE_HINT)
        
        if is_date_name or s.dtype == object:
            dt = parse_dates(s)
            if dt.notna().mean() >= (0.5 if is_date_name else 0.7) and dt.notna().sum() >= 3:
                out[c] = dt
                dates.append(c)
                continue
                
        if pd.api.types.is_numeric_dtype(s):
            out[c] = pd.to_numeric(s, errors="coerce")
            nums.append(c)
            continue
            
        num = to_numeric(s)
        if num.notna().mean() >= 0.6 and num.notna().sum() >= 3:
            out[c] = num
            nums.append(c)
            continue
            
        nun = s.dropna().nunique()
        ratio = nun / max(n, 1)
        is_freetext = any(h in name for h in FREETEXT_HINT) and name not in ("구분", "분야", "공사종류", "작업종류")
        
        if 1 < nun <= 25 and ratio < 0.6 and not is_freetext:
            cats.append(c)
        else:
            texts.append(c)
            
    return out, dates, nums, cats, texts


# ──────────────────────────────────────────────────────────────────────────
# 4. 차트 스타일 / 빌더
# ──────────────────────────────────────────────────────────────────────────
def style_fig(fig, h=300, legend=True):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Pretendard, sans-serif", color=TXT, size=12),
        margin=dict(l=10, r=10, t=10, b=10), height=h,
        colorway=COLORS,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, x=0,
                    font=dict(size=11)) if legend else dict(),
        showlegend=legend,
        hoverlabel=dict(font_family="Pretendard"),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, tickfont=dict(size=11))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(size=11))
    return fig


def card_title(title, desc="", color="#00f0ff"):
    st.markdown(f"<div class='ctitle'><span class='bar' style='background:{color}'></span>{title}</div>"
                + (f"<div class='cdesc'>{desc}</div>" if desc else ""),
                unsafe_allow_html=True)


def cfg():
    return {"displayModeBar": False}


# ──────────────────────────────────────────────────────────────────────────
# 5. 시트 단위 분석 렌더
# ──────────────────────────────────────────────────────────────────────────
def kpi_grid(items):
    html = "<div class='kpis'>"
    for lab, val, unit, cls in items:
        html += (f"<div class='kpi {cls}'><div class='lab'>{lab}</div>"
                 f"<div class='val'>{val}<span class='unit'>{unit}</span></div></div>")
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def build_kpis(df, dates, nums, cats, texts=None):
    texts = texts or []
    items = [("총 데이터 건수", f"{len(df):,}", "건", "k-cyan")]

    if dates:
        dc = dates[0]
        valid = df[dc].dropna()
        if len(valid):
            last = valid.max()
            this_month = ((valid.dt.year == pd.Timestamp.now().year) &
                          (valid.dt.month == pd.Timestamp.now().month)).sum()
            items.append(("최근 기록일", last.strftime("%y.%m.%d"), "", "k-blue"))
            items.append(("이번 달 건수", f"{this_month:,}", "건", "k-green"))

    for c in cats:
        vc = df[c].astype(str)
        if "긴급" in "".join(vc.unique()):
            items.append(("긴급 건수", f"{(vc == '긴급').sum():,}", "건", "k-red"))
            break

    if any("원인" in str(c) for c in cats):
        c = next(x for x in cats if "원인" in str(x))
        lightning = (df[c].astype(str) == "낙뢰").sum()
        if lightning:
            items.append(("낙뢰 피해", f"{lightning:,}", "건", "k-amber"))

    for c in cats + texts:
        s = df[c].dropna().astype(str)
        if s.str.fullmatch("완료").any() and df[c].nunique(dropna=True) <= 25:
            rate = s.eq("완료").sum() / len(df) * 100
            items.append(("완료율", f"{rate:.0f}", "%", "k-purple"))
            break

    if nums:
        c = nums[0]
        tot = df[c].sum()
        disp = f"{tot/1e8:.1f}억" if abs(tot) >= 1e8 else (f"{tot/1e4:.0f}만" if abs(tot) >= 1e4 else f"{tot:,.0f}")
        items.append((f"{c} 합계", disp, "", "k-blue"))

    kpi_grid(items[:6])


def trend_charts(df, dates):
    if not dates: return
    dc = dates[0]
    tmp = df.dropna(subset=[dc]).copy()
    if len(tmp) < 2: return
    
    st.markdown("<div class='sect'><span class='ico'>📈</span>추이 분석</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            card_title(f"월별 발생 추이", f"'{dc}' 기준 월 단위 집계", COLORS[0])
            m = (tmp.set_index(dc).resample("MS").size().reset_index(name="건수"))
            m = m[m["건수"] > 0].tail(36)
            fig = px.area(m, x=dc, y="건수", markers=True)
            fig.update_traces(line_color=COLORS[0], fillcolor="rgba(0,200,255,.12)")
            st.plotly_chart(style_fig(fig, 270, False), use_container_width=True, config=cfg())
    with c2:
        with st.container(border=True):
            card_title("연도별 발생량", f"'{dc}' 기준 연 단위 집계", COLORS[3])
            y = tmp[dc].dt.year.value_counts().sort_index().reset_index()
            y.columns = ["연도", "건수"]
            y["연도"] = y["연도"].astype(int).astype(str)
            fig = px.bar(y, x="연도", y="건수", text="건수")
            fig.update_traces(marker_color=COLORS[3], textposition="outside")
            st.plotly_chart(style_fig(fig, 270, False), use_container_width=True, config=cfg())


def dist_charts(df, cats):
    if not cats: return
    st.markdown("<div class='sect'><span class='ico'>🍩</span>분포 분석</div>", unsafe_allow_html=True)
    ordered = sorted(cats, key=lambda c: df[c].nunique())
    cols = st.columns(3)
    for i, c in enumerate(ordered):
        vc = df[c].dropna().astype(str).value_counts().head(12)
        if vc.empty: continue
        color = COLORS[i % len(COLORS)]
        with cols[i % 3]:
            with st.container(border=True):
                card_title(f"{c} 분포", f"고유값 {df[c].nunique()}종 · 상위 {len(vc)}", color)
                if len(vc) <= 6:
                    fig = px.pie(values=vc.values, names=vc.index, hole=0.55)
                    fig.update_traces(textinfo="percent", marker=dict(line=dict(width=0)))
                    st.plotly_chart(style_fig(fig, 250, True), use_container_width=True, config=cfg())
                else:
                    d = vc.sort_values().reset_index()
                    d.columns = [c, "건수"]
                    fig = px.bar(d, x="건수", y=c, orientation="h", text="건수")
                    fig.update_traces(marker_color=color, textposition="outside")
                    st.plotly_chart(style_fig(fig, 250, False), use_container_width=True, config=cfg())


def numeric_charts(df, nums, cats):
    if not nums: return
    st.markdown("<div class='sect'><span class='ico'>📊</span>수치 분석</div>", unsafe_allow_html=True)
    cols = st.columns(2)
    slot = 0
    if cats:
        c, n = cats[0], nums[0]
        g = df.groupby(df[c].astype(str))[n].sum().sort_values(ascending=False).head(12)
        if g.notna().any():
            with cols[slot % 2]:
                with st.container(border=True):
                    card_title(f"{c}별 {n} 합계", "범주별 수치 누계 비교", COLORS[1])
                    d = g.reset_index(); d.columns = [c, n]
                    fig = px.bar(d, x=c, y=n, text=n)
                    fig.update_traces(marker_color=COLORS[1], textposition="outside")
                    st.plotly_chart(style_fig(fig, 260, False), use_container_width=True, config=cfg())
            slot += 1
    for n in nums[:3]:
        if df[n].dropna().nunique() < 2: continue
        with cols[slot % 2]:
            with st.container(border=True):
                card_title(f"{n} 분포", "값 구간별 빈도(히스토그램)", COLORS[2])
                fig = px.histogram(df, x=n, nbins=25)
                fig.update_traces(marker_color=COLORS[2])
                st.plotly_chart(style_fig(fig, 260, False), use_container_width=True, config=cfg())
        slot += 1


def cross_chart(df, cats):
    if len(cats) < 2: return
    good = [c for c in cats if df[c].nunique() <= 12]
    if len(good) < 2: return
    a, b = good[0], good[1]
    st.markdown("<div class='sect'><span class='ico'>🔀</span>교차 분석</div>", unsafe_allow_html=True)
    with st.container(border=True):
        card_title(f"{a} × {b} 교차 분포", "두 범주의 조합별 건수", COLORS[4])
        ct = (df.assign(_a=df[a].astype(str), _b=df[b].astype(str))
              .groupby(["_a", "_b"]).size().reset_index(name="건수"))
        fig = px.bar(ct, x="_a", y="건수", color="_b", barmode="stack",
                     labels={"_a": a, "_b": b})
        st.plotly_chart(style_fig(fig, 320, True), use_container_width=True, config=cfg())


def render_sheet(name, raw):
    # 1. 원본 데이터의 구조만 안전하게 정리 (타입 변환 안함)
    df_clean = clean_df(raw)
    if df_clean.empty:
        st.info("이 시트에는 표시할 데이터가 없습니다.")
        return
        
    # 2. 차트 분석용으로만 강제 타입 변환 진행 (실패값은 NaN 처리됨)
    df_typed, dates, nums, cats, texts = classify(df_clean)

    # 필터 적용을 위해 복사
    fdf_typed = df_typed.copy()
    fdf_clean = df_clean.copy()

    # 날짜 필터 로직
    if dates:
        dc = dates[0]
        valid = df_typed[dc].dropna()
        if len(valid) > 1:
            lo, hi = valid.min().date(), valid.max().date()
            with st.sidebar:
                st.markdown("---")
                st.caption(f"📅 기간 필터 · {dc}")
                rng = st.date_input("기간", (lo, hi), min_value=lo, max_value=hi,
                                    key=f"date_{name}", label_visibility="collapsed")
            if isinstance(rng, (tuple, list)) and len(rng) == 2:
                s, e = pd.Timestamp(rng[0]), pd.Timestamp(rng[1]) + pd.Timedelta(days=1)
                mask = (df_typed[dc] >= s) & (df_typed[dc] < e)
                keep = mask | df_typed[dc].isna()
                # 필터 적용 시 차트용과 원본표용 모두 적용
                fdf_typed = fdf_typed[keep]
                fdf_clean = fdf_clean[keep]

    st.markdown(f"<div class='sect' style='font-size:20px'><span class='ico'>🛰️</span>{name}</div>",
                unsafe_allow_html=True)
                
    # 차트 그리기 (fdf_typed 사용)
    build_kpis(fdf_typed, dates, nums, cats, texts)
    trend_charts(fdf_typed, dates)
    dist_charts(fdf_typed, cats)
    numeric_charts(fdf_typed, nums, cats)
    cross_chart(fdf_typed, cats)

    # 원본 데이터 출력 (fdf_clean 사용 -> 텍스트 변환 누락 방지)
    st.markdown("<div class='sect'><span class='ico'>🗂️</span>원본 데이터</div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.dataframe(fdf_clean, use_container_width=True, height=360, hide_index=True)
        st.download_button("⬇️ 이 시트 CSV 다운로드",
                           fdf_clean.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{name}.csv", mime="text/csv",
                           use_container_width=True)


def render_overview(sheets):
    st.markdown("<div class='sect' style='font-size:20px'><span class='ico'>🏠</span>전체 개요</div>",
                unsafe_allow_html=True)
    counts = {n: len(clean_df(d)) for n, d in sheets.items()}
    total = sum(counts.values())
    items = [("연동 시트 수", f"{len(sheets)}", "개", "k-cyan"),
             ("총 데이터 건수", f"{total:,}", "건", "k-blue"),
             ("최다 데이터 시트", max(counts, key=counts.get)[:10], "", "k-purple"),
             ("동기화 상태", "LIVE", "", "k-green")]
    kpi_grid(items)

    c1, c2 = st.columns([1.4, 1])
    with c1:
        with st.container(border=True):
            card_title("시트별 데이터 보유량", "Google Sheets 각 탭의 행 수", COLORS[0])
            d = pd.Series(counts).sort_values().reset_index()
            d.columns = ["시트", "건수"]
            fig = px.bar(d, x="건수", y="시트", orientation="h", text="건수")
            fig.update_traces(marker_color=COLORS[0], textposition="outside")
            st.plotly_chart(style_fig(fig, 30 + 26 * len(counts), False),
                            use_container_width=True, config=cfg())
    with c2:
        with st.container(border=True):
            card_title("데이터 구성 비율", "전체 대비 시트 점유율", COLORS[2])
            d = pd.Series(counts)
            fig = px.pie(values=d.values, names=d.index, hole=0.55)
            fig.update_traces(textinfo="percent")
            st.plotly_chart(style_fig(fig, 320, True), use_container_width=True, config=cfg())
    st.caption("좌측 메뉴에서 개별 시트를 선택하면 해당 데이터의 KPI·추이·분포·수치·교차분석과 원본 표를 볼 수 있습니다.")


# ──────────────────────────────────────────────────────────────────────────
# 6. 레이아웃
# ──────────────────────────────────────────────────────────────────────────
now = pd.Timestamp.now().strftime("%Y-%m-%d  %H:%M")
st.markdown(f"""
<div class="hero">
  <div class="brand">
    <div class="logo">🛰️</div>
    <div><h1>안전공급팀 통합관제 대시보드<span class="sub">Daesung Clean Energy · Command Center</span></h1></div>
  </div>
  <div class="status">
    <div class="live"><span class="dot"></span>실시간 연동 &nbsp;·&nbsp; <span class="clock">{now}</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🌐 관제 메뉴")
    tlabel = "🌙 다크 모드" if IS_DARK else "☀️ 라이트 모드"
    if st.toggle(tlabel, value=IS_DARK, key="theme_toggle"):
        if st.session_state.theme != "dark":
            st.session_state.theme = "dark"; st.rerun()
    else:
        if st.session_state.theme != "light":
            st.session_state.theme = "light"; st.rerun()
    st.markdown("---")

try:
    with st.spinner("데이터를 실시간으로 동기화하고 있습니다..."):
        sheets = load_data()
        
    sheets = {k: v for k, v in sheets.items() if v is not None and not v.dropna(how="all").empty}

    with st.sidebar:
        menu = st.radio("📂 분석 대상 선택", ["🏠 전체 개요"] + list(sheets.keys()),
                        label_visibility="collapsed")
        st.markdown("---")
        # 새로고침 버튼 안내 보강
        if st.button("🔄 데이터 즉시 새로고침", use_container_width=True, help="구글 시트에 수정한 내용을 즉시 반영합니다."):
            load_data.clear(); st.rerun()
        st.caption("💡 시트 수정 후 1분 이내 자동 반영됩니다. 즉시 반영을 원하시면 위 버튼을 누르세요.")

    if menu == "🏠 전체 개요":
        render_overview(sheets)
    else:
        render_sheet(menu, sheets[menu])

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다. 시트 공유 설정(링크가 있는 모든 사용자 보기) 또는 네트워크를 확인하세요.")
    st.code(repr(e))