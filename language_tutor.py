import streamlit as st
import anthropic
import json
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="언어 학습 튜터",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS
st.markdown("""
<style>
    .stApp { max-width: 100%; }
    .user-message {
        background-color: #2563eb;
        color: white;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-left: 20%;
    }
    .assistant-message {
        background-color: #f3f4f6;
        color: #1f2937;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-right: 20%;
        border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# 세션 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'api_key' not in st.session_state:
    try:
        st.session_state.api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except:
        st.session_state.api_key = ""
if 'language' not in st.session_state:
    st.session_state.language = 'chinese'

LANGUAGES = {
    'chinese': {'name': '중국어', 'flag': '🇨🇳'},
    'spanish': {'name': '스페인어', 'flag': '🇪🇸'},
    'japanese': {'name': '일본어', 'flag': '🇯🇵'}
}

def get_response(messages, api_key):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system="You are a language tutor. Keep responses SHORT - 2-3 sentences maximum.",
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        return f"오류: {str(e)}"

# 헤더
st.title("📚 언어 학습 튜터")

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    
    if not st.session_state.api_key:
        api_key = st.text_input("Anthropic API Key", type="password")
        if api_key:
            st.session_state.api_key = api_key
    else:
        st.success("✅ API Key 설정됨")
    
    st.divider()
    
    language = st.selectbox(
        "학습 언어",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: f"{LANGUAGES[x]['flag']} {LANGUAGES[x]['name']}",
        index=list(LANGUAGES.keys()).index(st.session_state.language)
    )
    if language != st.session_state.language:
        st.session_state.language = language
        st.session_state.messages = []
        st.rerun()

# 메인
if not st.session_state.api_key:
    st.warning("⚠️ 사이드바에서 API Key를 입력하세요")
else:
    # 대화 표시
    if len(st.session_state.messages) == 0:
        st.info(f"{LANGUAGES[st.session_state.language]['name']} 학습을 시작하세요!")
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"<div class='user-message'>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='assistant-message'>{msg['content']}</div>", unsafe_allow_html=True)
    
    # 입력
    user_input = st.text_input("메시지 입력", key="input")
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        ai_response = get_response(messages_for_api, st.session_state.api_key)
        
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        st.rerun()
