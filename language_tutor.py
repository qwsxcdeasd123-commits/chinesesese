# -*- coding: utf-8 -*-
"""
Streamlit MobileLanguageTutor — WeChat 스타일 풀버전 (Anthropic 시스템 롤 수정)
기능: 언어/수준 선택, 목표 표시, 번역 토글, 중국어 상세 분석, 대화 저장, 타이핑 인디케이터
개선: 이모지/상단 ⋯ 버튼으로 드로어 토글, Anthropic 스트리밍/비스트리밍 폴백, 안전 인덱싱
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
# 설정 및 상수
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

GOALS_BY_LANGUAGE = {
    "chinese":  ["HSK 5급 필수 어휘 마스터","복잡한 문장 구조 이해","성어 및 관용 표현 학습"],
    "spanish":  ["불규칙 동사 활용","음식 어휘 확장"],
    "french":   ["명사의 성 구분","과거시제 활용"],
    "german":   ["격변화 이해","분리동사 학습"],
    "japanese": ["히라가나 읽기","경어 표현"],
    "italian":  ["동사 시제","전치사 결합"],
    "korean":   ["높임법 익히기","어미 활용 확장"],
}

# =========================
# 모델 백엔드 선택(옵션)
# =========================
def _has_openai():
    try:
        import openai  # noqa: F401
        return bool(os.environ.get("OPENAI_API_KEY"))
    except Exception:
        return False

def _has_anthropic():
    try:
        import anthropic  # noqa: F401
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    except Exception:
        return False

def _split_system_and_messages(messages: T.List[dict]):
    """Anthropic 전용: system 프롬프트와 user/assistant만 분리."""
    system_prompt = ""
    filtered = []
    for m in messages:
        role = m.get("role")
        if role == "system" and not system_prompt:
            system_prompt = m.get("content", "")
        elif role in ("user", "assistant"):
            filtered.append({"role": role, "content": m.get("content", "")})
        # 기타 롤은 무시
    return system_prompt, filtered

def stream_reply(messages: T.List[dict], temperature: float = 0.2, max_tokens: int = 400):
    """
    채팅 응답 스트리밍(선택: OpenAI/Anthropic). 없으면 mock.
    messages: [{"role": "user"/"assistant"/"system", "content": "..."}]
    """
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
            # 비스트리밍 폴백
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                )
                text = (resp.choices[0].message.content or "").strip()
                if text:
                    yield text
                    return
            except Exception:
                pass  # mock 폴백 진행

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

        system_prompt, filtered = _split_system_and_messages(messages)

        try:
            with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or None,
                messages=filtered,
            ) as s:
                for text in s.text_stream:
                    if text:
                        yield text
            return
        except Exception:
            # 비스트리밍 폴백
            try:
                resp = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt or None,
                    messages=filtered,
                )
                text = "".join([b.text for b in resp.content if hasattr(b, "text")]).strip()
                if text:
                    yield text
                    return
            except Exception:
                pass  # mock 폴백 진행

    # mock
    user_last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    mock = f"你好！很高兴认识你。今天想聊什么？\n\n(원문 미러) {user_last[:120]}"
    for tok in mock.split():
        yield tok + " "
        time.sleep(0.01)

def translate_to_korean(text: str, source_lang_name: str) -> str:
    """어시스턴트 메시지 한국어 번역. 백엔드 없으면 간단 치환."""
    provider = "mock"
    if _has_openai():
        provider = "openai"
    elif _has_anthropic():
        provider = "anthropic"

    prompt = f"다음 {source_lang_name} 텍스트를 한국어로 자연스럽게 번역하세요. 번역문만 출력:\n\n{text}"

    if provider == "openai":
        import openai
        client = openai.OpenAI()
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role":"user","content": prompt}],
                temperature=0.0,
                max_tokens=600,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception:
            return "(번역 실패)"

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        try:
            resp = client.messages.create(
                model=model, max_tokens=600, temperature=0.0,
                messages=[{"role":"user","content": prompt}],
            )
            return "".join([b.text for b in resp.content if hasattr(b, "text")]).strip()
        except Exception:
            return "(번역 실패)"

    return f"(번역-모의) {text}"

def analyze_chinese_json(text: str) -> dict:
    """중국어 상세 분석(JSON). 백엔드 없으면 예시 구조 반환."""
    provider = "mock"
    if _has_openai():
        provider = "openai"
    elif _has_anthropic():
        provider = "anthropic"

    if provider == "openai":
        import openai
        client = openai.OpenAI()
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        sys = "You are a precise language-teaching assistant. Return STRICT JSON only."
        user = f"""다음 중국어를 분석하세요. 순수 JSON만 출력:

{{
  "pinyin": "병음",
  "words": [{{"chinese": "단어", "pinyin": "병음", "meaning": "뜻"}}],
  "grammar": "문법 설명",
  "vocabulary": ["어휘 노트"],
  "notes": "추가 설명"
}}

텍스트: {text}
"""
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[{"role":"system","content":sys},{"role":"user","content":user}],
                temperature=0.1, max_tokens=700,
            )
            raw = (r.choices[0].message.content or "").strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
        except Exception:
            return {}

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        user = f"""다음 중국어를 분석하세요. 순수 JSON만 출력:

{{
  "pinyin": "병음",
  "words": [{{"chinese": "단어", "pinyin": "병음", "meaning": "뜻"}}],
  "grammar": "문법 설명",
  "vocabulary": ["어휘 노트"],
  "notes": "추가 설명"
}}

텍스트: {text}
"""
        try:
            r = client.messages.create(
                model=model, max_tokens=700, temperature=0.1,
                messages=[{"role":"user","content": user}],
            )
            raw = "".join([b.text for b in r.content if hasattr(b, "text")]).strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
        except Exception:
            return {}

    # mock
    return {
        "pinyin": "nǐ hǎo! hěn gāoxìng rènshi nǐ. jīntiān xiǎng liáo shénme?",
        "words": [
            {"chinese": "你好", "pinyin": "nǐ hǎo", "meaning": "안녕하세요"},
            {"chinese": "很",   "pinyin": "hěn",   "meaning": "매우"},
            {"chinese": "高兴", "pinyin": "gāoxìng","meaning": "기쁘다"},
            {"chinese": "认识", "pinyin": "rènshi", "meaning": "알다, 만나다"},
            {"chinese": "今天", "pinyin": "jīntiān","meaning": "오늘"},
            {"chinese": "想",   "pinyin": "xiǎng",  "meaning": "~하고 싶다"},
            {"chinese": "聊",   "pinyin": "liáo",   "meaning": "이야기하다"},
            {"chinese": "什么", "pinyin": "shénme", "meaning": "무엇"},
        ],
        "grammar": "간단한 인사문. ‘很高兴认识你’는 고정 결합의 예의 표현.",
        "vocabulary": ["‘认识’ HSK 3급 어휘","‘聊’ 구어체 빈출 동사"],
        "notes": "초면 인사에 적합.",
    }

# =========================
# 상태
# =========================
def ensure_state():
    st.session_state.setdefault("selectedLanguage", DEFAULT_LANGUAGE)
    st.session_state.setdefault("messages", [])  # [{id, role, content, translation, showTranslation, ts}]
    st.session_state.setdefault("input", "")
    st.session_state.setdefault("proficiencyLevel", "intermediate")
    st.session_state.setdefault("isLoading", False)
    st.session_state.setdefault("detailedAnalysis", None)
    st.session_state.setdefault("showAnalysis", False)
    st.session_state.setdefault("showDrawer", True)  # 드로어 표시 상태

def add_message(role: str, content: str):
    st.session_state.messages.append({
        "id": len(st.session_state.messages),
        "role": role,
        "content": content,
        "translation": None,
        "showTranslation": False,
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })

# =========================
# CSS
# =========================
def inject_wechat_css():
    st.markdown("""
<style>
.block-container {padding:0; max-width:860px;}
body {background:#ededed;}
header {visibility:hidden;}

/* 상단 헤더 */
.wx-top {
  position: sticky; top: 0; z-index: 10;
  background:#1aad19; color:#fff; height:52px; display:flex;
  align-items:center; justify-content:space-between;
  padding:0 12px; font-weight:600;
}
.wx-top .title {font-size:16px; text-align:center; width:100%;}

/* 폰 프레임 */
.phone {
  margin: 0 auto; width: 420px; max-width: 92vw;
  background:#e5e5e5; border:1px solid #d8d8d8; border-radius:28px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.06); overflow:hidden;
}
.phone-head {height: 36px; background:#f6f6f6; border-bottom:1px solid #e0e0e0;
  display:flex; align-items:center; justify-content:center; font-size:12px; color:#777;}
.chat {height: 62vh; max-height: 680px; overflow:auto; padding: 12px; background:#ececec;}
.row {display:flex; align-items:flex-end; margin:8px 0;}
.left {justify-content:flex-start;} .right{justify-content:flex-end;}
.avatar {width: 32px; height:32px; border-radius:6px; background:#d4d4d4;
  display:flex; align-items:center; justify-content:center; font-size:18px; margin:0 6px;}
.bubble {position:relative; max-width:72%; padding:9px 12px; font-size:14px;
  line-height:1.44; border-radius:10px; white-space:pre-wrap; word-wrap:break-word;}
.bot {background:#fff; border:1px solid #e7e7e7; color:#111; border-top-left-radius:4px;}
.user{background:#95ec69; color:#0b0b0b; border-top-right-radius:4px;}
.bot:after {
  content:""; position:absolute; left:-6px; bottom:8px; border-width:6px; border-style:solid;
  border-color:transparent #fff transparent transparent; filter: drop-shadow(-1px 0 0 #e7e7e7);
}
.user:after {
  content:""; position:absolute; right:-6px; bottom:8px; border-width:6px; border-style:solid;
  border-color:transparent transparent transparent #95ec69;
}
.meta {font-size:11px; color:#8a8f98; margin:4px 8px;}
.trans-tip {font-size:11px; color:#4f8ef7; border-top:1px solid #eef; margin-top:6px; padding-top:4px;}

/* 입력 바 */
.inputbar {display:flex; gap:8px; align-items:center; background:#f7f7f7; border-top:1px solid #e5e5e5; padding:8px;}
.inputwrap {flex:1; background:#fff; border:1px solid #e1e1e1; border-radius:20px; padding:6px 12px;}
.sendbtn {width:40px; height:40px; display:flex; align-items:center; justify-content:center; background:#1aad19; color:#fff; border-radius:50%;}

/* 사이드바 대체: 오른쪽 드로어 */
.drawer-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 9998;
}
.drawer {
  position: fixed; top: 0; right: 0; height: 100vh; width: min(86vw, 360px);
  background: #ffffff; border-left: 1px solid #e5e5e5; z-index: 9999;
  box-shadow: -8px 0 20px rgba(0,0,0,0.08);
  display: flex; flex-direction: column;
}
.drawer-header {
  height: 52px; display:flex; align-items:center; justify-content:space-between;
  padding: 0 12px; border-bottom:1px solid #eee; font-weight:600;
}
.drawer-body {
  padding: 12px; overflow: auto; height: calc(100vh - 52px);
}
.drawer-close-btn {
  border:1px solid #e5e5e5; border-radius: 18px; padding: 4px 10px; background:#fff;
}
.goal {background:#e8f4ff; border:1px solid #d8e9ff; padding:6px 8px; border-radius:8px; margin-bottom:6px; font-size:13px;}
</style>
    """, unsafe_allow_html=True)

# =========================
# 드로어(사이드바 대체) 내용
# =========================
def render_sidebar_content_in(container):
    with container:
        st.markdown(f"### {APP_TITLE}")
        st.caption("분석 · 저장 · 설정")

        # 언어/수준
        lang = st.selectbox(
            "언어", list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(st.session_state.selectedLanguage),
            format_func=lambda k: f"{LANGUAGES[k]['flag']} {LANGUAGES[k]['name']}",
            key="selectedLanguage",
        )
        st.selectbox(
            "숙련도", LEVELS,
            index=LEVELS.index(st.session_state.proficiencyLevel),
            format_func=lambda v: LEVEL_LABEL[v],
            key="proficiencyLevel",
        )

        # 학습 목표
        st.subheader("학습 목표")
        goals = GOALS_BY_LANGUAGE.get(lang, ["기초 문법","일상 어휘"])
        for g in goals:
            st.markdown(f"<div class='goal'>• {g}</div>", unsafe_allow_html=True)

        st.divider()

        # 중국어 상세 분석
        st.subheader("분석")
        last_user = next((m for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
        if st.button("내 마지막 발화 분석", key="analyze_btn_drawer"):
            if lang == "chinese" and last_user:
                try:
                    st.session_state.detailedAnalysis = analyze_chinese_json(last_user["content"])
                    st.session_state.showAnalysis = True
                except Exception:
                    st.session_state.detailedAnalysis = None
                    st.session_state.showAnalysis = False
            else:
                st.session_state.detailedAnalysis = None
                st.session_state.showAnalysis = False

        if st.session_state.detailedAnalysis and st.session_state.showAnalysis:
            da = st.session_state.detailedAnalysis
            with st.expander("상세 분석", expanded=True):
                if "pinyin" in da:
                    st.markdown("**병음**"); st.write(da.get("pinyin",""))
                if "words" in da and da["words"]:
                    st.markdown("**단어 (병음/뜻)**")
                    for w in da["words"]:
                        st.markdown(f"- {w.get('chinese','')} ({w.get('pinyin','')}) → {w.get('meaning','')}")
                if "grammar" in da:
                    st.markdown("**문법**"); st.write(da.get("grammar",""))
                if "vocabulary" in da:
                    st.markdown("**어휘 노트**")
                    for v in da.get("vocabulary",[]):
                        st.markdown(f"- {v}")
                if "notes" in da and da.get("notes"):
                    st.markdown("**추가 설명**"); st.write(da["notes"])

        st.divider()

        # 저장
        st.subheader("대화 저장")
        if st.session_state.messages:
            data = {
                "language": LANGUAGES[lang]["name"],
                "level": st.session_state.proficiencyLevel,
                "datetime": datetime.now().isoformat(timespec="seconds"),
                "messages": st.session_state.messages,
            }
            st.download_button(
                "JSON 다운로드",
                data=json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name=f"학습기록_{LANGUAGES[lang]['name']}_{datetime.now().date()}.json",
                key="download_json_drawer",
            )
            text_lines = []
            for m in st.session_state.messages:
                line = f"{'학습자' if m['role']=='user' else '튜터'}: {m['content']}"
                if m.get("translation"):
                    line += f"\n[번역] {m['translation']}"
                text_lines.append(line)
            st.download_button(
                "텍스트 다운로드",
                data="\n\n".join(text_lines).encode("utf-8"),
                file_name=f"학습기록_{LANGUAGES[lang]['name']}_{datetime.now().date()}.txt",
                key="download_txt_drawer",
            )
        else:
            st.caption("저장할 대화가 없습니다.")

# =========================
# UI 구성
# =========================
def chat_header():
    lang = st.session_state.selectedLanguage
    flag = LANGUAGES[lang]["flag"]
    label = LANGUAGES[lang]["name"]
    left, mid, right = st.columns([1,6,1])
    with left:
        st.markdown("<div>〈</div>", unsafe_allow_html=True)
    with mid:
        st.markdown(
            f"<div class='title'>{flag} {label} · {LEVEL_LABEL[st.session_state.proficiencyLevel]}</div>",
            unsafe_allow_html=True,
        )
    with right:
        if st.button("⋯", key="toggle_header"):
            st.session_state.showDrawer = not st.session_state.showDrawer

def render_message(msg: dict, idx: int, selected_lang_key: str):
    side = "right" if msg["role"] == "user" else "left"
    bubble_cls = "user" if msg["role"] == "user" else "bot"
    avatar = "🙂" if msg["role"] == "user" else "🧑‍🏫"

    if msg["role"] == "assistant":
        if msg.get("showTranslation") and msg.get("translation"):
            content = msg["translation"]
            tip = "<div class='trans-tip'>원문 보기</div>"
        else:
            content = msg["content"]
            tip = "<div class='trans-tip'>한국어 보기</div>"
    else:
        content = msg["content"]
        tip = ""

    safe = content.replace("&","&amp;").replace("<","&lt;").replace(">", "&gt;")
    st.markdown(
        f"""
<div class="row {side}">
  {'<div class="avatar">'+avatar+'</div>' if side=='left' else ''}
  <div>
    <div class="bubble {bubble_cls}">{safe}</div>
    <div class="meta">{msg['ts']}</div>
    {tip if msg['role']=='assistant' else ''}
  </div>
  {'<div class="avatar">'+avatar+'</div>' if side=='right' else ''}
</div>
        """,
        unsafe_allow_html=True,
    )

    # 번역 토글 버튼(안전 인덱싱)
    if msg["role"] == "assistant":
        col1, _, _ = st.columns([1,2,12])
        with col1:
            if st.button("번역", key=f"tr_{idx}"):
                if 0 <= idx < len(st.session_state.messages):
                    try:
                        if st.session_state.messages[idx].get("translation"):
                            st.session_state.messages[idx]["showTranslation"] = not st.session_state.messages[idx].get("showTranslation", False)
                        else:
                            tr = translate_to_korean(st.session_state.messages[idx]["content"], LANGUAGES[selected_lang_key]["name"])
                            st.session_state.messages[idx]["translation"] = tr or "(번역 결과 없음)"
                            st.session_state.messages[idx]["showTranslation"] = True
                    except Exception:
                        st.session_state.messages[idx]["translation"] = "(번역 실패)"
                        st.session_state.messages[idx]["showTranslation"] = True

def typing_indicator():
    st.markdown(
        """
<div class="row left">
  <div class="avatar">🧑‍🏫</div>
  <div class="bubble bot">
    입력 중…
  </div>
</div>
        """,
        unsafe_allow_html=True
    )

# =========================
# 메인
# =========================
def main():
    st.set_page_config(page_title=APP_TITLE, layout="centered")
    ensure_state()
    inject_wechat_css()

    # 상단 고정 헤더
    st.markdown('<div class="wx-top">', unsafe_allow_html=True)
    chat_header()
    st.markdown('</div>', unsafe_allow_html=True)

    # 휴대폰 프레임 시작
    st.markdown('<div class="phone">', unsafe_allow_html=True)
    st.markdown('<div class="phone-head">대화</div>', unsafe_allow_html=True)

    # 채팅 영역
    st.markdown('<div class="chat">', unsafe_allow_html=True)

    if not st.session_state.messages:
        lang = st.session_state.selectedLanguage
        flag = LANGUAGES[lang]["flag"]
        label = LANGUAGES[lang]["name"]
        st.markdown(
            f"""
<div style="text-align:center; padding:40px 0; color:#666;">
  <div style="font-size:64px; line-height:1.0;">{flag}</div>
  <div style="font-size:16px; margin-top:
