import streamlit as st
import anthropic
import json
from datetime import datetime

# 페이지 설정 - 모바일 최적화
st.set_page_config(
    page_title="언어 학습 튜터",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 모바일 최적화 CSS
st.markdown("""
<style>
    /* 모바일 최적화 */
    .stApp {
        max-width: 100%;
    }
    
    /* 메시지 스타일 */
    .user-message {
        background-color: #2563eb;
        color: white;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-left: 20%;
        text-align: left;
    }
    
    .assistant-message {
        background-color: #f3f4f6;
        color: #1f2937;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-right: 20%;
        text-align: left;
        border: 1px solid #e5e7eb;
    }
    
    .translation {
        background-color: #fef3c7;
        padding: 8px 12px;
        border-radius: 12px;
        margin-top: 8px;
        font-size: 0.9em;
        border-left: 3px solid #f59e0b;
    }
    
    /* 분석 패널 */
    .analysis-box {
        background-color: #f0f9ff;
        padding: 12px;
        border-radius: 12px;
        margin: 8px 0;
        border: 1px solid #bae6fd;
    }
    
    .word-item {
        background-color: white;
        padding: 8px;
        border-radius: 8px;
        margin: 4px 0;
        border: 1px solid #e5e7eb;
    }
    
    /* 버튼 스타일 */
    .stButton button {
        width: 100%;
        border-radius: 20px;
        padding: 10px;
    }
    
    /* 입력창 */
    .stTextInput input {
        border-radius: 20px;
        padding: 12px;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'language' not in st.session_state:
    st.session_state.language = 'chinese'
if 'proficiency' not in st.session_state:
    st.session_state.proficiency = 'intermediate'
if 'show_translation' not in st.session_state:
    st.session_state.show_translation = {}
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None

# 언어 설정
LANGUAGES = {
    'chinese': {'name': '중국어', 'flag': '🇨🇳'},
    'spanish': {'name': '스페인어', 'flag': '🇪🇸'},
    'french': {'name': '프랑스어', 'flag': '🇫🇷'},
    'german': {'name': '독일어', 'flag': '🇩🇪'},
    'japanese': {'name': '일본어', 'flag': '🇯🇵'},
    'italian': {'name': '이탈리아어', 'flag': '🇮🇹'},
    'korean': {'name': '한국어', 'flag': '🇰🇷'}
}

PROFICIENCY = {
    'beginner': '초급',
    'intermediate': '중급',
    'advanced': '고급'
}

# 학습 목표
GOALS = {
    'chinese': [
        'HSK 5급 필수 어휘 2,500개 마스터',
        '복잡한 문장 구조 이해하고 작성',
        '성어(成语) 및 관용 표현 학습',
        '읽기 독해력 향상',
        '작문 능력 향상'
    ],
    'spanish': ['불규칙 동사 활용', '음식 어휘 확장'],
    'french': ['명사의 성 구분', '과거시제 활용'],
    'german': ['격변화 이해', '분리동사 학습'],
    'japanese': ['히라가나 읽기', '경어 표현'],
    'italian': ['동사 시제', '전치사 결합']
}

def get_ai_response(messages, language, proficiency, api_key):
    """Claude API 호출"""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        system_prompt = f"""You are a {LANGUAGES[language]['name']} language tutor. 
Respond in {LANGUAGES[language]['name']} at {proficiency} level. 
Keep responses SHORT - maximum 2-3 sentences. 
Be natural and conversational like a real tutor."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system=system_prompt,
            messages=messages
        )
        
        return response.content[0].text
    except Exception as e:
        return f"오류 발생: {str(e)}"

def translate_to_korean(text, language, api_key):
    """한국어로 번역"""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"다음 {LANGUAGES[language]['name']} 텍스트를 한국어로 번역하세요. 번역문만 제공하세요:\n\n{text}"
            }]
        )
        
        return response.content[0].text
    except Exception as e:
        return f"번역 오류: {str(e)}"

def analyze_chinese(text, api_key):
    """중국어 상세 분석"""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""다음 중국어를 HSK 5급 학습자를 위해 분석하세요. 
반드시 순수 JSON 형식으로만 응답하세요:

{{
  "pinyin": "전체 문장의 병음",
  "words": [
    {{"chinese": "단어", "pinyin": "병음", "meaning": "한국어 뜻"}}
  ],
  "grammar": "문법 설명 (한국어)",
  "vocabulary": ["어휘 노트 (한국어)"],
  "notes": "추가 설명 (한국어)"
}}

텍스트: {text}"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis_text = response.content[0].text.strip()
        analysis_text = analysis_text.replace('```json', '').replace('```', '').strip()
        
        return json.loads(analysis_text)
    except Exception as e:
        return {
            "pinyin": "분석 불가",
            "words": [],
            "grammar": f"오류 발생: {str(e)}",
            "vocabulary": [],
            "notes": ""
        }

def save_conversation():
    """대화 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"언어학습_{LANGUAGES[st.session_state.language]['name']}_{timestamp}.txt"
    
    content = f"언어 학습 대화 기록\n"
    content += f"=" * 50 + "\n\n"
    content += f"언어: {LANGUAGES[st.session_state.language]['name']}\n"
    content += f"숙련도: {PROFICIENCY[st.session_state.proficiency]}\n"
    content += f"날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"대화 수: {len(st.session_state.messages)}\n\n"
    content += f"=" * 50 + "\n\n"
    
    for msg in st.session_state.messages:
        role = "학습자" if msg["role"] == "user" else "튜터"
        content += f"{role}: {msg['content']}\n\n"
    
    return content, filename

# 헤더
st.markdown(f"""
<div style='background-color: #2563eb; color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;'>
    <h1 style='margin: 0; font-size: 24px;'>📚 언어 학습 튜터</h1>
    <p style='margin: 5px 0 0 0; font-size: 14px;'>
        {LANGUAGES[st.session_state.language]['flag']} {LANGUAGES[st.session_state.language]['name']} · 
        {PROFICIENCY[st.session_state.proficiency]}
    </p>
</div>
""", unsafe_allow_html=True)

# 사이드바 - 설정
with st.sidebar:
    st.header("⚙️ 설정")
    
    # API 키 입력
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=st.session_state.api_key,
        help="https://console.anthropic.com/settings/keys 에서 발급"
    )
    if api_key:
        st.session_state.api_key = api_key
    
    st.divider()
    
    # 언어 선택
    language = st.selectbox(
        "학습 언어",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: f"{LANGUAGES[x]['flag']} {LANGUAGES[x]['name']}",
        index=list(LANGUAGES.keys()).index(st.session_state.language)
    )
    if language != st.session_state.language:
        st.session_state.language = language
        st.session_state.messages = []
        st.session_state.current_analysis = None
        st.rerun()
    
    # 숙련도 선택
    proficiency = st.selectbox(
        "숙련도",
        options=list(PROFICIENCY.keys()),
        format_func=lambda x: PROFICIENCY[x],
        index=list(PROFICIENCY.keys()).index(st.session_state.proficiency)
    )
    st.session_state.proficiency = proficiency
    
    st.divider()
    
    # 학습 목표
    st.subheader("🎯 학습 목표")
    goals = GOALS.get(st.session_state.language, ['기초 문법', '일상 어휘'])
    for goal in goals:
        st.markdown(f"• {goal}")
    
    st.divider()
    
    # 대화 저장
    if st.button("💾 대화 저장", disabled=len(st.session_state.messages) == 0):
        content, filename = save_conversation()
        st.download_button(
            label="📥 다운로드",
            data=content,
            file_name=filename,
            mime="text/plain"
        )
    
    # 대화 초기화
    if st.button("🗑️ 대화 초기화", disabled=len(st.session_state.messages) == 0):
        st.session_state.messages = []
        st.session_state.current_analysis = None
        st.rerun()

# 메인 영역
if not st.session_state.api_key:
    st.warning("⚠️ 왼쪽 사이드바에서 Anthropic API Key를 입력해주세요.")
    st.info("""
    API Key 발급 방법:
    1. https://console.anthropic.com/settings/keys 접속
    2. 'Create Key' 클릭
    3. 생성된 키를 복사하여 입력
    """)
else:
    # 대화 표시
    chat_container = st.container()
    with chat_container:
        if len(st.session_state.messages) == 0:
            st.markdown(f"""
            <div style='text-align: center; padding: 40px;'>
                <div style='font-size: 64px;'>{LANGUAGES[st.session_state.language]['flag']}</div>
                <h2>{LANGUAGES[st.session_state.language]['name']} 학습을 시작하세요!</h2>
                <p style='color: #6b7280;'>아래 입력창에 메시지를 입력하세요</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for idx, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)
                else:
                    # 메시지 표시
                    msg_key = f"msg_{idx}"
                    
                    # 번역 표시 여부 확인
                    if msg_key in st.session_state.show_translation and st.session_state.show_translation[msg_key]:
                        if 'translation' in message:
                            st.markdown(f"<div class='assistant-message'><div class='translation'>{message['translation']}</div></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='assistant-message'>{message['content']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='assistant-message'>{message['content']}</div>", unsafe_allow_html=True)
                    
                    # 번역 버튼
                    if st.button(f"🔄 번역", key=f"translate_{idx}"):
                        if 'translation' not in message:
                            message['translation'] = translate_to_korean(
                                message['content'],
                                st.session_state.language,
                                st.session_state.api_key
                            )
                        st.session_state.show_translation[msg_key] = not st.session_state.show_translation.get(msg_key, False)
                        st.rerun()
    
    # 중국어 분석 표시
    if st.session_state.language == 'chinese' and st.session_state.current_analysis:
        with st.expander("📚 상세 분석", expanded=True):
            analysis = st.session_state.current_analysis
            
            # 병음
            if analysis.get('pinyin'):
                st.markdown(f"**병음 (拼音)**")
                st.markdown(f"<div class='analysis-box'>{analysis['pinyin']}</div>", unsafe_allow_html=True)
            
            # 단어 분석
            if analysis.get('words'):
                st.markdown(f"**단어 분석**")
                for word in analysis['words']:
                    st.markdown(f"""
                    <div class='word-item'>
                        <strong style='font-size: 1.2em;'>{word['chinese']}</strong> 
                        <span style='color: #7c3aed;'>({word['pinyin']})</span><br>
                        → {word['meaning']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # 문법
            if analysis.get('grammar'):
                st.markdown(f"**문법 구조**")
                st.markdown(f"<div class='analysis-box'>{analysis['grammar']}</div>", unsafe_allow_html=True)
            
            # 어휘 노트
            if analysis.get('vocabulary'):
                st.markdown(f"**어휘 노트**")
                for note in analysis['vocabulary']:
                    st.markdown(f"• {note}")
    
    # 입력 영역
    st.divider()
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "메시지 입력",
            key="user_input",
            placeholder=f"{LANGUAGES[st.session_state.language]['name']}로 입력하세요...",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("📤", use_container_width=True)
    
    # 메시지 전송
    if (send_button or user_input) and user_input:
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # AI 응답 생성
        messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        ai_response = get_ai_response(
            messages_for_api,
            st.session_state.language,
            st.session_state.proficiency,
            st.session_state.api_key
        )
        
        # AI 응답 추가
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        
        # 중국어 분석
        if st.session_state.language == 'chinese':
            st.session_state.current_analysis = analyze_chinese(ai_response, st.session_state.api_key)
        
        st.rerun()
