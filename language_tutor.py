# -*- coding: utf-8 -*-
"""
Streamlit MobileLanguageTutor — WeChat 스타일 (Anthropic 오류 수정 안정버전)
Python 3.10+ / Streamlit 1.33+
옵션: openai>=1.40.0, anthropic>=0.34.0
"""

import os
import json
import time
from datetime import datetime
import typing as T
import streamlit as st

# =========================
# 설정
# =========================
APP_TITLE = "언어 학습 (WeChat)"
DEFAULT_LANGUAGE = "chinese"
LANGUAGES = {
    "spanish":  {"name": "스페인어",  "flag": "🇪🇸"},
    "french":   {"name": "프랑스어",  "flag": "🇫🇷"},
    "german":   {"name": "독일어",    "flag": "🇩🇪"},
    "japanese": {"name": "일본어",    "flag": "🇯🇵"},
    "italian":  {"name": "이탈리아어","flag": "🇮🇹"},
    "korean":   {"name": "한국어",    "flag": "🇰🇷"},
    "chinese":  {"name": "중국어",    "flag": "🇨🇳"},
}
LEVELS = ["beginner", "intermediate", "advanced"]
LEVEL_LABEL = {"beginner":"초급","intermediate":"중급","advanced":"고급"}

# =========================
# 모델 함수
# =========================
def _has_openai():
    try:
        import openai
        return bool(os.environ.get("OPENAI_API_KEY"))
    except Exception:
        return False

def _has_anthropic():
    try:
        import anthropic
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    except Exception:
        return False


def stream_reply(messages: list[dict], temperature=0.2, max_tokens=400):
    """스트리밍 응답 (Anthropic system role 수정 포함)"""
    provider = "mock"
    if _has_openai():
        provider = "openai"
    elif _has_anthropic():
        provider = "anthropic"

    if provider == "openai":
        import openai
        client = openai.OpenAI()
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield delta
            return
        except Exception:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            yield resp.choices[0].message.content or ""
            return

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

        # system 메시지 처리
        system_prompt = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            else:
                filtered.append({"role": m["role"], "content": m["content"]})

        try:
            with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=filtered,
            ) as s:
                for text in s.text_stream:
                    if text:
                        yield text
            return
        except Exception:
            try:
                resp = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=filtered,
                )
                text = "".join([b.text for b in resp.content if hasattr(b, "text")]).strip()
                if text:
                    yield text
                    return
            except Exception:
                pass

    # Mock fallback
    user_last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    mock = f"你好！今天想聊什么？\n\n(입력 미러) {user_last[:100]}"
    for tok in mock.split():
        yield tok + " "
        time.sleep(0.01)


# =========================
# 상태 관리
# =========================
def ensure_state():
    st.session_state.setdefault("selectedLanguage", DEFAULT_LANGUAGE)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("input", "")
    st.session_state.setdefault("isLoading", False)
    st.session_state.setdefault("showDrawer", False)


def add_message(role: str, content: str):
    st.session_state.messages.append({
        "id": len(st.session_state.messages),
        "role": role,
        "content": content,
        "ts": datetime.now().strftime("%H:%M"),
    })


# =========================
# UI
# =========================
def inject_css():
    st.markdown("""
<style>
body {background:#ededed;}
.block-container {padding:0; max-width:860px;}
header {visibility:hidden;}
.phone {margin:auto; width:420px; max-width:92vw; background:#e5e5e5; border-radius:28px; overflow:hidden;}
.chat {height:70vh; overflow:auto; padding:12px; background:#ececec;}
.row {display:flex; margin:8px 0;}
.left {justify-content:flex-start;}
.right{justify-content:flex-end;}
.bubble {max-width:72%; padding:9px 12px; border-radius:10px; white-space:pre-wrap;}
.user {background:#95ec69;}
.bot {background:#fff; border:1px solid #ddd;}
.inputbar {display:flex; padding:6px; gap:6px; border-top:1px solid #ddd; background:#f6f6f6;}
.drawer-overlay {position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:9998;}
.drawer {position:fixed; right:0; top:0; height:100vh; width:min(86vw,360px); background:#fff; z-index:9999; overflow:auto; padding:12px;}
</style>
    """, unsafe_allow_html=True)


def render_message(msg):
    side = "right" if msg["role"] == "user" else "left"
    cls = "user" if msg["role"] == "user" else "bot"
    st.markdown(
        f"<div class='row {side}'><div class='bubble {cls}'>{msg['content']}</div></div>",
        unsafe_allow_html=True,
    )


# =========================
# 메인
# =========================
def main():
    st.set_page_config(page_title=APP_TITLE, layout="centered")
    ensure_state()
    inject_css()

    st.markdown("<div class='phone'>", unsafe_allow_html=True)
    st.markdown("<div class='chat'>", unsafe_allow_html=True)

    for m in st.session_state.messages:
        render_message(m)
    if st.session_state.isLoading:
        st.markdown("<div class='row left'><div class='bubble bot'>입력 중...</div></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # 입력창
    c1, c2, c3 = st.columns([8,1,1])
    text = c1.text_input("", st.session_state.input, label_visibility="collapsed", placeholder="메시지 입력...")
    emoji = c2.button("🙂")
    send = c3.button("⮕")
    if emoji:
        st.session_state.showDrawer = not st.session_state.showDrawer

    if st.session_state.showDrawer:
        st.markdown("<div class='drawer-overlay'></div>", unsafe_allow_html=True)
        st.markdown("<div class='drawer'>", unsafe_allow_html=True)
        st.header("설정 / 분석")
        if st.button("닫기"):
            st.session_state.showDrawer = False
        st.selectbox("언어 선택", list(LANGUAGES.keys()),
                     index=list(LANGUAGES.keys()).index(st.session_state.selectedLanguage),
                     key="selectedLanguage", format_func=lambda k: f"{LANGUAGES[k]['flag']} {LANGUAGES[k]['name']}")
        st.selectbox("수준 선택", LEVELS,
                     index=LEVELS.index("intermediate"), format_func=lambda v: LEVEL_LABEL[v])
        st.markdown("</div>", unsafe_allow_html=True)

    # 전송
    if send and text.strip() and not st.session_state.isLoading:
        st.session_state.input = ""
        add_message("user", text.strip())
        st.session_state.isLoading = True
        msgs = [{"role":"system","content":"You are a helpful tutor."}] + st.session_state.messages
        acc = ""
        for chunk in stream_reply(msgs):
            acc += chunk
            ph = st.empty()
            ph.markdown(f"<div class='row left'><div class='bubble bot'>{acc}</div></div>", unsafe_allow_html=True)
        add_message("assistant", acc)
        st.session_state.isLoading = False
        st.rerun()
    else:
        st.session_state.input = text

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
