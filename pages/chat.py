import streamlit as st
from openai import OpenAI

# ==========================================
# 1. 페이지 기본 설정 및 은색/초록색 고급스러운 테마 커스텀
# ==========================================
st.set_page_config(
    page_title="Draco Malfoy - Slytherin Chamber",
    page_icon="🐍",
    layout="centered"
)

# 슬리더린 스타일(초록색 & 은색)의 클래식하고 우아한 디자인 적용
st.markdown("""
    <style>
    /* 전체 배경을 어두운 숲색/실버 톤으로 설정 */
    .stApp {
        background-color: #0b130e;
        color: #e0e0e0;
    }
    
    /* 제목 및 헤더 스타일 */
    h1 {
        color: #2e8b57 !important;
        font-family: 'Georgia', serif;
        border-bottom: 2px solid #c0c0c0;
        padding-bottom: 10px;
        text-shadow: 0 0 10px rgba(46, 139, 87, 0.4);
    }
    
    /* 설명글 스타일 */
    .stMarkdown p {
        font-family: 'Georgia', serif;
    }

    /* 채팅 말풍선 커스텀 */
    /* 사용자 메시지 (은색 테두리 및 어두운 배경) */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #1a241e !important;
        border: 1px solid #c0c0c0;
        border-radius: 12px;
        color: #e0e0e0;
    }

    /* AI(드레이코 말포이) 메시지 (슬리더린 초록색 테두리와 우아한 배경) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #122117 !important;
        border: 1px solid #2e8b57;
        border-radius: 12px;
        box-shadow: 0 0 8px rgba(46, 139, 87, 0.2);
    }

    /* 입력창 테두리 및 스타일 */
    .stChatInputContainer textarea {
        background-color: #141f17 !important;
        color: #e0e0e0 !important;
        border: 1px solid #2e8b57 !important;
        border-radius: 8px !important;
    }
    
    /* 입력창 포커스 시 은색 후광 효과 */
    .stChatInputContainer textarea:focus {
        border-color: #c0c0c0 !important;
        box-shadow: 0 0 10px rgba(192, 192, 192, 0.5) !important;
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
# Gemini OpenAI 호환 API 주소 설정
client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# 지정된 모델명 사용 (gemini-3.5-flash-lite)
MODEL_NAME = "gemini-3.5-flash-lite"

# ==========================================
# 4. 시스템 프롬프트 (AI 캐릭터 성격 설정)
# ==========================================
# 화면에는 띄우지 않고 AI 내부 프롬프트로만 사용
SYSTEM_PROMPT = {
    "role": "system",
    "content": "너는 소설 해리포터에 등장하는 드레이코 말포이야. 오만하고 귀족적인 성격을 가지고 있으며 자신감이 있고 매너 있고 비꼬기를 잘하고 능숙하고 능글거릴 때도 있는 성격이야. 반드시 일상 영국 영어로만 답해"
}

# ==========================================
# 5. 세션 상태(Session State) 대화 기록 초기화
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [SYSTEM_PROMPT]

# ==========================================
# 6. 이전 대화 내용 화면에 출력
# ==========================================
# system 메시지는 화면에 표시하지 않고, user와 assistant 메시지만 출력
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ==========================================
# 7. 사용자 입력 처리 및 AI 응답 (스트리밍)
# ==========================================
if prompt := st.chat_input("Message Draco Malfoy..."):
    # 사용자 메시지를 세션 및 화면에 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI(드레이코 말포이) 응답 출력
    with st.chat_message("assistant"):
        try:
            # 이전 모든 대화 기록을 전달하여 context 유지
            response_stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages,
                stream=True
            )

            # 스트리밍 응답 출력 (글자가 실시간으로 흘러나옴)
            full_response = st.write_stream(response_stream)

            # 답변이 완료되면 대화 기록에 저장
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception:
            # 오류 발생 시 빨간 에러창 대신 한국어 안내 문구 출력
            st.error("💡 죄송합니다. 답변을 생성하는 중에 오류가 발생했습니다. 잠시 후 다시 질문해 주세요.")
