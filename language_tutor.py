# -*- coding: utf-8 -*-
"""
Streamlit Language Tutor — WeChat-like UI (정교한 스타일) + 분석 사이드바
Python 3.10+ / Streamlit 1.33+
옵션: openai>=1.40.0, anthropic>=0.34.0
"""

import os
import json
import time
import typing as T
from datetime import datetime

import streamlit as st

# =========================
# 기본 설정
# =========================
APP_TITLE = "언어 학습 챗봇"
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
LEVELS = {"초급": "beginner", "중급": "intermediate", "고급": "advanced"}

# =========================
# 모델 백엔드 (선택)
# =========================
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
    OpenAI/Anthropic 설치 시 스트리밍, 미설치 시 mock로 빠른 데모 동작
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

    # mock: 매우 빠른 로컬 데모
    user_last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    mock = f"네, 확인했습니다. 간단히 계속해 보겠습니다.\n\n원문: {user_last[:90]}"
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
    피드백/단어·병음/문법/노트 JSON만 반환하도록 요청.
    백엔드 없으면 간단한 대체값 반환.
    """
    sys = "You are a precise language-teaching assistant. Return STRICT JSON only."
    prompt = f"""
언어 코드: {lang_code}
학습자 수준: {level}
다음 스키마로 JSON만 출력하십시오.

{{
  "feedback": "학습자 발화에 대한 간단한 정교 피드백",
  "words": [{{"term": "단어", "pinyin": "가능 시 로마자/병음", "meaning": "국문 뜻"}}],
  "grammar": "핵심 문법/표현 설명",
  "notes": "추가 학습 노트"
}}

분석 대상:
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

    return {
        "feedback": "어순은 적절합니다. 조사/전치사 위치에 유의하십시오.",
        "words": [
            {"term": "你好", "pinyin": "nǐ hǎo", "meaning": "안녕하세요"},
            {"term": "明天", "pinyin": "míngtiān", "meaning": "내일"},
        ],
        "grammar": "인사 표현과 의문문 어순 확인.",
        "notes": "주제 확장 어휘 3개 이상으로 문장을 재구성해 보십시오.",
    }

# =========================
# 상태 관리
# =========================
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

# =========================
# WeChat 스타일 CSS
# =========================
def inject_wechat_css():
    st.markdown(
        """
<style>
/* 컨테이너 넓이 및 배경 */
.block-container {padding-top:0; padding-bottom:0; max-width: 860px;}
body {background:#ededed;}
header {visibility:hidden;}

/* 상단 네비게이션 바 (WeChat 유사) */
.wx-nav {
  position: sticky; top: 0; z-index: 10;
  height: 54px; display:flex; align-items:center; justify-content:space-between;
  padding: 0 12px; background:#f7f7f7; border-bottom:1px solid #e6e6e6;
  font-weight:600;
}
.wx-nav .left, .wx-nav .right {display:flex; gap:12px; align-items:center;}
.wx-nav .title {font-size:16px;}

/* 채팅 프레임 (모바일 비율) */
.phone-frame {
  margin: 10px auto 0 auto; width: 420px; max-width: 92vw;
  background:#eaeaea; border:1px solid #d8d8d8; border-radius:28px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
  overflow:hidden;
}
.phone-header {
  height: 44px; background:#f6f6f6; border-bottom:1px solid #e5e5e5;
  display:flex; align-items:center; justify-content:center; font-size:13px; color:#777;
}

/* 채팅 영역 */
.chat-wrap {
  height: 62vh; max-height: 680px; overflow:auto;
  padding: 10px 12px 12px 12px; background:#ececec;
}

/* 버블 공통 */
.row {display:flex; align-items:flex-end; margin:8px 0;}
.row.left  {justify-content:flex-start;}
.row.right {justify-content:flex-end;}

.avatar {
  width: 34px; height:34px; border-radius:6px; background:#d4d4d4;
  display:flex; align-items:center; justify-content:center; font-size:18px; margin:0 6px;
}

/* 버블(좌: 회색, 우: 연녹색) */
.bubble {
  position:relative; max-width: 72%; padding: 9px 12px; font-size:14px; line-height: 1.42;
  border-radius:10px; word-wrap:break-word; white-space:pre-wrap;
}
.bubble.bot {
  background:#ffffff; border:1px solid #e7e7e7; color:#111;
  border-top-left-radius:4px;
}
.bubble.user {
  background:#95ec69; color:#0b0b0b;
  border-top-right-radius:4px;
}

/* 꼬리 (삼각형) */
.bubble.bot:after {
  content:""; position:absolute; left:-6px; bottom:8px;
  border-width:6px; border-style:solid;
  border-color:transparent #fff transparent transparent;
  filter: drop-shadow(-1px 0 0 #e7e7e7);
}
.bubble.user:after {
  content:""; position:absolute; right:-6px; bottom:8px;
  border-width:6px; border-style:solid;
  border-color:transparent transparent transparent #95ec69;
}

/* 타임스탬프 */
.meta {font-size:11px; color:#8a8f98; margin:4px 8px;}

/* 입력 바 */
.input-bar {
  display:flex; align-items:center; gap:8px;
  padding: 8px; background:#f7f7f7; border-top:1px solid #e5e5e5;
}
.input-box {
  flex:1; background:#fff; border:1px solid #e6e6e6; border-radius:22px; padding:8px 12px;
}
.icon-btn {
  width:36px; height:36px; display:flex; align-items:center; justify-content:center;
  background:#fff; border:1px solid #e6e6e6; border-radius:50%;
}
.stTextInput>div>div>input {border:none !important;}

/* 사이드바 타이포 */
.sidebar-title {font-weight:700; margin-bottom:6px;}
</style>
        """,
        unsafe_allow_html=True,
    )

# =========================
# UI 렌더
# =========================
def render_row(role: str, content: str, ts: str, show_avatar: bool = True):
    side = "right" if role == "user" else "left"
    bubble_cls = "bubble user" if role == "user" else "bubble bot"
    avatar = "🙂" if role == "user" else "🧑‍🏫"
    st.markdown(
        f"""
<div class="row {side}">
  {'<div class="avatar">'+avatar+'</div>' if side=='left' and show_avatar else ''}
  <div>
    <div class="{bubble_cls}">{content}</div>
    <div class="meta">{ts}</div>
  </div>
  {'<div class="avatar">'+avatar+'</div>' if side=='right' and show_avatar else ''}
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

# =========================
# 메인
# =========================
def main():
    ensure_state()
    st.set_page_config(page_title=f"{APP_TITLE}", layout="centered")
    inject_wechat_css()

    # ---------- 사이드바 ----------
    with st.sidebar:
        flag = LANGUAGE_MAP[st.session_state.chat_language]["flag"]
        st.markdown(f"<div class='sidebar-title'>{flag} {APP_TITLE}</div>", unsafe_allow_html=True)
        st.caption("분석 · 저장 · 설정")

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
        for w in analysis.get("words", [])[:40]:
            term = w.get("term", "")
            pinyin = w.get("pinyin", "")
            meaning = w.get("meaning", "")
            st.markdown(f"- {term} ({pinyin}) — {meaning}")

        st.markdown("**3) 문법 설명**")
        st.write(analysis.get("grammar", "분석 결과 없음"))

        st.markdown("**4) 대화 저장**")
        payload = download_payload(st.session_state.messages, lang_label, level_label)
        st.download_button("JSON 다운로드", data=payload.encode("utf-8"), file_name="conversation.json")
        txt = "\n".join([f"[{m['role']}] {m['content']}" for m in st.session_state.messages])
        st.download_button("텍스트 다운로드", data=txt.encode("utf-8"), file_name="conversation.txt")

    # ---------- 중앙(폰 프레임) ----------
    # 상단 네비게이션 바
    st.markdown(
        f"""
<div class="wx-nav">
  <div class="left">＜</div>
  <div class="title">{LANGUAGE_MAP[st.session_state.chat_language]['label']} · {st.session_state.level_label}</div>
  <div class="right">···</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="phone-frame">', unsafe_allow_html=True)
    st.markdown('<div class="phone-header">대화</div>', unsafe_allow_html=True)

    # 채팅 영역
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    # 연속 동일 화자 아바타 최소화
    prev_role = None
    for msg in st.session_state.messages:
        show_avatar = (msg["role"] != prev_role)
        safe = (
            msg["content"]
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        render_row(msg["role"], safe, msg["ts"], show_avatar=show_avatar)
        prev_role = msg["role"]
    st.markdown("</div>", unsafe_allow_html=True)

    # 입력 바
    with st.container():
        c1, c2, c3, c4 = st.columns([1, 9, 1, 1])
        with c1:
            st.markdown('<div class="icon-btn">＋</div>', unsafe_allow_html=True)
        with c2:
            user_input = st.text_input("", key="chat_input", label_visibility="collapsed", placeholder="메시지 입력…")
        with c3:
            st.markdown('<div class="icon-btn">🙂</div>', unsafe_allow_html=True)
        with c4:
            send = st.button("⮕", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)  # phone-frame 종료

    # ---------- 전송 처리 ----------
    if send and user_input.strip():
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.messages.append({"role": "user", "content": user_input.strip(), "ts": ts})

        system_prompt = (
            "You are a concise, corrective language partner. "
            "Reply in the target language. Keep responses short (<= 3 sentences)."
        )
        msgs = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages:
            msgs.append({"role": m["role"], "content": m["content"]})

        # 스트리밍 표시: 리스트에 임시 추가 없이 placeholder로만 미리보기 후 최종 1회 기록
        with st.spinner("응답 생성 중…"):
            acc = ""
            ph = st.empty()
            for ck in call_model_stream(
                messages=msgs, provider=provider, temperature=temp, max_tokens=max_tok
            ):
                acc += ck
                safe_acc = acc.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                ph.markdown(
                    f"""
<div class="phone-frame" style="border:none; box-shadow:none; margin:0; background:transparent;">
  <div class="chat-wrap" style="height:auto; max-height:none; background:transparent; padding:0;">
    <div class="row left">
      <div>
        <div class="bubble bot">{safe_acc}</div>
      </div>
    </div>
  </div>
</div>
                    """,
                    unsafe_allow_html=True,
                )
                time.sleep(0.002)

        ph.empty()
        ts2 = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.messages.append({"role": "assistant", "content": acc.strip(), "ts": ts2})

        # 최신 사용자 발화 자동 분석 캐시
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
