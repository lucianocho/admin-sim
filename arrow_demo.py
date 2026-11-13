"""애로우 불가능성 정리 시연 — 에이전트 3·4·5명.
선호 순위는 정리를 보여 주기 위해 설계한 것이며, 집계는 모두 코드가 계산한다(AI 호출 없음)."""
import pandas as pd
import streamlit as st

NAMES = {"A": "구조개혁", "B": "정책지원", "C": "문화변화", "D": "이민 확대"}
AV = {"경제학자": "📈", "사회학자": "👥", "정책전문가": "🏛️", "지자체 담당자": "🏙️", "청년 당사자": "🧑"}

CASES = {
    3: {
        "alts": "ABC",
        "agents": [
            ("경제학자", "ABC", "노동시장과 주거 구조를 바꾸지 않으면 지원금은 밑 빠진 독입니다."),
            ("사회학자", "CAB", "성평등과 일·생활 균형 문화가 먼저입니다. 돈만으로는 선택이 바뀌지 않습니다."),
            ("정책전문가", "BCA", "당장 체감되는 돌봄·현금 지원이 우선입니다. 구조개혁은 시간이 너무 걸립니다."),
        ],
    },
    4: {
        "alts": "ABCD",
        "agents": [
            ("경제학자", "ADBC", "구조개혁이 우선이고, 인구 문제는 이민으로 보완해야 합니다."),
            ("사회학자", "CADB", "문화가 바뀌어야 합니다. 그다음이 구조개혁입니다."),
            ("정책전문가", "BCAD", "정책지원이 가장 빠릅니다. 이민은 사회적 합의가 멉니다."),
            ("지자체 담당자", "BACD", "현장에서는 지원 사업이 가장 급합니다. 이민은 지역에서 감당하기 어렵습니다."),
        ],
    },
    5: {
        "alts": "ABCD",
        "agents": [
            ("경제학자", "ADBC", "구조개혁이 우선이고, 인구 문제는 이민으로 보완해야 합니다."),
            ("사회학자", "CADB", "문화가 바뀌어야 합니다. 그다음이 구조개혁입니다."),
            ("정책전문가", "BCAD", "정책지원이 가장 빠릅니다. 이민은 사회적 합의가 멉니다."),
            ("지자체 담당자", "BACD", "현장에서는 지원 사업이 가장 급합니다."),
            ("청년 당사자", "CABD", "일하면서 아이를 키울 수 있는 문화가 아니면 소용없습니다."),
        ],
        "liar": 2, "lie": "CBDA",
    },
}


# ── 집계 함수 ───────────────────────────────────────────
def prefers(rank, a, b):
    return rank.index(a) < rank.index(b)


def pair_count(prof, a, b):
    return sum(prefers(r, a, b) for r in prof)


def borda(prof, alts):
    sc = {a: 0 for a in alts}
    for r in prof:
        rr = [a for a in r if a in alts]
        for i, a in enumerate(rr):
            sc[a] += len(rr) - 1 - i
    return sc


def plurality(prof, alts):
    sc = {a: 0 for a in alts}
    for r in prof:
        sc[[a for a in r if a in alts][0]] += 1
    return sc


def winner(sc):
    m = max(sc.values())
    w = [a for a in sc if sc[a] == m]
    return w[0] if len(w) == 1 else None


def agenda_winner(prof, order):
    cur = order[0]
    for nxt in order[1:]:
        cur = cur if pair_count(prof, cur, nxt) > len(prof) / 2 else nxt
    return cur


def fmt(rank):
    return "  >  ".join(NAMES[a] for a in rank)


def score_chart(sc, label):
    df = pd.DataFrame({label: [sc[a] for a in sc]}, index=[NAMES[a] for a in sc])
    st.bar_chart(df, height=220)


def speak(agents):
    for name, rank, line in agents:
        with st.chat_message("assistant", avatar=AV[name]):
            st.markdown(f"**{name}**  {line}")
            st.caption(f"선호 순위: {fmt(rank)}")


# ── 3명: 순환과 의제 조작 ───────────────────────────────
def case3(step):
    c = CASES[3]; prof = [a[1] for a in c["agents"]]
    st.subheader("① 세 에이전트의 주장과 선호")
    speak(c["agents"])
    st.info("각 에이전트의 선호는 내부적으로 일관됩니다(이행성 충족).")
    if step < 2: return
    st.subheader("② 두 대안씩 다수결에 부치면")
    rows = []
    for a, b in [("A", "B"), ("B", "C"), ("C", "A")]:
        n = pair_count(prof, a, b)
        rows.append({"대결": f"{NAMES[a]} 대 {NAMES[b]}", "득표": f"{n} : {len(prof) - n}", "승자": NAMES[a if n > len(prof) / 2 else b]})
    l, r = st.columns([3, 2])
    l.table(pd.DataFrame(rows).set_index("대결"))
    r.graphviz_chart('digraph{rankdir=LR; node[shape=box,style="rounded,filled",fillcolor="#EFF2F8",color="#003A8E",fontname="sans-serif"];'
                     'edge[color="#003A8E"]; "구조개혁"->"정책지원"->"문화변화"->"구조개혁"}')
    st.error("구조개혁 > 정책지원 > 문화변화 > 구조개혁. 사회 전체의 선호가 순환해 1위를 정할 수 없습니다.")
    if step < 3: return
    st.subheader("③ 표결 순서를 정하는 사람이 결과를 정한다")
    rows = []
    for order in ["ABC", "BCA", "CAB"]:
        w = agenda_winner(prof, order)
        rows.append({"표결 순서": f"{NAMES[order[0]]} 대 {NAMES[order[1]]}, 승자가 {NAMES[order[2]]}와 대결", "최종 승자": NAMES[w]})
    st.table(pd.DataFrame(rows).set_index("표결 순서"))
    st.warning("같은 선호, 같은 다수결인데 의제 순서에 따라 세 대안이 모두 승자가 될 수 있습니다.")
    if step < 4: return
    st.subheader("④ 정리")
    st.success("개인은 합리적이어도 다수결로 합친 집단의 선호는 합리적이지 않을 수 있습니다. "
               "쌍대 다수결은 **이행성**을 지키지 못합니다.")


# ── 4명: 규칙에 따라 달라지는 승자, IIA 위반 ────────────
def case4(step):
    c = CASES[4]; prof = [a[1] for a in c["agents"]]; alts = c["alts"]
    st.subheader("① 네 에이전트의 주장과 선호")
    st.caption("대안에 '이민 확대'가 추가되고, 지자체 담당자가 참여합니다.")
    speak(c["agents"])
    if step < 2: return
    st.subheader("② 순환을 피하려고 집계 규칙을 바꾸면")
    p, b = plurality(prof, alts), borda(prof, alts)
    l, r = st.columns(2)
    with l:
        st.markdown(f"**최다득표제** (1순위 표만 계산) → 승자: **{NAMES[winner(p)]}**")
        score_chart(p, "1순위 득표")
    with r:
        st.markdown(f"**보르다 점수제** (순위마다 점수 부여) → 승자: **{NAMES[winner(b)]}**")
        score_chart(b, "보르다 점수")
    st.warning("선호는 그대로인데 집계 규칙에 따라 승자가 달라집니다.")
    if step < 3: return
    st.subheader("③ 보르다 점수제에서 '이민 확대'를 의제에서 빼면")
    rest = [a for a in alts if a != "D"]; b2 = borda(prof, rest)
    l, r = st.columns(2)
    with l:
        st.markdown(f"**이민 확대 포함** → 승자: **{NAMES[winner(b)]}**")
        score_chart(b, "보르다 점수")
    with r:
        st.markdown(f"**이민 확대 제외** → 승자: **{NAMES[winner(b2)]}**")
        score_chart(b2, "보르다 점수")
    n = pair_count(prof, "A", "B")
    st.error(f"구조개혁과 정책지원 사이의 선호는 아무도 바꾸지 않았습니다({n}명 대 {len(prof) - n}명 그대로). "
             "그런데 무관한 대안 하나를 빼자 둘의 순위가 뒤집혔습니다.")
    if step < 4: return
    st.subheader("④ 정리")
    st.success("보르다 점수제는 순환을 만들지 않지만 **무관한 대안으로부터의 독립성(IIA)** 을 지키지 못합니다. "
               "어떤 대안을 의제에 올리느냐로 결과를 바꿀 수 있습니다.")


# ── 5명: 전략적 허위 표명, 독재 ─────────────────────────
def case5(step):
    c = CASES[5]; prof = [a[1] for a in c["agents"]]; alts = c["alts"]
    st.subheader("① 다섯 에이전트의 주장과 선호")
    st.caption("청년 당사자가 참여합니다.")
    speak(c["agents"])
    if step < 2: return
    st.subheader("② 보르다 점수제로 집계")
    b = borda(prof, alts)
    st.markdown(f"승자: **{NAMES[winner(b)]}**")
    score_chart(b, "보르다 점수")
    if step < 3: return
    i, lie = c["liar"], c["lie"]; name, true, _ = c["agents"][i]
    st.subheader(f"③ {name}가 선호를 거짓으로 말하면")
    with st.chat_message("assistant", avatar=AV[name]):
        st.markdown(f"**{name}의 속마음**  내 1순위인 정책지원은 어차피 안 됩니다. 구조개혁이 되는 것보다는 문화변화가 낫습니다. "
                    "문화변화를 1순위로, 구조개혁을 꼴찌로 적어 내겠습니다.")
        st.caption(f"실제 선호: {fmt(true)}")
        st.caption(f"표명한 선호: {fmt(lie)}")
    p2 = list(prof); p2[i] = lie; b2 = borda(p2, alts)
    l, r = st.columns(2)
    with l:
        st.markdown(f"**정직하게 표명** → 승자: **{NAMES[winner(b)]}**")
        score_chart(b, "보르다 점수")
    with r:
        st.markdown(f"**거짓으로 표명** → 승자: **{NAMES[winner(b2)]}**")
        score_chart(b2, "보르다 점수")
    st.error(f"{name}는 거짓말로 자신에게 더 나은 결과({NAMES[winner(b2)]})를 얻었습니다. "
             "규칙이 정직한 선호 표명을 보장하지 못합니다.")
    if step < 4: return
    st.subheader("④ 그렇다면 모든 조건을 지키는 규칙은?")
    st.markdown(f"**독재 규칙**: 경제학자의 순위를 그대로 사회의 순위로 채택 → {fmt(prof[0])}")
    df = pd.DataFrame(
        {"이행성": ["✗ 순환 발생", "✓", "✓"], "파레토 원칙": ["✓", "✓", "✓"],
         "무관한 대안으로부터의 독립성": ["✓", "✗ 의제에 따라 역전", "✓"], "비독재성": ["✓", "✓", "✗"]},
        index=["쌍대 다수결", "보르다 점수제", "독재 규칙"])
    st.table(df)
    st.success("**애로우의 불가능성 정리(1951)**: 대안이 셋 이상일 때 이행성, 파레토 원칙, 무관한 대안으로부터의 독립성을 "
               "모두 지키는 집계 규칙은 독재뿐입니다.")
    st.info("**토론** 합의 실패는 참여자의 무능이나 악의 때문이 아니라 집계 구조에서 비롯됩니다. "
            "그래서 현실의 정책 결정은 투표가 아니라 협상, 중재, 의제 설정 규칙 같은 제도 설계에 의존합니다.")


# ── 실시간 모드: AI가 선호를 생성 ───────────────────────
import itertools
import json
import re

PERSONAS = {
    "경제학자": "노동시장, 주거비, 재정 효율을 중시하는 노동경제학자",
    "사회학자": "성평등, 가족 가치관, 일·생활 균형을 연구하는 가족사회학자",
    "정책전문가": "중앙부처에서 저출산 대책을 집행해 본 정책 실무 전문가",
    "지자체 담당자": "인구 감소 지역 군청의 인구정책 담당 팀장",
    "청년 당사자": "수도권에서 맞벌이를 하는 30대 초반 직장인",
}
DESC = {"A": "구조개혁(노동시장·주거 구조 개편)", "B": "정책지원(현금·돌봄 서비스 확대)",
        "C": "문화변화(성평등·일생활균형 문화 확산)", "D": "이민 확대(외국 인력·이민 수용)"}


def ask_rank(ask, name, alts):
    opts = "\n".join(f"- {DESC[a]}" for a in alts)
    system = (f"당신은 {PERSONAS[name]}이다. 저출산 대책의 우선순위를 정하는 정부 위원회에 참석했다. "
              "자신의 전문성과 처지에서 솔직하게 판단한다. 다른 위원의 눈치를 보지 않는다.")
    user = (f"다음 대안을 가장 우선해야 할 것부터 순서대로 모두 나열하라.\n{opts}\n\n"
            'JSON만 출력한다. 형식: {"ranking": ["' + '", "'.join(NAMES[a] for a in alts) + '"], "reason": "한 문장"}\n'
            "ranking에는 위 대안의 이름(괄호 앞 단어)을 정확히 한 번씩 쓴다.")
    inv = {NAMES[a]: a for a in alts}
    for _ in range(2):
        try:
            d = json.loads(re.search(r"\{.*\}", ask(system, [{"role": "user", "content": user}], 300), re.S).group(0))
            rank = "".join(inv[x.strip()] for x in d["ranking"])
            if sorted(rank) == sorted(alts):
                return rank, str(d.get("reason", ""))
        except Exception:
            pass
    return None, None


def analyze(prof, alts):
    n = len(prof); out = {}
    wins = {a: sum(pair_count(prof, a, b) > n / 2 for b in alts if b != a) for a in alts}
    out["condorcet"] = next((a for a in alts if wins[a] == len(alts) - 1), None)
    cyc = None
    for x, y, z in itertools.permutations(alts, 3):
        if pair_count(prof, x, y) > n / 2 and pair_count(prof, y, z) > n / 2 and pair_count(prof, z, x) > n / 2:
            cyc = (x, y, z); break
    out["cycle"] = cyc
    p, b = plurality(prof, alts), borda(prof, alts)
    out["plur"], out["borda"] = p, b
    out["rule_diff"] = winner(p) is not None and winner(b) is not None and winner(p) != winner(b)
    flip = None
    for z in alts:
        rest = [a for a in alts if a != z]; b2 = borda(prof, rest)
        for x, y in itertools.combinations(rest, 2):
            if (b[x] - b[y]) * (b2[x] - b2[y]) < 0:
                flip = (z, x, y, b2); break
        if flip: break
    out["iia"] = flip
    man = None; w = winner(b)
    if w:
        for i, true in enumerate(prof):
            for lie in itertools.permutations(alts):
                q = list(prof); q[i] = "".join(lie); w2 = winner(borda(q, alts))
                if w2 and w2 != w and prefers(true, w2, w):
                    man = (i, "".join(lie), w2); break
            if man: break
    out["manip"] = man
    return out


def live(ask):
    ss = st.session_state
    st.caption("AI 에이전트가 각자의 처지에서 선호를 정하고, 집계와 판정은 코드가 계산합니다. 실행할 때마다 결과가 달라질 수 있습니다.")
    n = st.radio("에이전트 수", [3, 4, 5], horizontal=True, key="live_n")
    alts = "ABC" if n == 3 else "ABCD"
    agents = list(PERSONAS)[:n]
    ss.setdefault("live_runs", [])
    if st.button("에이전트에게 선호 묻기", type="primary"):
        res = []
        with st.spinner("에이전트가 선호를 정하는 중입니다."):
            for name in agents:
                try:
                    rank, reason = ask_rank(ask, name, alts)
                except Exception as e:
                    st.error(f"AI 호출에 실패했습니다. 사이드바의 키와 모델 이름을 확인하세요. ({type(e).__name__})"); st.stop()
                if not rank:
                    st.error(f"{name}의 응답을 해석하지 못했습니다. 다시 눌러 주세요."); st.stop()
                res.append((name, rank, reason))
        ss.live_cur = (n, alts, res)
        o = analyze([r[1] for r in res], alts)
        ss.live_runs.append({"에이전트": n, "순환": "발생" if o["cycle"] else "없음",
                             "규칙별 승자": "다름" if o["rule_diff"] else "같음",
                             "의제에 따른 역전": "발생" if o["iia"] else "없음",
                             "거짓 표명의 이득": "가능" if o["manip"] else "없음"})
    cur = ss.get("live_cur")
    if not cur or cur[0] != n:
        st.info("버튼을 누르면 에이전트가 선호를 생성합니다.")
    else:
        _, alts, res = cur; prof = [r[1] for r in res]; o = analyze(prof, alts)
        st.subheader("① 에이전트의 주장과 선호")
        speak(res)
        st.subheader("② 쌍대 다수결")
        rows = [{"대결": f"{NAMES[a]} 대 {NAMES[b]}", "득표": f"{pair_count(prof, a, b)} : {len(prof) - pair_count(prof, a, b)}"}
                for a, b in itertools.combinations(alts, 2)]
        st.table(pd.DataFrame(rows).set_index("대결"))
        if o["cycle"]:
            st.error("순환 발생: " + " > ".join(NAMES[x] for x in o["cycle"]) + f" > {NAMES[o['cycle'][0]]}")
        elif o["condorcet"]:
            st.success(f"이번에는 순환이 없습니다. 모든 대결에서 이기는 대안: {NAMES[o['condorcet']]}")
        else:
            st.warning("모든 대결에서 이기는 대안이 없습니다(동률 포함).")
        st.subheader("③ 집계 규칙별 승자")
        l, r = st.columns(2)
        with l:
            w = winner(o["plur"]); st.markdown(f"**최다득표제** → {'**' + NAMES[w] + '**' if w else '동률'}"); score_chart(o["plur"], "1순위 득표")
        with r:
            w = winner(o["borda"]); st.markdown(f"**보르다 점수제** → {'**' + NAMES[w] + '**' if w else '동률'}"); score_chart(o["borda"], "보르다 점수")
        st.subheader("④ 의제 변경과 거짓 표명")
        if o["iia"]:
            z, x, y, _ = o["iia"]
            st.error(f"'{NAMES[z]}'를 의제에서 빼면 보르다 점수제에서 {NAMES[x]}와 {NAMES[y]}의 순위가 뒤집힙니다.")
        else:
            st.success("이번 선호에서는 대안 하나를 빼도 보르다 순위가 뒤집히지 않습니다.")
        if o["manip"]:
            i, lie, w2 = o["manip"]
            st.error(f"{res[i][0]}가 선호를 '{fmt(lie)}'로 거짓 표명하면 승자가 {NAMES[w2]}로 바뀌어 본인에게 유리해집니다.")
        else:
            st.success("이번 선호에서는 한 명의 거짓 표명으로 결과를 유리하게 바꿀 수 없습니다.")
    if ss.live_runs:
        st.divider()
        st.subheader("실행 기록")
        st.caption("문제가 매번 나타나지는 않습니다. 정리가 말하는 것은 어떤 규칙도 모든 경우에 문제를 피할 수는 없다는 점입니다.")
        df = pd.DataFrame(ss.live_runs); df.index = [f"{i + 1}회" for i in range(len(df))]
        st.table(df)
        if st.button("기록 지우기"):
            ss.live_runs = []; ss.pop("live_cur", None); st.rerun()


def render(ask=None):
    ss = st.session_state
    st.title("🗳️ 애로우 불가능성 정리 시연")
    if ask is not None:
        mode = st.radio("모드", ["설계된 선호 (시연)", "AI가 생성한 선호 (실시간)"], horizontal=True)
        if mode.startswith("AI"):
            live(ask)
            return
    st.caption("저출산 대책의 우선순위 정하기 · 에이전트 수를 늘려 가며 집계 규칙의 한계를 확인 · 선호는 시연용 설계, 집계는 코드가 계산")
    n = st.radio("에이전트 수", [3, 4, 5], horizontal=True,
                 format_func=lambda k: {3: "3명 · 다수결의 순환", 4: "4명 · 규칙과 의제에 따른 역전", 5: "5명 · 거짓 표명과 독재"}[k])
    key = f"arrow_step_{n}"
    ss.setdefault(key, 1)
    {3: case3, 4: case4, 5: case5}[n](ss[key])
    st.divider()
    l, r, _ = st.columns([1, 1, 4])
    if ss[key] < 4 and l.button("다음 단계 ▶", type="primary"):
        ss[key] += 1
        st.rerun()
    if ss[key] > 1 and r.button("처음부터"):
        ss[key] = 1
        st.rerun()
