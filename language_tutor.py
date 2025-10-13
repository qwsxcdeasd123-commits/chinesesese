# -*- coding: utf-8 -*-
"""
Streamlit Language Tutor — WeChat-style UI with analysis sidebar
Runtime: Python 3.10+ / Streamlit 1.33+
Deps (optional): openai>=1.40.0, anthropic>=0.34.0
"""

import os
import json
import time
import typing as T
from datetime import datetime

import streamlit as st

APP_TITLE = "언어 학습 챗봇 (WeChat 스타일)"
DEFAULT_LANGUAGE = "중국어"
LANGUAGE_MAP = {
    "중국어": {"code": "zh", "label": "중국어", "flag": "🇨🇳"},
    "일본어": {"code": "ja", "label": "일본어", "flag": "🇯🇵"},
    "영어": {"code": "en", "label": "영어", "flag": "🇬🇧"},
    "프랑스어": {"code": "fr", "label": "프랑스어", "flag": "🇫🇷"},
    "스페인어": {"code": "es", "label": "스페인어", "flag": "🇪🇸"},
    "독일어": {"code": "de", "label": "독일어", "flag": "🇩🇪"},
    "한국어": {"code": "ko", "label": "한국어", "flag": "🇰🇷"},
}

LEVELS = {
    "초급": "beginner",
    "중급": "intermediate",
    "고급": "advanced",
}

def _has_openai():
    try:
        import openai  # noqa: F401
        return True
    except Exception:
        return False

def _has_anthropic():
    try:
        import anthropic  # noqa: F401
        return True
    except Exception:
        return False

def call_model_stream(
    messages: T.List[dict],
    provider: str = "auto",
    model: str = "",
    temperature: float = 0.2,
    max_tokens: int = 400,
) -> T.Iterable[str]:
    """
    Streaming text generator. Supports OpenAI or Anthropic when installed.
    Falls back to a local mock for offline demo.
    """
    provider = provider.lower()
    if provider == "auto":
        if _has_openai() and os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        elif _has_anthropic() and os.environ.get("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        else:
            provider = "mock"

    if provider == "openai":
        import openai
        client = openai.OpenAI()
        model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
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

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        model = model or os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
        ) as stream:
            for text in stream.text_stream:
                if text:
                    yield text
        return

    # Mock provider (fast, offline) — deterministic short reply
    user_last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    mock = f"네, 확인했습니다. 다음 주제로 계속하시겠습니까?\n\n원문: {user_last[:90]}"
    for token in mock.split():
        yield token + " "
        time.sleep(0.01)


def analyze_text_json(
    text: str,
    lang_code: str,
    level: str,
    provider: str = "auto",
    model: str = "",
    max_tokens: int = 400,
) -> dict:
    """
    Ask the model to return strict JSON for: feedback, words(pinyin/meaning),
    grammar, study notes.
    If no provider available, returns a lightweight heuristic fallback.
    """
    sys = (
        "You are a precise language-teaching assistant. "
        "Return STRICT JSON only. No preface."
    )
    prompt = f"""
언어 코드: {lang_code}
학습자 수준: {level}
아래 학습자 발화를 분석하여 다음 스키마로 JSON만 출력하십시오.

{{
  "feedback": "학습자 발화에 대한 간단하고 구체적인 피드백",
  "words": [{{"term": "단어", "pinyin": "병음 또는 로마자 표기(가능 시)", "meaning": "국문 뜻"}}],
  "grammar": "핵심 문법/표현 설명",
  "notes": "추가 학습 노트"
}}

분석 대상 텍스트:
{text}
"""
    messages = [{"role": "system", "content": sys}, {"role": "user", "content": prompt}]

    if provider == "auto":
        if _has_openai() and os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        elif _has_anthropic() and os.environ.get("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        else:
            provider = "mock"

    if provider == "openai":
        import openai
        client = openai.OpenAI()
        mdl = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=mdl,
            messages=messages,
            temperature=0.1,
            max_tokens=max_tokens,
        )
        raw = resp.choices[0].message.content.strip()
        try:
            return json.loads(raw)
        except Exception:
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        mdl = model or os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        resp = client.messages.create(
            model=mdl,
            max_tokens=max_tokens,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join([b.text for b in resp.content if hasattr(b, "text")]).strip()
        try:
            return json.loads(raw)
        except Exception:
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)

    # Mock analysis (no external calls)
    return {
        "feedback": "문장 구조는 명확합니다. 목적어 앞 전치 사용에 주의하십시오.",
        "words": [
            {"term": "你好", "pinyin": "nǐ hǎo", "meaning": "안녕하세요"},
            {"term": "今天", "pinyin": "jīntiān", "meaning": "오늘"},
        ],
        "grammar": "인사 표현과 의문문 어순 확인.",
        "notes": "주제 확장용 어휘를 3개 더 만들어 연습하십시오.",
    }


def reset_state():
    st.session_state.messages = []
    st.session_state.analysis = None
    st.session_state.chat_language = DEFAULT_LANGUAGE
    st.session_state.level_label = "중급"


def ensure_state():
    if "messages" not in st.session_state:
        reset_state()
    st.session_state.setdefault("analysis", None)
    st.session_state.setdefault("chat_language", DEFAULT_LANGUAGE)
    st.session_state.setdefault("level_label", "중급")


def wechat_css():
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 860px;}
        header {visibility: hidden;}
        .bubble {padding: 10px 14px; border-radius: 12px; margin: 6px 0; max-width: 80%;}
        .bubble-user {background: #95ec69; color: #0b0b0b; margin-left: auto; border-top-right-radius: 6px;}
        .bubble-bot {background: #ffffff; color: #111; border: 1px solid #e5e6ea; border-top-left-radius: 6px;}
        .row {display: flex; align-items: flex-end; gap: 8px;}
        .row-right {justify-content: flex-end;}
        .avatar {width: 34px; height: 34px; border-radius: 6px; background: #f0f0f0; display:flex; align-items:center; justify-content:center; font-size: 18px;}
        .meta {font-size: 11px; color: #8a8f98; margin-top: 2px;}
        .chat-wrap {height: min(60vh, 600px); overflow: auto; padding: 8px; background: #f7f7f7; border: 1px solid #ececec; border-radius: 12px;}
        .toolbar {display:flex; gap:8px; align-items:center;}
        .stTextInput>div>div>input {border-radius: 20px !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_bubble(role: str, content: str, ts: str):
    is_user = role == "user"
    row_cls = "row row-right" if is_user else "row"
    bubble_cls = "bubble bubble-user" if is_user else "bubble bubble-bot"
    avatar = "🙂" if is_user else "🧑‍🏫"
    st.markdown(
        f"""
        <div class="{row_cls}">
          <div class="avatar">{avatar}</div>
          <div>
            <div class="{bubble_cls}">{content}</div>
            <div class="meta">{ts}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def download_payload(messages: list, lang_label: str, level_label: str) -> str:
    data = {
        "title": APP_TITLE,
        "language": lang_label,
        "level": level_label,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "messages": messages,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def main():
    ensure_state()
    st.set_page_config(page_title=APP_TITLE, layout="centered")
    wechat_css()

    # Sidebar
    with st.sidebar:
        flag = LANGUAGE_MAP[st.session_state.chat_language]["flag"]
        st.markdown(f"### {flag} {APP_TITLE}")
        st.caption("사이드바: 분석 · 저장 · 설정")

        st.subheader("설정")
        lang_label = st.selectbox(
            "언어 선택",
            list(LANGUAGE_MAP.keys()),
            index=list(LANGUAGE_MAP.keys()).index(st.session_state.chat_language),
            key="chat_language",
        )
        level_label = st.select_slider("수준 선택", options=list(LEVELS.keys()), key="level_label")

        with st.expander("응답 성능 옵션"):
            provider = st.radio("모델 공급자", ["auto", "openai", "anthropic", "mock"], horizontal=True)
            temp = st.slider("temperature", 0.0, 1.0, 0.2, 0.1)
            max_tok = st.slider("max_tokens", 64, 1024, 400, 32)

        st.divider()

        st.subheader("분석")
        last_user = next((m for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
        analyze_btn = st.button("내 마지막 발화 분석")
        if analyze_btn and last_user:
            with st.spinner("분석 중…"):
                st.session_state.analysis = analyze_text_json(
                    last_user["content"],
                    lang_code=LANGUAGE_MAP[lang_label]["code"],
                    level=LEVELS[level_label],
                    provider=provider,
                    max_tokens=256,
                )

        analysis = st.session_state.analysis or {}
        st.markdown("**1) 피드백**")
        st.write(analysis.get("feedback", "분석 결과 없음"))

        st.markdown("**2) 단어 뜻 · 병음**")
        words = analysis.get("words", [])
        if words:
            for w in words[:30]:
                term = w.get("term", "")
                pinyin = w.get("pinyin", "")
                meaning = w.get("meaning", "")
                st.markdown(f"- {term} ({pinyin}) — {meaning}")
        else:
            st.caption("표시할 항목 없음")

        st.markdown("**3) 문법 설명**")
        st.write(analysis.get("grammar", "분석 결과 없음"))

        st.markdown("**4) 대화 저장**")
        payload = download_payload(st.session_state.messages, lang_label, level_label)
        st.download_button("JSON 다운로드", data=payload.encode("utf-8"), file_name="conversation.json")
        txt = "\n".join([f"[{m['role']}] {m['content']}" for m in st.session_state.messages])
        st.download_button("텍스트 다운로드", data=txt.encode("utf-8"), file_name="conversation.txt")

    # Header
    flag = LANGUAGE_MAP[st.session_state.chat_language]["flag"]
    st.markdown(f"## {flag} {LANGUAGE_MAP[st.session_state.chat_language]['label']} · {st.session_state.level_label}")

    # Chat area
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        render_bubble(msg["role"], msg["content"], msg["ts"])
    st.markdown("</div>", unsafe_allow_html=True)

    # Input area
    with st.container(border=True):
        cols = st.columns([8, 1])
        user_input = cols[0].text_input("메시지 입력", key="chat_input", label_visibility="collapsed")
        send = cols[1].button("전송")

    if send and user_input.strip():
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.messages.append({"role": "user", "content": user_input.strip(), "ts": ts})

        system_prompt = (
            "You are a concise, corrective language partner. "
            "Reply in the target language. Keep responses short (<= 3 sentences)."
        )
        messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages:
            messages.append({"role": m["role"], "content": m["content"]})

        with st.spinner("응답 생성 중…"):
            chunks = call_model_stream(
                messages=messages,
                provider=provider,
                temperature=temp,
                max_tokens=max_tok,
            )
            acc = ""
            ph = st.empty()
            for ck in chunks:
                acc += ck
                ph.markdown(
                    "<div class='row'><div><div class='bubble bubble-bot'>"
                    + acc.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    + "</div></div></div>",
                    unsafe_allow_html=True,
                )
                time.sleep(0.001)

        ts2 = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.messages.append({"role": "assistant", "content": acc.strip(), "ts": ts2})

        try:
            st.session_state.analysis = analyze_text_json(
                user_input.strip(),
                lang_code=LANGUAGE_MAP[st.session_state.chat_language]["code"],
                level=LEVELS[st.session_state.level_label],
                provider=provider,
                max_tokens=256,
            )
        except Exception:
            pass

        st.rerun()


if __name__ == "__main__":
    main()
