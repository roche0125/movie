import streamlit as st
from openai import OpenAI

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="친절한 정보 선생님 AI 채팅",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 친절한 정보 선생님과의 대화")
st.write("궁금한 정보나 코딩, 컴퓨터 개념이 있다면 무엇이든 물어보세요! 친절하게 설명해 드릴게요.")

# ==========================================
# 2. 비밀 금고(Secrets)에서 Gemini API 키 불러오기
# ==========================================
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.warning("⚠️ API 키가 설정되지 않았습니다. 비밀 금고(Secrets)에서 `GEMINI_API_KEY`를 등록해 주세요.")
    st.stop()

# ==========================================
# 3. OpenAI 클라이언트를 Gemini 호환 주소로 설정
# ==========================================
# Gemini OpenAPI 호환 서버 주소 설정
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
    "content": "너는 중고등학생에게 설명하는 친절한 정보 선생님이야. 어려운 말은 쉬운 말로 바꿔 주고, 반드시 순수 한국어로만 답해."
}

# ==========================================
# 5. 세션 상태(Session State) 대화 기록 초기화
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [SYSTEM_PROMPT]

# ==========================================
# 6. 이전 대화 내용 화면에 출력
# ==========================================
# system 메시지는 화면에 표시하지 않고, user와 assistant 메시지만 표시
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ==========================================
# 7. 사용자 입력 처리 및 AI 응답 (스트리밍)
# ==========================================
if prompt := st.chat_input("선생님께 질문할 내용을 입력하세요..."):
    # 사용자 메시지 화면 및 세션에 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 출력 영역 생성
    with st.chat_message("assistant"):
        try:
            # API 요청 (이전 모든 대화 기록을 함께 전달하여 맥락 기억)
            response_stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages,
                stream=True
            )

            # 스트리밍 응답 출력 (글자가 실시간으로 흘러나옴)
            full_response = st.write_stream(response_stream)

            # 답변 완결 후 세션 대화 기록에 저장
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            # 에러 발생 시 시스템 예외 화면 대신 친절한 한국어 안내 문구 표시
            st.error("💡 죄송합니다. 답변을 생성하는 중에 오류가 발생했습니다. 잠시 후 다시 질문해 주세요.")
