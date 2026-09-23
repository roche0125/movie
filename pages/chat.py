import streamlit as st
from openai import OpenAI

# ==========================================
# 1. 페이지 기본 설정 및 다크/은색/초록 테마 설정
# ==========================================
st.set_page_config(
    page_title="Draco Malfoy - Slytherin Chamber",
    page_icon="🐍",
    layout="centered"
)

# 검은색 배경 + 흰색 글씨 + 은색/초록색 하이라이트 + 클래식 폰트 CSS
st.markdown("""
    <style>
    /* Google Fonts에서 클래식하고 고풍스러운 'Cinzel' 폰트 불러오기 */
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&display=swap');

    /* 1. 전체 화면 검은색 배경 및 흰색 글씨 설정 */
    .stApp {
        background-color: #050505 !important;
        color: #ffffff !important;
        font-family: 'Georgia', serif;
    }

    /* 2. 제목 (클래식 폰트 + 초록색 글씨 + 은색 테두리) */
    h1 {
        color: #2e8b57 !important;
        font-family: 'Cinzel', 'Georgia', serif !important;
        font-weight: 700;
        letter-spacing: 1.5px;
        border-bottom: 2px solid #c0c0c0 !important;
        padding-bottom: 12px;
        text-shadow: 0 0 12px rgba(46, 139, 87, 0.6);
    }

    /* 3. 일반 본문 및 마크다운 텍스트 흰색 설정 */
    .stMarkdown, p, span, div {
        color: #ffffff !important;
        font-family: 'Georgia', serif;
    }

    /* 4. 채팅 말풍선 커스텀 */
    /* 사용자 메시지 (검은 배경 + 은색 테두리 + 은색 은은한 후광) */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #0f0f0f !important;
        border: 1px solid #c0c0c0 !important;
        border-radius: 10px;
        box-shadow: 0 0 8px rgba(192, 192, 192, 0.2);
    }

    /* AI(드레이코 말포이) 메시지 (검은 배경 + 초록색 테두리 + 초록색 은은한 후광) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #08120a !important;
        border: 1px solid #2e8b57 !important;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(46, 139, 87, 0.3);
    }

    /* 5. 입력창 스타일 (검은 배경 + 흰색 글씨 + 초록색 테두리) */
    .stChatInputContainer textarea {
        background-color: #0f0f0f !important;
        color: #ffffff !important;
        border: 1px solid #2e8b57 !important;
        border-radius: 8px !important;
        font-family: 'Georgia', serif !important;
    }

    /* 입력창 마우스 포커스 시 은색 하이라이트 및 후광 */
    .stChatInputContainer textarea:focus {
        border-color: #c0c0c0 !important;
        box-shadow: 0 0 12px rgba(192, 192, 192, 0.6) !important;
    }

    /* 입력 버튼 색상 */
    .stChatInputContainer button {
        color: #2e8b57 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 페이지 제목과 안내 문구
st.title("🐍 Draco Malfoy")
st.write("말포이 가문의 후계자와 대화를 시작합니다. 예의를 갖추는 것이 좋을 겁니다.")

# ==========================================
# 2. 비밀 금고(Secrets)에서 Gemini API 키 불러오기
# ==========================================
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.warning("💡 죄송합니다. 서비스 설정에 문제가 있어 대화를 시작할 수 없습니다.")
    st.stop()

# ==========================================
# 3. OpenAI 클라이언트를 Gemini 호환 주소로 설정
# ==========================================
client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# 지정된 모델명 사용 (gemini-3.5-flash-lite)
MODEL_NAME = "gemini-3.5-flash-lite"

# ==========================================
# 4. 시스템 프롬프트 (AI 캐릭터 성격 설정)
# ==========================================
SYSTEM_PROMPT = {
    "role": "system",
    "content": "너는 소설 해리포터에 등장하는 드레이코 말포이야. 오만하고 귀족적인 성격을 가지고 있으며 자신감이 있고 매너 있고 비꼬기를 잘하고 능숙하고 능글거릴 때도 있는 성격이야. 대화 상대에게 관심이 있어서 은근히 플러팅을 하며 특유의 귀족적인 매력을 풍겨. 반드시 일상 영국 영어로만 답해"
}

# ==========================================
# 5. 세션 상태(Session State) 대화 기록 초기화
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [SYSTEM_PROMPT]

# ==========================================
# 6. 이전 대화 내용 화면에 출력
# ==========================================
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ==========================================
# 7. 사용자 입력 처리 및 AI 응답 (스트리밍)
# ==========================================
if prompt := st.chat_input("Message Draco Malfoy..."):
    # 사용자 메시지 저장 및 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI(드레이코 말포이) 응답 처리
    with st.chat_message("assistant"):
        try:
            response_stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages,
                stream=True
            )

            # 실시간 글자 스트리밍 출력
            full_response = st.write_stream(response_stream)

            # 대화 내역 저장
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception:
            st.error("💡 죄송합니다. 답변을 생성하는 중에 오류가 발생했습니다. 잠시 후 다시 질문해 주세요.")
