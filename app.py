"""정책 설득 시뮬레이터 — 시나리오별 3단계 설득·협상
실행: python -m streamlit run app.py
"""
import json
import os
import re
import time
import uuid

import streamlit as st

from scenarios import SCENARIOS
from scenarios.common import system_prompt

st.set_page_config(page_title="행정과정 시뮬레이션", page_icon="🏛️", layout="wide")


# ── 설정 ────────────────────────────────────────────────
def secret(name, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)


DEFAULT_MODEL = secret("MODEL", "claude-opus-5-5")
ACCESS_CODE = secret("ACCESS_CODE")


SESSION_CAP = 60     # 공개 키로 한 접속자가 쓸 수 있는 호출 수
SHARED_CAP = 1500    # 공개 한 번에 전체 접속자가 쓸 수 있는 호출 수


@st.cache_resource
def shared():
    """발표자가 공개한 키. 서버 메모리에만 있고, 시간이 지나거나 앱이 재시작되면 사라진다."""
    return {"key": "", "model": "", "until": 0.0, "calls": 0, "owner": ""}


def shared_left():
    sh = shared()
    if sh["key"] and (time.time() >= sh["until"] or sh["calls"] >= SHARED_CAP):
        sh.update(key="", until=0.0, owner="")
    return max(0, int((sh["until"] - time.time()) // 60) + 1) if sh["key"] else 0


def creds():
    s = st.session_state
    if s.get("api_key"):
        return s["api_key"], s["model"], False
    if shared_left():
        return shared()["key"], shared()["model"], True
    return "", "", False


class LimitReached(Exception):
    pass


def client():
    """키는 서버 메모리에만 둔다. 파일이나 저장소에 기록하지 않는다."""
    key, model, is_shared = creds()
    s = st.session_state
    if is_shared:
        if s.get("shared_calls", 0) >= SESSION_CAP:
            raise LimitReached()
        s["shared_calls"] = s.get("shared_calls", 0) + 1
        shared()["calls"] += 1
    if s.get("_client_key") != key:
        import anthropic
        s["_client"] = anthropic.Anthropic(api_key=key)
        s["_client_key"] = key
    return s["_client"], model


def ask(system, messages, max_tokens=700):
    c, model = client()
    r = c.messages.create(model=model, max_tokens=max_tokens, system=system, messages=messages)
    return "".join(b.text for b in r.content if b.type == "text").strip()


def stream(system, messages):
    c, model = client()
    with c.messages.stream(model=model, max_tokens=700, system=system, messages=messages) as s:
        yield from s.text_stream


def explain(e):
    n = type(e).__name__
    if n == "LimitReached":
        return "이 창에서 쓸 수 있는 실시간 대화 횟수를 모두 썼습니다. 예시 재생 모드로 계속 볼 수 있습니다."
    return {"AuthenticationError": "API 키가 올바르지 않습니다. 사이드바에서 다시 입력하세요.",
            "NotFoundError": "모델 이름을 찾을 수 없습니다. 사이드바의 모델 이름을 확인하세요.",
            "PermissionDeniedError": "이 키로는 해당 모델을 쓸 수 없습니다.",
            "RateLimitError": "호출 한도에 걸렸습니다. 잠시 뒤 다시 시도하세요."}.get(n, f"AI 호출에 실패했습니다. ({n})")


# ── 상태 ────────────────────────────────────────────────
ss = st.session_state
ss.setdefault("sc", 0)
ss.setdefault("phase", "brief")      # brief → chat → result → final
ss.setdefault("stage", 0)
ss.setdefault("chats", {})           # key → [{"role","content"}]
ss.setdefault("results", {})         # key → {"decision":…, "coach":…}
ss.setdefault("api_key", "")
ss.setdefault("model", DEFAULT_MODEL)
ss.setdefault("sid", uuid.uuid4().hex)
API_KEY, _, USING_SHARED = creds()
ss.setdefault("demo", not API_KEY)
if not API_KEY:
    ss.demo = True
ss.setdefault("demo_pos", 0)
ss.setdefault("authed", not ACCESS_CODE)


def reset():
    for k in ("phase", "stage", "chats", "results", "demo_pos"):
        ss.pop(k, None)


def _on_pick():
    reset()
    ss.sc = ss.sc_pick


def scenario_picker():
    ss.setdefault("sc_pick", ss.sc)
    st.selectbox("시나리오", range(len(SCENARIOS)), key="sc_pick", on_change=_on_pick,
                 format_func=lambda i: SCENARIOS[i]["name"])


def _on_demo():
    ss.demo = ss.demo_toggle
    reset()


def _on_key():
    ss.api_key = ss.key_input.strip()
    ss.demo = not ss.api_key
    reset()


def _stop_share():
    sh = shared()
    if sh["key"] and sh["key"] == ss.api_key:
        sh.update(key="", until=0.0, owner="")


def _clear_key():
    _stop_share()
    ss.api_key = ""
    ss.key_input = ""
    ss.demo = True
    reset()


def _start_share():
    shared().update(key=ss.api_key, model=ss.model, until=time.time() + ss.share_min * 60, calls=0, owner=ss.sid)


def key_panel():
    with st.expander("실시간 AI 설정", expanded=not ss.api_key):
        st.text_input("Claude API 키", type="password", key="key_input", on_change=_on_key,
                      placeholder="sk-ant-...", help="입력한 키는 이 브라우저 창에서만 쓰이고 저장되지 않습니다. 창을 닫거나 새로 고치면 사라집니다.")
        st.text_input("모델", key="model")
        if ss.api_key:
            st.success("키 입력됨 · 실시간 모드 사용 가능")
            sh = shared(); left = shared_left()
            if left and sh["key"] == ss.api_key:
                st.warning(f"다른 접속자에게 공개 중 · 약 {left}분 남음 · {sh['calls']}회 사용됨")
                st.button("공개 중지", on_click=_stop_share, type="primary")
            else:
                st.selectbox("공개 시간(분)", [10, 20, 30, 60], index=1, key="share_min")
                st.button("다른 접속자에게 실시간 모드 열기", on_click=_start_share,
                          help="정한 시간 동안 이 주소에 접속한 모든 사람이 내 키로 실시간 대화를 할 수 있습니다.")
            st.button("키 지우기", on_click=_clear_key)
        else:
            st.caption("키가 없으면 예시 재생(시연) 모드로만 동작합니다.")
    if USING_SHARED:
        st.info(f"발표자가 실시간 모드를 열었습니다 · 약 {shared_left()}분 남음."
                + (" '예시 재생 모드'를 끄면 직접 대화할 수 있습니다." if ss.demo else " 직접 입력해 대화할 수 있습니다."))


# ── 접속코드 ────────────────────────────────────────────
if not ss.authed:
    st.title("🏛️ 정책 설득 시뮬레이터")
    code = st.text_input("접속코드", type="password")
    if code and code == ACCESS_CODE:
        ss.authed = True
        st.rerun()
    elif code:
        st.error("접속코드가 맞지 않습니다.")
    st.stop()

if SCENARIOS[ss.sc].get("kind") == "arrow":
    import arrow_demo
    with st.sidebar:
        scenario_picker()
        key_panel()
    arrow_demo.render(ask if API_KEY else None)
    st.stop()

SC = SCENARIOS[ss.sc]
STAGES, DEMO, MAX_TURNS, CASE = SC["stages"], SC["demo"], SC["max_turns"], SC["case"]


def transcript(stage):
    who = {"user": "과장(사용자)", "assistant": stage["who"]}
    return "\n\n".join(f"{who[m['role']]}: {m['content']}" for m in ss.chats[stage["key"]])


def carry_text():
    lines = []
    for s in STAGES[:ss.stage]:
        d = ss.results[s["key"]]["decision"]
        cond = "; ".join(d.get("conditions", [])) or "없음"
        lines.append(f"- {s['title']}: {d['decision']}, {d['outcome']}. 조건: {cond}")
    return "\n".join(lines)


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def decide(stage):
    if ss.demo:
        return DEMO[stage["key"]]["decision"], DEMO[stage["key"]]["coach"]
    sys_p = system_prompt(SC, stage, carry_text())
    msg = f"[대화록]\n{transcript(stage)}\n\n{SC['judge']}"
    for _ in range(2):
        try:
            d = parse_json(ask(sys_p, [{"role": "user", "content": msg}], 1200))
            d["outcome"] = str(d.get("outcome", ""))
            break
        except Exception:
            d = None
    if d is None:
        d = {"decision": "결정 실패", "outcome": "-", "criteria": [], "conditions": [],
             "statement": "결정문을 만들지 못했습니다. 다시 시도해 주세요."}
    report = (f"[단계] {stage['title']} / 목표: {stage['goal']}\n[대화록]\n{transcript(stage)}\n\n"
              f"[결과]\n{json.dumps(d, ensure_ascii=False)}")
    coach = ask(SC["coach_prompt"], [{"role": "user", "content": report}], 600)
    return d, coach


# ── 사이드바 ────────────────────────────────────────────
with st.sidebar:
    scenario_picker()
    st.header("진행 상황")
    for i, s in enumerate(STAGES):
        r = ss.results.get(s["key"])
        if r:
            d = r["decision"]
            st.markdown(f"✅ **{s['title']}**  \n{d['decision']} · {d['outcome']}")
        elif i == ss.stage and ss.phase != "brief":
            st.markdown(f"▶️ **{s['title']}**")
        else:
            st.markdown(f"◻️ {s['title']}")
    st.divider()
    if API_KEY:
        ss.demo_toggle = ss.demo
        st.toggle("예시 재생 모드", key="demo_toggle", on_change=_on_demo,
                  help="사전에 작성한 예시 대화를 재생합니다. AI를 호출하지 않습니다.")
    key_panel()
    with st.expander("사례 자료", expanded=False):
        st.text(CASE)
    if st.button("처음부터 다시"):
        reset()
        st.rerun()

st.title("🏛️ 정책 설득 시뮬레이터")
st.caption(SC["caption"])
if ss.demo:
    st.warning("예시 재생 모드입니다. 아래 대화는 사전에 작성한 예시이며 AI가 실시간으로 생성한 것이 아닙니다.")

# ── 1. 임무 ─────────────────────────────────────────────
if ss.phase == "brief":
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader(SC["role"])
        with st.chat_message("assistant", avatar="👔"):
            st.markdown(SC["briefing"])
        if st.button("1단계 시작", type="primary"):
            ss.phase = "chat"
            st.rerun()
    with c2:
        st.subheader("사례 자료")
        st.text(CASE)
    st.stop()

# ── 4. 최종 ─────────────────────────────────────────────
if ss.phase == "final":
    st.subheader("최종 결과")
    cols = st.columns(len(STAGES) + 1)
    cols[0].caption(SC["target"][0])
    cols[0].markdown(f"#### {SC['target'][1]}")
    for c, s in zip(cols[1:], STAGES):
        d = ss.results[s["key"]]["decision"]
        c.caption(s["title"].split("·")[1].strip())
        c.markdown(f"#### {d['outcome']}")
        c.caption(d["decision"])
    md = [f"# {SC['name']} 기록\n\n{'(예시 재생 모드)' if ss.demo else ''}\n"]
    for s in STAGES:
        r = ss.results[s["key"]]
        d = r["decision"]
        with st.expander(f"{s['title']} — {d['decision']} · {d['outcome']}"):
            for c in d.get("criteria", []):
                st.markdown(f"{'✅' if c['met'] else '❌'} **{c['name']}** — {c['comment']}")
            st.markdown(f"**{SC['coach']} 피드백** {r['coach']}")
        md.append(f"## {s['title']}\n\n{transcript(s)}\n\n**결과** {d['decision']} · {d['outcome']}\n\n"
                  + "\n".join(f"- [{'O' if c['met'] else 'X'}] {c['name']}: {c['comment']}" for c in d.get("criteria", []))
                  + "\n\n**조건** " + ("; ".join(d.get("conditions", [])) or "없음")
                  + f"\n\n**{SC['coach']} 피드백** {r['coach']}\n")
    st.download_button("대화록과 평가 내려받기", "\n".join(md), f"{SC['id']}_기록.md", "text/markdown")
    if SC["epilogue"]:
        st.subheader("실제로는 어떻게 되었나")
        st.markdown(SC["epilogue"])
    st.stop()

# ── 2·3. 설득과 결과 ────────────────────────────────────
stage = STAGES[ss.stage]
key = stage["key"]
chat = ss.chats.setdefault(key, [])
used = sum(m["role"] == "user" for m in chat)

st.subheader(stage["title"])
a, b, c = st.columns([3, 3, 1])
a.markdown(f"**상대** {stage['who']}  \n**시점** {stage['when']}")
b.markdown(f"**목표** {stage['goal']}" + (f"  \n**이전 결과** {carry_text().splitlines()[-1][2:]}" if ss.stage else ""))
c.metric("남은 발언", f"{MAX_TURNS - used}")

with st.chat_message("assistant", avatar="🧑‍💼"):
    st.markdown(stage["opening"])
for m in chat:
    with st.chat_message(m["role"], avatar="🧑‍💼" if m["role"] == "assistant" else "🙋"):
        st.markdown(m["content"])

if ss.phase == "chat":
    demo_turns = DEMO[key]["turns"]
    done = (ss.demo and ss.demo_pos >= len(demo_turns)) or (not ss.demo and used >= MAX_TURNS)
    if ss.demo and not done:
        if st.button("다음 발언 보기 ▶", type="primary"):
            for role, text in demo_turns[ss.demo_pos:ss.demo_pos + 2]:
                chat.append({"role": role, "content": text})
            ss.demo_pos += 2
            st.rerun()
    if not ss.demo and not done:
        if text := st.chat_input("설득 발언을 입력하세요"):
            chat.append({"role": "user", "content": text})
            with st.chat_message("user", avatar="🙋"):
                st.markdown(text)
            api_msgs = [{"role": "assistant", "content": stage["opening"]}] + chat
            api_msgs = [{"role": "user", "content": "(과장이 사무실에 들어온다.)"}] + api_msgs
            with st.chat_message("assistant", avatar="🧑‍💼"):
                try:
                    reply = st.write_stream(stream(system_prompt(SC, stage, carry_text()), api_msgs))
                except Exception as e:
                    chat.pop()
                    st.error(explain(e))
                    st.stop()
            chat.append({"role": "assistant", "content": reply})
            st.rerun()
    if done:
        st.info("발언 기회를 모두 썼습니다. 결정을 요청하세요.")
    if used >= 1 and st.button("결정 요청", type="primary" if done else "secondary"):
        with st.spinner(f"상대가 결정을 내리고, {SC['coach']}에게 결과를 보고하는 중입니다."):
            try:
                d, coach = decide(stage)
            except Exception as e:
                st.error(explain(e))
                st.stop()
        ss.results[key] = {"decision": d, "coach": coach}
        ss.phase = "result"
        st.rerun()

if ss.phase == "result":
    r = ss.results[key]
    d = r["decision"]
    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown(f"### 결정: {d['decision']} · {d['outcome']}")
        with st.chat_message("assistant", avatar="🧑‍💼"):
            st.markdown(d.get("statement", ""))
        for cnd in d.get("conditions", []):
            st.markdown(f"- {cnd}")
        st.markdown("**판단기준(대화 중에는 비공개)**")
        for cr in d.get("criteria", []):
            st.markdown(f"{'✅' if cr['met'] else '❌'} **{cr['name']}** — {cr['comment']}")
    with right:
        st.markdown(f"### {SC['coach']}의 피드백")
        with st.chat_message("assistant", avatar="👔"):
            st.markdown(r["coach"])
    last = ss.stage == len(STAGES) - 1
    if st.button("최종 결과 보기" if last else "다음 단계로", type="primary"):
        if last:
            ss.phase = "final"
        else:
            ss.stage += 1
            ss.phase = "chat"
            ss.demo_pos = 0
        st.rerun()
