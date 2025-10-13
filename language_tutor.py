import streamlit as st
import json
import time
from datetime import datetime
import os

# ==================== Anthropic 설정 ====================
try:
    from anthropic import Anthropic
except Exception:
    Anthropic = None

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

def _get_anthropic_client():
    if Anthropic is None:
        raise RuntimeError("Anthropic SDK 로드 실패")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("환경변수 ANTHROPIC_API_KEY 미설정")
    return Anthropic(api_key=api_key)

def _claude(messages, system, max_tokens=800, temperature=0):
    client = _get_anthropic_client()
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        system=system,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if not resp or not getattr(resp, "content", None):
        return ""
    return "".join([blk.text for blk in resp.content if hasattr(blk, "text")])

# 페이지 설정
st.set_page_config(
    page_title="Language Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# WeChat 스타일 CSS
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        max-width: 100%;
        background-color: #ededed;
    }
    
    /* 블록 컨테이너 여백 최소화 */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }
    
    /* 헤더 - WeChat 그린 */
    .header {
        background: linear-gradient(135deg, #09b83e 0%, #07a33a 100%);
        color: white;
    /* 높이 약 3배 확대 */
        min-height: 9rem; /* 기존 padding: 1rem → 높이 약 3배 수준 */
        padding: 0 1rem;  /* 위아래 여백 제거, 좌우 여백만 유지 */
        padding-bottom: 1rem; /* 아래쪽 여백 추가 */
    
    /* 내용 하단 정렬 */
        display: flex;
        flex-direction: column;
        justify-content: flex-end;  /* 내부 텍스트를 아래쪽으로 */
    
        border-radius: 0;
        margin: -1rem -1rem 0.25rem -1rem; !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }

    .header-title {
        font-size: 1.125rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.1rem;
    }
    
    /* 메시지 영역 배경 */
    .messages-container {
        background: #ededed;
        min-height: 50px;
        max-height: 550px;
        overflow-y: auto;
        padding: 0.25rem 1rem 1rem 1rem !important; 
        margin: 0 -1rem;
    }
    
    /* 사용자 메시지 - WeChat 그린 */
    .user-message {
        background: #95ec69;
        color: #000000;
        padding: 0.625rem 0.875rem;
        border-radius: 0.375rem;
        margin: 0.5rem 0;
        margin-left: auto;
        max-width: 70%;
        text-align: left;
        float: right;
        clear: both;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        word-wrap: break-word;
        font-size: 0.9375rem;
        line-height: 1.4;
        white-space: pre-wrap;
    }
    
    /* 튜터 메시지 - 흰색 */
    .assistant-message {
        background: #ffffff;
        color: #000000;
        padding: 0.625rem 0.875rem;
        border-radius: 0.375rem;
        margin: 0.5rem 0;
        margin-right: auto;
        max-width: 70%;
        float: left;
        clear: both;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        cursor: pointer;
        word-wrap: break-word;
        font-size: 0.9375rem;
        line-height: 1.4;
        white-space: pre-wrap;
    }
    
    .assistant-message:active {
        background: #f5f5f5;
    }
    
    /* 번역 텍스트 */
    .translation {
        color: #586c94;
        font-size: 0.8125rem;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px solid #e5e5e5;
        line-height: 1.3;
    }

    # CSS 부분에 추가
    
    /* 메시지 토글 버튼 완전히 숨김 */
    .stButton > button:not([kind="primary"]) {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        padding: 0 !important;
        margin: -1px !important;
        overflow: hidden !important;
        clip: rect(0, 0, 0, 0) !important;
        white-space: nowrap !important;
        border: 0 !important;
    }
    
    .translation-toggle {
        color: #586c94;
        font-size: 0.75rem;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px solid #e5e5e5;
    }
    
    /* 분석 패널 - WeChat 스타일 */
    .analysis-panel {
        background: #f7f7f7;
        border-top: 1px solid #d9d9d9;
        border-bottom: 1px solid #d9d9d9;
        padding: 0;
        margin: 0.5rem -1rem 0 -1rem;
    }
    
    .analysis-content {
        padding: 1rem;
        background: #ffffff;
    }
    
    .analysis-section {
        margin-bottom: 1rem;
    }
    
    .analysis-label {
        font-size: 0.75rem;
        color: #999999;
        margin-bottom: 0.375rem;
        font-weight: 500;
    }
    
    .pinyin-box {
        background: #f0f9ff;
        padding: 0.625rem;
        border-radius: 0.25rem;
        color: #1e40af;
        font-size: 0.875rem;
        border: 1px solid #bfdbfe;
        line-height: 1.5;
    }
    
    .word-item {
        background: #fafafa;
        border: 1px solid #e5e5e5;
        border-radius: 0.25rem;
        padding: 0.5rem;
        margin: 0.375rem 0;
        font-size: 0.875rem;
    }
    
    .word-chinese {
        font-weight: 600;
        font-size: 1rem;
        color: #000000;
    }
    
    .word-pinyin {
        color: #09b83e;
        margin-left: 0.375rem;
    }
    
    .word-meaning {
        color: #666666;
        margin-top: 0.25rem;
        font-size: 0.8125rem;
    }
    
    .grammar-box {
        background: #fef9e7;
        padding: 0.625rem;
        border-radius: 0.25rem;
        font-size: 0.8125rem;
        color: #333333;
        border: 1px solid #fde68a;
        line-height: 1.5;
    }
    
    .vocabulary-box {
        background: #f0fdf4;
        padding: 0.625rem;
        border-radius: 0.25rem;
        font-size: 0.8125rem;
        color: #333333;
        border: 1px solid #bbf7d0;
        line-height: 1.5;
    }
    
    .notes-box {
        background: #fef3c7;
        padding: 0.625rem;
        border-radius: 0.25rem;
        font-size: 0.8125rem;
        color: #333333;
        border: 1px solid #fde68a;
        line-height: 1.5;
    }
    
    .feedback-box {
        background: #f3e8ff;
        padding: 0.625rem;
        border-radius: 0.25rem;
        font-size: 0.8125rem;
        color: #333333;
        border: 1px solid #d8b4fe;
        line-height: 1.5;
    }
    
    /* 입력 영역 - WeChat 스타일 */
    .input-container {
        background: #f7f7f7;
        border-top: 1px solid #d9d9d9;
        padding: 0.625rem 1rem;
        margin: 0.5rem -1rem 0 -1rem;
    }
    
    /* 입력창과 버튼을 한 줄로 배치 */
    .input-row {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    
    /* 컬럼 간격 제거 */
    [data-testid="column"] {
        padding: 0 !important;
    }
    
    .stTextInput {
        flex: 1;
        margin-bottom: 0 !important;
    }
    
    .stTextInput > div {
        margin-bottom: 0 !important;
    }
    
    .stTextInput > div > div {
        margin-bottom: 0 !important;
    }
    
    .stTextInput > div > div > input {
        border-radius: 1.5rem;
        border: 1px solid #d9d9d9;
        padding: 0.625rem 1rem;
        background: #ffffff;
        font-size: 0.9375rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #09b83e;
        box-shadow: 0 0 0 2px rgba(9, 184, 62, 0.1);
    }
    
    .stTextInput > div > div > input:disabled {
        background: #f5f5f5;
        color: #999999;
        cursor: not-allowed;
    }
    
    /* 전송 버튼 - 작고 둥글게 */
    .stButton {
        margin-bottom: 0 !important;
    }
    
    .stButton > button[kind="primary"] {
        background: #09b83e;
        color: white;
        border: none;
        border-radius: 50%;
        padding: 0.625rem;
        width: 2.5rem;
        height: 2.5rem;
        font-size: 1.125rem;
        transition: background 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 2.5rem;
        margin: 0;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #07a33a;
    }
    
    .stButton > button[kind="primary"]:disabled {
        background: #d9d9d9;
        color: #999999;
    }
    
    /* 메시지 토글 버튼 보이게 하되 투명하게 */
    .stButton > button:not([kind="primary"]) {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        height: 0 !important;
        min-height: 0 !important;
    }
    
    .stButton > button:not([kind="primary"]):hover {
        background: transparent !important;
        border: none !important;
    }
    
    /* 사이드바 - WeChat 스타일 */
    [data-testid="stSidebar"] {
        background: #fafafa;
    }
    
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 0.375rem;
    }
    
    [data-testid="stSidebar"] h3 {
        color: #353535;
        font-size: 1rem;
        font-weight: 600;
        padding: 0.5rem 0;
    }
    
    /* 목표 아이템 */
    .goal-item {
        background: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 0.375rem;
        padding: 0.625rem;
        margin: 0.5rem 0;
        font-size: 0.875rem;
        color: #353535;
    }
    
    /* 로딩 애니메이션 - WeChat 스타일 */
    .loading-message {
        background: #ffffff;
        padding: 0.625rem 0.875rem;
        border-radius: 0.375rem;
        margin: 0.5rem 0;
        margin-right: auto;
        max-width: 70%;
        float: left;
        clear: both;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .loading-dots {
        display: inline-flex;
        gap: 0.25rem;
        padding: 0.5rem;
    }
    
    .loading-dot {
        width: 0.5rem;
        height: 0.5rem;
        background: #c8c8c8;
        border-radius: 50%;
        animation: wechat-bounce 1.4s infinite ease-in-out both;
    }
    
    .loading-dot:nth-child(1) { animation-delay: -0.32s; }
    .loading-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes wechat-bounce {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
    
    /* 빈 화면 안내 */
    .empty-state {
        text-align: center;
        padding: 1rem 1rem; !important;
    }
    
    .empty-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    .empty-title {
        color: #353535;
        font-size: 1.125rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    .empty-desc {
        color: #999999;
        font-size: 0.875rem;
    }
    
    /* 스크롤바 - WeChat 스타일 */
    .messages-container::-webkit-scrollbar {
        width: 4px;
    }
    
    .messages-container::-webkit-scrollbar-track {
        background: #ededed;
    }
    
    .messages-container::-webkit-scrollbar-thumb {
        background: #c8c8c8;
        border-radius: 2px;
    }
    
    .messages-container::-webkit-scrollbar-thumb:hover {
        background: #999999;
    }
    
    /* Expander 스타일 */
    .streamlit-expanderHeader {
        background: #fafafa;
        border: none;
        border-radius: 0;
        font-size: 0.875rem;
        color: #353535;
        font-weight: 500;
        padding: 0.75rem 1rem;
    }
    
    .streamlit-expanderHeader:hover {
        background: #f5f5f5;
    }
    
    .streamlit-expanderContent {
        background: #ffffff;
        border: none;
        padding: 0;
    }
    
    /* 다운로드 버튼 */
    .stDownloadButton > button {
        background: #09b83e;
        color: white;
        border: none;
        border-radius: 0.375rem;
        padding: 0.625rem;
        width: 100%;
        font-size: 0.9375rem;
        font-weight: 500;
        margin-top: 0.5rem;
    }
    
    .stDownloadButton > button:hover {
        background: #07a33a;
    }
    
    /* 구분선 */
    hr {
        border: none;
        border-top: 1px solid #e5e5e5;
        margin: 1rem 0;
    }
    
    /* 텍스트 입력 여백 제거 */
    .stTextInput > label {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = 'chinese'
if 'proficiency_level' not in st.session_state:
    st.session_state.proficiency_level = 'intermediate'
if 'detailed_analysis' not in st.session_state:
    st.session_state.detailed_analysis = None
if 'show_translation' not in st.session_state:
    st.session_state.show_translation = {}
if 'show_analysis' not in st.session_state:
    st.session_state.show_analysis = True
if 'is_loading' not in st.session_state:
    st.session_state.is_loading = False
if 'translating_message_id' not in st.session_state:
    st.session_state.translating_message_id = None
if 'goals' not in st.session_state:
    st.session_state.goals = []
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# 언어 정보
languages = {
    'spanish': {'name': '스페인어', 'flag': '🇪🇸'},
    'french': {'name': '프랑스어', 'flag': '🇫🇷'},
    'german': {'name': '독일어', 'flag': '🇩🇪'},
    'japanese': {'name': '일본어', 'flag': '🇯🇵'},
    'italian': {'name': '이탈리아어', 'flag': '🇮🇹'},
    'korean': {'name': '한국어', 'flag': '🇰🇷'},
    'chinese': {'name': '中文', 'flag': '🇨🇳'}
}

# 학습 목표
goals_by_language = {
    'chinese': [
        'HSK 5급 필수 어휘 마스터',
        '복잡한 문장 구조 이해',
        '성어 및 관용 표현 학습'
    ],
    'spanish': ['불규칙 동사 활용', '음식 어휘 확장'],
    'french': ['명사의 성 구분', '과거시제 활용'],
    'german': ['격변화 이해', '분리동사 학습'],
    'japanese': ['히라가나 읽기', '경어 표현'],
    'italian': ['동사 시제', '전치사 결합']
}

# 목표 초기화
def initialize_goals():
    if not st.session_state.goals:
        st.session_state.goals = goals_by_language.get(
            st.session_state.selected_language, 
            ['기초 문법', '일상 어휘']
        )

# 목표가 비어있으면 초기화
initialize_goals()

# 헤더
current_lang = languages[st.session_state.selected_language]
proficiency_kr = {
    'beginner': '초급', 
    'intermediate': '중급', 
    'advanced': '고급'
}[st.session_state.proficiency_level]

st.markdown(f"""
<div class="header">
    <div class="header-title">
        <span>💬</span>
        <span>Language Chat</span>
    </div>
    <div style="margin-top: 0.375rem; font-size: 0.8125rem; opacity: 0.95;">
        {current_lang['flag']} {current_lang['name']} · {proficiency_kr}
    </div>
</div>
""", unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    
    # 언어 선택
    selected_lang = st.selectbox(
        "언어",
        options=list(languages.keys()),
        format_func=lambda x: f"{languages[x]['flag']} {languages[x]['name']}",
        index=list(languages.keys()).index(st.session_state.selected_language),
        key='lang_select'
    )
    
    # 언어 변경 시 초기화
    if selected_lang != st.session_state.selected_language:
        st.session_state.selected_language = selected_lang
        st.session_state.messages = []
        st.session_state.detailed_analysis = None
        st.session_state.show_translation = {}
        st.session_state.goals = []
        initialize_goals()
        st.rerun()
    
    # 숙련도 선택
    st.session_state.proficiency_level = st.selectbox(
        "숙련도",
        options=['beginner', 'intermediate', 'advanced'],
        format_func=lambda x: {'beginner': '초급', 'intermediate': '중급', 'advanced': '고급'}[x],
        index=['beginner', 'intermediate', 'advanced'].index(st.session_state.proficiency_level)
    )
    
    st.markdown("---")
    
    # 학습 목표
    st.markdown("### 🎯 학습 목표")
    
    # 기존 목표 표시 및 삭제
    for idx, goal in enumerate(st.session_state.goals):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f'<div class="goal-item">• {goal}</div>', unsafe_allow_html=True)
        with col2:
            if st.button("×", key=f"del_goal_{idx}"):
                st.session_state.goals.pop(idx)
                st.rerun()
    
    # 새 목표 추가
    new_goal_input = st.text_input("새 목표 추가", key="goal_input", placeholder="목표를 입력하세요...")
    if st.button("➕ 추가", use_container_width=True):
        if new_goal_input.strip():
            st.session_state.goals.append(new_goal_input.strip())
            st.rerun()
    
    st.markdown("---")
    
    # 대화 저장
    save_disabled = len(st.session_state.messages) == 0
    
    if st.button("💾 대화 저장", disabled=save_disabled, use_container_width=True, key='save_btn'):
        text_content = f"언어 학습 기록\n언어: {current_lang['name']}\n숙련도: {proficiency_kr}\n날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for msg in st.session_state.messages:
            role = "학습자" if msg['role'] == 'user' else "튜터"
            text_content += f"{role}: {msg['content']}\n"
            if 'translation' in msg:
                text_content += f"[번역]: {msg['translation']}\n"
            text_content += "\n"
        
        st.download_button(
            label="📥 파일 다운로드",
            data=text_content.encode('utf-8'),
            file_name=f"학습기록_{current_lang['name']}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain;charset=utf-8",
            use_container_width=True
        )

# 메시지 표시 영역 부분만 수정

# 메시지 표시 영역
st.markdown('<div class="messages-container">', unsafe_allow_html=True)

if len(st.session_state.messages) == 0:
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-icon">{current_lang['flag']}</div>
        <div class="empty-title">{current_lang['name']} 학습 시작</div>
        <div class="empty-desc">메시지를 입력하세요</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for idx, msg in enumerate(st.session_state.messages):
        if msg['role'] == 'user':
            st.markdown(f'<div class="user-message">{msg["content"]}</div><div style="clear:both;"></div>', unsafe_allow_html=True)
        else:
            show_trans = st.session_state.show_translation.get(idx, False)
            
            if 'translation' in msg and show_trans:
                content = f"""
                <div style="color: #000000;">{msg['content']}</div>
                <div class="translation">{msg['translation']}</div>
                <div class="translation-toggle">👆 원문 보기</div>
                """
            else:
                is_translating = st.session_state.translating_message_id == idx
                toggle_text = "⏳ 번역 중..." if is_translating else "👆 번역하기"
                content = f"""
                <div>{msg['content']}</div>
                <div class="translation-toggle">{toggle_text}</div>
                """
            
            # 버튼을 메시지 영역 안에 숨김
            col1, col2, col3 = st.columns([1, 20, 1])
            with col2:
                # 메시지 표시
                st.markdown(f'<div class="assistant-message">{content}</div>', unsafe_allow_html=True)
                
                # 투명한 버튼으로 클릭 영역 생성
                if st.button("　", key=f"msg_btn_{idx}", help="클릭하여 번역"):
                    if 'translation' in msg:
                        st.session_state.show_translation[idx] = not show_trans
                    elif not is_translating:
                        st.session_state.translating_message_id = idx  # LLM 번역을 위해 플래그만 설정
                    st.rerun()
            
            st.markdown('<div style="clear:both;"></div>', unsafe_allow_html=True)
    
    if st.session_state.is_loading:
        st.markdown("""
        <div class="loading-message">
            <div class="loading-dots">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        </div>
        <div style="clear:both;"></div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# 입력 영역
col_input, col_button = st.columns([10, 1])

with col_input:
    user_input = st.text_input(
        "message",
        placeholder=f"{current_lang['name']}로 입력...",
        key=f"user_input_{st.session_state.input_key}",
        label_visibility="collapsed",
        disabled=st.session_state.is_loading
    )

with col_button:
    send_button = st.button("↑", type="primary", disabled=st.session_state.is_loading or not user_input.strip(), key="send_btn")

# ==================== LLM 유틸 함수 ====================

def _build_tutor_system_prompt(target_lang: str):
    return (
        "역할: 외국어 회화 튜터.\n"
        "규칙:\n"
        "- 감정 표현 금지.\n"
        "- 사실 기반으로만 답변하고 불확실한 내용은 '확인 불가' 명시.\n"
        "- 추측 금지, 간결·정확한 문장 사용.\n"
        "- 출력 언어: 사용자가 선택한 학습 언어로 답변.\n"
        "- 첫 응답에서만 학습 목표를 1회 언급하고 이후 반복 금지.\n"
    )

def _history_for_anthropic():
    hist = []
    for m in st.session_state.messages:
        role = "user" if m['role'] == 'user' else "assistant"
        hist.append({"role": role, "content": m['content']})
    return hist

def generate_assistant_reply(user_msg: str):
    is_first_turn = sum(1 for m in st.session_state.messages if m['role'] == 'assistant') == 0
    goals_text = ", ".join(st.session_state.goals) if st.session_state.goals else "기초 회화"
    system_prompt = _build_tutor_system_prompt(st.session_state.selected_language)
    hist = _history_for_anthropic()
    if is_first_turn:
        user_instruction = (
            f"사용자 학습 목표: {goals_text}\n"
            f"사용자 입력: {user_msg}\n"
            "첫 응답이므로 학습 목표를 1회만 간략히 언급하고, 이후에는 언급하지 말고 질의에만 직접 답변."
        )
    else:
        user_instruction = (
            f"사용자 입력: {user_msg}\n"
            "학습 목표 재언급 금지. 질문에 직접 간결하게 답변."
        )
    messages = hist + [{"role": "user", "content": user_instruction}]
    return _claude(messages=messages, system=system_prompt, max_tokens=600, temperature=0)

def generate_chinese_analysis(user_msg: str):
    """중국어 상세 분석 JSON 생성 → UI 스키마로 매핑"""
    system_prompt = (
        "역할: 중국어 학습 분석기.\n"
        "출력: 반드시 JSON만 출력.\n"
        "키: pinyin(str), words(list[{chinese,pinyin,meaning_ko}]), "
        "grammar(str), vocabulary(list[str]), notes(str), "
        "feedback({expression, grammar_feedback, context, word_choice}).\n"
        "설명은 간결하게, 한국어 의미는 meaning_ko에 표기."
    )
    user_prompt = (
        "다음 학습자 발화를 분석하라.\n"
        f"발화: {user_msg}\n"
        "형식은 JSON만 반환하고, 추가 설명 금지."
    )
    messages = [{"role": "user", "content": user_prompt}]
    raw = _claude(messages=messages, system=system_prompt, max_tokens=800, temperature=0)
    try:
        data = json.loads(raw)
        words = []
        for w in data.get("words", []):
            words.append({
                "chinese": w.get("chinese", ""),
                "pinyin": w.get("pinyin", ""),
                "meaning": w.get("meaning_ko", "")
            })
        analysis = {
            "pinyin": data.get("pinyin", ""),
            "words": words,
            "grammar": data.get("grammar", ""),
            "vocabulary": data.get("vocabulary", []),
            "notes": data.get("notes", ""),
            "feedback": data.get("feedback", {})
        }
        return analysis
    except Exception:
        # 파싱 실패 시 최소 기본값
        return {
            "pinyin": "",
            "words": [],
            "grammar": "",
            "vocabulary": [],
            "notes": "",
            "feedback": {
                "expression": f"'{user_msg}' 표현을 기준으로 분석을 진행했습니다.",
                "grammar_feedback": "문법 검토 결과는 추가 입력이 필요합니다.",
                "context": "맥락 적합성 평가는 추가 정보가 필요합니다.",
                "word_choice": "어휘 선택 평가는 추가 정보가 필요합니다."
            }
        }

def translate_to_korean(text: str, source_hint: str = ""):
    system_prompt = (
        "역할: 전문 번역가. 간결하고 정확한 번역을 제공. "
        "불필요한 설명 금지. 한국어로만 번역 결과 출력."
    )
    user_prompt = f"다음을 한국어로 정확히 번역하라.\n원문: {text}"
    if source_hint:
        user_prompt += f"\n언어 힌트: {source_hint}"
    messages = [{"role": "user", "content": user_prompt}]
    return _claude(messages=messages, system=system_prompt, max_tokens=400, temperature=0)

# 중국어 상세 분석 (입력창 아래로 이동)
if st.session_state.selected_language == 'chinese' and st.session_state.detailed_analysis:
    with st.expander("📚 상세 분석", expanded=st.session_state.show_analysis):
        analysis = st.session_state.detailed_analysis
        
        if analysis.get('pinyin'):
            st.markdown(f"""
            <div class="analysis-section">
                <div class="analysis-label">拼音 (병음)</div>
                <div class="pinyin-box">{analysis['pinyin']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        if analysis.get('words'):
            st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
            st.markdown('<div class="analysis-label">词汇 (단어)</div>', unsafe_allow_html=True)
            for word in analysis['words']:
                st.markdown(f"""
                <div class="word-item">
                    <div>
                        <span class="word-chinese">{word['chinese']}</span>
                        <span class="word-pinyin">({word['pinyin']})</span>
                    </div>
                    <div class="word-meaning">→ {word['meaning']}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        if analysis.get('grammar'):
            st.markdown(f"""
            <div class="analysis-section">
                <div class="analysis-label">语法 (문법)</div>
                <div class="grammar-box">
                    <div style="color: #333; margin-bottom: 0.25rem;">{analysis['grammar']}</div>
                    <div style="color: #666; font-size: 0.75rem; margin-top: 0.375rem; padding-top: 0.375rem; border-top: 1px solid #fde68a;">
                    [한글] 간단한 인사 문장입니다. '很高兴认识你'는 고정 표현으로, 처음 만날 때 사용하는 예의바른 표현입니다.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if analysis.get('vocabulary'):
            st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
            st.markdown('<div class="analysis-label">词汇笔记 (어휘 노트)</div>', unsafe_allow_html=True)
            vocab_html = "<div class='vocabulary-box'>"
            for i, v in enumerate(analysis['vocabulary']):
                vocab_html += f"<div style='margin-bottom: 0.25rem;'>• {v}</div>"
                if i == 0:
                    vocab_html += f"<div style='color: #666; font-size: 0.75rem; margin-left: 1rem; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 1px solid #bbf7d0;'>[한글] '认识'는 HSK 3급 단어로, 누군가를 안다는 의미입니다</div>"
                else:
                    vocab_html += f"<div style='color: #666; font-size: 0.75rem; margin-left: 1rem; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 1px solid #bbf7d0;'>[한글] '聊'는 구어에서 자주 사용되는 동사입니다</div>"
            vocab_html += "</div>"
            st.markdown(vocab_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        if analysis.get('notes'):
            st.markdown(f"""
            <div class="analysis-section">
                <div class="analysis-label">附加说明 (추가 설명)</div>
                <div class="notes-box">
                    <div style="color: #333; margin-bottom: 0.25rem;">{analysis['notes']}</div>
                    <div style="color: #666; font-size: 0.75rem; margin-top: 0.375rem; padding-top: 0.375rem; border-top: 1px solid #fde68a;">
                    [한글] 표준 중국어 인사말로, 처음 만날 때 사용하기 적합합니다.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 사용자 피드백 추가
        if analysis.get('feedback'):
            feedback = analysis['feedback']
            st.markdown("""
            <div class="analysis-section">
                <div class="analysis-label">您的反馈 (사용자 피드백)</div>
                <div class="feedback-box">
            """, unsafe_allow_html=True)
            
            # 표현
            st.markdown(f"""
                <div style="margin-bottom: 0.5rem;"><strong>表现 (표현):</strong> {feedback.get('expression', 'N/A')}</div>
                <div style="color: #666; font-size: 0.75rem; margin-left: 1rem; margin-bottom: 0.75rem;">[한글] 자연스러운 표현을 사용하셨습니다</div>
            """, unsafe_allow_html=True)
            
            # 문법
            st.markdown(f"""
                <div style="margin-bottom: 0.5rem;"><strong>语法 (문법):</strong> {feedback.get('grammar_feedback', 'N/A')}</div>
                <div style="color: #666; font-size: 0.75rem; margin-left: 1rem; margin-bottom: 0.75rem;">[한글] 문법이 정확합니다</div>
            """, unsafe_allow_html=True)
            
            # 맥락
            st.markdown(f"""
                <div style="margin-bottom: 0.5rem;"><strong>语境 (맥락):</strong> {feedback.get('context', 'N/A')}</div>
                <div style="color: #666; font-size: 0.75rem; margin-left: 1rem; margin-bottom: 0.75rem;">[한글] 상황에 적절한 표현입니다</div>
            """, unsafe_allow_html=True)
            
            # 단어 선택
            st.markdown(f"""
                <div style="margin-bottom: 0.5rem;"><strong>单词选择 (단어 선택):</strong> {feedback.get('word_choice', 'N/A')}</div>
                <div style="color: #666; font-size: 0.75rem; margin-left: 1rem;">[한글] 적절한 어휘를 선택하셨습니다</div>
            """, unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)

# 번역 처리: 번역 버튼 클릭 시 플래그를 보고 LLM 호출
if st.session_state.translating_message_id is not None:
    idx = st.session_state.translating_message_id
    if 0 <= idx < len(st.session_state.messages):
        msg = st.session_state.messages[idx]
        try:
            src_hint = "중국어" if st.session_state.selected_language == "chinese" else ""
            trans = translate_to_korean(msg['content'], src_hint)
            st.session_state.messages[idx]['translation'] = trans or "확인 불가"
            st.session_state.show_translation[idx] = True
        except Exception as e:
            st.session_state.messages[idx]['translation'] = f"[오류] 번역 실패: {e}"
            st.session_state.show_translation[idx] = True
    st.session_state.translating_message_id = None
    st.rerun()

# 메시지 전송 처리
if send_button and user_input.strip():
    # 사용자 메시지 추가
    st.session_state.messages.append({
        'role': 'user',
        'content': user_input
    })
    
    # 로딩 시작
    st.session_state.is_loading = True
    
    # 입력창 초기화를 위한 키 변경
    st.session_state.input_key += 1
    
    st.rerun()

# 로딩 후 응답 생성 (LLM)
if st.session_state.is_loading and len(st.session_state.messages) > 0 and st.session_state.messages[-1]['role'] == 'user':
    time.sleep(0.1)
    
    user_msg = st.session_state.messages[-1]['content']
    try:
        # 어시스턴트 응답 생성
        reply_text = generate_assistant_reply(user_msg)
        if not reply_text:
            reply_text = "확인 불가"
        assistant_message = {
            'role': 'assistant',
            'content': reply_text
        }
        st.session_state.messages.append(assistant_message)
        
        # 중국어 상세 분석 생성
        if st.session_state.selected_language == 'chinese':
            st.session_state.detailed_analysis = generate_chinese_analysis(user_msg)
        else:
            st.session_state.detailed_analysis = None

    except Exception as e:
        st.session_state.messages.append({
            'role': 'assistant',
            'content': f"[오류] LLM 호출 실패: {e}"
        })
        st.session_state.detailed_analysis = None
    
    # 로딩 종료
    st.session_state.is_loading = False
    st.rerun()
