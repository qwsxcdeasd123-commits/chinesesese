import streamlit as st
import json
import time
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="微信语言学习",
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
    
    /* 헤더 - WeChat 그린 */
    .header {
        background: linear-gradient(135deg, #09b83e 0%, #07a33a 100%);
        color: white;
        padding: 1rem;
        border-radius: 0;
        margin: -1rem -1rem 0 -1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    
    .header-title {
        font-size: 1.125rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* 메시지 영역 배경 */
    .messages-container {
        background: #ededed;
        min-height: 450px;
        max-height: 550px;
        overflow-y: auto;
        padding: 1rem;
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
    
    .translation-toggle {
        color: #586c94;
        font-size: 0.75rem;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px solid #e5e5e5;
    }
    
    /* 메시지 시간 표시 */
    .message-time {
        text-align: center;
        color: #999999;
        font-size: 0.75rem;
        margin: 1rem 0 0.5rem 0;
        clear: both;
    }
    
    /* 분석 패널 - WeChat 스타일 */
    .analysis-panel {
        background: #f7f7f7;
        border-top: 1px solid #d9d9d9;
        border-bottom: 1px solid #d9d9d9;
        padding: 0;
        margin: 0 -1rem;
    }
    
    .analysis-header {
        background: #fafafa;
        padding: 0.75rem 1rem;
        font-weight: 500;
        font-size: 0.875rem;
        color: #353535;
        border-bottom: 1px solid #e5e5e5;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
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
    
    /* 입력 영역 - WeChat 스타일 */
    .input-container {
        background: #f7f7f7;
        border-top: 1px solid #d9d9d9;
        padding: 0.625rem 1rem;
        margin: 0 -1rem -1rem -1rem;
    }
    
    .stTextInput > div > div > input {
        border-radius: 0.375rem;
        border: 1px solid #d9d9d9;
        padding: 0.625rem 0.875rem;
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
    
    /* 전송 버튼 - WeChat 그린 */
    .stButton > button[kind="primary"] {
        background: #09b83e;
        color: white;
        border: none;
        border-radius: 0.375rem;
        padding: 0.625rem 1.25rem;
        font-size: 0.9375rem;
        font-weight: 500;
        width: 100%;
        transition: background 0.2s;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #07a33a;
    }
    
    .stButton > button[kind="primary"]:disabled {
        background: #d9d9d9;
        color: #999999;
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
    
    /* 저장 버튼 */
    .stButton > button[kind="secondary"] {
        background: #ffffff;
        color: #09b83e;
        border: 1px solid #09b83e;
        border-radius: 0.375rem;
        padding: 0.625rem;
        width: 100%;
        font-size: 0.9375rem;
        font-weight: 500;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #f0fdf4;
    }
    
    .stButton > button[kind="secondary"]:disabled {
        background: #f5f5f5;
        color: #d9d9d9;
        border-color: #d9d9d9;
        cursor: not-allowed;
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
        padding: 3rem 1rem;
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
    
    /* 메시지 클릭 버튼 숨김 */
    .message-click-btn {
        opacity: 0;
        height: 0;
        padding: 0;
        margin: 0;
        border: none;
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
    
    /* 에러 메시지 */
    .error-message {
        background: #fee;
        color: #c33;
        padding: 0.625rem 0.875rem;
        border-radius: 0.375rem;
        margin: 0.5rem 0;
        font-size: 0.875rem;
        border: 1px solid #fcc;
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

# 언어 정보 (1.1, 1.2)
languages = {
    'spanish': {'name': '스페인어', 'flag': '🇪🇸'},
    'french': {'name': '프랑스어', 'flag': '🇫🇷'},
    'german': {'name': '독일어', 'flag': '🇩🇪'},
    'japanese': {'name': '일본어', 'flag': '🇯🇵'},
    'italian': {'name': '이탈리아어', 'flag': '🇮🇹'},
    'korean': {'name': '한국어', 'flag': '🇰🇷'},
    'chinese': {'name': '中文', 'flag': '🇨🇳'}
}

# 학습 목표 (6.1-6.10)
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

# 목표 초기화 (6.10)
def initialize_goals():
    st.session_state.goals = goals_by_language.get(
        st.session_state.selected_language, 
        ['기초 문법', '일상 어휘']
    )

# 목표가 비어있으면 초기화
if not st.session_state.goals:
    initialize_goals()

# 헤더 (8.1, 1.2)
current_lang = languages[st.session_state.selected_language]
proficiency_kr = {
    'beginner': '初级', 
    'intermediate': '中级', 
    'advanced': '高级'
}[st.session_state.proficiency_level]

st.markdown(f"""
<div class="header">
    <div class="header-title">
        <span>💬</span>
        <span>语言学习</span>
    </div>
    <div style="margin-top: 0.375rem; font-size: 0.8125rem; opacity: 0.95;">
        {current_lang['flag']} {current_lang['name']} · {proficiency_kr}
    </div>
</div>
""", unsafe_allow_html=True)

# 사이드바 설정 (8.2, 8.3)
with st.sidebar:
    st.markdown("### ⚙️ 设置")
    
    # 언어 선택 (1.1, 2.1)
    selected_lang = st.selectbox(
        "语言",
        options=list(languages.keys()),
        format_func=lambda x: f"{languages[x]['flag']} {languages[x]['name']}",
        index=list(languages.keys()).index(st.session_state.selected_language),
        key='lang_select'
    )
    
    # 언어 변경 시 초기화 (9.8)
    if selected_lang != st.session_state.selected_language:
        st.session_state.selected_language = selected_lang
        st.session_state.messages = []
        st.session_state.detailed_analysis = None
        st.session_state.show_translation = {}
        initialize_goals()
        st.rerun()
    
    # 숙련도 선택 (2.1, 2.3)
    st.session_state.proficiency_level = st.selectbox(
        "水平",
        options=['beginner', 'intermediate', 'advanced'],
        format_func=lambda x: {'beginner': '初级', 'intermediate': '中级', 'advanced': '高级'}[x],
        index=['beginner', 'intermediate', 'advanced'].index(st.session_state.proficiency_level)
    )
    
    st.markdown("---")
    
    # 학습 목표 (6.8, 6.9)
    st.markdown("### 🎯 学习目标")
    for goal in st.session_state.goals:
        st.markdown(f'<div class="goal-item">• {goal}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 대화 저장 (7.1-7.8)
    save_disabled = len(st.session_state.messages) == 0
    
    if st.button("💾 保存对话", disabled=save_disabled, use_container_width=True, key='save_btn'):
        # 메타데이터 포함 (7.4)
        text_content = f"语言学习记录\n语言: {current_lang['name']}\n水平: {proficiency_kr}\n日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 역할 표시, 번역문 포함 (7.5, 7.6)
        for msg in st.session_state.messages:
            role = "学习者" if msg['role'] == 'user' else "老师"
            text_content += f"{role}: {msg['content']}\n"
            if 'translation' in msg:
                text_content += f"[翻译]: {msg['translation']}\n"
            text_content += "\n"
        
        # 파일 다운로드 (7.3, 7.7)
        st.download_button(
            label="📥 下载文件",
            data=text_content.encode('utf-8'),
            file_name=f"学习记录_{current_lang['name']}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain;charset=utf-8",
            use_container_width=True
        )

# 메시지 표시 영역 (8.9)
st.markdown('<div class="messages-container">', unsafe_allow_html=True)

# 빈 화면 안내 (3.10, 8.13)
if len(st.session_state.messages) == 0:
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-icon">{current_lang['flag']}</div>
        <div class="empty-title">{current_lang['name']} 学习</div>
        <div class="empty-desc">开始你的语言学习之旅</div>
    </div>
    """, unsafe_allow_html=True)
else:
    # 시간 표시 (첫 메시지)
    if st.session_state.messages:
        st.markdown(f'<div class="message-time">{datetime.now().strftime("%p %I:%M")}</div>', unsafe_allow_html=True)
    
    # 메시지 히스토리 표시 (3.4, 3.5, 3.6, 3.7, 3.8)
    for idx, msg in enumerate(st.session_state.messages):
        if msg['role'] == 'user':
            # 사용자 메시지 (3.4)
            st.markdown(f'<div class="user-message">{msg["content"]}</div><div style="clear:both;"></div>', unsafe_allow_html=True)
        else:
            # 튜터 메시지 (3.5)
            show_trans = st.session_state.show_translation.get(idx, False)
            
            # 번역 표시 로직 (4.1, 4.2, 4.7)
            if 'translation' in msg and show_trans:
                content = f"""
                <div style="color: #000000;">{msg['content']}</div>
                <div class="translation">{msg['translation']}</div>
                <div class="translation-toggle">👆 点击查看原文</div>
                """
            else:
                # 번역 중 표시 (4.3, 4.4)
                is_translating = st.session_state.translating_message_id == idx
                toggle_text = "⏳ 翻译中..." if is_translating else "👆 点击翻译"
                content = f"""
                <div>{msg['content']}</div>
                <div class="translation-toggle">{toggle_text}</div>
                """
            
            # 클릭 이벤트 (4.1)
            col1, col2, col3 = st.columns([0.5, 10, 0.5])
            with col2:
                # 번역 토글 버튼
                if st.button(f"toggle_{idx}", key=f"msg_btn_{idx}", use_container_width=True):
                    if 'translation' in msg:
                        # 번역 토글 (4.1, 4.2)
                        st.session_state.show_translation[idx] = not show_trans
                        st.rerun()
                    elif not is_translating:
                        # 번역 시작 (4.3, 4.6)
                        st.session_state.translating_message_id = idx
                        st.rerun()
                        
                        # 실제로는 API 호출하지만 여기서는 시뮬레이션
                        time.sleep(1)
                        
                        # 번역 결과 저장 (4.7)
                        st.session_state.messages[idx]['translation'] = f"[翻译] {msg['content']}"
                        st.session_state.translating_message_id = None
                        st.session_state.show_translation[idx] = True
                        st.rerun()
                
                st.markdown(f'<div class="assistant-message">{content}</div>', unsafe_allow_html=True)
            
            st.markdown('<div style="clear:both;"></div>', unsafe_allow_html=True)
        
        # 일부 메시지 후 시간 표시
        if (idx + 1) % 4 == 0 and idx < len(st.session_state.messages) - 1:
            st.markdown(f'<div class="message-time">{datetime.now().strftime("%p %I:%M")}</div>', unsafe_allow_html=True)
    
    # 로딩 인디케이터 (8.5)
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

# 중국어 상세 분석 (5.1-5.10, 5.8)
if st.session_state.selected_language == 'chinese' and st.session_state.detailed_analysis:
    st.markdown('<div class="analysis-panel">', unsafe_allow_html=True)
    
    # 분석 패널 토글 (5.6)
    with st.expander("📚 详细分析", expanded=st.session_state.show_analysis):
        analysis = st.session_state.detailed_analysis
        
        st.markdown('<div class="analysis-content">', unsafe_allow_html=True)
        
        # 병음 표시 (5.1)
        if analysis.get('pinyin'):
            st.markdown(f"""
            <div class="analysis-section">
                <div class="analysis-label">拼音</div>
                <div class="pinyin-box">{analysis['pinyin']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 단어 분해 (5.2)
        if analysis.get('words'):
            st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
            st.markdown('<div class="analysis-label">词汇</div>', unsafe_allow_html=True)
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
        
        # 문법 설명 (5.3)
        if analysis.get('grammar'):
            st.markdown(f"""
            <div class="analysis-section">
                <div class="analysis-label">语法</div>
                <div class="grammar-box">{analysis['grammar']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 어휘 노트 (5.4)
        if analysis.get('vocabulary'):
            st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
            st.markdown('<div class="analysis-label">词汇笔记</div>', unsafe_allow_html=True)
            vocab_text = "<br>".join([f"• {v}" for v in analysis['vocabulary']])
            st.markdown(f'<div class="vocabulary-box">{vocab_text}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 추가 설명 (5.5)
        if analysis.get('notes'):
            st.markdown(f"""
            <div class="analysis-section">
                <div class="analysis-label">附加说明</div>
                <div class="notes-box">{analysis['notes']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>',
