import streamlit as st
import json
import time
from datetime import datetime
import os
import textwrap

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

# ==================== 스타일 ====================
st.markdown("""
<style>
    .stApp { max-width: 100%; background-color: #ededed; }
    .block-container { padding-top: 0rem !important; padding-bottom: 0 !important; max-width: 100% !important; }

    /* 헤더 */
    .header {
        background: linear-gradient(135deg, #09b83e 0%, #07a33a 100%);
        color: white; min-height: 9rem; padding: 0 1rem; padding-bottom: 1rem;
        display: flex; flex-direction: column; justify-content: flex-end;
        border-radius: 0; margin: -1rem -1rem 0.25rem -1rem !important; box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    .header-title { font-size: 1.125rem; font-weight: 500; display: flex; align-items: center; gap: 0.1rem; }

    /* 메시지 영역 */
    .messages-container {
        background: #ededed; min-height: 200px; max-height: 550px; overflow-y: auto;
        padding: 0.25rem 1rem 1rem 1rem !important; margin: 0 -1rem;
    }
    /* 사용자 말풍선 */
    .user-message {
        background: #95ec69; color: #000; padding: 0.625rem 0.875rem; border-radius: 0.375rem;
        margin: 0.5rem 0; margin-left: auto; max-width: 70%; text-align: left; float: right; clear: both;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1); word-wrap: break-word; font-size: 0.9375rem; line-height: 1.4; white-space: pre-wrap;
    }
    /* 튜터 말풍선 — 여백/패딩 더 축소 */
    .assistant-message {
        background: #fff; color: #000; padding: 0.2rem 0.2rem !important; border-radius: 0.375rem;
        margin: 0.1rem 0 !important; margin-right: auto; max-width: 70%; float: left; clear: both;
        box-shadow: none !important; cursor: pointer; word-wrap: break-word; font-size: 0.875rem !important;
        line-height: 1.25 !important; white-space: pre-wrap;
    }
    .assistant-message + .assistant-message{ margin-top: 0.05rem !important; }
    .assistant-message:active { background: #f5f5f5; }

    /* 번역 관련 */
    .translation { color: #586c94; font-size: 0.8125rem; margin-top: 0.25rem !important; padding-top: 0.25rem !important; border-top: 1px solid #e5e5e5 !important; line-height: 1.3; }
    .assistant-message .translation-toggle{ color: #586c94; font-size: 0.75rem; margin-top: 0.125rem !important; padding-top: 0.125rem !important; border-top: none !important; }
    .stButton > button:not([kind="primary"]) {
        position: absolute !important; width: 1px !important; height: 1px !important; padding: 0 !important; margin: -1px !important;
        overflow: hidden !important; clip: rect(0, 0, 0, 0) !important; white-space: nowrap !important; border: 0 !important;
    }

    /* 로딩(튜터 입력 중) 표시 */
    .loading-message {
        background: #ffffff;
        padding: 0.5rem 0.75rem;
        border-radius: 0.375rem;
        margin: 0.25rem 0;
        margin-right: auto;
        max-width: 30%;
        float: left;
        clear: both;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .loading-dots { display: inline-flex; gap: 0.25rem; padding: 0.2rem; }
    .loading-dot { width: 6px; height: 6px; background: #c8c8c8; border-radius: 50%; animation: wechat-bounce 1.4s infinite ease-in-out both; }
    .loading-dot:nth-child(1) { animation-delay: -0.32s; }
    .loading-dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes wechat-bounce { 0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; } 40% { transform: scale(1); opacity: 1; } }

    /* 분석 패널 */
    .analysis-panel { background: #f7f7f7; border-top: 1px solid #d9d9d9; border-bottom: 1px solid #d9d9d9; padding: 0; margin: 0.5rem -1rem 0 -1rem; }
    .analysis-content { padding: 1rem; background: #fff; }
    .analysis-section { margin-bottom: 1rem; }
    .analysis-label { font-size: 0.75rem; color: #999; margin-bottom: 0.375rem; font-weight: 500; }
    .pinyin-box { background: #f0f9ff; padding: 0.625rem; border-radius: 0.25rem; color: #1e40af; font-size: 0.75rem; border: 1px solid #bfdbfe; line-height: 1.5; }
    .word-item { background: #fafafa; border: 1px solid #e5e5e5; border-radius: 0.25rem; padding: 0.5rem; margin: 0.375rem 0; font-size: 0.75rem; }
    .word-chinese { font-weight: 600; font-size: 0.75rem; color: #000; }
    .word-pinyin { color: #09b83e; margin-left: 0.375rem; }
    .word-meaning { color: #666; margin-top: 0.25rem; font-size: 0.75rem; }

    .grammar-box { background: #fef9e7; padding: 0.625rem; border-radius: 0.25rem; font-size: 0.75rem; color: #333; border: 1px solid #fde68a; line-height: 1.5; }
    .vocabulary-box { background: #f0fdf4; padding: 0.625rem; border-radius: 0.25rem; font-size: 0.75rem; color: #333; border: 1px solid #bbf7d0; line-height: 1.5; }
    .notes-box { background: #fff7e6; padding: 0.625rem; border-radius: 0.25rem; font-size: 0.75rem; color: #333; border: 1px dashed #f5c97a; line-height: 1.5; }

    /* 피드백 박스(보라) */
    .feedback-box {
        background: #f3e8ff;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        color: #333333;
        border: 1px solid #d8b4fe;
        line-height: 1.45;
    }
    .feedback-list { margin: 0.25rem 0 0 0.75rem; padding: 0; }
    .feedback-list li { margin: 0.1rem 0; }

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

    /* ===== 상세분석 폰트 통일: 병음과 동일(0.875rem) ===== */
    .pinyin-box,
    .grammar-box,
    .vocabulary-box,
    .notes-box,
    .feedback-box,
    .analysis-section,
    .analysis-section * { 
        font-size: 0.75rem !important;
        line-height: 1.5;
    }
    .gram-badge{
        display:inline-block; padding:0.125rem 0.375rem; border-radius:0.25rem;
        background:#e6f4ea; border:1px solid #b7e0c2; color:#1b5e20; font-weight:600; 
        margin-left:0.375rem; font-size:0.75rem !important;
    }

    /* 입력 영역 */
    .input-container { background: #f7f7f7; border-top: 1px solid #d9d9d9; padding: 0.625rem 1rem; margin: 0.5rem -1rem 0 -1rem; }
    .input-row { display: flex; gap: 0.5rem; align-items: center; }
    [data-testid="column"] { padding: 0 !important; }
    .stTextInput { flex: 1; margin-bottom: 0 !important; }
    .stTextInput > div, .stTextInput > div > div { margin-bottom: 0 !important; }
    .stTextInput > div > div > input {
        border-radius: 1.5rem; border: 1px solid #d9d9d9; padding: 0.625rem 1rem; background: #fff; font-size: 0.9375rem;
    }
    .stTextInput > div > div > input:focus { border-color: #09b83e; box-shadow: 0 0 0 2px rgba(9,184,62,0.1); }
    .stTextInput > div > div > input:disabled { background: #f5f5f5; color: #999; cursor: not-allowed; }

    .stButton { margin-bottom: 0 !important; }
    .stButton > button[kind="primary"] {
        background: #09b83e; color: #fff; border: none; border-radius: 50%;
        padding: 0.625rem; width: 2.5rem; height: 2.5rem; font-size: 1.125rem; transition: background 0.2s;
        display: flex; align-items: center; justify-content: center; min-width: 2.5rem; margin: 0;
    }
    .stButton > button[kind="primary"]:hover { background: #07a33a; }
    .stButton > button[kind="primary"]:disabled { background: #d9d9d9; color: #999; }

    [data-testid="stSidebar"] { background: #fafafa; }
    [data-testid="stSidebar"] .stSelectbox > div > div { background: #fff; border: 1px solid #e5e5e5; border-radius: 0.375rem; }
    [data-testid="stSidebar"] h3 { color: #353535; font-size: 1rem; font-weight: 600; padding: 0.5rem 0; }

    .empty-state { text-align: center; padding: 1rem 1rem !important; }
    .empty-icon { font-size: 4rem; margin-bottom: 1rem; }
    .empty-title { color: #353535; font-size: 1.125rem; font-weight: 500; margin-bottom: 0.5rem; }
    .empty-desc { color: #999; font-size: 0.875rem; }

    .messages-container::-webkit-scrollbar { width: 4px; }
    .messages-container::-webkit-scrollbar-track { background: #ededed; }
    .messages-container::-webkit-scrollbar-thumb { background: #c8c8c8; border-radius: 2px; }
    .messages-container::-webkit-scrollbar-thumb:hover { background: #999; }

    .streamlit-expanderHeader { background: #fafafa; border: none; border-radius: 0; font-size: 0.875rem; color: #353535; font-weight: 500; padding: 0.75rem 1rem; }
    .streamlit-expanderHeader:hover { background: #f5f5f5; }
    .streamlit-expanderContent { background: #fff; border: none; padding: 0; }

    .stDownloadButton > button { background: #09b83e; color: white; border: none; border-radius: 0.375rem; padding: 0.625rem; width: 100%; font-size: 0.9375rem; font-weight: 500; margin-top: 0.5rem; }
    .stDownloadButton > button:hover { background: #07a33a; }

    hr { border: none; border-top: 1px solid #e5e5e5; margin: 1rem 0; }
    .stTextInput > label { display: none; }
</style>
""", unsafe_allow_html=True)

# ==================== 세션 상태 ====================
if 'messages' not in st.session_state: st.session_state.messages = []
if 'selected_language' not in st.session_state: st.session_state.selected_language = 'chinese'
if 'proficiency_level' not in st.session_state: st.session_state.proficiency_level = 'intermediate'
if 'detailed_analysis' not in st.session_state: st.session_state.detailed_analysis = None
if 'show_translation' not in st.session_state: st.session_state.show_translation = {}
if 'show_analysis' not in st.session_state: st.session_state.show_analysis = True
if 'is_loading' not in st.session_state: st.session_state.is_loading = False
if 'translating_message_id' not in st.session_state: st.session_state.translating_message_id = None
if 'goals' not in st.session_state: st.session_state.goals = []
if 'input_key' not in st.session_state: st.session_state.input_key = 0
if 'user_name' not in st.session_state: st.session_state.user_name = None  # 대화명 저장

# ==================== 언어 및 목표 ====================
languages = {
    'spanish': {'name': '스페인어', 'flag': '🇪🇸'},
    'french': {'name': '프랑스어', 'flag': '🇫🇷'},
    'german': {'name': '독일어', 'flag': '🇩🇪'},
    'japanese': {'name': '일본어', 'flag': '🇯🇵'},
    'italian': {'name': '이탈리아어', 'flag': '🇮🇹'},
    'korean': {'name': '한국어', 'flag': '🇰🇷'},
    'chinese': {'name': '中文', 'flag': '🇨🇳'}
}
goals_by_language = {
    'chinese': ['HSK 5급 필수 어휘 마스터', '복잡한 문장 구조 이해', '성어 및 관용 표현 학습'],
    'spanish': ['불규칙 동사 활용', '음식 어휘 확장'],
    'french': ['명사의 성 구분', '과거시제 활용'],
    'german': ['격변화 이해', '분리동사 학습'],
    'japanese': ['히라가나 읽기', '경어 표현'],
    'italian': ['동사 시제', '전치사 결합']
}
def initialize_goals():
    if not st.session_state.goals:
        st.session_state.goals = goals_by_language.get(
            st.session_state.selected_language, ['기초 문법', '일상 어휘']
        )
initialize_goals()

# ==================== 헤더 ====================
current_lang = languages[st.session_state.selected_language]
proficiency_kr = {'beginner': '초급','intermediate': '중급','advanced': '고급'}[st.session_state.proficiency_level]
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

# ==================== 사이드바 ====================
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    selected_lang = st.selectbox(
        "언어",
        options=list(languages.keys()),
        format_func=lambda x: f"{languages[x]['flag']} {languages[x]['name']}",
        index=list(languages.keys()).index(st.session_state.selected_language),
        key='lang_select'
    )
    if selected_lang != st.session_state.selected_language:
        st.session_state.selected_language = selected_lang
        st.session_state.messages = []
        st.session_state.detailed_analysis = None
        st.session_state.show_translation = {}
        st.session_state.goals = []
        initialize_goals()
        st.rerun()

    st.session_state.proficiency_level = st.selectbox(
        "숙련도",
        options=['beginner', 'intermediate', 'advanced'],
        format_func=lambda x: {'beginner': '초급', 'intermediate': '중급', 'advanced': '고급'}[x],
        index=['beginner', 'intermediate', 'advanced'].index(st.session_state.proficiency_level)
    )

    st.markdown("---")
    st.markdown("### 🎯 학습 목표")
    for idx, goal in enumerate(st.session_state.goals):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.write(f"• {goal}")  # 이 줄을 st.markdown에서 st.write로 변경
        with col2:
            if st.button("×", key=f"del_goal_{idx}"):
                st.session_state.goals.pop(idx)
                st.rerun()

    new_goal_input = st.text_input("새 목표 추가", key="goal_input", placeholder="목표를 입력하세요...")
    if st.button("➕ 추가", use_container_width=True):
        if new_goal_input.strip():
            st.session_state.goals.append(new_goal_input.strip())
            st.rerun()

    st.markdown("---")
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

# ==================== 메시지 표시 ====================
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
                <div class="translation-toggle">원문 보기</div>
                """
            else:
                is_translating = st.session_state.translating_message_id == idx
                toggle_text = "번역 중..." if is_translating else "번역하기"
                content = f"""
                <div>{msg['content']}</div>
                <div class="translation-toggle">{toggle_text}</div>
                """
            col1, col2, col3 = st.columns([1, 20, 1])
            with col2:
                st.markdown(f'<div class="assistant-message">{content}</div>', unsafe_allow_html=True)
                if st.button("　", key=f"msg_btn_{idx}", help="클릭하여 번역"):
                    if 'translation' in msg:
                        st.session_state.show_translation[idx] = not show_trans
                    elif not is_translating:
                        st.session_state.translating_message_id = idx
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

# ==================== 입력 영역 ====================
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

# ==================== LLM 유틸 ====================
def _build_tutor_system_prompt(target_lang: str):
    return (
        "역할: 외국어 회화 튜터.\n"
        "규칙:\n"
        "- 감정 표현 금지.\n"
        "- 사실 기반으로만 답변하고 불확실한 내용은 '확인 불가' 명시.\n"
        "- 추측 금지, 간결·정확한 문장 사용.\n"
        "- 출력 언어: 사용자가 선택한 학습 언어로 답변.\n"
        "- 첫 응답에서 학습 목표를 1회만 간략히 언급하고, 사용자 이름을 친근히 확인.\n"
        "- 이후부터는 목표 재언급 금지, 저장된 사용자 이름이 있으면 존칭으로 호명.\n"
        "- 친절한 친구와 같은 말투로 대화할 것.\n"
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

    user_name = st.session_state.user_name or ""
    name_clause = f"저장된 사용자 이름: {user_name}" if user_name else "사용자 이름 미저장"

    if is_first_turn:
        user_instruction = (
            f"사용자 학습 목표: {goals_text}\n"
            f"{name_clause}\n"
            f"사용자 입력: {user_msg}\n"
            "첫 응답이므로 학습 목표를 1회만 간략히 언급하고, 정중히 이름을 확인하는 문장을 포함하라."
            "이후에는 목표를 반복하지 말고, 이름이 저장되면 존칭으로 호명하여 대화하라."
        )
    else:
        user_instruction = (
            f"{name_clause}\n"
            f"사용자 입력: {user_msg}\n"
            "목표는 재언급 금지. 저장된 이름이 있으면 존칭으로 호명하여 간결히 답변."
        )

    messages = hist + [{"role": "user", "content": user_instruction}]
    return _claude(messages=messages, system=system_prompt, max_tokens=600, temperature=0)

def extract_user_name_from_message(latest_user_msg: str) -> str:
    system_prompt = (
        "역할: 정보 추출기.\n"
        "규칙: 입력 문장에서 스스로 밝힌 이름만 한국어 표기 그대로 추출. "
        "이름이 없으면 빈 문자열. 설명 금지. JSON만."
    )
    user_prompt = (
        "다음 문장에서 사용자 스스로 밝힌 이름(호칭 제외, 예: 미주)을 추출하라.\n"
        f"문장: {latest_user_msg}\n"
        "형식: {\"name\": \"...\"} 또는 {\"name\": \"\"}"
    )
    raw = _claude(messages=[{"role":"user","content":user_prompt}], system=system_prompt, max_tokens=100, temperature=0)
    try:
        data = json.loads(raw)
        name = (data.get("name") or "").strip()
        if len(name) > 10 or " " in name:
            return ""
        return name
    except Exception:
        return ""

# ---------- 방어적 노멀라이저 ----------
def _normalize_grammar_list(raw):
    out = []
    if not isinstance(raw, list):
        return out
    for i, g in enumerate(raw, 1):
        if isinstance(g, dict):
            out.append({
                "title": g.get("title") or f"문법 포인트 {i}",
                "pattern": g.get("pattern") or "확인 불가",
                "explanation_ko": g.get("explanation_ko") or "확인 불가",
                "examples": g.get("examples") or [],
                "pitfalls": g.get("pitfalls") or []
            })
        elif isinstance(g, str):
            out.append({
                "title": f"문법 포인트 {i}",
                "pattern": "확인 불가",
                "explanation_ko": g,
                "examples": [],
                "pitfalls": []
            })
    return out

def _normalize_vocab_list(raw):
    out = []
    if not isinstance(raw, list):
        return out
    for v in raw:
        if isinstance(v, dict):
            out.append({
                "word": v.get("word") or "",
                "pinyin": v.get("pinyin") or "",
                "pos": v.get("pos") or "확인 불가",
                "hsk_level": v.get("hsk_level") or "확인 불가",
                "meaning_ko": v.get("meaning_ko") or "확인 불가",
                "synonyms": v.get("synonyms") or [],
                "collocations": v.get("collocations") or [],
                "example": v.get("example") or {}
            })
        elif isinstance(v, str):
            out.append({
                "word": v, "pinyin": "", "pos": "확인 불가", "hsk_level": "확인 불가",
                "meaning_ko": "확인 불가", "synonyms": [], "collocations": [], "example": {}
            })
    return out

# -------- 상세분석(튜터 발화 기준) & 사용자 피드백(학습자 발화 기준) ----------
def analyze_assistant_output(assistant_text: str):
    system_prompt = (
        "역할: 중국어 학습 분석기.\n"
        "출력: 반드시 JSON만 출력.\n"
        "필수 키:\n"
        "- pinyin\n"
        "- grammar: [{title, pattern, explanation_ko, examples:[{cn, pinyin, ko}], pitfalls:[str]}]\n"
        "- vocabulary: [{word, pinyin, pos, hsk_level, meaning_ko, synonyms:[str], collocations:[str], example:{cn, pinyin, ko}}]\n"
        "- notes: 한국어 3~5문장 요약/학습팁\n"
        "불확실하면 '확인 불가' 명시."
    )
    user_prompt = (
        "다음 텍스트를 분석하라. 대상은 튜터의 중국어 발화다.\n"
        f"[튜터 발화]\n{assistant_text}\n"
        "형식은 JSON만 반환."
    )
    raw = _claude(messages=[{"role":"user","content":user_prompt}], system=system_prompt, max_tokens=1100, temperature=0)
    try:
        data = json.loads(raw)
        return {
            "pinyin": data.get("pinyin",""),
            "grammar": _normalize_grammar_list(data.get("grammar", [])),
            "vocabulary": _normalize_vocab_list(data.get("vocabulary", [])),
            "notes": data.get("notes","")
        }
    except Exception:
        return {"pinyin":"확인 불가","grammar":[],"vocabulary":[],"notes":"확인 불가"}

def generate_user_feedback(user_msg: str):
    system_prompt = (
        "역할: 중국어 학습 피드백 생성기.\n"
        "출력: 반드시 JSON만 출력.\n"
        "키: feedback({expression, grammar_feedback, context, word_choice, "
        "alternatives:[str], synonyms:[str], corrections:[{before, after, reason_ko}]})."
    )
    user_prompt = (
        "다음 학습자 발화에 대해 상세 피드백을 생성하라.\n"
        f"[학습자 발화]\n{user_msg}\n"
        "형식은 JSON만."
    )
    raw = _claude(messages=[{"role":"user","content":user_prompt}], system=system_prompt, max_tokens=700, temperature=0)
    try:
        data = json.loads(raw)
        return data.get("feedback", {})
    except Exception:
        return {
            "expression":"확인 불가",
            "grammar_feedback":"확인 불가",
            "context":"확인 불가",
            "word_choice":"확인 불가",
            "alternatives":[],
            "synonyms":[],
            "corrections":[]
        }

def translate_to_korean(text: str, source_hint: str = ""):
    system_prompt = "역할: 전문 번역가. 간결하고 정확한 번역 제공. 설명 금지. 한국어만 출력."
    user_prompt = f"다음을 한국어로 정확히 번역하라.\n원문: {text}"
    if source_hint:
        user_prompt += f"\n언어 힌트: {source_hint}"
    return _claude(messages=[{"role":"user","content":user_prompt}], system=system_prompt, max_tokens=400, temperature=0)

# ==================== 상세 분석 렌더링 ====================
if st.session_state.selected_language == 'chinese' and st.session_state.detailed_analysis:
    with st.expander("📚 상세 분석", expanded=st.session_state.show_analysis):
        analysis = st.session_state.detailed_analysis

        # 병음
        pinyin = analysis.get("pinyin")
        if pinyin:
            st.markdown(f"""
            <div class="analysis-section">
                <div class="analysis-label">拼音 (병음)</div>
                <div class="pinyin-box">{pinyin}</div>
            </div>
            """, unsafe_allow_html=True)

        # 문법(단일 HTML로 묶고, 들여쓰기 제거하여 코드블록 방지)
            grammar_list = _normalize_grammar_list(analysis.get("grammar", []))
            if grammar_list:
                grammar_html = textwrap.dedent("""
                <div class="analysis-section">
                  <div class="analysis-label">语法 (문법)</div>
                  <div class="grammar-box">
                """)
                for g in grammar_list:
                    title   = g.get("title","문법 포인트")
                    pattern = g.get("pattern","확인 불가")
                    exp     = g.get("explanation_ko","확인 불가")

        # 항목 헤더 + 설명
                    grammar_html += textwrap.dedent(f"""
                    <div style="margin-bottom:0.5rem;">
                      <strong>{title}</strong> — <code>{pattern}</code>
                      <div style="margin-top:0.25rem;">{exp}</div>
                    """)

        # 예문
                    exs = g.get("examples",[])
                    if exs:
                        grammar_html += textwrap.dedent("""
                        <div style='margin:0.25rem 0 0.25rem 0.75rem;'>예문:</div>
                        """)
                        for e in exs:
                            grammar_html += (
                                f"<div style='margin-left:1rem;'>• {e.get('cn','')} "
                                f"<span style='color:#888'>({e.get('pinyin','')})</span> — {e.get('ko','')}</div>"
                            )

        # 주의
                    pits = g.get("pitfalls",[])
                    if pits:
                        grammar_html += textwrap.dedent("""
                        <div style='margin:0.25rem 0 0.25rem 0.75rem;'>주의:</div>
                        """)
                        for p in pits:
                            grammar_html += f"<div style='margin-left:1rem;'>- {p}</div>"
        
        # 구분선 + 항목 닫기
                    grammar_html += "<hr style='border-top:1px dashed #fde68a; margin:0.5rem 0;'/>"
                    grammar_html += "</div>"

        # 박스/섹션 닫기
                grammar_html += "</div></div>"

                st.markdown(grammar_html, unsafe_allow_html=True)


        # 어휘 노트
        vocab_list = _normalize_vocab_list(analysis.get("vocabulary", []))
        if vocab_list:
            vocab_html = """
            <div class="analysis-section">
              <div class="analysis-label">词汇笔记 (어휘 노트)</div>
              <div class="vocabulary-box">
            """
            for v in vocab_list:
                vocab_html += (
                    f"<div style='margin-bottom:0.5rem;'>"
                    f"<strong>{v.get('word','')}</strong> ({v.get('pinyin','')}) — {v.get('pos','')} / HSK {v.get('hsk_level','확인 불가')}<br>"
                    f"{v.get('meaning_ko','')}<br>"
                )
                syns = v.get("synonyms",[])
                if syns:
                    vocab_html += f"<div style='margin-top:0.25rem;'>유의어: {', '.join(syns)}</div>"
                cols = v.get("collocations",[])
                if cols:
                    vocab_html += f"<div>결합: {', '.join(cols)}</div>"
                ex = v.get("example",{})
                if ex:
                    vocab_html += f"<div>예문: {ex.get('cn','')} <span style='color:#888'>({ex.get('pinyin','')})</span> — {ex.get('ko','')}</div>"
                vocab_html += "</div>"
            vocab_html += "</div></div>"
            st.markdown(vocab_html, unsafe_allow_html=True)

        # 추가 설명
        notes = analysis.get("notes")
        if notes:
            st.markdown(f"""
            <div class="analysis-section">
                <div class="analysis-label">附加说明 (추가 설명 · HSK 대비)</div>
                <div class="notes-box">{notes}</div>
            </div>
            """, unsafe_allow_html=True)

        # 사용자 피드백(단일 HTML로 묶기)
        if analysis.get('feedback'):
            fdb = analysis['feedback']
            fb_html = """
            <div class="analysis-section">
              <div class="analysis-label">您的反馈 (사용자 피드백)</div>
              <div class="feedback-box">
            """
            fb_html += f"<div><strong>표현:</strong> {fdb.get('expression','확인 불가')}</div>"
            fb_html += f"<div><strong>문법:</strong> {fdb.get('grammar_feedback','확인 불가')}</div>"
            fb_html += f"<div><strong>맥락:</strong> {fdb.get('context','확인 불가')}</div>"
            fb_html += f"<div><strong>단어 선택:</strong> {fdb.get('word_choice','확인 불가')}</div>"

            alts = fdb.get("alternatives", [])
            if alts:
                fb_html += "<div style='margin-top:0.25rem;'><strong>대안 표현:</strong></div><ul class='feedback-list'>"
                fb_html += "".join([f"<li>{a}</li>" for a in alts]) + "</ul>"

            syns = fdb.get("synonyms", [])
            if syns:
                fb_html += "<div style='margin-top:0.25rem;'><strong>유사 어휘:</strong></div><ul class='feedback-list'>"
                fb_html += "".join([f"<li>{s}</li>" for s in syns]) + "</ul>"

            cors = fdb.get("corrections", [])
            if cors:
                fb_html += "<div style='margin-top:0.25rem;'><strong>교정 제안:</strong></div><ul class='feedback-list'>"
                for c in cors:
                    fb_html += (
                        f"<li><code>{c.get('before','')}</code> → "
                        f"<code>{c.get('after','')}</code> — {c.get('reason_ko','')}</li>"
                    )
                fb_html += "</ul>"

            fb_html += "</div></div>"
            st.markdown(fb_html, unsafe_allow_html=True)

# ==================== 번역 처리 ====================
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

# ==================== 전송 처리 ====================
if send_button and user_input.strip():
    st.session_state.messages.append({'role': 'user', 'content': user_input})
    if st.session_state.user_name is None:
        try:
            cand = extract_user_name_from_message(user_input)
            if cand:
                st.session_state.user_name = cand
        except Exception:
            pass
    st.session_state.is_loading = True
    st.session_state.input_key += 1
    st.rerun()

# ==================== LLM 응답 생성 ====================
if st.session_state.is_loading and len(st.session_state.messages) > 0 and st.session_state.messages[-1]['role'] == 'user':
    time.sleep(0.1)
    user_msg = st.session_state.messages[-1]['content']
    try:
        reply_text = generate_assistant_reply(user_msg) or "확인 불가"
        st.session_state.messages.append({'role': 'assistant', 'content': reply_text})

        if st.session_state.selected_language == 'chinese':
            analysis_core = analyze_assistant_output(reply_text)
            analysis_core['feedback'] = generate_user_feedback(user_msg)
            st.session_state.detailed_analysis = analysis_core
        else:
            st.session_state.detailed_analysis = None

    except Exception as e:
        st.session_state.messages.append({'role': 'assistant','content': f"[오류] LLM 호출 실패: {e}"})
        st.session_state.detailed_analysis = None

    st.session_state.is_loading = False
    st.rerun()
