import streamlit as st
import anthropic
import json
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="语言学习", page_icon="💬", layout="wide")

# CSS
st.markdown("""
<style>
    .stApp {background-color: #ededed;}
    header, footer, #MainMenu {display: none !important;}
    
    /* 레이아웃 */
    .main .block-container {
        padding: 0;
        max-width: 100%;
    }
    
    /* 상단 헤더 */
    .wechat-header {
        background: linear-gradient(135deg, #09b83e 0%, #0aa146 100%);
        color: white;
        padding: 15px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 메시지 영역 */
    .msg-container {
        display: flex;
        margin: 15px 0;
        align-items: flex-start;
    }
    
    .msg-container.user {
        justify-content: flex-end;
    }
    
    .msg-container.assistant {
        justify-content: flex-start;
    }
    
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 6px;
        background: #d0d0d0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        flex-shrink: 0;
    }
    
    .bubble {
        max-width: 70%;
        padding: 12px 15px;
        border-radius: 10px;
        font-size: 16px;
        line-height: 1.5;
        word-wrap: break-word;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .bubble.user {
        background: #95ec69;
        color: #000;
        margin-right: 10px;
        border-radius: 10px 10px 2px 10px;
    }
    
    .bubble.assistant {
        background: white;
        color: #000;
        margin-left: 10px;
        border-radius: 10px 10px 10px 2px;
    }
    
    .translation {
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid #e0e0e0;
        font-size: 14px;
        color: #666;
    }
    
    /* 분석 카드 */
    .analysis-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .word-box {
        background: #f7f7f7;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid #09b83e;
    }
    
    /* 피드백 */
    .feedback-box {
        background: #fff3cd;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid #ffc107;
    }
    
    /* 버튼 */
    .stButton button {
        background: #09b83e;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 500;
    }
    
    .stButton button:hover {
        background: #0aa146;
    }
    
    /* 입력창 */
    .stTextInput input {
        border-radius: 20px;
        border: 1px solid #d0d0d0;
        padding: 12px 15px;
        font-size: 16px;
    }
    
    /* 설정 패널 */
    .settings-panel {
        background: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# 세션 초기화
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
if 'show_translation' not in st.session_state:
    st.session_state.show_translation = {}
if 'analyses' not in st.session_state:
    st.session_state.analyses = {}
if 'feedbacks' not in st.session_state:
    st.session_state.feedbacks = {}

LANGUAGES = {
    'chinese': {'name': '中文', 'flag': '🇨🇳'},
    'spanish': {'name': 'Español', 'flag': '🇪🇸'},
    'french': {'name': 'Français', 'flag': '🇫🇷'},
    'japanese': {'name': '日本語', 'flag': '🇯🇵'}
}

PROFICIENCY = {'beginner': '初级', 'intermediate': '中级', 'advanced': '高级'}

def send_message(text, api_key, language, proficiency):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system=f"You are a {LANGUAGES[language]['name']} tutor. Respond in {LANGUAGES[language]['name']} at {proficiency} level. Keep responses SHORT (2-3 sentences).",
            messages=msgs
        )
        return response.content[0].text
    except Exception as e:
        return f"错误: {str(e)}"

def translate_text(text, api_key):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": f"Translate to Korean (translation only):\n\n{text}"}]
        )
        return response.content[0].text
    except:
        return "翻译错误"

def analyze_message(text, api_key, language):
    if language != 'chinese':
        return None
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": f"""Analyze this Chinese text for HSK 5 learner. Return JSON only:

{{
  "pinyin": "full sentence pinyin with tones",
  "words": [
    {{"chinese": "word", "pinyin": "pinyin", "meaning": "Korean meaning"}}
  ],
  "grammar": "grammar explanation in Korean",
  "notes": "usage notes in Korean"
}}

Text: {text}"""
            }]
        )
        txt = response.content[0].text.replace('```json', '').replace('```', '').strip()
        return json.loads(txt)
    except:
        return None

def get_feedback(user_msg, api_key, language):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"Provide brief feedback on this {LANGUAGES[language]['name']} sentence in Korean (grammar, vocabulary, naturalness). Keep it under 3 sentences:\n\n{user_msg}"
            }]
        )
        return response.content[0].text
    except:
        return None

def save_conversation():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"对话_{LANGUAGES[st.session_state.language]['name']}_{timestamp}.txt"
    
    content = f"语言学习对话记录\n"
    content += f"=" * 50 + "\n\n"
    content += f"语言: {LANGUAGES[st.session_state.language]['name']}\n"
    content += f"水平: {PROFICIENCY[st.session_state.proficiency]}\n"
    content += f"日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"对话数: {len(st.session_state.messages)}\n\n"
    content += f"=" * 50 + "\n\n"
    
    for i, msg in enumerate(st.session_state.messages):
        role = "学习者" if msg["role"] == "user" else "老师"
        content += f"{role}: {msg['content']}\n"
        
        if f"msg_{i}" in st.session_state.show_translation:
            if st.session_state.show_translation[f"msg_{i}"] and 'translation' in msg:
                content += f"[翻译]: {msg['translation']}\n"
        
        content += "\n"
    
    return content, filename

# 상단 헤더
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #09b83e 0%, #0aa146 100%); color: white; 
                padding: 15px 20px; border-radius: 10px; margin-bottom: 10px;'>
        <div style='font-size: 20px; font-weight: 500;'>
            {LANGUAGES[st.session_state.language]['flag']} {LANGUAGES[st.session_state.language]['name']}学习
        </div>
        <div style='font-size: 14px; opacity: 0.9; margin-top: 4px;'>
            {PROFICIENCY[st.session_state.proficiency]}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_h2:
    st.markdown("<div style='margin-bottom: 10px;'>", unsafe_allow_html=True)
    if st.button("💾 保存对话", use_container_width=True):
        if st.session_state.messages:
            content, filename = save_conversation()
            st.download_button("📥 下载", content, filename, "text/plain", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# 메인 레이아웃
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("### 💬 对话")
    
    # 메시지 표시
    chat_area = st.container()
    with chat_area:
        if not st.session_state.messages:
            st.markdown(f"""
            <div style='text-align: center; padding: 60px 20px; background: white; border-radius: 10px;'>
                <div style='font-size: 64px;'>{LANGUAGES[st.session_state.language]['flag']}</div>
                <p style='color: #666; font-size: 18px; margin-top: 16px;'>开始对话</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for idx, msg in enumerate(st.session_state.messages):
                msg_key = f"msg_{idx}"
                
                if msg['role'] == 'user':
                    st.markdown(f"""
                    <div class='msg-container user'>
                        <div class='bubble user'>{msg['content']}</div>
                        <div class='avatar'>👤</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 사용자 메시지 피드백
                    if msg_key in st.session_state.feedbacks:
                        st.markdown(f"""
                        <div class='feedback-box'>
                            <strong>💡 反馈:</strong> {st.session_state.feedbacks[msg_key]}
                        </div>
                        """, unsafe_allow_html=True)
                
                else:
                    # 번역 표시
                    msg_content = msg['content']
                    if st.session_state.show_translation.get(msg_key, False) and 'translation' in msg:
                        msg_content = f"{msg['content']}<div class='translation'>📱 {msg['translation']}</div>"
                    
                    st.markdown(f"""
                    <div class='msg-container assistant'>
                        <div class='avatar'>🤖</div>
                        <div class='bubble assistant'>{msg_content}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 번역 버튼
                    if st.button(f"{'隐藏翻译' if st.session_state.show_translation.get(msg_key, False) else '显示翻译'}", 
                               key=f"trans_{idx}"):
                        if 'translation' not in msg:
                            msg['translation'] = translate_text(msg['content'], st.session_state.api_key)
                        st.session_state.show_translation[msg_key] = not st.session_state.show_translation.get(msg_key, False)
                        st.rerun()
                    
                    # 튜터 메시지 분석
                    if msg_key in st.session_state.analyses:
                        analysis = st.session_state.analyses[msg_key]
                        
                        if analysis.get('pinyin'):
                            st.markdown(f"""
                            <div class='analysis-card' style='background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);'>
                                <strong>🔤 拼音:</strong> {analysis['pinyin']}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if analysis.get('words'):
                            for word in analysis['words']:
                                st.markdown(f"""
                                <div class='word-box'>
                                    <strong style='font-size: 18px; color: #09b83e;'>{word['chinese']}</strong> 
                                    <span style='color: #666;'>({word['pinyin']})</span>
                                    <div style='margin-top: 4px;'>→ {word['meaning']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        if analysis.get('grammar'):
                            st.markdown(f"""
                            <div class='analysis-card' style='background: #fff3cd;'>
                                <strong>📚 语法:</strong> {analysis['grammar']}
                            </div>
                            """, unsafe_allow_html=True)
    
    # 입력창
    st.markdown("---")
    col_inp1, col_inp2 = st.columns([5, 1])
    with col_inp1:
        user_input = st.text_input("", placeholder="输入消息...", key="msg_input", label_visibility="collapsed")
    with col_inp2:
        send_btn = st.button("📤 发送", use_container_width=True)
    
    if send_btn and user_input and st.session_state.api_key:
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": user_input})
        user_idx = len(st.session_state.messages) - 1
        
        # AI 응답 생성
        msgs_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        ai_response = send_message(user_input, st.session_state.api_key, 
                                   st.session_state.language, st.session_state.proficiency)
        
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        ai_idx = len(st.session_state.messages) - 1
        
        # 피드백 생성
        feedback = get_feedback(user_input, st.session_state.api_key, st.session_state.language)
        if feedback:
            st.session_state.feedbacks[f"msg_{user_idx}"] = feedback
        
        # 중국어 분석
        if st.session_state.language == 'chinese':
            analysis = analyze_message(ai_response, st.session_state.api_key, st.session_state.language)
            if analysis:
                st.session_state.analyses[f"msg_{ai_idx}"] = analysis
        
        st.rerun()

with col_right:
    st.markdown("### ⚙️ 设置")
    
    st.markdown("<div class='settings-panel'>", unsafe_allow_html=True)
    
    # API 키
    if not st.session_state.api_key:
        api_key = st.text_input("API密钥", type="password", placeholder="输入 API Key")
        if api_key:
            st.session_state.api_key = api_key
            st.success("✅ 已设置")
            st.rerun()
    else:
        st.success("✅ API已连接")
    
    st.markdown("---")
    
    # 언어 선택
    lang = st.selectbox(
        "学习语言",
        list(LANGUAGES.keys()),
        format_func=lambda x: f"{LANGUAGES[x]['flag']} {LANGUAGES[x]['name']}",
        index=list(LANGUAGES.keys()).index(st.session_state.language)
    )
    if lang != st.session_state.language:
        st.session_state.language = lang
        st.session_state.messages = []
        st.session_state.analyses = {}
        st.session_state.feedbacks = {}
        st.rerun()
    
    # 숙련도 선택
    prof = st.selectbox(
        "水平",
        list(PROFICIENCY.keys()),
        format_func=lambda x: PROFICIENCY[x],
        index=list(PROFICIENCY.keys()).index(st.session_state.proficiency)
    )
    if prof != st.session_state.proficiency:
        st.session_state.proficiency = prof
        st.rerun()
    
    st.markdown("---")
    
    # 통계
    st.markdown("### 📊 统计")
    st.metric("对话数", len(st.session_state.messages))
    
    st.markdown("---")
    
    # 초기화
    if st.button("🗑️ 清空对话", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.analyses = {}
        st.session_state.feedbacks = {}
        st.session_state.show_translation = {}
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
