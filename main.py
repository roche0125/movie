from datetime import datetime, timedelta, timezone
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# ==========================================
# 1. 스트림릿 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="어제 일별 박스오피스",
    page_icon="🎬",
    layout="wide"
)

# ==========================================
# 2. 한국 시간(KST) 기준 '어제' 날짜 계산
# ==========================================
# 배포 서버(Streamlit Cloud)의 시계는 UTC 기준일 수 있으므로, 
# 한국 표준시(UTC+9)를 명시적으로 설정해 줍니다.
kst = timezone(timedelta(hours=9))
now_kst = datetime.now(kst)
yesterday_kst = now_kst - timedelta(days=1)

# API 요청용 날짜 형식 (YYYYMMDD)
target_date_str = yesterday_kst.strftime("%Y%m%m")
# 화면 표시용 날짜 형식 (YYYY년 MM월 DD일)
display_date_str = yesterday_kst.strftime("%Y년 %m월 %d일")

st.title("🎬 어제 일별 박스오피스 순위")
st.caption(f"📅 기준 날짜: **{display_date_str}** (한국 시각 기준 어제)")

# ==========================================
# 3. KOBIS API 인증키 가져오기 (비밀 금고)
# ==========================================
# Streamlit Cloud의 Secrets에 등록된 'KOBIS_KEY' 항목을 불러옵니다.
kobis_key = st.secrets.get("KOBIS_KEY")

if not kobis_key:
    st.error("🔑 API 인증키(KOBIS_KEY)가 설정되지 않았습니다.")
    st.info("""
    **확인 방법:**
    1. `.streamlit/secrets.toml` 파일 또는 Streamlit Cloud 비밀 금고(Secrets) 환경 변수를 확인해 주세요.
    2. `KOBIS_KEY = "발급받은_인증키"` 형태로 저장해야 합니다.
    """)
    st.stop()

# ==========================================
# 4. KOBIS API 데이터 요청
# ==========================================
API_URL = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"

params = {
    "key": kobis_key,
    "targetDt": yesterday_kst.strftime("%Y%m%d")  # YYYYMMDD
}

@st.cache_data(ttl=3600)  # 1시간 동안 응답 데이터를 캐싱합니다.
def fetch_box_office(url, request_params):
    try:
        response = requests.get(url, params=request_params, timeout=10)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)

with st.spinner("박스오피스 데이터를 불러오는 중입니다..."):
    data, error_msg = fetch_box_office(API_URL, params)

# ==========================================
# 5. 예외 및 오류 처리
# ==========================================
# 네트워크 또는 서버 연결 실패 시
if error_msg:
    st.error("⚠️ 데이터를 불러오는 중 네트워크 오류가 발생했습니다.")
    st.warning(f"상세 오류 내용: {error_msg}")
    st.stop()

# KOBIS API는 인증키가 틀려도 HTTP 200 코드로 오고 'faultInfo' 응답을 전달합니다.
if "faultInfo" in data:
    st.error("🚨 API 인증 오류가 발생했습니다.")
    fault = data["faultInfo"]
    st.warning(f"오류 메시지: {fault.get('message', '알 수 없는 오류')}")
    st.info("""
    **무엇을 확인해야 할까요?**
    1. KOBIS 영화관입장권통합전산망에서 발급받은 인증키가 올바른지 확인해 주세요.
    2. Streamlit Secrets에 `KOBIS_KEY` 오탈자가 없는지 확인해 주세요.
    """)
    st.stop()

# 정상 응답 구조 확인 및 데이터 목록 추출
box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

# 영화 목록이 비어 있는 경우
if not daily_list:
    st.warning("⚠️ 어제 자 박스오피스 데이터가 아직 집계되지 않았거나 존재하지 않습니다.")
    st.info("""
    **무엇을 확인해야 할까요?**
    - KOBIS 시스템의 일일 데이터 업데이트 지연일 수 있습니다. 잠시 후 다시 시도해 주세요.
    """)
    st.stop()

# ==========================================
# 6. 데이터 전처리 (문자열 -> 숫자 변환)
# ==========================================
df = pd.DataFrame(daily_list)

# KOBIS API는 모든 숫자 데이터가 문자열로 제공되므로 수치형으로 변환합니다.
df['rank'] = pd.to_numeric(df['rank'])
df['rankInten'] = pd.to_numeric(df['rankInten'])
df['audiCnt'] = pd.to_numeric(df['audiCnt'])
df['audiAcc'] = pd.to_numeric(df['audiAcc'])
df['scrnCnt'] = pd.to_numeric(df['scrnCnt'])

# ==========================================
# 7. 대시보드 화면 구성
# ==========================================

# A. 1위 영화 지표 카드 3장
st.markdown("---")
st.subheader("🥇 어제 박스오피스 1위")

top_1 = df.iloc[0]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🎬 1위 영화명",
        value=top_1['movieNm'],
        delta=f"개봉일: {top_1['openDt']}"
    )

with col2:
    st.metric(
        label="🍿 일일 관객수",
        value=f"{top_1['audiCnt']:,} 명"
    )

with col3:
    st.metric(
        label="👥 누적 관객수",
        value=f"{top_1['audiAcc']:,} 명"
    )

st.markdown("---")

# B. 관객수 상위 5편 막대그래프 & 전체 박스오피스 표
col_chart, col_table = st.columns([1, 1])

# 관객수 상위 5편 추출
df_top5 = df.head(5).copy()

with col_chart:
    st.subheader("📊 관객수 상위 5편")
    
    # Plotly 시각화
    fig = px.bar(
        df_top5,
        x='movieNm',
        y='audiCnt',
        text='audiCnt',
        labels={'movieNm': '영화명', 'audiCnt': '일일 관객수(명)'},
        color='audiCnt',
        color_continuous_scale='Blues'
    )
    
    # 그래프 스타일 지정
    fig.update_traces(
        texttemplate='%{text:,}명', 
        textposition='outside'
    )
    fig.update_layout(
        xaxis_tickangle=-15,
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=50)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.subheader("📋 전체 박스오피스 순위")
    
    # 표에 출력할 컬럼 정리 및 이름 변경
    display_df = df[['rank', 'rankInten', 'movieNm', 'openDt', 'audiCnt', 'audiAcc', 'scrnCnt']].copy()
    
    # 순위 증감 텍스트 정리 (예: +2, -1, 동일)
    def format_rank_change(val):
        if val > 0:
            return f"▲ {val}"
        elif val < 0:
            return f"▼ {abs(val)}"
        return "-"
    
    display_df['rankInten'] = display_df['rankInten'].apply(format_rank_change)
    
    display_df.columns = [
        '순위', '순위증감', '영화명', '개봉일', '일일관객수', '누적관객수', '스크린수'
    ]
    
    # 천 단위 쉼표 포맷팅 및 데이터프레임 출력
    st.dataframe(
        display_df,
        column_config={
            "일일관객수": st.column_config.NumberColumn(format="%d 명"),
            "누적관객수": st.column_config.NumberColumn(format="%d 명"),
            "스크린수": st.column_config.NumberColumn(format="%d 개"),
        },
        hide_index=True,
        use_container_width=True
    )
