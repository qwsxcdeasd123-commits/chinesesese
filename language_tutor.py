import streamlit as st
import anthropic
import json

# 페이지 설정
st.set_page_config(page_title="语言学习", page_icon="💬", layout="centered")

# CSS
st.markdown("""
<style>
    .stApp {background-color: #ededed;}
    header, footer {display: none !important;}
    
    /* 상단 헤더 */
    .top-header {
        background: linear-gradient(135deg, #09b83e 0%, #0aa146 100%);
        color: white;
        padding: 15px;
        margin: -1rem -1rem 0 -1rem;
        text-align: center;
        font-size: 18px;
        font-weight: 500;
    }
    
    /* 메시지 스타일 */
    .msg-row {
        display: flex;
        margin: 15px 0;
        align-items: flex-start;
    }
    .msg-row.user {justify-content: flex-end;}
    .msg-row.assistant {justify-content: flex-start;}
    
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 6px;
        background: #ccc;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        flex-shrink: 0;
    }
    
    .bubble {
        max-width: 70%;
        padding: 12px;
        border-radius: 10px;
        font-size: 16px;
        line-height: 1.5;
        word-wrap: break-word;
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
    
    /* 탭 버튼 */
    .tab-container {
        display: flex;
        background: white;
        border-top: 1px solid #ddd;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 1000;
    }
    
    .stButton button {
        width: 100%;
        height: 60px;
        background: white;
        color: #666;
        border: none;
        font-size: 12px;
        padding: 8px;
    }
    
    .stButton button:hover {
        background: #f5f5f5;
    }
    
    /* 입력창 */
    .stTextInput input {
        border-radius: 20px;
        border: 1px solid #ddd;
        padding: 10px 15px;
    }
</style>
""", unsafe_allow_html=True)

# 세션 초기화
if 'tab' not in st.session_state:
    st.session_state.tab = '对话'
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'api_key' not in st.session_state:
    try:
        st.session_state.api_key = st.secrets["ANTHROPIC_API_KEY"]
    except:
        st.session_state.api_key = ""
if 'language' not in st.session_state:
    st.session_state.language = 'chinese'
if 'analysis' not in st.session_state:
    st.session_state.analysis = None

LANGS = {
    'chinese': '🇨🇳 中文',
    'spanish': '🇪🇸 Español',
    'french': '🇫🇷 Français',
    'japanese': '🇯🇵 日本語'
}

# 함수들
def send_message(text, api_key):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system="You are a language tutor. Respond in the target language. Keep it short (2-3 sentences).",
            messages=msgs
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_chinese(text, api_key):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"Analyze this Chinese text. Return JSON only:\n{{'pinyin': 'pinyin', 'words': [{{'ch': 'word', 'py': 'pinyin', 'kr': 'meaning'}}], 'grammar': 'explanation in Korean'}}\n\nText: {text}"
            }]
        )
        txt = response.content[0].text.replace('```json', '').replace('```', '').strip()
        return json.loads(txt)
    except:
        return None

# 헤더
st.markdown(f"<div class='top-header'>{LANGS[st.session_state.language]} 学习</div>", unsafe_allow_html=True)

# 탭 콘텐츠
if st.session_state.tab == '对话':
    # 메시지 표시
    for msg in st.session_state.messages:
        if msg['role'] == 'user':
            st.markdown(f"""
            <div class='msg-row user'>
                <div class='bubble user'>{msg['content']}</div>
                <div class='avatar'>👤</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='msg-row assistant'>
                <div class='avatar'>🤖</div>
                <div class='bubble assistant'>{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # 여백
    st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
    
    # 입력
    col1, col2 = st.columns([5, 1])
    with col1:
        inp = st.text_input("", placeholder="输入消息...", key="input", label_visibility="collapsed")
    with col2:
        send = st.button("📤")
    
    if send and inp and st.session_state.api_key:
        st.session_state.messages.append({"role": "user", "content": inp})
        ai_resp = send_message(inp, st.session_state.api_key)
        st.session_state.messages.append({"role": "assistant", "content": ai_resp})
        
        if st.session_state.language == 'chinese':
            st.session_state.analysis = analyze_chinese(ai_resp, st.session_state.api_key)
        
        st.rerun()

elif st.session_state.tab == '分析':
    st.markdown("<div style='padding: 20px;'>", unsafe_allow_html=True)
    st.markdown("## 📖 词汇分析")
    
    if st.session_state.analysis:
        a = st.session_state.analysis
        
        if a.get('pinyin'):
            st.info(f"**拼音:** {a['pinyin']}")
        
        if a.get('words'):
            st.markdown("**词汇:**")
            for w in a['words']:
                st.markdown(f"- **{w.get('ch', '')}** ({w.get('py', '')}) → {w.get('kr', '')}")
        
        if a.get('grammar'):
            st.success(f"**语法:** {a['grammar']}")
    else:
        st.info("开始对话后查看分析")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

elif st.session_state.tab == '统计':
    st.markdown("<div style='padding: 20px;'>", unsafe_allow_html=True)
    st.markdown("## 📊 学习统计")
    st.metric("对话次数", len(st.session_state.messages))
    st.metric("当前语言", LANGS[st.session_state.language])
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

elif st.session_state.tab == '设置':
    st.markdown("<div style='padding: 20px;'>", unsafe_allow_html=True)
    st.markdown("## ⚙️ 设置")
    
    if not st.session_state.api_key:
        key = st.text_input("API Key", type="password")
        if key:
            st.session_state.api_key = key
            st.success("✅ 已设置")
    else:
        st.success("✅ API已连接")
    
    st.markdown("---")
    
    lang = st.selectbox("学习语言", list(LANGS.keys()), 
                        format_func=lambda x: LANGS[x],
                        index=list(LANGS.keys()).index(st.session_state.language))
    if lang != st.session_state.language:
        st.session_state.language = lang
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    if st.button("🗑️ 清空对话"):
        st.session_state.messages = []
        st.session_state.analysis = None
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

# 하단 탭 버튼
st.markdown("<div style='height: 70px;'></div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💬\n对话"):
        st.session_state.tab = '对话'
        st.rerun()
with col2:
    if st.button("📖\n分析"):
        st.session_state.tab = '分析'
        st.rerun()
with col3:
    if st.button("📊\n统计"):
        st.session_state.tab = '统计'
        st.rerun()
with col4:
    if st.button("⚙️\n设置"):
        st.session_state.tab = '设置'
        st.rerun()
