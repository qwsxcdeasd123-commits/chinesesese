import streamlit as st
import anthropic
import json
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="语言学习",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# WeChat 스타일 CSS
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background-color: #ededed;
    }
    
    /* 헤더 및 푸터 숨기기 */
    header, footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* 메인 컨테이너 */
    .main .block-container {
        padding: 0;
        max-width: 100%;
    }
    
    /* WeChat 헤더 */
    .wechat-header {
        background: linear-gradient(135deg, #09b83e 0%, #0aa146 100%);
        color: white;
        padding: 15px 20px;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 채팅 영역 */
    .chat-container {
        padding: 60px 15px 80px 15px;
        min-height: calc(100vh - 140px);
    }
    
    /* 메시지 컨테이너 */
    .msg-wrapper {
        display: flex;
        margin: 12px 0;
        align-items: flex-start;
    }
    
    .msg-wrapper.user {
        justify-content: flex-end;
    }
    
    .msg-wrapper.assistant {
        justify-content: flex-start;
    }
    
    /* 아바타 */
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 6px;
        background-color: #d0d0d0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        flex-shrink: 0;
    }
    
    .avatar.user {
        background-color: #5B9BD5;
        margin-left: 8px;
    }
    
    /* 사용자 메시지 */
    .user-message {
        background-color: #95ec69;
        color: #000;
        padding: 10px 14px;
        border-radius: 10px 10px 2px 10px;
        max-width: 75%;
        word-wrap: break-word;
        font-size: 16px;
        line-height: 1.5;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* 튜터 메시지 */
    .assistant-message {
        background-color: #ffffff;
        color: #000;
        padding: 10px 14px;
        border-radius: 10px 10px 10px 2px;
        max-width: 75%;
        word-wrap: break-word;
        font-size: 16px;
        line-height: 1.5;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        margin-right: 8px;
    }
    
    /* 번역 텍스트 */
    .translation {
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid #e0e0e0;
        font-size: 14px;
        color: #666;
    }
    
    /* 하단 탭 네비게이션 */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        border-top: 1px solid #d0d0d0;
        display: flex;
        justify-content: space-around;
        padding: 8px 0;
        z-index: 1000;
    }
    
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 4px 16px;
        cursor: pointer;
        color: #8e8e93;
        text-decoration: none;
    }
    
    .nav-item.active {
        color: #09b83e;
    }
    
    .nav-item span {
        font-size: 11px;
        margin-top: 2px;
    }
    
    /* 분석 카드 */
    .analysis-card {
        background: white;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* 통계 카드 */
    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        margin: 12px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 입력 영역 */
    .input-container {
        position: fixed;
        bottom: 60px;
        left: 0;
        right: 0;
        background: #f7f7f7;
        padding: 10px;
        border-top: 1px solid #d0d0d0;
        z-index: 999;
    }
    
    /* 버튼 스타일 */
    .stButton button {
        background-color: #09b83e;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 500;
    }
    
    .stButton button:hover {
        background-color: #0aa146;
    }
    
    /* 입력창 */
    .stTextInput input {
        border-radius: 6px;
        border: 1px solid #d0d0d0;
        padding: 10px 15px;
    }
    
    /* 셀렉트 박스 */
    .stSelectbox select {
        border-radius: 6px;
        border: 1px solid #d0d0d0;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'api_key' not in st.session_state:
    try:
        st.session_state.api_key = st.secrets["ANTHROPIC_API_KEY"]
    except:
        st.session_state.api_key = ""
if 'language' not in st.session_state:
    st.session_state.language = 'chinese'
if 'proficiency' not in st.session_state:
    st.session_state.proficiency = 'intermediate'
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 'chat'
if 'show_translation' not in st.session_state:
    st.session_state.show_translation = {}
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None

# 언어 설정
LANGUAGES = {
    'chinese': {'name': '中文', 'flag': '🇨🇳'},
    'spanish': {'name': 'Español', 'flag': '🇪🇸'},
    'french': {'name': 'Français', 'flag': '🇫🇷'},
    'japanese': {'name': '日本語', 'flag': '🇯🇵'}
}

PROFICIENCY = {
    'beginner': '初级',
    'intermediate': '中级',
    'advanced': '高级'
}

def get_ai_response(messages, language, proficiency, api_key):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system=f"You are a {LANGUAGES[language]['name']} tutor. Respond in {LANGUAGES[language]['name']}. Keep responses SHORT (2-3 sentences).",
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        return f"错误: {str(e)}"

def translate_to_korean(text, api_key):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": f"Translate to Korean (translation only): {text}"}]
        )
        return response.content[0].text
    except Exception as e:
        return f"翻译错误: {str(e)}"

def analyze_chinese(text, api_key):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"""Analyze this Chinese text in JSON format:
{{
  "pinyin": "full pinyin",
  "words": [{{"chinese": "word", "pinyin": "pinyin", "meaning": "Korean meaning"}}],
  "grammar": "grammar explanation in Korean"
}}

Text: {text}"""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis_text = response.content[0].text.replace('```json', '').replace('```', '').strip()
        return json.loads(analysis_text)
    except Exception as e:
        return {"pinyin": "分析错误", "words": [], "grammar": str(e)}

# WeChat 헤더
st.markdown(f"""
<div class='wechat-header'>
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <div style='font-size: 18px; font-weight: 500;'>
            {LANGUAGES[st.session_state.language]['flag']} {LANGUAGES[st.session_state.language]['name']}学习
        </div>
        <div style='font-size: 14px; opacity: 0.9;'>
            {PROFICIENCY[st.session_state.proficiency]}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 하단 네비게이션
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💬\n对话", key="nav_chat", use_container_width=True):
        st.session_state.current_tab = 'chat'
        st.rerun()
with col2:
    if st.button("📖\n分析", key="nav_analysis", use_container_width=True):
        st.session_state.current_tab = 'analysis'
        st.rerun()
with col3:
    if st.button("📊\n统计", key="nav_stats", use_container_width=True):
        st.session_state.current_tab = 'stats'
        st.rerun()
with col4:
    if st.button("⚙️\n设置", key="nav_settings", use_container_width=True):
        st.session_state.current_tab = 'settings'
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# 탭별 콘텐츠
if st.session_state.current_tab == 'chat':
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
    if len(st.session_state.messages) == 0:
        st.markdown(f"""
        <div style='text-align: center; padding: 60px 20px;'>
            <div style='font-size: 64px; margin-bottom: 16px;'>{LANGUAGES[st.session_state.language]['flag']}</div>
            <p style='color: #8e8e93; font-size: 16px;'>开始对话</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, msg in enumerate(st.session_state.messages):
            if msg['role'] == 'user':
                st.markdown(f"""
                <div class='msg-wrapper user'>
                    <div class='user-message'>{msg['content']}</div>
                    <div class='avatar user'>👤</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                msg_key = f"msg_{idx}"
                msg_content = msg['content']
                
                if msg_key in st.session_state.show_translation and st.session_state.show_translation[msg_key]:
                    if 'translation' in msg:
                        msg_content = f"{msg['content']}<div class='translation'>{msg['translation']}</div>"
                
                st.markdown(f"""
                <div class='msg-wrapper assistant'>
                    <div class='avatar'>🤖</div>
                    <div class='assistant-message'>{msg_content}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"{'隐藏翻译' if st.session_state.show_translation.get(msg_key, False) else '显示翻译'}", key=f"trans_{idx}"):
                    if 'translation' not in msg:
                        msg['translation'] = translate_to_korean(msg['content'], st.session_state.api_key)
                    st.session_state.show_translation[msg_key] = not st.session_state.show_translation.get(msg_key, False)
                    st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    
    # 입력 영역
    st.markdown("<div class='input-container'>", unsafe_allow_html=True)
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_input = st.text_input("", placeholder="输入消息...", key="chat_input", label_visibility="collapsed")
    with col_send:
        send_btn = st.button("📤", key="send_btn", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    if user_input and send_btn and st.session_state.api_key:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        ai_response = get_ai_response(messages_for_api, st.session_state.language, st.session_state.proficiency, st.session_state.api_key)
        
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        
        if st.session_state.language == 'chinese':
            st.session_state.current_analysis = analyze_chinese(ai_response, st.session_state.api_key)
        
        st.rerun()

elif st.session_state.current_tab == 'analysis':
    st.markdown("<div style='padding: 70px 15px 80px;'>", unsafe_allow_html=True)
    st.markdown("## 📖 词汇分析")
    
    if st.session_state.current_analysis:
        analysis = st.session_state.current_analysis
        
        if analysis.get('pinyin'):
            st.markdown(f"""
            <div class='analysis-card' style='background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);'>
                <div style='font-size: 12px; font-weight: 600; color: #666; margin-bottom: 6px;'>拼音</div>
                <div style='color: #7c3aed; font-size: 16px;'>{analysis['pinyin']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        if analysis.get('words'):
            st.markdown("<div style='font-size: 12px; font-weight: 600; color: #666; margin: 16px 0 8px;'>词汇</div>", unsafe_allow_html=True)
            for word in analysis['words']:
                st.markdown(f"""
                <div class='analysis-card'>
                    <div style='font-size: 20px; font-weight: bold; color: #09b83e;'>{word['chinese']}</div>
                    <div style='font-size: 14px; color: #666; margin: 4px 0;'>({word['pinyin']})</div>
                    <div style='font-size: 15px; color: #333; margin-top: 6px;'>→ {word['meaning']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        if analysis.get('grammar'):
            st.markdown(f"""
            <div class='analysis-card' style='background: #fff3cd; border-left: 4px solid #09b83e;'>
                <div style='font-size: 12px; font-weight: 600; color: #666; margin-bottom: 6px;'>语法</div>
                <div style='color: #333; font-size: 15px;'>{analysis['grammar']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("开始对话后查看分析")
    
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.current_tab == 'stats':
    st.markdown("<div style='padding: 70px 15px 80px;'>", unsafe_allow_html=True)
    st.markdown("## 📊 学习统计")
    
    st.markdown(f"""
    <div class='stat-card'>
        <div style='font-size: 14px; color: #8e8e93; margin-bottom: 8px;'>对话次数</div>
        <div style='font-size: 36px; font-weight: bold; color: #09b83e;'>{len(st.session_state.messages)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class='stat-card'>
        <div style='font-size: 14px; color: #8e8e93; margin-bottom: 8px;'>今日学习</div>
        <div style='font-size: 36px; font-weight: bold; color: #007aff;'>活跃中</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class='stat-card'>
        <div style='font-size: 14px; color: #8e8e93; margin-bottom: 8px;'>当前语言</div>
        <div style='font-size: 28px; font-weight: bold;'>{LANGUAGES[st.session_state.language]['flag']} {LANGUAGES[st.session_state.language]['name']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.current_tab == 'settings':
    st.markdown("<div style='padding: 70px 15px 80px;'>", unsafe_allow_html=True)
    st.markdown("## ⚙️ 设置")
    
    if not st.session_state.api_key:
        api_key = st.text_input("API密钥", type="password", placeholder="输入 Anthropic API Key")
        if api_key:
            st.session_state.api_key = api_key
            st.success("✅ API密钥已设置")
            st.rerun()
    else:
        st.success("✅ API密钥已设置")
        if st.button("修改API密钥"):
            st.session_state.api_key = ""
            st.rerun()
    
    st.markdown("---")
    
    language = st.selectbox(
        "学习语言",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: f"{LANGUAGES[x]['flag']} {LANGUAGES[x]['name']}",
        index=list(LANGUAGES.keys()).index(st.session_state.language)
    )
    if language != st.session_state.language:
        st.session_state.language = language
        st.session_state.messages = []
        st.session_state.current_analysis = None
        st.rerun()
    
    proficiency = st.selectbox(
        "水平",
        options=list(PROFICIENCY.keys()),
        format_func=lambda x: PROFICIENCY[x],
        index=list(PROFICIENCY.keys()).index(st.session_state.proficiency)
    )
    if proficiency != st.session_state.proficiency:
        st.session_state.proficiency = proficiency
        st.rerun()
    
    st.markdown("---")
    
    if st.button("🗑️ 清空对话", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.current_analysis = None
        st.session_state.show_translation = {}
        st.success("对话已清空")
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# WeChat 스타일 CSS
st.markdown("""
<style>
    /* 전체 배경 - WeChat 스타일 */
    .stApp {
        background-color: #ededed;
        max-width: 100%;
    }
    
    /* 헤더 숨기기 */
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    footer {visibility: hidden;}
    
    /* 모바일 반응형 */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            position: fixed;
            right: -100%;
            top: 0;
            height: 100vh;
            width: 80%;
            transition: right 0.3s ease;
            z-index: 1000;
            box-shadow: -2px 0 8px rgba(0,0,0,0.2);
        }
        
        [data-testid="stSidebar"][data-testid="stSidebar--open"] {
            right: 0;
        }
        
        .wechat-header {
            margin: 0 !important;
            padding: 12px 15px !important;
        }
        
        .main .block-container {
            padding: 0.5rem !important;
            max-width: 100% !important;
        }
        
        .settings-toggle {
            display: block !important;
            position: fixed;
            top: 15px;
            right: 15px;
            z-index: 999;
            background: rgba(255,255,255,0.9);
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
    }
    
    @media (min-width: 769px) {
        .settings-toggle {
            display: none;
        }
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #f7f7f7;
        border-left: 2px solid #d0d0d0;
        min-width: 280px;
        max-width: 320px;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background-color: #f7f7f7;
    }
    
    /* WeChat 헤더 */
    .wechat-header {
        background: linear-gradient(135deg, #09b83e 0%, #0aa146 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 0;
        margin: -1rem -1rem 1rem -1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        position: sticky;
        top: 0;
        z-index: 100;
    }
    
    /* 메인 컨테이너 */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 6rem;
        max-width: 100%;
    }
    
    /* 메시지 컨테이너 */
    .msg-container {
        display: flex;
        margin: 12px 0;
        align-items: flex-start;
    }
    
    .msg-container.user {
        justify-content: flex-end;
        flex-direction: row-reverse;
    }
    
    .msg-container.assistant {
        justify-content: flex-start;
        flex-direction: row;
    }
    
    /* 사용자 메시지 - WeChat 녹색 */
    .user-message {
        background-color: #95ec69;
        color: #000;
        padding: 10px 14px;
        border-radius: 8px;
        text-align: left;
        position: relative;
        word-wrap: break-word;
        font-size: 16px;
        line-height: 1.5;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        max-width: 70%;
        display: inline-block;
    }
    
    .user-message::after {
        content: '';
        position: absolute;
        right: -8px;
        top: 10px;
        width: 0;
        height: 0;
        border-left: 8px solid #95ec69;
        border-top: 6px solid transparent;
        border-bottom: 6px solid transparent;
    }
    
    /* 튜터 메시지 - WeChat 흰색 */
    .assistant-message {
        background-color: #ffffff;
        color: #000;
        padding: 10px 14px;
        border-radius: 8px;
        text-align: left;
        position: relative;
        word-wrap: break-word;
        font-size: 16px;
        line-height: 1.5;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        max-width: 70%;
        display: inline-block;
    }
    
    .assistant-message::before {
        content: '';
        position: absolute;
        left: -8px;
        top: 10px;
        width: 0;
        height: 0;
        border-right: 8px solid #ffffff;
        border-top: 6px solid transparent;
        border-bottom: 6px solid transparent;
    }
    
    /* 아바타 */
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 6px;
        margin: 0 8px;
        font-size: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #d0d0d0;
        flex-shrink: 0;
    }
    
    /* 번역 텍스트 */
    .translation {
        background-color: #f5f5f5;
        padding: 8px 12px;
        border-radius: 6px;
        margin-top: 8px;
        font-size: 14px;
        color: #666;
        border-left: 3px solid #09b83e;
    }
    
    /* 분석 패널 */
    .analysis-box {
        background-color: #f7f7f7;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border: 1px solid #e0e0e0;
    }
    
    .word-item {
        background-color: white;
        padding: 10px;
        border-radius: 8px;
        margin: 6px 0;
        border: 1px solid #e8e8e8;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* 버튼 */
    .stButton button {
        width: 100%;
        border-radius: 6px;
        padding: 10px;
        background-color: #09b83e;
        color: white;
        border: none;
        font-weight: 500;
    }
    
    .stButton button:hover {
        background-color: #0aa146;
    }
    
    /* 입력창 */
    .stTextInput input {
        border-radius: 6px;
        padding: 12px 15px;
        background-color: white;
        border: 1px solid #d0d0d0;
        font-size: 16px;
    }
    
    /* 입력 영역 */
    .input-area {
        background-color: #f7f7f7;
        padding: 10px;
        border-top: 1px solid #d0d0d0;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 100;
    }
    
    @media (min-width: 769px) {
        .input-area {
            right: 320px;
        }
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'api_key' not in st.session_state:
    # Secrets에서 API 키 가져오기
    try:
        st.session_state.api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception as e:
        st.session_state.api_key = ""
if 'language' not in st.session_state:
    st.session_state.language = 'chinese'
if 'proficiency' not in st.session_state:
    st.session_state.proficiency = 'intermediate'
if 'show_translation' not in st.session_state:
    st.session_state.show_translation = {}
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None
if 'last_input' not in st.session_state:
    st.session_state.last_input = ""

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

# 헤더 - WeChat 스타일
st.markdown(f"""
<div class='wechat-header'>
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <div style='font-size: 18px; font-weight: 500;'>
            {LANGUAGES[st.session_state.language]['flag']} {LANGUAGES[st.session_state.language]['name']}学习
        </div>
        <div style='font-size: 14px; opacity: 0.9;'>
            {PROFICIENCY[st.session_state.proficiency]}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 사이드바 - 설정
with st.sidebar:
    st.header("⚙️ 설정")
    
    # API 키 입력 (Secrets에 없을 경우에만 표시)
    if not st.session_state.api_key:
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value="",
            help="https://console.anthropic.com/settings/keys 에서 발급"
        )
        if api_key:
            st.session_state.api_key = api_key
    else:
        st.success("✅ API Key 설정됨")
        if st.button("API Key 변경"):
            st.session_state.api_key = ""
            st.rerun()
    
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
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)  # 입력창 공간 확보
    
    st.markdown("<div class='input-area'>", unsafe_allow_html=True)
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input(
            "메시지 입력",
            key="user_input",
            placeholder="输入消息...",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("💬", use_container_width=True, type="primary")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 메시지 전송
    if user_input and (send_button or user_input != st.session_state.get('last_input', '')):
        st.session_state.last_input = user_input
        
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

# JavaScript로 Enter 키 처리
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        const input = document.querySelector('input[aria-label="메시지 입력"]');
        if (input && input.value) {
            e.preventDefault();
            const button = Array.from(document.querySelectorAll('button')).find(btn => btn.textContent === '💬');
            if (button) button.click();
        }
    }
});
</script>
""", unsafe_allow_html=True)
