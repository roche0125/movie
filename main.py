from datetime import datetime, timedelta, timezone
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# ==========================================
# 1. 스트림릿 페이지 기본 설정 & 클래식 테마 CSS
# ==========================================
st.set_page_config(
    page_title="Classic Cinema Box Office",
    page_icon="🎬",
    layout="wide"
)

# 클래식 스타일링 (고전 영화관 테마)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Serif KR', serif;
    }
    
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }

    /* 클래식 헤더 */
    .classic-header {
        text-align: center;
        padding: 20px;
        border-bottom: 2px solid #d97706;
        margin-bottom: 25px;
    }
    .classic-title {
        font-size: 2.4rem;
        font-weight: 700;
        color: #fef3c7;
        letter-spacing: 2px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }
    .classic-subtitle {
        color: #d97706;
        font-size: 1rem;
        margin-top: 5px;
    }

    /* 메트릭 카드 */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid #b45309;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stMetricLabel"] {
        color: #fcd34d !important;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
    }

    /* 티켓 디자인 */
    .ticket-box {
        background: #fef3c7;
        color: #1e1b4b;
        border: 2px dashed #b45309;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    .ticket-header {
        border-bottom: 2px solid #b45309;
        padding-bottom: 10px;
        margin-bottom: 15px;
        text-align: center;
    }
    .ticket-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #78350f;
    }
    .ticket-detail {
        font-size: 0.95rem;
        line-height: 1.8;
        color: #451a03;
    }

    /* 버튼 스타일 */
    .stButton>button {
        background-color: #b45309;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #d97706;
        color: #ffffff;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 한국 시간 기준 및 날짜 설정 (2000년 ~ 2026년)
# ==========================================
kst = timezone(timedelta(hours=9))
now_kst = datetime.now(kst)
yesterday_kst = (now_kst - timedelta(days=1)).date()

# 헤더
st.markdown("""
<div class="classic-header">
    <div class="classic-title">🎬 CLASSIC CINEMA BOX OFFICE</div>
    <div class="classic-subtitle">2000년 ~ 2026년 대한민국 일별 박스오피스 & 클래식 예매관</div>
</div>
""", unsafe_allow_html=True)

# 사이드바 설정
st.sidebar.header("📜 박스오피스 조회 설정")

# 2000년 1월 1일부터 조회 가능하도록 날짜 범위 설정
min_date = datetime(2000, 1, 1).date()
max_date = yesterday_kst

selected_date = st.sidebar.date_input(
    "📅 조회 날짜 선택",
    value=yesterday_kst,
    min_value=min_date,
    max_value=max_date,
    help="2000년 1월 1일부터 어제 날짜까지 선택할 수 있습니다."
)

target_date_str = selected_date.strftime("%Y%m%d")
display_date_str = selected_date.strftime("%Y년 %m월 %d일")

st.sidebar.markdown(f"**선택된 날짜:** `{display_date_str}`")

# ==========================================
# 3. KOBIS API 인증키 불러오기
# ==========================================
kobis_key = st.secrets.get("KOBIS_KEY")

if not kobis_key:
    st.error("🔑 API 인증키(KOBIS_KEY)가 설정되지 않았습니다.")
    st.info("""
    **확인 방법:**
    Streamlit Secrets(`.streamlit/secrets.toml`)에 `KOBIS_KEY = "발급받은_키"`를 저장해 주세요.
    """)
    st.stop()

# ==========================================
# 4. API 데이터 호출 및 캐싱
# ==========================================
API_URL = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"

params = {
    "key": kobis_key,
    "targetDt": target_date_str
}

@st.cache_data(ttl=3600)
def fetch_box_office(url, request_params):
    try:
        response = requests.get(url, params=request_params, timeout=10)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)

with st.spinner(f"📜 {display_date_str} 영화 기록을 찾아보는 중..."):
    data, error_msg = fetch_box_office(API_URL, params)

# 예외 처리
if error_msg:
    st.error("⚠️ 데이터를 불러오는 중 네트워크 오류가 발생했습니다.")
    st.warning(f"상세 오류 내용: {error_msg}")
    st.stop()

if "faultInfo" in data:
    st.error("🚨 API 인증 오류가 발생했습니다.")
    fault = data["faultInfo"]
    st.warning(f"오류 메시지: {fault.get('message', '알 수 없는 오류')}")
    st.stop()

box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning(f"⚠️ {display_date_str}의 박스오피스 데이터가 존재하지 않거나 집계 전입니다.")
    st.stop()

# 데이터프레임 전처리
df = pd.DataFrame(daily_list)
df['rank'] = pd.to_numeric(df['rank'])
df['rankInten'] = pd.to_numeric(df['rankInten'])
df['audiCnt'] = pd.to_numeric(df['audiCnt'])
df['audiAcc'] = pd.to_numeric(df['audiAcc'])
df['scrnCnt'] = pd.to_numeric(df['scrnCnt'])

# ==========================================
# 5. 티켓 예매 대화상자 (Dialog)
# ==========================================
@st.dialog("🎟️ 클래식 영화 티켓 예매")
def open_ticket_booking(movie_name, open_date):
    st.subheader(f"🎬 {movie_name}")
    st.caption(f"개봉일: {open_date} | 관람 선택일: {display_date_str}")
    
    col_a, col_b = st.columns(2)
    with col_a:
        time_slot = st.selectbox("⏰ 상영 시간", ["10:30 (조조)", "13:45", "16:20", "19:10 (프라임)", "21:50"])
        people_cnt = st.number_input("👥 관람 인원 (명)", min_value=1, max_value=8, value=2)
    
    with col_b:
        seat_type = st.radio("💺 좌석 타입", ["일반석 (14,000원)", "커플석 (18,000원)", "프리미엄석 (22,000원)"])
        seat_code = st.text_input("📍 좌석 번호 지정", value="G07, G08")
    
    # 가격 계산
    price_map = {"일반석 (14,000원)": 14000, "커플석 (18,000원)": 18000, "프리미엄석 (22,000원)": 22000}
    total_price = price_map[seat_type] * people_cnt

    st.markdown(f"### 💳 총 결제 금액: **{total_price:,} 원**")

    if st.button("✨ 예매 확정 및 티켓 발권", use_container_width=True):
        st.balloons()
        st.success("🎉 성공적으로 예매되었습니다!")
        
        # 영수증 형태의 실물 티켓 느낌 출력
        st.markdown(f"""
        <div class="ticket-box">
            <div class="ticket-header">
                <div class="ticket-title">🎟️ CLASSIC CINEMA TICKET</div>
                <small>CLASSIC TICKET ID: #{hash(movie_name + target_date_str) % 1000000:06d}</small>
            </div>
            <div class="ticket-detail">
                <b>• 영화명:</b> {movie_name}<br>
                <b>• 상영일시:</b> {display_date_str} [{time_slot}]<br>
                <b>• 상영관:</b> 클래식관 1관 (3F)<br>
                <b>• 인원/좌석:</b> {people_cnt}명 ({seat_type.split()[0]}) / {seat_code}<br>
                <b>• 결제금액:</b> {total_price:,}원 (결제 완료)
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 6. 상단 1위 영화 하이라이트 & 예매
# ==========================================
st.subheader("🥇 최고 흥행작 (1위)")

top_1 = df.iloc[0]
c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1.2])

with c1:
    st.metric(label="🎬 영화명", value=top_1['movieNm'], delta=f"개봉일: {top_1['openDt']}")
with c2:
    st.metric(label="🍿 일일 관객수", value=f"{top_1['audiCnt']:,} 명")
with c3:
    st.metric(label="👥 누적 관객수", value=f"{top_1['audiAcc']:,} 명")
with c4:
    st.write("")
    st.write("")
    if st.button("🎟️ 1위 예매하기", key="btn_top1", use_container_width=True):
        open_ticket_booking(top_1['movieNm'], top_1['openDt'])

st.markdown("---")

# ==========================================
# 7. 관객수 그래프 및 박스오피스 순위 표
# ==========================================
col_graph, col_list = st.columns([1, 1.2])

# 관객수 TOP 5 그래프
with col_graph:
    st.subheader("📊 관객수 TOP 5 (클래식 챠트)")
    df_top5 = df.head(5)
    
    fig = px.bar(
        df_top5,
        x='movieNm',
        y='audiCnt',
        text='audiCnt',
        labels={'movieNm': '영화명', 'audiCnt': '관객수'},
        color='audiCnt',
        color_continuous_scale='YlOrBr'
    )
    
    fig.update_traces(texttemplate='%{text:,}명', textposition='outside')
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#fef3c7'),
        xaxis=dict(showgrid=False, tickangle=-15),
        yaxis=dict(showgrid=True, gridcolor='#334155'),
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

# 박스오피스 표 및 각 영화별 예매 버튼
with col_list:
    st.subheader("📋 순위 목록 & 티켓 예매")
    
    for idx, row in df.iterrows():
        rank = row['rank']
        title = row['movieNm']
        audi = row['audiCnt']
        open_d = row['openDt']
        
        # 순위 아이콘
        rank_badge = f"🥇 {rank}위" if rank == 1 else (f"🥈 {rank}위" if rank == 2 else (f"🥉 {rank}위" if rank == 3 else f"  {rank}위"))
        
        col_r, col_t, col_a, col_b = st.columns([1, 2.5, 1.8, 1.5])
        with col_r:
            st.write(f"**{rank_badge}**")
        with col_t:
            st.write(f"**{title}**")
        with col_a:
            st.write(f"{audi:,} 명")
        with col_b:
            if st.button("🎟️ 예매", key=f"book_{rank}_{idx}", use_container_width=True):
                open_ticket_booking(title, open_d)
